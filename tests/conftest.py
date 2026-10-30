"""
Fixtures compartilhadas pelos testes.

A fixture `client` entrega um cliente HTTP da API ligado a um banco SQLite
em memória, novo a cada teste. O PostgreSQL do Aiven NÃO é tocado.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registra todos os modelos na Base)
from app.database.base import Base
from app.database.connection import get_db
from app.main import app


@pytest.fixture()
def client():
    """Cliente HTTP da API com um banco de teste limpo."""
    # "sqlite://" = banco em memória. StaticPool mantém UMA conexão só,
    # senão cada conexão nova enxergaria um banco vazio diferente.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # O SQLite ignora chaves estrangeiras por padrão. Este evento liga a
    # verificação em toda conexão, imitando o comportamento do PostgreSQL.
    @event.listens_for(engine, "connect")
    def _ativar_chaves_estrangeiras(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        """Mesma ideia do get_db real, mas usando o banco de teste."""
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    # Troca a dependência: as rotas passam a usar o banco de teste.
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client  # o teste roda aqui

    # Limpeza após cada teste.
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()