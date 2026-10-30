"""
Modelo da tabela `circuits` (circuitos de Fórmula 1).
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Circuit(Base):
    """Representa um circuito (ex.: Interlagos, Monza)."""

    # Nome da tabela no PostgreSQL.
    __tablename__ = "circuits"

    # Chave primária: inteiro autoincremental gerado pelo banco.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Nome do circuito. unique=True impede dois circuitos com o mesmo nome.
    # nullable=False (padrão para tipos sem Optional) torna o campo obrigatório.
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Cidade/região onde o circuito fica.
    location: Mapped[str] = mapped_column(String(100))

    # País do circuito.
    country: Mapped[str] = mapped_column(String(100))

    def __repr__(self) -> str:
        """Representação legível, útil ao depurar no terminal."""
        return f"Circuit(id={self.id!r}, name={self.name!r})"