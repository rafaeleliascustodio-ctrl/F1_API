"""
Testes das rotas de pilotos (/drivers).

Todos usam a fixture `client` (conftest.py): banco SQLite em memória,
novo a cada teste. Nada toca o Aiven nem a internet.
"""

import pytest

# Piloto "padrão" reutilizado em vários testes.
HAMILTON = {
    "first_name": "Lewis",
    "last_name": "Hamilton",
    "acronym": "HAM",
    "number": 44,
    "country_code": "GBR",
}


def criar_piloto(client, **alteracoes):
    """Cria um piloto via API e devolve o JSON da resposta.

    `alteracoes` sobrescreve campos do HAMILTON (ex.: acronym="VER").
    """
    dados = {**HAMILTON, **alteracoes}
    resposta = client.post("/drivers", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------- criação


def test_cria_piloto(client):
    resposta = client.post("/drivers", json=HAMILTON)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] >= 1  # o banco gerou o id
    assert corpo["acronym"] == "HAM"
    assert corpo["number"] == 44


def test_cria_piloto_so_com_campos_obrigatorios(client):
    # number e country_code são opcionais.
    resposta = client.post(
        "/drivers",
        json={"first_name": "Max", "last_name": "Verstappen", "acronym": "VER"},
    )

    assert resposta.status_code == 201
    assert resposta.json()["number"] is None
    assert resposta.json()["country_code"] is None


def test_sigla_duplicada_retorna_409(client):
    criar_piloto(client)

    resposta = client.post("/drivers", json={**HAMILTON, "first_name": "Outro"})

    assert resposta.status_code == 409


# ------------------------------------------------------------- validação


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("acronym", "ham"),        # minúscula
        ("acronym", "HA"),         # curta demais
        ("acronym", "HAMI"),       # longa demais
        ("country_code", "gb"),    # fora do padrão ^[A-Z]{3}$
        ("number", 0),             # abaixo de 1
        ("number", 100),           # acima de 99
    ],
)
def test_dados_invalidos_retornam_422(client, campo, valor):
    resposta = client.post("/drivers", json={**HAMILTON, campo: valor})

    assert resposta.status_code == 422


def test_campo_obrigatorio_ausente_retorna_422(client):
    resposta = client.post("/drivers", json={"first_name": "Sem", "acronym": "SEM"})

    assert resposta.status_code == 422  # falta last_name


# ---------------------------------------------------------------- leitura


def test_busca_piloto_por_id(client):
    criado = criar_piloto(client)

    resposta = client.get(f"/drivers/{criado['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criado


def test_piloto_inexistente_retorna_404(client):
    assert client.get("/drivers/9999").status_code == 404


def test_lista_vazia_no_inicio(client):
    resposta = client.get("/drivers")

    assert resposta.status_code == 200
    assert resposta.json() == []


# -------------------------------------------------------------- paginação


def test_paginacao_skip_e_limit(client):
    for sigla in ("AAA", "BBB", "CCC"):
        criar_piloto(client, acronym=sigla, number=None)

    pagina1 = client.get("/drivers", params={"skip": 0, "limit": 2}).json()
    pagina2 = client.get("/drivers", params={"skip": 2, "limit": 2}).json()

    assert len(pagina1) == 2
    assert len(pagina2) == 1
    # As duas páginas juntas cobrem os 3 pilotos, sem repetir nenhum.
    siglas = {d["acronym"] for d in pagina1 + pagina2}
    assert siglas == {"AAA", "BBB", "CCC"}


# ------------------------------------------------------------------ PATCH


def test_patch_parcial_preserva_campos_nao_enviados(client):
    criado = criar_piloto(client)

    resposta = client.patch(f"/drivers/{criado['id']}", json={"last_name": "Novo"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["last_name"] == "Novo"       # mudou
    assert corpo["first_name"] == "Lewis"     # preservado
    assert corpo["acronym"] == "HAM"          # preservado
    assert corpo["number"] == 44              # preservado


def test_patch_inexistente_retorna_404(client):
    resposta = client.patch("/drivers/9999", json={"last_name": "X"})

    assert resposta.status_code == 404


def test_patch_para_sigla_existente_retorna_409(client):
    criar_piloto(client, acronym="HAM")
    outro = criar_piloto(client, acronym="VER", number=1)

    resposta = client.patch(f"/drivers/{outro['id']}", json={"acronym": "HAM"})

    assert resposta.status_code == 409


def test_patch_com_valor_invalido_retorna_422(client):
    criado = criar_piloto(client)

    resposta = client.patch(f"/drivers/{criado['id']}", json={"acronym": "x"})

    assert resposta.status_code == 422


# ----------------------------------------------------------------- DELETE


def test_apaga_piloto(client):
    criado = criar_piloto(client)

    resposta = client.delete(f"/drivers/{criado['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/drivers/{criado['id']}").status_code == 404


def test_apagar_inexistente_retorna_404(client):
    assert client.delete("/drivers/9999").status_code == 404


def test_nao_apaga_piloto_com_resultados(client):
    """Piloto vinculado a um resultado não pode ser apagado (409)."""
    piloto = criar_piloto(client)

    # Monta a cadeia mínima exigida por um resultado: circuito, equipe, corrida.
    circuito = client.post(
        "/circuits",
        json={"name": "Interlagos", "location": "Sao Paulo", "country": "Brazil"},
    ).json()
    equipe = client.post(
        "/teams", json={"name": "Mercedes", "country": "Germany"}
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

    resposta = client.delete(f"/drivers/{piloto['id']}")

    assert resposta.status_code == 409
    # O piloto continua existindo.
    assert client.get(f"/drivers/{piloto['id']}").status_code == 200