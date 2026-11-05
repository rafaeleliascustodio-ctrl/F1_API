"""
Gerador de páginas de CRUD para recursos que só têm campos de texto
(equipes, circuitos). Segue o mesmo padrão da página de pilotos.

Cada campo é um dicionário:
    {"chave": "name", "rotulo": "Nome", "obrigatorio": True}
"""

from collections.abc import Callable

import streamlit as st

import api_client
from api_client import ApiError


def criar_pagina(
    recurso: str,
    titulo: str,
    singular: str,
    campos: list[dict],
    rotulo_registro: Callable[[dict], str],
) -> Callable[[], None]:
    """Devolve a função de página, pronta para o st.Page."""
    chave_aviso = f"aviso_{recurso}"

    def concluir(mensagem: str):
        # Guarda o aviso e recarrega, para a aba "Lista" mostrar os dados novos.
        st.session_state[chave_aviso] = mensagem
        st.rerun()

    def desenhar_campos(valores: dict, sufixo: str) -> dict:
        """Uma caixa de texto por campo, lado a lado. Devolve {chave: texto}."""
        lidos = {}
        for coluna, campo in zip(st.columns(len(campos)), campos):
            rotulo = campo["rotulo"] + (" *" if campo["obrigatorio"] else "")
            lidos[campo["chave"]] = coluna.text_input(
                rotulo,
                value=valores.get(campo["chave"]) or "",
                key=f"{recurso}_{campo['chave']}_{sufixo}",
            )
        return lidos

    def limpar(lidos: dict) -> dict | None:
        """Tira espaços; campo opcional vazio vira None. None = falta obrigatório."""
        dados = {}
        for campo in campos:
            texto = lidos[campo["chave"]].strip()
            if not texto and campo["obrigatorio"]:
                st.error(f"O campo '{campo['rotulo']}' é obrigatório.")
                return None
            dados[campo["chave"]] = texto or None
        return dados

    def aba_lista(registros: list[dict]):
        if not registros:
            st.info(f"Nenhum registro ainda. Use a aba 'Cadastrar'.")
            return
        st.dataframe(
            registros,
            hide_index=True,
            width="stretch",
            column_order=["id"] + [c["chave"] for c in campos],
            column_config={"id": "ID", **{c["chave"]: c["rotulo"] for c in campos}},
        )
        st.caption(f"{len(registros)} registro(s).")

    def aba_cadastrar():
        with st.form(f"form_novo_{recurso}"):
            lidos = desenhar_campos({}, "novo")
            enviar = st.form_submit_button(f"Cadastrar {singular.lower()}")
        if not enviar:
            return
        dados = limpar(lidos)
        if dados is None:
            return
        try:
            criado = api_client.criar(recurso, dados)
        except ApiError as erro:
            st.error(str(erro))  # 409 (nome repetido), 422 (dados inválidos)
        else:
            concluir(f"{singular} cadastrado(a): {rotulo_registro(criado)}.")

    def aba_editar_apagar(registros: list[dict]):
        if not registros:
            st.info("Não há registros para editar.")
            return
        rotulos = {r["id"]: rotulo_registro(r) for r in registros}
        id_sel = st.selectbox(singular, options=list(rotulos), format_func=rotulos.get)
        atual = next(r for r in registros if r["id"] == id_sel)

        st.subheader("Editar")
        with st.form(f"form_editar_{recurso}_{id_sel}"):
            lidos = desenhar_campos(atual, str(id_sel))
            salvar = st.form_submit_button("Salvar alterações")
        if salvar:
            dados = limpar(lidos)
            if dados is not None:
                # PATCH parcial: só o que mudou.
                alterados = {k: v for k, v in dados.items() if v != atual.get(k)}
                if not alterados:
                    st.info("Nenhuma alteração para salvar.")
                else:
                    try:
                        api_client.atualizar(recurso, id_sel, alterados)
                    except ApiError as erro:
                        st.error(str(erro))
                    else:
                        concluir(f"Registro id {id_sel} atualizado.")

        st.divider()
        st.subheader("Apagar")
        confirmo = st.checkbox(
            f"Confirmo que quero apagar {rotulos[id_sel]}",
            key=f"{recurso}_confirma_{id_sel}",
        )
        if st.button(
            f"Apagar {singular.lower()}",
            type="primary",
            disabled=not confirmo,
            key=f"{recurso}_apagar_{id_sel}",
        ):
            try:
                api_client.apagar(recurso, id_sel)
            except ApiError as erro:
                st.error(str(erro))  # 409 se houver vínculos
            else:
                concluir(f"Registro id {id_sel} apagado.")

    def pagina():
        st.title(titulo)
        aviso = st.session_state.pop(chave_aviso, None)
        if aviso:
            st.success(aviso)
        try:
            registros = api_client.listar(recurso)
        except ApiError as erro:
            st.error(str(erro))
            return
        t_lista, t_novo, t_editar = st.tabs(["Lista", "Cadastrar", "Editar / Apagar"])
        with t_lista:
            aba_lista(registros)
        with t_novo:
            aba_cadastrar()
        with t_editar:
            aba_editar_apagar(registros)

    return pagina