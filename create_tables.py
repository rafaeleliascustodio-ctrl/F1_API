"""
Cria as tabelas no banco de dados (PostgreSQL do Aiven).

Uso, na raiz do projeto:
    python create_tables.py
"""

from sqlalchemy import inspect

import app.models  # noqa: F401  (registra todos os modelos na Base)
from app.database.base import Base
from app.database.connection import engine


def main() -> None:
    # Cria somente as tabelas que ainda não existem.
    Base.metadata.create_all(bind=engine)

    # Consulta o banco para confirmar o que existe de fato.
    tabelas = sorted(inspect(engine).get_table_names())
    print("Tabelas no banco:", tabelas)


if __name__ == "__main__":
    main()