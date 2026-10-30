"""
Testes das rotas /openf1 (app/routes/openf1.py).

Mock nas funções do service: aqui testamos só a camada de rotas.
Nenhum teste acessa a internet nem o banco real.
"""

import pytest

from app.services import openf1_service as svc


@pytest.fixture(autouse=True)
def bloquear_rede(monkeypatch):
    """Proíbe requests.get real: se uma rota escapar do mock, o teste falha."""

    def proibido(*args, **kwargs):
        raise AssertionError("requests.get real chamado: simule o service!")

    monkeypatch.setattr(svc.requests, "get", proibido)


@pytest.fixture()
def simular(monkeypatch):
    """Substitui uma função do service por uma falsa.

    Uso: chamadas = simular("get_meetings", retorno=[...])
         chamadas = simular("get_meetings", erro=svc.OpenF1Error("..."))
    Devolve a lista `chamadas`, com (args, kwargs) de cada chamada recebida.
    """

    def configurar(nome, retorno=None, erro=None):
        chamadas = []

        def falsa(*args, **kwargs):
            chamadas.append((args, kwargs))
            if erro is not None:
                raise erro
            return retorno

        monkeypatch.setattr(svc, nome, falsa)
        return chamadas

    return configurar


# -------------------------------------------------------------- /meetings


def test_meetings_devolve_os_dados_do_service(client, simular):
    dados = [{"meeting_key": 1264, "name": "Abu Dhabi Grand Prix"}]
    chamadas = simular("get_meetings", retorno=dados)

    resposta = client.get("/openf1/meetings", params={"year": 2025})

    assert resposta.status_code == 200
    assert resposta.json() == dados
    assert chamadas == [((2025,), {})]  # a rota repassou o ano ao service


def test_meetings_lista_vazia_retorna_200(client, simular):
    simular("get_meetings", retorno=[])

    resposta = client.get("/openf1/meetings", params={"year": 2030})

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_meetings_erro_do_service_vira_502(client, simular):
    simular("get_meetings", erro=svc.OpenF1Error("Limite de requisições atingido."))

    resposta = client.get("/openf1/meetings", params={"year": 2025})

    assert resposta.status_code == 502
    assert resposta.json()["detail"] == "Limite de requisições atingido."


@pytest.mark.parametrize("params", [{}, {"year": 2022}, {"year": 2101}, {"year": "abc"}])
def test_meetings_year_invalido_retorna_422(client, simular, params):
    chamadas = simular("get_meetings", retorno=[])

    resposta = client.get("/openf1/meetings", params=params)

    assert resposta.status_code == 422
    assert chamadas == []  # a validação barrou antes de chamar o service


# -------------------------------------------------------------- /sessions


def test_sessions_sem_filtros_repassa_none(client, simular):
    chamadas = simular("get_sessions", retorno=[])

    resposta = client.get("/openf1/sessions")

    assert resposta.status_code == 200
    assert chamadas == [((None, None, None), {})]


def test_sessions_repassa_todos_os_filtros(client, simular):
    chamadas = simular("get_sessions", retorno=[{"session_key": 9839}])

    resposta = client.get(
        "/openf1/sessions",
        params={"year": 2025, "session_name": "Race", "meeting_key": 1264},
    )

    assert resposta.status_code == 200
    assert resposta.json() == [{"session_key": 9839}]
    assert chamadas == [((2025, "Race", 1264), {})]


def test_sessions_erro_do_service_vira_502(client, simular):
    simular("get_sessions", erro=svc.OpenF1Error("falhou"))

    assert client.get("/openf1/sessions").status_code == 502


@pytest.mark.parametrize("params", [{"year": 2022}, {"meeting_key": 0}])
def test_sessions_filtro_invalido_retorna_422(client, simular, params):
    simular("get_sessions", retorno=[])

    assert client.get("/openf1/sessions", params=params).status_code == 422


# ---------------------------------------- /drivers e /session-results

ROTAS_POR_SESSAO = [
    ("/openf1/drivers", "get_drivers"),
    ("/openf1/session-results", "get_session_results"),
]


@pytest.mark.parametrize("rota, funcao", ROTAS_POR_SESSAO)
def test_rotas_por_sessao_devolvem_os_dados(client, simular, rota, funcao):
    dados = [{"qualquer": "coisa"}]
    chamadas = simular(funcao, retorno=dados)

    resposta = client.get(rota, params={"session_key": 9839})

    assert resposta.status_code == 200
    assert resposta.json() == dados
    assert chamadas == [((9839,), {})]


@pytest.mark.parametrize("rota, funcao", ROTAS_POR_SESSAO)
def test_rotas_por_sessao_erro_do_service_vira_502(client, simular, rota, funcao):
    simular(funcao, erro=svc.OpenF1Error("A OpenF1 respondeu com status 500."))

    resposta = client.get(rota, params={"session_key": 9839})

    assert resposta.status_code == 502
    assert resposta.json()["detail"] == "A OpenF1 respondeu com status 500."


@pytest.mark.parametrize("rota, funcao", ROTAS_POR_SESSAO)
@pytest.mark.parametrize("params", [{}, {"session_key": 0}, {"session_key": -5}])
def test_rotas_por_sessao_session_key_invalido_retorna_422(
    client, simular, rota, funcao, params
):
    chamadas = simular(funcao, retorno=[])

    resposta = client.get(rota, params=params)

    assert resposta.status_code == 422
    assert chamadas == []