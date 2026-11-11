"""Piezas visuales compartidas por las secciones."""
from __future__ import annotations

import plotly.graph_objects as go

TEAL = "#0F766E"
GRIS = "#6B7780"
TINTA = "#33474C"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]


def soles(valor: float) -> str:
    signo = "-" if valor < 0 else ""
    return f"{signo}S/ {abs(valor):,.0f}"


def nombre_mes(clave: str) -> str:
    anio, mes = clave.split("-")
    return f"{MESES[int(mes) - 1].capitalize()} {anio}"


def barras_horizontales(etiquetas: list[str], valores: list[float], sufijo: str = "", prefijo: str = "") -> go.Figure:
    """Barras de una sola serie, ordenadas de mayor a menor, con su valor al lado."""
    textos = [f"{prefijo}{v:,.0f}{sufijo}" for v in valores]
    fig = go.Figure(
        go.Bar(
            x=valores[::-1],
            y=etiquetas[::-1],
            orientation="h",
            marker={"color": TEAL, "cornerradius": 4},
            text=textos[::-1],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: " + prefijo + "%{x:,.0f}" + sufijo + "<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(180, 46 * len(etiquetas) + 40),
        margin={"l": 10, "r": 70, "t": 10, "b": 10},
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font={"color": TINTA},
        bargap=0.35,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(showgrid=False, ticks="")
    return fig
