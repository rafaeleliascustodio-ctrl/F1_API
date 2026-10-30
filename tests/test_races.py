"""
Testes das rotas de corridas (/races) e de temporadas (/seasons).

Usam a fixture `client` (conftest.py): SQLite em memória, sem Aiven e sem internet.
"""

import pytest


@pytest.fixture()
def circuito(client):
    """Cria um circuito e devolve o JSON. Toda corrida precisa de um."""
    resposta = client.post(
        "/circuits",
        json={"name": "Interlagos", "location": "Sao Paulo", "country": "Brazil"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def dados_corrida(circuito, **alteracoes):
    """Monta o JSON de uma corrida válida; `alteracoes` sobrescreve campos."""
    base = {
        "circuit_id": circuito["id"],
        "season": 2025,
        "round": 1,
        "name": "Sao Paulo GP",
        "date": "2025-11-09",
    }
    return {**base, **alteracoes}


def criar_corrida(client, circuito, **alteracoes):
    """Cria uma corrida via API e devolve o JSON da resposta."""
    resposta = client.post("/races", json=dados_corrida(circuito, **alteracoes))
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------- criação


def test_cria_corrida(client, circuito):
    resposta = client.post("/races", json=dados_corrida(circuito))

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] >= 1
    assert corpo["circuit_id"] == circuito["id"]
    assert corpo["season"] == 2025
    assert corpo["round"] == 1
    assert corpo["date"] == "2025-11-09"


def test_circuito_inexistente_retorna_404(client):
    resposta = client.post(
        "/races",
        json={
            "circuit_id": 9999,
            "season": 2025,
            "round": 1,
            "name": "GP Fantasma",
            "date": "2025-01-01",
        },
    )

    assert resposta.status_code == 404


def test_temporada_e_rodada_duplicadas_retornam_409(client, circuito):
    criar_corrida(client, circuito)

    resposta = client.post("/races", json=dados_corrida(circuito, name="Outro nome"))

    assert resposta.status_code == 409


def test_mesma_rodada_em_outra_temporada_e_permitida(client, circuito):
    # A unicidade é do PAR (season, round), não de cada campo isolado.
    criar_corrida(client, circuito, season=2024, round=1)

    resposta = client.post("/races", json=dados_corrida(circuito, season=2025, round=1))

    assert resposta.status_code == 201


# ------------------------------------------------------------- validação


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("season", 1949),           # abaixo de 1950
        ("season", 2101),           # acima de 2100
        ("round", 0),               # abaixo de 1
        ("round", 31),              # acima de 30
        ("date", "nao-e-uma-data"),  # formato inválido
    ],
)
def test_dados_invalidos_retornam_422(client, circuito, campo, valor):
    resposta = client.post("/races", json=dados_corrida(circuito, **{campo: valor}))

    assert resposta.status_code == 422


def test_campo_obrigatorio_ausente_retorna_422(client, circuito):
    dados = dados_corrida(circuito)
    del dados["name"]

    resposta = client.post("/races", json=dados)

    assert resposta.status_code == 422


# ---------------------------------------------------------------- leitura


