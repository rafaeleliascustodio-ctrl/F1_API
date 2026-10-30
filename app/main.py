"""
Ponto de entrada da aplicação F1 API.

Cria a instância do FastAPI e define os endpoints iniciais.
Para executar:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.database.connection import check_connection

# Instância principal da aplicação. Título, versão e descrição aparecem
# na documentação Swagger (/docs).
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
)


@app.get("/", tags=["Geral"])
def root() -> dict:
    """Endpoint principal: confirma que a API está no ar."""
    return {
        "mensagem": f"Bem-vindo à {settings.APP_NAME}!",
        "versao": settings.APP_VERSION,
        "documentacao": "/docs",
    }


@app.get("/health", tags=["Geral"])
def health() -> dict:
    """Verifica se a API consegue se comunicar com o banco de dados."""
    try:
        check_connection()
    except Exception:
        # Não devolvemos o texto do erro ao cliente: ele poderia expor
        # detalhes internos (host, usuário) da conexão.
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponível.",
        )
    return {"api": "ok", "banco_de_dados": "ok"}