"""
Testes do service da OpenF1 (app/services/openf1_service.py).

Nenhum teste acessa a internet: `requests.get` é trocado por uma função falsa.
Uma fixture automática garante que, se algum teste esquecer de simular a
resposta, ele FALHA em vez de chamar a OpenF1 de verdade.
"""

import pytest
import requests

from app.core.config import settings
from app.services import openf1_service as svc


class RespostaFalsa:
    """Imita o objeto Response do requests (só o que o service usa)."""

    def __init__(self, status_code=200, dados=None, json_invalido=False):
        self.status_code = status_code
        self._dados = dados
        self._json_invalido = json_invalido

    def json(self):
        if self._json_invalido:
            raise ValueError("corpo não é JSON")
        return self._dados


@pytest.fixture(autouse=True)
def bloquear_rede(monkeypatch):
    """Roda em TODO teste deste arquivo: proíbe chamadas reais à OpenF1."""

    def proibido(*args, **kwargs):
        raise AssertionError("requests.get real chamado: simule a resposta!")

    monkeypatch.setattr(svc.requests, "get", proibido)


@pytest.fixture()
def simular(monkeypatch):
    """Devolve uma função que define a resposta (ou o erro) do requests.get.

    A função devolve a lista `chamadas`, onde cada chamada feita ao
    requests.get fica registrada (url, params, timeout).
    """

    def configurar(resposta=None, erro=None):
        chamadas = []

        def falso_get(url, params=None, timeout=None):
            chamadas.append({"url": url, "params": params, "timeout": timeout})
            if erro is not None:
                raise erro
            return resposta

        monkeypatch.setattr(svc.requests, "get", falso_get)
        return chamadas

    return configurar


# ------------------------------------------------------------------ _get


def test_get_devolve_a_lista_da_resposta(simular):
    simular(RespostaFalsa(200, [{"a": 1}, {"a": 2}]))

    assert svc._get("meetings", {"year": 2025}) == [{"a": 1}, {"a": 2}]


def test_get_monta_url_timeout_e_remove_params_none(simular):
    chamadas = simular(RespostaFalsa(200, []))

    svc._get("sessions", {"year": 2025, "session_name": None})

    assert len(chamadas) == 1
    assert chamadas[0]["url"] == f"{settings.OPENF1_BASE_URL}/sessions"
    assert chamadas[0]["timeout"] == settings.OPENF1_TIMEOUT
    assert chamadas[0]["params"] == {"year": 2025}  # o None foi removido


def test_get_trata_404_como_lista_vazia(simular):
    # Comportamento observado (não documentado): sem resultados, a OpenF1 dá 404.
    simular(RespostaFalsa(404))

    assert svc._get("meetings", {"year": 2030}) == []


def test_get_429_levanta_openf1error(simular):
    simular(RespostaFalsa(429))

    with pytest.raises(svc.OpenF1Error, match="Limite"):
        svc._get("meetings")


@pytest.mark.parametrize("status", [403, 500, 503])
def test_get_status_inesperado_levanta_openf1error(simular, status):
    simular(RespostaFalsa(status))

    with pytest.raises(svc.OpenF1Error, match=str(status)):
        svc._get("meetings")


@pytest.mark.parametrize(
    "erro",
    [requests.ConnectionError("sem rede"), requests.Timeout("demorou")],
)
def test_get_falha_de_rede_levanta_openf1error(simular, erro):
    simular(erro=erro)

    with pytest.raises(svc.OpenF1Error) as info:
        svc._get("meetings")

    # `raise ... from exc` preserva o erro original como causa.
    assert info.value.__cause__ is erro


def test_get_json_invalido_levanta_openf1error(simular):
    simular(RespostaFalsa(200, json_invalido=True))

    with pytest.raises(svc.OpenF1Error, match="JSON"):
        svc._get("meetings")


def test_get_resposta_que_nao_e_lista_levanta_openf1error(simular):
    simular(RespostaFalsa(200, {"detail": "objeto, não lista"}))

    with pytest.raises(svc.OpenF1Error, match="Formato"):
        svc._get("meetings")


