"""
Classe base para todos os modelos do banco de dados.

Cada modelo (Driver, Team, Circuit, Race, Result) herdará de `Base`.
O SQLAlchemy usa essa classe para registrar as tabelas em `Base.metadata`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy 2.x. Não precisa de conteúdo próprio."""
    pass