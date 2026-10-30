"""
Schemas Pydantic de resultados.
"""

from pydantic import BaseModel, ConfigDict, Field


class ResultBase(BaseModel):
    """Campos comuns a criação e resposta."""

    # IDs que apontam para races, drivers e teams. gt=0 recusa zero e negativos.
    race_id: int = Field(gt=0, examples=[1])
    driver_id: int = Field(gt=0, examples=[1])
    team_id: int = Field(gt=0, examples=[1])

    # Posição de largada. Opcional (ex.: largou dos boxes).
    grid: int | None = Field(default=None, ge=0, le=30, examples=[3])

    # Posição final. None = piloto que não terminou a corrida.
    position: int | None = Field(default=None, ge=1, le=30, examples=[1])

    # Pontos ganhos. Padrão 0. ge=0 recusa pontos negativos.
    points: float = Field(default=0, ge=0, examples=[25])

    # Situação final (ex.: "Finished", "Accident"). Opcional.
    status: str | None = Field(default=None, min_length=1, max_length=50, examples=["Finished"])


class ResultCreate(ResultBase):
    """Corpo do POST. Sem `id`."""

    pass


class ResultUpdate(BaseModel):
    """Corpo do PATCH. Todos os campos opcionais."""

    race_id: int | None = Field(default=None, gt=0)
    driver_id: int | None = Field(default=None, gt=0)
    team_id: int | None = Field(default=None, gt=0)
    grid: int | None = Field(default=None, ge=0, le=30)
    position: int | None = Field(default=None, ge=1, le=30)
    points: float | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class ResultResponse(ResultBase):
    """Resposta da API. Inclui o `id` gerado pelo banco."""

    id: int

    # Permite converter um objeto Result do SQLAlchemy neste schema.
    model_config = ConfigDict(from_attributes=True)