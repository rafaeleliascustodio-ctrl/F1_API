"""
Schemas Pydantic de circuitos.

Definem o formato dos dados que entram e saem da API,
separados do modelo do banco (app/models/circuit.py).
"""

from pydantic import BaseModel, ConfigDict, Field


class CircuitBase(BaseModel):
    """Campos comuns a criação e resposta."""

    # Field(...) adiciona regras de validação.
    # min_length/max_length espelham o String(100) do banco.
    name: str = Field(min_length=1, max_length=100, examples=["Autódromo José Carlos Pace"])
    location: str = Field(min_length=1, max_length=100, examples=["São Paulo"])
    country: str = Field(min_length=1, max_length=100, examples=["Brasil"])


class CircuitCreate(CircuitBase):
    """Corpo do POST. Herda tudo de CircuitBase; não tem `id`."""

    pass


class CircuitUpdate(BaseModel):
    """Corpo do PATCH. Todos os campos são opcionais (atualização parcial)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=1, max_length=100)


class CircuitResponse(CircuitBase):
    """Resposta da API. Inclui o `id` gerado pelo banco."""

    id: int

    # from_attributes=True permite criar o schema a partir de um objeto
    # SQLAlchemy (que usa atributos, não dicionário).
    model_config = ConfigDict(from_attributes=True)