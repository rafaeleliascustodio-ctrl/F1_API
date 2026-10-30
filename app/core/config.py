"""
Configurações centrais da aplicação.

Lê as variáveis do arquivo .env e as expõe através do objeto `settings`.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Path(__file__) é o caminho deste arquivo (app/core/config.py).
# .parent.parent.parent sobe três níveis: core -> app -> F1_API (raiz do projeto).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carrega o arquivo .env da raiz do projeto para dentro das variáveis de
# ambiente do sistema. Depois disso, os.getenv() consegue enxergá-las.
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Agrupa as configurações da aplicação em um só objeto."""

    # Informações exibidas na documentação Swagger
    APP_NAME: str = "F1 API"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "API própria de Fórmula 1, inspirada no projeto OpenF1."

    # Integração com a OpenF1 (não precisa de chave para dados históricos).
    OPENF1_BASE_URL: str = "https://api.openf1.org/v1"
    OPENF1_TIMEOUT: int = 15  # segundos de espera antes de desistir
    def __init__(self) -> None:
        self.DATABASE_URL: str = self._load_database_url()

    @staticmethod
    def _load_database_url() -> str:
        """Lê a DATABASE_URL do .env e a ajusta para o driver psycopg 3."""
        url = os.getenv("DATABASE_URL")

        # Falha cedo e com mensagem clara se a variável não existir.
        if not url:
            raise RuntimeError(
                "A variável DATABASE_URL não foi encontrada. "
                "Crie o arquivo .env na raiz do projeto (veja o .env.example)."
            )

        # O Aiven pode fornecer a URL começando com "postgres://" ou
        # "postgresql://". Nenhum dos dois diz ao SQLAlchemy qual driver usar,
        # e "postgres://" nem é mais aceito pelo SQLAlchemy 2.x.
        # Por isso padronizamos para "postgresql+psycopg://" (driver psycopg 3).
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                url = "postgresql+psycopg://" + url[len(prefixo):]
                break

        return url


# Criamos UMA instância que será importada por todo o projeto:
#   from app.core.config import settings
settings = Settings()