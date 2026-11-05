"""
Front-end Streamlit da F1 API: ponto de entrada.

Execução (na raiz do projeto, com a API rodando em outro terminal):
    streamlit run frontend/app.py

O Streamlit adiciona a pasta deste arquivo ao caminho de imports, por isso
o módulo é importado como `api_client` (e não `frontend.api_client`).
"""

import requests
import streamlit as st
from paginas import pilotos
import api_client
from api_client import ApiError
from paginas import circuitos, equipes, pilotos

# Deve ser a primeira chamada do Streamlit no script.
st.set_page_config(page_title="F1 API", page_icon="🏁", layout="wide")

# Recursos exibidos na página inicial: (rota, rótulo).
RECURSOS = [
    ("drivers", "Pilotos"),
    ("teams", "Equipes"),
    ("circuits", "Circuitos"),
    ("races", "Corridas"),
    ("results", "Resultados"),
]


def api_esta_no_ar() -> bool:
    """Testa GET / na API (não toca o banco)."""
    try:
        resp = requests.get(f"{api_client.API_URL}/", timeout=api_client.TIMEOUT)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def pagina_inicio():
    st.title("🏁 F1 API")
    st.caption("Painel de consulta e cadastro, ligado à nossa API REST.")

    if not api_esta_no_ar():
        st.error(
            f"A API não responde em {api_client.API_URL}. "
            "Suba-a em outro terminal: uvicorn app.main:app --reload"
        )
        return
    st.success(f"API no ar em {api_client.API_URL}")

    # Uma coluna por recurso, cada uma com a contagem de registros.
    colunas = st.columns(len(RECURSOS))
    for coluna, (rota, rotulo) in zip(colunas, RECURSOS):
        try:
            total = len(api_client.listar(rota, limit=100))
            # Se vier o máximo pedido, pode haver mais registros.
            texto = f"{total}+" if total == 100 else str(total)
        except ApiError as erro:
            texto = "erro"
            coluna.caption(str(erro))
        coluna.metric(rotulo, texto)

    try:
        temporadas = api_client.listar_temporadas()
        st.write(
            "**Temporadas cadastradas:** "
            + (", ".join(str(t) for t in sorted(temporadas)) or "nenhuma")
        )
    except ApiError as erro:
        st.warning(f"Não foi possível ler as temporadas: {erro}")


# Navegação lateral. Cada nova página vira mais um st.Page nesta lista.
navegacao = st.navigation(
    [
        st.Page(pagina_inicio, title="Início", icon="🏠", default=True),
        st.Page(pilotos.pagina, title="Pilotos", icon="🧑‍✈️", url_path="pilotos"),
        st.Page(equipes.pagina, title="Equipes", icon="🏎️", url_path="equipes"),
        st.Page(circuitos.pagina, title="Circuitos", icon="🏁", url_path="circuitos"),
    ]
)
navegacao.run()