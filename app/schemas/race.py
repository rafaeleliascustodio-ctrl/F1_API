"""
Schemas Pydantic de corridas.
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field


class RaceBase(BaseModel):
    """Campos comuns a criação e resposta."""

    # ID do circuito onde a corrida acontece (precisa existir em `circuits`).
    # gt=0 (greater than) recusa zero e negativos.
    circuit_id: int = Field(gt=0, examples=[1])

    # Ano da temporada. Limites razoáveis: a F1 começou em 1950.
    season: int = Field(ge=1950, le=2100, examples=[2024])

    # Número da rodada dentro da temporada.
    round: int = Field(ge=1, le=30, examples=[21])

    name: str = Field(min_length=1, max_length=150, examples=["Brazilian Grand Prix"])

    # Data da corrida. O Pydantic aceita texto "AAAA-MM-DD" e converte.
    date: datetime.date = Field(examples=["2024-11-03"])


class RaceCreate(RaceBase):
    """Corpo do POST. Sem `id`."""

    pass


class RaceUpdate(BaseModel):
    """Corpo do PATCH. Todos os campos opcionais."""

    circuit_id: int | None = Field(default=None, gt=0)
    season: int | None = Field(default=None, ge=1950, le=2100)
    round: int | None = Field(default=None, ge=1, le=30)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    date: datetime.date | None = Field(default=None)


class RaceResponse(RaceBase):
    """Resposta da API. Inclui o `id` gerado pelo banco."""

    id: int

    # Permite converter um objeto Race do SQLAlchemy neste schema.
    model_config = ConfigDict(from_attributes=True)