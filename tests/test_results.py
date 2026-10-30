"""
Testes das rotas de resultados (/results).

Usam a fixture `client` (conftest.py): SQLite em memória, sem Aiven e sem internet.
"""

import pytest


@pytest.fixture()
def base(client):
    """Cria o cenário mínimo: circuito, corrida, dois pilotos e duas equipes.

    Devolve um dicionário com o JSON de cada registro criado.
    """

    def post(rota, json):
        resposta = client.post(rota, json=json)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    circuito = post(
        "/circuits",
        {"name": "Interlagos", "location": "Sao Paulo", "country": "Brazil"},
    )
    return {
        "corrida": post(
            "/races",
            {
                "circuit_id": circuito["id"],
                "season": 2025,
                "round": 1,
                "name": "Sao Paulo GP",
                "date": "2025-11-09",
            },
        ),
        "corrida2": post(
            "/races",
            {
                "circuit_id": circuito["id"],
                "season": 2025,
                "round": 2,
                "name": "Las Vegas GP",
                "date": "2025-11-22",
            },
        ),
        "piloto1": post(
            "/drivers",
            {"first_name": "Lewis", "last_name": "Hamilton", "acronym": "HAM"},
        ),
        "piloto2": post(
            "/drivers",
            {"first_name": "Max", "last_name": "Verstappen", "acronym": "VER"},
        ),
        "equipe1": post("/teams", {"name": "Mercedes", "country": "Germany"}),
        "equipe2": post("/teams", {"name": "Red Bull", "country": "Austria"}),
    }


def dados_resultado(base, **alteracoes):
    """Monta o JSON de um resultado válido (piloto1, equipe1, corrida)."""
    padrao = {
        "race_id": base["corrida"]["id"],
        "driver_id": base["piloto1"]["id"],
        "team_id": base["equipe1"]["id"],
        "grid": 1,
        "position": 1,
        "points": 25,
        "status": "Finished",
    }
    return {**padrao, **alteracoes}


def criar_resultado(client, base, **alteracoes):
    """Cria um resultado via API e devolve o JSON da resposta."""
    resposta = client.post("/results", json=dados_resultado(base, **alteracoes))
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------- criação


def test_cria_resultado(client, base):
    resposta = client.post("/results", json=dados_resultado(base))

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] >= 1
    assert corpo["race_id"] == base["corrida"]["id"]
    assert corpo["driver_id"] == base["piloto1"]["id"]
    assert corpo["team_id"] == base["equipe1"]["id"]
    assert corpo["position"] == 1
    assert corpo["points"] == 25


def test_piloto_que_nao_terminou_tem_position_nula(client, base):
    # position None = não terminou; points assume o padrão 0.
    resposta = client.post(
        "/results",
        json={
            "race_id": base["corrida"]["id"],
            "driver_id": base["piloto1"]["id"],
            "team_id": base["equipe1"]["id"],
            "position": None,
            "status": "Retired",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["position"] is None
    assert resposta.json()["points"] == 0


@pytest.mark.parametrize(
    "campo, id_inexistente",
    [
        ("race_id", 9999),
        ("driver_id", 9999),
        ("team_id", 9999),
    ],
)
def test_referencia_inexistente_retorna_404(client, base, campo, id_inexistente):
    resposta = client.post(
        "/results", json=dados_resultado(base, **{campo: id_inexistente})
    )

    assert resposta.status_code == 404


def test_corrida_e_piloto_duplicados_retornam_409(client, base):
    criar_resultado(client, base)

    # Mesmo piloto na mesma corrida, mesmo com outra equipe e posição.
    resposta = client.post(
        "/results",
        json=dados_resultado(base, team_id=base["equipe2"]["id"], position=2),
    )

    assert resposta.status_code == 409


def test_mesmo_piloto_em_outra_corrida_e_permitido(client, base):
    criar_resultado(client, base)

    resposta = client.post(
        "/results", json=dados_resultado(base, race_id=base["corrida2"]["id"])
    )

    assert resposta.status_code == 201


def test_outro_piloto_na_mesma_corrida_e_permitido(client, base):
    criar_resultado(client, base)

    resposta = client.post(
        "/results",
        json=dados_resultado(base, driver_id=base["piloto2"]["id"], position=2),
    )

    assert resposta.status_code == 201


# ------------------------------------------------------------- validação


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("grid", -1),        # abaixo de 0
        ("grid", 31),        # acima de 30
        ("position", 0),     # abaixo de 1
        ("position", 31),    # acima de 30
        ("points", -1),      # pontos não podem ser negativos
    ],
)
def test_dados_invalidos_retornam_422(client, base, campo, valor):
    resposta = client.post("/results", json=dados_resultado(base, **{campo: valor}))

    assert resposta.status_code == 422


