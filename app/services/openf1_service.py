"""
Service da OpenF1: consulta a API externa e trata as respostas.

Documentação oficial: https://openf1.org/docs
Esta camada NÃO grava no nosso banco; só busca e organiza os dados.
"""

import requests

from app.core.config import settings


class OpenF1Error(Exception):
    """Erro ao consultar a OpenF1 (rede, limite de uso ou resposta inválida)."""


def _get(endpoint: str, params: dict | None = None) -> list[dict]:
    """Faz um GET na OpenF1 e devolve a lista de registros (JSON)."""
    url = f"{settings.OPENF1_BASE_URL}/{endpoint}"
    # Remove parâmetros None, para não enviar filtros vazios.
    filtros = {k: v for k, v in (params or {}).items() if v is not None}

    try:
        resp = requests.get(url, params=filtros, timeout=settings.OPENF1_TIMEOUT)
    except requests.RequestException as exc:
        raise OpenF1Error("Não foi possível contatar a OpenF1.") from exc

    if resp.status_code == 429:
        # Plano gratuito: 3 req/s e 30 req/min.
        raise OpenF1Error("Limite de requisições da OpenF1 atingido. Aguarde e tente de novo.")
    if resp.status_code == 404:
        # Comportamento observado em teste (não documentado): a OpenF1 responde
        # 404 quando o filtro não encontra nada. Tratamos como lista vazia.
        return []
    if resp.status_code != 200:
        raise OpenF1Error(f"A OpenF1 respondeu com status {resp.status_code}.")

    try:
        dados = resp.json()
    except ValueError as exc:
        raise OpenF1Error("A OpenF1 devolveu uma resposta que não é JSON.") from exc

    if not isinstance(dados, list):
        raise OpenF1Error("Formato inesperado na resposta da OpenF1.")
    return dados


def get_meetings(year: int) -> list[dict]:
    """Grandes Prêmios (fins de semana de corrida) de um ano."""
    return [
        {
            "meeting_key": m.get("meeting_key"),
            "year": m.get("year"),
            "name": m.get("meeting_name"),
            "circuit_key": m.get("circuit_key"),
            "circuit_name": m.get("circuit_short_name"),
            "location": m.get("location"),
            "country_name": m.get("country_name"),
            "date_start": m.get("date_start"),
        }
        for m in _get("meetings", {"year": year})
    ]


def get_sessions(
    year: int | None = None,
    session_name: str | None = None,
    meeting_key: int | None = None,
) -> list[dict]:
    """Sessões (treinos, classificação, corrida...). Todos os filtros são opcionais."""
    bruto = _get(
        "sessions",
        {"year": year, "session_name": session_name, "meeting_key": meeting_key},
    )
    return [
        {
            "session_key": s.get("session_key"),
            "meeting_key": s.get("meeting_key"),
            "session_name": s.get("session_name"),
            "session_type": s.get("session_type"),
            "date_start": s.get("date_start"),
            "year": s.get("year"),
        }
        for s in bruto
    ]


def get_drivers(session_key: int) -> list[dict]:
    """Pilotos de UMA sessão, com a equipe pela qual correram nela."""
    return [
        {
            "first_name": d.get("first_name"),
            "last_name": d.get("last_name"),
            "acronym": d.get("name_acronym"),
            "number": d.get("driver_number"),
            # .get(): este campo será removido pela OpenF1 no fim de 2026.
            "country_code": d.get("country_code"),
            "team_name": d.get("team_name"),
        }
        for d in _get("drivers", {"session_key": session_key})
    ]


def get_session_results(session_key: int) -> list[dict]:
    """Resultado final de uma sessão. A OpenF1 NÃO informa pontos nem equipe aqui."""
    return [
        {
            "position": r.get("position"),
            "driver_number": r.get("driver_number"),
            "dnf": r.get("dnf"),
            "dns": r.get("dns"),
            "dsq": r.get("dsq"),
            "number_of_laps": r.get("number_of_laps"),
        }
        for r in _get("session_result", {"session_key": session_key})
    ]