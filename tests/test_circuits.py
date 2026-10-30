"""
Testes das rotas de circuitos (/circuits).

Usam a fixture `client` (conftest.py): SQLite em memória, sem Aiven e sem internet.
"""

INTERLAGOS = {"name": "Interlagos", "location": "Sao Paulo", "country": "Brazil"}


def criar_circuito(client, **alteracoes):
    """Cria um circuito via API e devolve o JSON da resposta."""
    dados = {**INTERLAGOS, **alteracoes}
    resposta = client.post("/circuits", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------- criação


def test_cria_circuito(client):
    resposta = client.post("/circuits", json=INTERLAGOS)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] >= 1
    assert corpo["name"] == "Interlagos"
    assert corpo["location"] == "Sao Paulo"
    assert corpo["country"] == "Brazil"


def test_nome_duplicado_retorna_409(client):
    criar_circuito(client)

    resposta = client.post("/circuits", json={**INTERLAGOS, "country": "Outro"})

    assert resposta.status_code == 409


def test_campo_obrigatorio_ausente_retorna_422(client):
    resposta = client.post("/circuits", json={"location": "Sao Paulo"})

    assert resposta.status_code == 422  # falta name


# ---------------------------------------------------------------- leitura


def test_busca_circuito_por_id(client):
    criado = criar_circuito(client)

    resposta = client.get(f"/circuits/{criado['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criado


def test_circuito_inexistente_retorna_404(client):
    assert client.get("/circuits/9999").status_code == 404


def test_lista_vazia_no_inicio(client):
    resposta = client.get("/circuits")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_paginacao_skip_e_limit(client):
    for nome in ("Pista A", "Pista B", "Pista C"):
        criar_circuito(client, name=nome)

    pagina1 = client.get("/circuits", params={"skip": 0, "limit": 2}).json()
    pagina2 = client.get("/circuits", params={"skip": 2, "limit": 2}).json()

    assert len(pagina1) == 2
    assert len(pagina2) == 1
    nomes = {c["name"] for c in pagina1 + pagina2}
    assert nomes == {"Pista A", "Pista B", "Pista C"}


# ------------------------------------------------------------------ PATCH


def test_patch_parcial_preserva_campos_nao_enviados(client):
    criado = criar_circuito(client)

    resposta = client.patch(f"/circuits/{criado['id']}", json={"country": "Brasil"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["country"] == "Brasil"       # mudou
    assert corpo["name"] == "Interlagos"      # preservado
    assert corpo["location"] == "Sao Paulo"   # preservado


def test_patch_inexistente_retorna_404(client):
    resposta = client.patch("/circuits/9999", json={"country": "X"})

    assert resposta.status_code == 404


def test_patch_para_nome_existente_retorna_409(client):
    criar_circuito(client, name="Interlagos")
    outro = criar_circuito(client, name="Monza")

    resposta = client.patch(f"/circuits/{outro['id']}", json={"name": "Interlagos"})

    assert resposta.status_code == 409


def test_patch_mantendo_o_proprio_nome_nao_da_409(client):
    criado = criar_circuito(client)

    resposta = client.patch(f"/circuits/{criado['id']}", json={"name": "Interlagos"})

    assert resposta.status_code == 200


# ----------------------------------------------------------------- DELETE


def test_apaga_circuito(client):
    criado = criar_circuito(client)

    resposta = client.delete(f"/circuits/{criado['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/circuits/{criado['id']}").status_code == 404


def test_apagar_inexistente_retorna_404(client):
    assert client.delete("/circuits/9999").status_code == 404


def test_nao_apaga_circuito_com_corridas(client):
    """Circuito vinculado a uma corrida não pode ser apagado (409)."""
    circuito = criar_circuito(client)
    corrida = client.post(
        "/races",
        json={
            "circuit_id": circuito["id"],
            "season": 2025,
            "round": 1,
            "name": "Sao Paulo GP",
            "date": "2025-11-09",
        },
    )
    assert corrida.status_code == 201, corrida.text

    resposta = client.delete(f"/circuits/{circuito['id']}")

    assert resposta.status_code == 409
    assert client.get(f"/circuits/{circuito['id']}").status_code == 200