def test_campo_obrigatorio_ausente_retorna_422(client, base):
    dados = dados_resultado(base)
    del dados["team_id"]

    resposta = client.post("/results", json=dados)

    assert resposta.status_code == 422


# ---------------------------------------------------------------- leitura


def test_busca_resultado_por_id(client, base):
    criado = criar_resultado(client, base)

    resposta = client.get(f"/results/{criado['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criado


def test_resultado_inexistente_retorna_404(client):
    assert client.get("/results/9999").status_code == 404


def test_lista_vazia_no_inicio(client):
    resposta = client.get("/results")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_paginacao_skip_e_limit(client, base):
    criar_resultado(client, base, driver_id=base["piloto1"]["id"], position=1)
    criar_resultado(client, base, driver_id=base["piloto2"]["id"], position=2)
    criar_resultado(
        client, base, race_id=base["corrida2"]["id"], position=1
    )

    pagina1 = client.get("/results", params={"skip": 0, "limit": 2}).json()
    pagina2 = client.get("/results", params={"skip": 2, "limit": 2}).json()

    assert len(pagina1) == 2
    assert len(pagina2) == 1
    ids = {r["id"] for r in pagina1 + pagina2}
    assert len(ids) == 3  # nenhum repetido


# ------------------------------------------------------------------ PATCH


def test_patch_parcial_preserva_campos_nao_enviados(client, base):
    criado = criar_resultado(client, base)

    resposta = client.patch(f"/results/{criado['id']}", json={"points": 18})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["points"] == 18                              # mudou
    assert corpo["position"] == 1                             # preservado
    assert corpo["grid"] == 1                                 # preservado
    assert corpo["status"] == "Finished"                      # preservado
    assert corpo["race_id"] == base["corrida"]["id"]          # preservado
    assert corpo["driver_id"] == base["piloto1"]["id"]        # preservado


def test_patch_inexistente_retorna_404(client):
    resposta = client.patch("/results/9999", json={"points": 1})

    assert resposta.status_code == 404


def test_patch_para_par_existente_retorna_409(client, base):
    criar_resultado(client, base, driver_id=base["piloto1"]["id"])
    outro = criar_resultado(
        client, base, driver_id=base["piloto2"]["id"], position=2
    )

    # Muda só o piloto: o valor FINAL (corrida, piloto1) já existe.
    resposta = client.patch(
        f"/results/{outro['id']}", json={"driver_id": base["piloto1"]["id"]}
    )

    assert resposta.status_code == 409


def test_patch_mantendo_o_proprio_par_nao_da_409(client, base):
    criado = criar_resultado(client, base)

    # Reenviar o mesmo (race_id, driver_id): o resultado não conflita consigo mesmo.
    resposta = client.patch(
        f"/results/{criado['id']}",
        json={"race_id": base["corrida"]["id"], "driver_id": base["piloto1"]["id"]},
    )

    assert resposta.status_code == 200


@pytest.mark.parametrize("campo", ["race_id", "driver_id", "team_id"])
def test_patch_com_referencia_inexistente_retorna_404(client, base, campo):
    criado = criar_resultado(client, base)

    resposta = client.patch(f"/results/{criado['id']}", json={campo: 9999})

    assert resposta.status_code == 404


def test_patch_com_valor_invalido_retorna_422(client, base):
    criado = criar_resultado(client, base)

    resposta = client.patch(f"/results/{criado['id']}", json={"position": 0})

    assert resposta.status_code == 422


# ----------------------------------------------------------------- DELETE


def test_apaga_resultado(client, base):
    criado = criar_resultado(client, base)

    resposta = client.delete(f"/results/{criado['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/results/{criado['id']}").status_code == 404


def test_apagar_inexistente_retorna_404(client):
    assert client.delete("/results/9999").status_code == 404


def test_apagar_resultado_nao_apaga_piloto_corrida_nem_equipe(client, base):
    # Resultado é a ponta da cadeia: apagá-lo não pode afetar quem ele referencia.
    criado = criar_resultado(client, base)

    client.delete(f"/results/{criado['id']}")

    assert client.get(f"/drivers/{base['piloto1']['id']}").status_code == 200
    assert client.get(f"/races/{base['corrida']['id']}").status_code == 200
    assert client.get(f"/teams/{base['equipe1']['id']}").status_code == 200