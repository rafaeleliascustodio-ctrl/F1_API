"""
Rotas (endpoints REST) de resultados.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories import driver_repository, race_repository, team_repository
from app.repositories import result_repository as repo
from app.schemas.result import ResultCreate, ResultResponse, ResultUpdate

router = APIRouter(prefix="/results", tags=["Resultados"])

MSG_DUPLICADO = "Esse piloto já possui resultado nessa corrida."


def _validate_references(
    db: Session, race_id: int | None, driver_id: int | None, team_id: int | None
) -> None:
    """Confere se corrida, piloto e equipe informados existem (None = não checar)."""
    if race_id is not None and race_repository.get_race(db, race_id) is None:
        raise HTTPException(status_code=404, detail="Corrida não encontrada.")
    if driver_id is not None and driver_repository.get_driver(db, driver_id) is None:
        raise HTTPException(status_code=404, detail="Piloto não encontrado.")
    if team_id is not None and team_repository.get_team(db, team_id) is None:
        raise HTTPException(status_code=404, detail="Equipe não encontrada.")


@router.get("", response_model=list[ResultResponse])
def list_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista resultados, com paginação simples."""
    return repo.list_results(db, skip=skip, limit=limit)


@router.get("/{result_id}", response_model=ResultResponse)
def get_result(result_id: int, db: Session = Depends(get_db)):
    """Busca um resultado pelo id."""
    result = repo.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado não encontrado.")
    return result


@router.post("", response_model=ResultResponse, status_code=status.HTTP_201_CREATED)
def create_result(data: ResultCreate, db: Session = Depends(get_db)):
    """Cria um resultado. 404 se corrida/piloto/equipe não existir; 409 se duplicado."""
    _validate_references(db, data.race_id, data.driver_id, data.team_id)
    if repo.get_result_by_race_driver(db, data.race_id, data.driver_id):
        raise HTTPException(status_code=409, detail=MSG_DUPLICADO)
    try:
        return repo.create_result(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=MSG_DUPLICADO)


@router.patch("/{result_id}", response_model=ResultResponse)
def update_result(result_id: int, data: ResultUpdate, db: Session = Depends(get_db)):
    """Atualiza parcialmente um resultado."""
    result = repo.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado não encontrado.")

    changes = data.model_dump(exclude_unset=True)

    # Valida só as referências que estão mudando.
    _validate_references(
        db,
        changes.get("race_id") if changes.get("race_id") != result.race_id else None,
        changes.get("driver_id") if changes.get("driver_id") != result.driver_id else None,
        changes.get("team_id") if changes.get("team_id") != result.team_id else None,
    )

    # Confere se a combinação corrida+piloto FINAL pertence a OUTRO resultado.
    race_id = changes.get("race_id", result.race_id)
    driver_id = changes.get("driver_id", result.driver_id)
    if (race_id, driver_id) != (result.race_id, result.driver_id):
        existing = repo.get_result_by_race_driver(db, race_id, driver_id)
        if existing is not None and existing.id != result.id:
            raise HTTPException(status_code=409, detail=MSG_DUPLICADO)

    try:
        return repo.update_result(db, result, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=MSG_DUPLICADO)


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: int, db: Session = Depends(get_db)):
    """Apaga um resultado."""
    result = repo.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado não encontrado.")
    repo.delete_result(db, result)
    return Response(status_code=status.HTTP_204_NO_CONTENT)