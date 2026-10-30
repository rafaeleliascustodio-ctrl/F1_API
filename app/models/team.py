"""
Modelo da tabela `teams` (equipes de Fórmula 1).
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Team(Base):
    """Representa uma equipe (ex.: Ferrari, McLaren)."""

    __tablename__ = "teams"

    # Chave primária autoincremental.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Nome da equipe. Único: não pode haver duas equipes com o mesmo nome.
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # País de origem da equipe.
    country: Mapped[str] = mapped_column(String(100))

    def __repr__(self) -> str:
        return f"Team(id={self.id!r}, name={self.name!r})"
