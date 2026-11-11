"""Seccion Noticias: titulares de economia y bolsa de Peru y del mundo."""
from __future__ import annotations

import html

import streamlit as st

from app.secciones import frases
from backend import noticias

ESTILO = """
<style>
.nota {padding: 12px 14px; margin-bottom: 8px; border-radius: 12px; background: rgba(255,255,255,.04);
       border: 1px solid rgba(255,255,255,.08); transition: background .2s, border-color .2s, transform .2s;}
.nota:hover {background: rgba(45,212,191,.10); border-color: rgba(45,212,191,.45); transform: translateX(3px);}
.nota a {color: #F2FBF9; font-weight: 600; text-decoration: none; line-height: 1.35;}
.nota a:hover {color: #7FE0CC;}
.nota .meta {font-size: .82rem; color: #8FB3AC; margin-top: 4px;}
</style>
"""


@st.cache_data(ttl=1800, show_spinner="Buscando titulares...")
def _cargar() -> tuple[list[dict], list[str]]:
    lista, fallidas = noticias.descargar()
    return [
        {"titulo": n.titulo, "enlace": n.enlace, "fuente": n.fuente, "region": n.region, "fecha": n.fecha, "mercado": n.de_mercado}
        for n in lista
    ], fallidas


def _tarjeta(n: dict) -> str:
    meta = " · ".join(x for x in (n["fuente"], noticias.hace_cuanto(n["fecha"])) if x)
    return (
        f'<div class="nota"><a href="{html.escape(n["enlace"], quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(n["titulo"])}</a><div class="meta">{html.escape(meta)}</div></div>'
    )


def mostrar() -> None:
    st.markdown(ESTILO, unsafe_allow_html=True)
    frases.mostrar(*frases.NOTICIAS)
    arriba_izq, arriba_der = st.columns([3, 1])
    solo_mercado = arriba_izq.toggle("Solo bolsa, tasas, dólar y materias primas", value=True)
    if arriba_der.button("Actualizar titulares"):
        _cargar.clear()

    lista, fallidas = _cargar()
    if not lista:
        st.warning("No se pudieron cargar las noticias en este momento. Intenta de nuevo en unos minutos.")
        return

    peru, mundo = st.columns(2, gap="large")
    for columna, region, titulo in ((peru, "Perú", "Perú"), (mundo, "Internacional", "Internacional")):
        with columna:
            st.subheader(titulo)
            elegidas = [n for n in lista if n["region"] == region and (n["mercado"] or not solo_mercado)][:12]
            if elegidas:
                st.markdown("".join(_tarjeta(n) for n in elegidas), unsafe_allow_html=True)
            else:
                st.caption("Sin titulares para este filtro.")

    fuentes = ", ".join(f[0] for f in noticias.FUENTES)
    st.caption(
        f"Fuentes: {fuentes}. Se muestran solo titulares con enlace a la nota original y se actualizan cada 30 minutos."
        + (f" No respondieron: {', '.join(fallidas)}." if fallidas else "")
    )
