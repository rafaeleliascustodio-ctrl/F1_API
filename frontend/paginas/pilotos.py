"""
Página de Pilotos: listar, cadastrar, editar e apagar.

Este arquivo é o MODELO das demais páginas de CRUD. Toda regra de negócio
(duplicidade, validação, vínculos) continua na API: aqui só mostramos o
resultado e traduzimos erros em mensagens para o usuário.
"""

import streamlit as st

import api_client
from api_client import ApiError

RECURSO = "drivers"
CHAVE_AVISO = "aviso_pilotos"


def _concluir(mensagem: str):
    """Guarda um aviso e recarrega a página.

    O Streamlit executa o script de cima para baixo. Sem recarregar, a aba
    "Lista" (que já foi desenhada) continuaria mostrando os dados antigos.
    O aviso fica na session_state para sobreviver ao recarregamento.
    """
    st.session_state[CHAVE_AVISO] = mensagem
    st.rerun()


def _texto_ou_none(valor: str) -> str | None:
    """Campo opcional: texto vazio vira None (a API espera null)."""
    valor = valor.strip().upper()
    return valor or None


def _aba_lista(pilotos: list[dict]):
    if not pilotos:
        st.info("Nenhum piloto cadastrado ainda. Use a aba 'Cadastrar'.")
        return
    st.dataframe(
        pilotos,
        hide_index=True,
        width="stretch",
        column_order=["id", "acronym", "first_name", "last_name", "number", "country_code"],
        column_config={
            "id": "ID",
            "acronym": "Sigla",
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "number": "Número",
            "country_code": "País",
        },
    )
    st.caption(f"{len(pilotos)} piloto(s).")


def _aba_cadastrar():
    with st.form("form_novo_piloto", clear_on_submit=False):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome")
        sobrenome = col2.text_input("Sobrenome")
        col3, col4, col5 = st.columns(3)
        sigla = col3.text_input("Sigla (3 letras)", max_chars=3)
        numero = col4.number_input(
            "Número (0 = sem número)", min_value=0, max_value=99, value=0, step=1
        )
        pais = col5.text_input("País (3 letras, opcional)", max_chars=3)
        enviar = st.form_submit_button("Cadastrar piloto")

    if not enviar:
        return

    # Checagem mínima no front-end; as regras de verdade são da API.
    if not nome.strip() or not sobrenome.strip() or not sigla.strip():
        st.error("Nome, sobrenome e sigla são obrigatórios.")
        return

    dados = {
        "first_name": nome.strip(),
        "last_name": sobrenome.strip(),
        "acronym": sigla.strip().upper(),  # a API exige maiúsculas
        "number": int(numero) or None,     # 0 = não informado
        "country_code": _texto_ou_none(pais),
    }
    try:
        criado = api_client.criar(RECURSO, dados)
    except ApiError as erro:
        st.error(str(erro))  # 409 (sigla repetida), 422 (dados inválidos)
    else:
        _concluir(f"Piloto {criado['acronym']} cadastrado (id {criado['id']}).")


def _aba_editar_apagar(pilotos: list[dict]):
    if not pilotos:
        st.info("Não há pilotos para editar.")
        return

    # {id: "HAM - Lewis Hamilton (id 2)"} para o seletor.
    rotulos = {
        p["id"]: f"{p['acronym']} - {p['first_name']} {p['last_name']} (id {p['id']})"
        for p in pilotos
    }
    id_sel = st.selectbox("Piloto", options=list(rotulos), format_func=rotulos.get)
    atual = next(p for p in pilotos if p["id"] == id_sel)

    st.subheader("Editar")
    # A chave do formulário e dos campos inclui o id: ao trocar de piloto,
    # os campos são recriados com os valores dele.
    with st.form(f"form_editar_{id_sel}"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome", value=atual["first_name"], key=f"nome_{id_sel}")
        sobrenome = col2.text_input(
            "Sobrenome", value=atual["last_name"], key=f"sobrenome_{id_sel}"
        )
        col3, col4, col5 = st.columns(3)
        sigla = col3.text_input(
            "Sigla (3 letras)", value=atual["acronym"], max_chars=3, key=f"sigla_{id_sel}"
        )
        numero = col4.number_input(
            "Número (0 = sem número)",
            min_value=0, max_value=99, step=1,
            value=atual["number"] or 0,
            key=f"numero_{id_sel}",
        )
        pais = col5.text_input(
            "País (3 letras, opcional)",
            value=atual["country_code"] or "",
            max_chars=3,
            key=f"pais_{id_sel}",
        )
        salvar = st.form_submit_button("Salvar alterações")

    if salvar:
        novos = {
            "first_name": nome.strip(),
            "last_name": sobrenome.strip(),
            "acronym": sigla.strip().upper(),
            "number": int(numero) or None,
            "country_code": _texto_ou_none(pais),
        }
        # PATCH parcial: envia só o que mudou.
        alterados = {campo: v for campo, v in novos.items() if v != atual.get(campo)}
        if not alterados:
            st.info("Nenhuma alteração para salvar.")
        else:
            try:
                api_client.atualizar(RECURSO, id_sel, alterados)
            except ApiError as erro:
                st.error(str(erro))
            else:
                _concluir(f"Piloto id {id_sel} atualizado.")

    st.divider()
    st.subheader("Apagar")
    confirmo = st.checkbox(
        f"Confirmo que quero apagar {rotulos[id_sel]}", key=f"confirma_{id_sel}"
    )
    if st.button("Apagar piloto", type="primary", disabled=not confirmo):
        try:
            api_client.apagar(RECURSO, id_sel)
        except ApiError as erro:
            st.error(str(erro))  # 409 se o piloto tem resultados
        else:
            _concluir(f"Piloto id {id_sel} apagado.")


def pagina():
    st.title("🧑‍✈️ Pilotos")

    # Mostra (uma vez) o aviso deixado pela ação anterior.
    aviso = st.session_state.pop(CHAVE_AVISO, None)
    if aviso:
        st.success(aviso)

    try:
        pilotos = api_client.listar(RECURSO)
    except ApiError as erro:
        st.error(str(erro))
        return

    aba_lista, aba_novo, aba_editar = st.tabs(["Lista", "Cadastrar", "Editar / Apagar"])
    with aba_lista:
        _aba_lista(pilotos)
    with aba_novo:
        _aba_cadastrar()
    with aba_editar:
        _aba_editar_apagar(pilotos)