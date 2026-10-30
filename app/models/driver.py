"""
Modelo da tabela `drivers` (pilotos de Fórmula 1).
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Driver(Base):
    """Representa um piloto (ex.: Ayrton Senna, Lewis Hamilton)."""

    __tablename__ = "drivers"

    # Chave primária autoincremental.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Nome e sobrenome, obrigatórios.
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    # Sigla de três letras usada na transmissão (ex.: HAM, VER).
    # Única: não pode haver duas siglas iguais.
    acronym: Mapped[str] = mapped_column(String(3), unique=True)

    # Número do carro. OPCIONAL: "int | None" faz a coluna aceitar NULL.
    number: Mapped[int | None] = mapped_column(default=None)

    # Código do país (ex.: BRA, GBR). OPCIONAL.
    country_code: Mapped[str | None] = mapped_column(String(3), default=None)

    def __repr__(self) -> str:
        return f"Driver(id={self.id!r}, acronym={self.acronym!r})"