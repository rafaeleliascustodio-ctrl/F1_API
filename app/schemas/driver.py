"""
Schemas Pydantic de pilotos.
"""

from pydantic import BaseModel, ConfigDict, Field


class DriverBase(BaseModel):
    """Campos comuns a criação e resposta."""

    first_name: str = Field(min_length=1, max_length=100, examples=["Lewis"])
    last_name: str = Field(min_length=1, max_length=100, examples=["Hamilton"])

    # Sigla de exatamente 3 letras. `pattern` é uma expressão regular:
    # ^[A-Z]{3}$ = começa e termina com exatamente 3 letras maiúsculas.
    acronym: str = Field(pattern=r"^[A-Z]{3}$", examples=["HAM"])

    # Opcionais no Create: se o cliente não enviar, o valor é None.
    # ge=1 (greater or equal) recusa números menores que 1.
    number: int | None = Field(default=None, ge=1, le=99, examples=[44])

    # Código do país com 3 letras maiúsculas (ex.: GBR, BRA).
    country_code: str | None = Field(
        default=None, pattern=r"^[A-Z]{3}$", examples=["GBR"]
    )


class DriverCreate(DriverBase):
    """Corpo do POST. Sem `id`."""

    pass


class DriverUpdate(BaseModel):
    """Corpo do PATCH. Todos os campos opcionais."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    acronym: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    number: int | None = Field(default=None, ge=1, le=99)
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


class DriverResponse(DriverBase):
    """Resposta da API. Inclui o `id` gerado pelo banco."""

    id: int

    # Permite converter um objeto Driver do SQLAlchemy neste schema.
    model_config = ConfigDict(from_attributes=True)