def test_busca_corrida_por_id(client, circuito):
    criada = criar_corrida(client, circuito)

    resposta = client.get(f"/races/{criada['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criada


def test_corrida_inexistente_retorna_404(client):
    assert client.get("/races/9999").status_code == 404


def test_lista_vazia_no_inicio(client):
    resposta = client.get("/races")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_paginacao_skip_e_limit(client, circuito):
    for rodada in (1, 2, 3):
        criar_corrida(client, circuito, round=rodada, name=f"GP {rodada}")

    pagina1 = client.get("/races", params={"skip": 0, "limit": 2}).json()
    pagina2 = client.get("/races", params={"skip": 2, "limit": 2}).json()

    assert len(pagina1) == 2
    assert len(pagina2) == 1
    rodadas = {r["round"] for r in pagina1 + pagina2}
    assert rodadas == {1, 2, 3}


# ------------------------------------------------------------------ PATCH


def test_patch_parcial_preserva_campos_nao_enviados(client, circuito):
    criada = criar_corrida(client, circuito)

    resposta = client.patch(f"/races/{criada['id']}", json={"name": "Novo nome"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["name"] == "Novo nome"        # mudou
    assert corpo["season"] == 2025             # preservado
    assert corpo["round"] == 1                 # preservado
    assert corpo["date"] == "2025-11-09"       # preservado
    assert corpo["circuit_id"] == circuito["id"]


def test_patch_inexistente_retorna_404(client):
    resposta = client.patch("/races/9999", json={"name": "X"})

    assert resposta.status_code == 404


def test_patch_para_rodada_existente_retorna_409(client, circuito):
    criar_corrida(client, circuito, round=1)
    outra = criar_corrida(client, circuito, round=2, name="GP 2")

    # Muda só a rodada: o valor FINAL (2025, 1) já pertence à outra corrida.
    resposta = client.patch(f"/races/{outra['id']}", json={"round": 1})

    assert resposta.status_code == 409


def test_patch_para_temporada_que_colide_retorna_409(client, circuito):
    criar_corrida(client, circuito, season=2025, round=1)
    outra = criar_corrida(client, circuito, season=2024, round=1, name="GP 2024")

    # Muda só a temporada: o valor FINAL (2025, 1) já existe.
    resposta = client.patch(f"/races/{outra['id']}", json={"season": 2025})

    assert resposta.status_code == 409


def test_patch_mantendo_a_propria_rodada_nao_da_409(client, circuito):
    criada = criar_corrida(client, circuito)

    # Reenviar o mesmo (season, round): a corrida não conflita consigo mesma.
    resposta = client.patch(
        f"/races/{criada['id']}", json={"season": 2025, "round": 1}
    )

    assert resposta.status_code == 200


def test_patch_com_circuito_inexistente_retorna_404(client, circuito):
    criada = criar_corrida(client, circuito)

    resposta = client.patch(f"/races/{criada['id']}", json={"circuit_id": 9999})

    assert resposta.status_code == 404


# ----------------------------------------------------------------- DELETE


def test_apaga_corrida(client, circuito):
    criada = criar_corrida(client, circuito)

    resposta = client.delete(f"/races/{criada['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/races/{criada['id']}").status_code == 404


def test_apagar_inexistente_retorna_404(client):
    assert client.delete("/races/9999").status_code == 404


def test_nao_apaga_corrida_com_resultados(client, circuito):
    """Corrida vinculada a um resultado não pode ser apagada (409)."""
    corrida = criar_corrida(client, circuito)
    piloto = client.post(
        "/drivers",
        json={"first_name": "Lewis", "last_name": "Hamilton", "acronym": "HAM"},
    ).json()
    equipe = client.post(
        "/teams", json={"name": "Mercedes", "country": "Germany"}
    ).json()
    resultado = client.post(
        "/results",
        json={
            "race_id": corrida["id"],
            "driver_id": piloto["id"],
            "team_id": equipe["id"],
            "grid": 1,
            "position": 1,
            "points": 25,
            "status": "Finished",
        },
    )
    assert resultado.status_code == 201, resultado.text

    resposta = client.delete(f"/races/{corrida['id']}")

    assert resposta.status_code == 409
    assert client.get(f"/races/{corrida['id']}").status_code == 200


# --------------------------------------------------------------- /seasons


def test_seasons_vazio_no_inicio(client):
    resposta = client.get("/seasons")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_seasons_lista_anos_distintos(client, circuito):
    # Duas corridas em 2025 e uma em 2024: o ano 2025 não pode repetir.
    criar_corrida(client, circuito, season=2025, round=1, name="GP 1")
    criar_corrida(client, circuito, season=2025, round=2, name="GP 2")
    criar_corrida(client, circuito, season=2024, round=1, name="GP 2024")

    resposta = client.get("/seasons")

    assert resposta.status_code == 200
    anos = resposta.json()
    assert len(anos) == 2  # distintos, sem repetição
    assert set(anos) == {2024, 2025}