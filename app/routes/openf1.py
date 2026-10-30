"""
Rotas que expõem dados consultados na OpenF1 (sem gravar no nosso banco).
"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Query

from app.services import openf1_service as svc

router = APIRouter(prefix="/openf1", tags=["OpenF1"])


def _call(func: Callable[..., list[dict]], *args, **kwargs) -> list[dict]:
    """Executa uma função do service e traduz OpenF1Error em HTTP 502."""
    try:
        return func(*args, **kwargs)
    except svc.OpenF1Error as exc:
        # 502 = o serviço externo falhou. A mensagem do OpenF1Error é nossa
        # (não contém URL nem detalhes internos), então pode ir ao cliente.
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/meetings")
def list_meetings(year: int = Query(ge=2023, le=2100, description="A OpenF1 só tem dados desde 2023.")):
    """Grandes Prêmios de um ano (inclui testes de pré-temporada)."""
    return _call(svc.get_meetings, year)


@router.get("/sessions")
def list_sessions(
    year: int | None = Query(None, ge=2023, le=2100),
    session_name: str | None = Query(None, examples=["Race"]),
    meeting_key: int | None = Query(None, gt=0),
):
    """Sessões (treinos, classificação, corrida). Todos os filtros são opcionais."""
    return _call(svc.get_sessions, year, session_name, meeting_key)


@router.get("/drivers")
def list_drivers(session_key: int = Query(gt=0, examples=[9839])):
    """Pilotos de uma sessão, com a equipe daquela sessão."""
    return _call(svc.get_drivers, session_key)


@router.get("/session-results")
def list_session_results(session_key: int = Query(gt=0, examples=[9839])):
    """Resultado de uma sessão (sem pontos nem equipe: a OpenF1 não informa)."""
    return _call(svc.get_session_results, session_key)