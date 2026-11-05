"""Página de Equipes (CRUD), gerada pelo módulo genérico crud_texto."""

from paginas.crud_texto import criar_pagina

pagina = criar_pagina(
    recurso="teams",
    titulo="🏎️ Equipes",
    singular="Equipe",
    campos=[
        {"chave": "name", "rotulo": "Nome", "obrigatorio": True},
        {"chave": "country", "rotulo": "País", "obrigatorio": False},
    ],
    rotulo_registro=lambda r: f"{r['name']} (id {r['id']})",
)