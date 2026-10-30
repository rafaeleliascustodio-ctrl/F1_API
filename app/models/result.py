"""
Modelo da tabela `results` (resultado de cada piloto em cada corrida).
"""

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.driver import Driver
from app.models.race import Race
from app.models.team import Team


class Result(Base):
    """Representa o resultado de um piloto em uma corrida."""

    __tablename__ = "results"

    # Um piloto só pode ter um resultado por corrida.
    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", name="uq_results_race_driver"),
    )

    # Chave primária autoincremental.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Três chaves estrangeiras: corrida, piloto e a equipe pela qual
    # o piloto correu NAQUELA corrida.
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    # Posição de largada. OPCIONAL (ex.: largou dos boxes).
    grid: Mapped[int | None] = mapped_column(Integer, default=None)

    # Posição final. OPCIONAL: fica NULL se o piloto não terminou a corrida.
    position: Mapped[int | None] = mapped_column(Integer, default=None)

    # Pontos ganhos. Float porque algumas corridas já deram pontos
    # fracionados (ex.: 0.5, 1.5). Padrão 0.
    points: Mapped[float] = mapped_column(Float, default=0)

    # Situação final (ex.: "Finished", "Accident", "Engine"). OPCIONAL.
    status: Mapped[str | None] = mapped_column(String(50), default=None)

    # Relacionamentos: permitem result.race, result.driver e result.team.
    race: Mapped[Race] = relationship()
    driver: Mapped[Driver] = relationship()
    team: Mapped[Team] = relationship()

    def __repr__(self) -> str:
        return (
            f"Result(id={self.id!r}, race_id={self.race_id!r}, "
            f"driver_id={self.driver_id!r}, position={self.position!r})"
        )