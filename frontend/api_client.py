"""
Cliente HTTP da F1 API, usado pelo front-end Streamlit.

Todas as páginas falam com a API por aqui. O front-end NÃO acessa o banco:
as regras (404, 409, 422) continuam sendo da API.
"""

import os

import requests

# Endereço da API. Pode ser trocado pela variável de ambiente F1_API_URL.
API_URL = os.getenv("F1_API_URL", "http://127.0.0.1:8000")
TIMEOUT = 15  # segundos


class ApiError(Exception):
    """Erro devolvido pela API ou falha ao contatá-la."""

    def __init__(self, mensagem: str, status_code: int | None = None):
        super().__init__(mensagem)
        self.status_code = status_code


def _mensagem_de_erro(resp: requests.Response) -> str:
    """Extrai uma mensagem legível do corpo de erro do FastAPI."""
    try:
        detail = resp.json().get("detail")
    except (ValueError, AttributeError):
        return f"A API respondeu com status {resp.status_code}."

    # 422: detail é uma lista de {"loc": [...], "msg": "..."}.
    if isinstance(detail, list):
        partes = []
        for erro in detail:
            campo = ".".join(str(p) for p in erro.get("loc", []) if p != "body")
            partes.append(f"{campo}: {erro.get('msg')}" if campo else erro.get("msg", ""))
        return "; ".join(partes)

    # 404, 409, 502: detail é um texto.
    return str(detail) if detail else f"A API respondeu com status {resp.status_code}."


def _request(metodo: str, caminho: str, **kwargs):
    """Faz a chamada e traduz falhas em ApiError. Devolve o JSON (ou None no 204)."""
    try:
        resp = requests.request(
            metodo, f"{API_URL}{caminho}", timeout=TIMEOUT, **kwargs
        )
    except requests.RequestException as exc:
        raise ApiError("Não foi possível contatar a API. Ela está rodando?") from exc

    if resp.status_code >= 400:
        raise ApiError(_mensagem_de_erro(resp), resp.status_code)
    if resp.status_code == 204:  # DELETE: sem corpo
        return None
    return resp.json()


# ------------------------------------------------------------------ CRUD
# `recurso` é o nome da rota: "drivers", "teams", "circuits", "races", "results".


def listar(recurso: str, skip: int = 0, limit: int = 100) -> list[dict]:
    return _request("GET", f"/{recurso}", params={"skip": skip, "limit": limit})


def buscar(recurso: str, id_: int) -> dict:
    return _request("GET", f"/{recurso}/{id_}")


def criar(recurso: str, dados: dict) -> dict:
    return _request("POST", f"/{recurso}", json=dados)


def atualizar(recurso: str, id_: int, dados: dict) -> dict:
    return _request("PATCH", f"/{recurso}/{id_}", json=dados)


def apagar(recurso: str, id_: int) -> None:
    _request("DELETE", f"/{recurso}/{id_}")


def listar_temporadas() -> list[int]:
    return _request("GET", "/seasons")