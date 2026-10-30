"""
Testes das rotas de equipes (/teams).

Usam a fixture `client` (conftest.py): SQLite em memória, sem Aiven e sem internet.
"""

MERCEDES = {"name": "Mercedes", "country": "Germany"}


def criar_equipe(client, **alteracoes):
    """Cria uma equipe via API e devolve o JSON da resposta."""
    dados = {**MERCEDES, **alteracoes}
    resposta = client.post("/teams", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------- criação


def test_cria_equipe(client):
    resposta = client.post("/teams", json=MERCEDES)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] >= 1
    assert corpo["name"] == "Mercedes"
    assert corpo["country"] == "Germany"


def test_nome_duplicado_retorna_409(client):
    criar_equipe(client)

    resposta = client.post("/teams", json={**MERCEDES, "country": "UK"})

    assert resposta.status_code == 409


def test_campo_obrigatorio_ausente_retorna_422(client):
    resposta = client.post("/teams", json={"country": "Germany"})

    assert resposta.status_code == 422  # falta name


# ---------------------------------------------------------------- leitura


def test_busca_equipe_por_id(client):
    criada = criar_equipe(client)

    resposta = client.get(f"/teams/{criada['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criada


def test_equipe_inexistente_retorna_404(client):
    assert client.get("/teams/9999").status_code == 404


def test_lista_vazia_no_inicio(client):
    resposta = client.get("/teams")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_paginacao_skip_e_limit(client):
    for nome in ("Alpha", "Beta", "Gamma"):
        criar_equipe(client, name=nome)

    pagina1 = client.get("/teams", params={"skip": 0, "limit": 2}).json()
    pagina2 = client.get("/teams", params={"skip": 2, "limit": 2}).json()

    assert len(pagina1) == 2
    assert len(pagina2) == 1
    nomes = {t["name"] for t in pagina1 + pagina2}
    assert nomes == {"Alpha", "Beta", "Gamma"}


# ------------------------------------------------------------------ PATCH


def test_patch_parcial_preserva_campos_nao_enviados(client):
    criada = criar_equipe(client)

    resposta = client.patch(f"/teams/{criada['id']}", json={"country": "UK"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["country"] == "UK"        # mudou
    assert corpo["name"] == "Mercedes"     # preservado


def test_patch_inexistente_retorna_404(client):
    resposta = client.patch("/teams/9999", json={"country": "UK"})

    assert resposta.status_code == 404


def test_patch_para_nome_existente_retorna_409(client):
    criar_equipe(client, name="Mercedes")
    outra = criar_equipe(client, name="Ferrari")

    resposta = client.patch(f"/teams/{outra['id']}", json={"name": "Mercedes"})

    assert resposta.status_code == 409


def test_patch_mantendo_o_proprio_nome_nao_da_409(client):
    # Reenviar o nome atual não é duplicidade: a equipe não conflita consigo mesma.
    criada = criar_equipe(client)

    resposta = client.patch(f"/teams/{criada['id']}", json={"name": "Mercedes"})

    assert resposta.status_code == 200


# ----------------------------------------------------------------- DELETE


def test_apaga_equipe(client):
    criada = criar_equipe(client)

    resposta = client.delete(f"/teams/{criada['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/teams/{criada['id']}").status_code == 404


def test_apagar_inexistente_retorna_404(client):
    assert client.delete("/teams/9999").status_code == 404


def test_nao_apaga_equipe_com_resultados(client):
    """Equipe vinculada a um resultado não pode ser apagada (409)."""
    equipe = criar_equipe(client)
    piloto = client.post(
        "/drivers",
        json={"first_name": "Lewis", "last_name": "Hamilton", "acronym": "HAM"},
    ).json()
    circuito = client.post(
        "/circuits",
        json={"name": "Interlagos", "location": "Sao Paulo", "country": "Brazil"},
    ).json()
    corrida = client.post(
        "/races",
        json={
            "circuit_id": circuito["id"],
            "season": 2025,
            "round": 1,
            "name": "Sao Paulo GP",
            "date": "2025-11-09",
        },
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

    resposta = client.delete(f"/teams/{equipe['id']}")

    assert resposta.status_code == 409
    assert client.get(f"/teams/{equipe['id']}").status_code == 200