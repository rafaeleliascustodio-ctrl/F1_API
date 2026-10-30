"""
Modelo da tabela `races` (corridas de Fórmula 1).
"""

import datetime

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.circuit import Circuit


class Race(Base):
    """Representa uma corrida (ex.: GP do Brasil de 2024)."""

    __tablename__ = "races"

    # Restrição única composta: não pode haver duas corridas com a mesma
    # combinação de temporada + número da rodada.
    __table_args__ = (
        UniqueConstraint("season", "round", name="uq_races_season_round"),
    )

    # Chave primária autoincremental.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Chave estrangeira: aponta para a coluna `id` da tabela `circuits`.
    circuit_id: Mapped[int] = mapped_column(ForeignKey("circuits.id"))

    # Ano da temporada (ex.: 2024). Declarado com mapped_column() para que
    # a coluna exista quando a restrição única for criada.
    season: Mapped[int] = mapped_column(Integer)

    # Número da rodada dentro da temporada (1, 2, 3...).
    round: Mapped[int] = mapped_column(Integer)

    # Nome da corrida (ex.: "Brazilian Grand Prix").
    name: Mapped[str] = mapped_column(String(150))

    # Data da corrida. Usamos `datetime.date` (e não `date` direto) para
    # não confundir o tipo com o nome da coluna.
    date: Mapped[datetime.date] = mapped_column(Date)

    # Relacionamento: permite usar `race.circuit` para obter o objeto Circuit.
    # NÃO cria coluna no banco.
    circuit: Mapped[Circuit] = relationship()

    def __repr__(self) -> str:
        return f"Race(id={self.id!r}, season={self.season!r}, round={self.round!r})"