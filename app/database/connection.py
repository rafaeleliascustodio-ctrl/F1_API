"""
Conexão com o banco de dados PostgreSQL (Aiven).

Define o engine, a fábrica de sessões e a dependência `get_db`
usada pelas rotas do FastAPI.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# O engine é o "gerenciador de conexões". Ele NÃO conecta ao banco ao ser
# criado; a conexão real só acontece na primeira consulta.
engine = create_engine(
    settings.DATABASE_URL,
    # Antes de reaproveitar uma conexão do pool, testa se ela ainda está viva.
    # Serviços na nuvem (como o Aiven) podem derrubar conexões ociosas.
    pool_pre_ping=True,
    # Quantidade de conexões mantidas abertas no pool.
    pool_size=5,
    # Conexões extras permitidas em momentos de pico.
    max_overflow=5,
)

# Fábrica de sessões. Cada chamada a SessionLocal() cria uma sessão nova.
# autoflush=False -> o SQLAlchemy não envia alterações ao banco automaticamente
#                    antes de cada consulta (comportamento mais previsível).
# autocommit=False -> alterações só são gravadas quando chamamos commit().
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """
    Dependência do FastAPI: entrega uma sessão para a rota e a fecha depois.

    Uso nas rotas:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        # 'yield' entrega a sessão para a rota. O código após o yield
        # só roda quando a requisição termina.
        yield db
    finally:
        # Sempre fecha a sessão, com sucesso ou erro, devolvendo a
        # conexão ao pool.
        db.close()


def check_connection() -> bool:
    """Testa a conexão executando um 'SELECT 1'. Retorna True se funcionar."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True