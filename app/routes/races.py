"""
Rotas (endpoints REST) de corridas e temporadas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories import circuit_repository
from app.repositories import race_repository as repo
from app.schemas.race import RaceCreate, RaceResponse, RaceUpdate

router = APIRouter(prefix="/races", tags=["Corridas"])

# Router separado para temporadas: GET /seasons
seasons_router = APIRouter(prefix="/seasons", tags=["Temporadas"])

MSG_DUPLICADA = "Já existe uma corrida nessa temporada e rodada."
MSG_SEM_CIRCUITO = "Circuito não encontrado."


@seasons_router.get("", response_model=list[int])
def list_seasons(db: Session = Depends(get_db)):
    """Lista os anos de temporada que possuem corridas cadastradas."""
    return repo.list_seasons(db)


@router.get("", response_model=list[RaceResponse])
def list_races(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista corridas (da mais recente para a mais antiga)."""
    return repo.list_races(db, skip=skip, limit=limit)


@router.get("/{race_id}", response_model=RaceResponse)
def get_race(race_id: int, db: Session = Depends(get_db)):
    """Busca uma corrida pelo id."""
    race = repo.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Corrida não encontrada.")
    return race


@router.post("", response_model=RaceResponse, status_code=status.HTTP_201_CREATED)
def create_race(data: RaceCreate, db: Session = Depends(get_db)):
    """Cria uma corrida. 404 se o circuito não existir; 409 se temporada+rodada já existir."""
    # Valida a chave estrangeira ANTES de gravar.
    if circuit_repository.get_circuit(db, data.circuit_id) is None:
        raise HTTPException(status_code=404, detail=MSG_SEM_CIRCUITO)
    if repo.get_race_by_season_round(db, data.season, data.round):
        raise HTTPException(status_code=409, detail=MSG_DUPLICADA)
    try:
        return repo.create_race(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=MSG_DUPLICADA)


@router.patch("/{race_id}", response_model=RaceResponse)
def update_race(race_id: int, data: RaceUpdate, db: Session = Depends(get_db)):
    """Atualiza parcialmente uma corrida."""
    race = repo.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Corrida não encontrada.")

    # Só os campos realmente enviados no PATCH.
    changes = data.model_dump(exclude_unset=True)

    # Se o circuito está mudando, ele precisa existir.
    if "circuit_id" in changes and changes["circuit_id"] != race.circuit_id:
        if circuit_repository.get_circuit(db, changes["circuit_id"]) is None:
            raise HTTPException(status_code=404, detail=MSG_SEM_CIRCUITO)

    # Calcula a temporada/rodada FINAL e confere se pertence a OUTRA corrida.
    season = changes.get("season", race.season)
    round_ = changes.get("round", race.round)
    if (season, round_) != (race.season, race.round):
        existing = repo.get_race_by_season_round(db, season, round_)
        if existing is not None and existing.id != race.id:
            raise HTTPException(status_code=409, detail=MSG_DUPLICADA)

    try:
        return repo.update_race(db, race, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=MSG_DUPLICADA)


@router.delete("/{race_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_race(race_id: int, db: Session = Depends(get_db)):
    """Apaga uma corrida. 409 se ela tiver resultados vinculados."""
    race = repo.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Corrida não encontrada.")
    try:
        repo.delete_race(db, race)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível apagar: a corrida possui resultados vinculados.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)