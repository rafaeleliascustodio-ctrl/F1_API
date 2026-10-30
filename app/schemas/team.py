"""
Schemas Pydantic de equipes.
"""

from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    """Campos comuns a criação e resposta."""

    # Limites espelham o String(100) do modelo Team.
    name: str = Field(min_length=1, max_length=100, examples=["Ferrari"])
    country: str = Field(min_length=1, max_length=100, examples=["Itália"])


class TeamCreate(TeamBase):
    """Corpo do POST. Sem `id`."""

    pass


class TeamUpdate(BaseModel):
    """Corpo do PATCH. Todos os campos opcionais."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=1, max_length=100)


class TeamResponse(TeamBase):
    """Resposta da API. Inclui o `id` gerado pelo banco."""

    id: int

    # Permite converter um objeto Team do SQLAlchemy neste schema.
    model_config = ConfigDict(from_attributes=True)