# ------------------------------------------------------- funções públicas


def test_get_meetings_renomeia_campos(simular):
    chamadas = simular(
        RespostaFalsa(
            200,
            [
                {
                    "meeting_key": 1264,
                    "year": 2025,
                    "meeting_name": "Abu Dhabi Grand Prix",
                    "circuit_key": 70,
                    "circuit_short_name": "Yas Marina",
                    "location": "Yas Island",
                    "country_name": "United Arab Emirates",
                    "date_start": "2025-12-05T09:30:00+00:00",
                    "campo_extra": "deve ser ignorado",
                }
            ],
        )
    )

    resultado = svc.get_meetings(2025)

    assert chamadas[0]["url"].endswith("/meetings")
    assert chamadas[0]["params"] == {"year": 2025}
    assert resultado == [
        {
            "meeting_key": 1264,
            "year": 2025,
            "name": "Abu Dhabi Grand Prix",
            "circuit_key": 70,
            "circuit_name": "Yas Marina",
            "location": "Yas Island",
            "country_name": "United Arab Emirates",
            "date_start": "2025-12-05T09:30:00+00:00",
        }
    ]


def test_get_meetings_sem_resultados_devolve_lista_vazia(simular):
    simular(RespostaFalsa(404))

    assert svc.get_meetings(2030) == []


def test_get_meetings_propaga_openf1error(simular):
    simular(RespostaFalsa(429))

    with pytest.raises(svc.OpenF1Error):
        svc.get_meetings(2025)


def test_get_sessions_so_envia_filtros_informados(simular):
    chamadas = simular(RespostaFalsa(200, []))

    svc.get_sessions(year=2025, session_name="Race")

    assert chamadas[0]["url"].endswith("/sessions")
    # meeting_key não foi informado: não pode ir na consulta.
    assert chamadas[0]["params"] == {"year": 2025, "session_name": "Race"}


def test_get_sessions_renomeia_campos(simular):
    simular(
        RespostaFalsa(
            200,
            [
                {
                    "session_key": 9839,
                    "meeting_key": 1264,
                    "session_name": "Race",
                    "session_type": "Race",
                    "date_start": "2025-12-07T13:00:00+00:00",
                    "year": 2025,
                    "campo_extra": "ignorado",
                }
            ],
        )
    )

    assert svc.get_sessions(year=2025) == [
        {
            "session_key": 9839,
            "meeting_key": 1264,
            "session_name": "Race",
            "session_type": "Race",
            "date_start": "2025-12-07T13:00:00+00:00",
            "year": 2025,
        }
    ]


def test_get_drivers_renomeia_campos_e_tolera_country_code_ausente(simular):
    chamadas = simular(
        RespostaFalsa(
            200,
            [
                {
                    "first_name": "Lando",
                    "last_name": "Norris",
                    "name_acronym": "NOR",
                    "driver_number": 1,
                    "team_name": "McLaren",
                    # sem "country_code": a OpenF1 vai remover o campo.
                }
            ],
        )
    )

    resultado = svc.get_drivers(9839)

    assert chamadas[0]["url"].endswith("/drivers")
    assert chamadas[0]["params"] == {"session_key": 9839}
    assert resultado == [
        {
            "first_name": "Lando",
            "last_name": "Norris",
            "acronym": "NOR",
            "number": 1,
            "country_code": None,
            "team_name": "McLaren",
        }
    ]


def test_get_session_results_renomeia_campos(simular):
    chamadas = simular(
        RespostaFalsa(
            200,
            [
                {
                    "position": 1,
                    "driver_number": 1,
                    "dnf": False,
                    "dns": False,
                    "dsq": False,
                    "number_of_laps": 58,
                    "duration": 5400.0,  # não repassamos este campo
                }
            ],
        )
    )

    resultado = svc.get_session_results(9839)

    assert chamadas[0]["url"].endswith("/session_result")
    assert chamadas[0]["params"] == {"session_key": 9839}
    assert resultado == [
        {
            "position": 1,
            "driver_number": 1,
            "dnf": False,
            "dns": False,
            "dsq": False,
            "number_of_laps": 58,
        }
    ]