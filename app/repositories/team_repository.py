"""
Repository de equipes: todas as consultas ao banco da tabela `teams`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate


def list_teams(db: Session, skip: int = 0, limit: int = 100) -> list[Team]:
    """Lista equipes ordenadas por nome, com paginação simples."""
    stmt = select(Team).order_by(Team.name).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_team(db: Session, team_id: int) -> Team | None:
    """Busca uma equipe pelo id. Devolve None se não existir."""
    return db.get(Team, team_id)


def get_team_by_name(db: Session, name: str) -> Team | None:
    """Busca uma equipe pelo nome (único). Útil para evitar duplicatas."""
    stmt = select(Team).where(Team.name == name)
    return db.scalars(stmt).one_or_none()


def create_team(db: Session, data: TeamCreate) -> Team:
    """Insere uma nova equipe e devolve o objeto já com o id gerado."""
    team = Team(**data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def update_team(db: Session, team: Team, data: TeamUpdate) -> Team:
    """Atualiza apenas os campos enviados no PATCH."""
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team


def delete_team(db: Session, team: Team) -> None:
    """Apaga uma equipe."""
    db.delete(team)
    db.commit()