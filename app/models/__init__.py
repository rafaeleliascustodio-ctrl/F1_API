"""
Importa todos os modelos para registrá-los em Base.metadata.

Sem estes imports, o create_all() não saberia quais tabelas criar.
"""

from app.models.circuit import Circuit
from app.models.driver import Driver
from app.models.race import Race
from app.models.result import Result
from app.models.team import Team

# __all__ define o que é exportado por `from app.models import *`
# e deixa explícito que estes imports são intencionais.
__all__ = ["Circuit", "Driver", "Race", "Result", "Team"]