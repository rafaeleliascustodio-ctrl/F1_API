"""Página de Circuitos (CRUD), gerada pelo módulo genérico crud_texto."""

from paginas.crud_texto import criar_pagina

pagina = criar_pagina(
    recurso="circuits",
    titulo="🏁 Circuitos",
    singular="Circuito",
    campos=[
        {"chave": "name", "rotulo": "Nome", "obrigatorio": True},
        {"chave": "location", "rotulo": "Localidade", "obrigatorio": False},
        {"chave": "country", "rotulo": "País", "obrigatorio": False},
    ],
    rotulo_registro=lambda r: f"{r['name']} (id {r['id']})",
)