"""
Repository de corridas: todas as consultas ao banco da tabela `races`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.race import Race
from app.schemas.race import RaceCreate, RaceUpdate


def list_races(db: Session, skip: int = 0, limit: int = 100) -> list[Race]:
    """Lista corridas da mais recente para a mais antiga, com paginação simples."""
    stmt = (
        select(Race)
        .order_by(Race.season.desc(), Race.round.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def list_seasons(db: Session) -> list[int]:
    """Lista os anos de temporada que possuem corridas (sem repetição)."""
    # distinct() elimina anos repetidos; não existe tabela `seasons`.
    stmt = select(Race.season).distinct().order_by(Race.season.desc())
    return list(db.scalars(stmt).all())


def get_race(db: Session, race_id: int) -> Race | None:
    """Busca uma corrida pelo id. Devolve None se não existir."""
    return db.get(Race, race_id)


def get_race_by_season_round(db: Session, season: int, round_: int) -> Race | None:
    """Busca a corrida de uma temporada e rodada (combinação única)."""
    # `round_` evita sobrescrever a função embutida round() do Python.
    stmt = select(Race).where(Race.season == season, Race.round == round_)
    return db.scalars(stmt).one_or_none()


def create_race(db: Session, data: RaceCreate) -> Race:
    """Insere uma nova corrida e devolve o objeto já com o id gerado."""
    race = Race(**data.model_dump())
    db.add(race)
    db.commit()
    db.refresh(race)
    return race


def update_race(db: Session, race: Race, data: RaceUpdate) -> Race:
    """Atualiza apenas os campos enviados no PATCH."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(race, field, value)
    db.commit()
    db.refresh(race)
    return race


def delete_race(db: Session, race: Race) -> None:
    """Apaga uma corrida."""
    db.delete(race)
    db.commit()