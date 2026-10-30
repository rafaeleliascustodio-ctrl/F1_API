"""
Rotas (endpoints REST) de equipes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories import team_repository as repo
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate

router = APIRouter(prefix="/teams", tags=["Equipes"])


@router.get("", response_model=list[TeamResponse])
def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista equipes, com paginação simples."""
    return repo.list_teams(db, skip=skip, limit=limit)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Busca uma equipe pelo id."""
    team = repo.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Equipe não encontrada.")
    return team


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamCreate, db: Session = Depends(get_db)):
    """Cria uma equipe. Devolve 409 se o nome já existir."""
    if repo.get_team_by_name(db, data.name):
        raise HTTPException(status_code=409, detail="Já existe uma equipe com esse nome.")
    try:
        return repo.create_team(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma equipe com esse nome.")


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, data: TeamUpdate, db: Session = Depends(get_db)):
    """Atualiza parcialmente uma equipe."""
    team = repo.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Equipe não encontrada.")

    # Só checa duplicidade se o nome está mudando.
    if data.name is not None and data.name != team.name:
        if repo.get_team_by_name(db, data.name):
            raise HTTPException(status_code=409, detail="Já existe uma equipe com esse nome.")

    try:
        return repo.update_team(db, team, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma equipe com esse nome.")


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    """Apaga uma equipe. Devolve 409 se ela tiver resultados vinculados."""
    team = repo.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Equipe não encontrada.")
    try:
        repo.delete_team(db, team)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível apagar: a equipe possui resultados vinculados.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)