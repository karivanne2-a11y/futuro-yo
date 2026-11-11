"""Seccion Portafolio: inversiones realizadas, valor actual y composicion."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from interfaz import frases
from interfaz.comunes import barras_horizontales, soles
from backend import portafolio


def mostrar(tipo_cambio: dict, en_vivo: bool) -> pd.DataFrame:
    st.subheader("Tus inversiones")
    izquierda, derecha = st.columns([2.2, 1], gap="large")
    with derecha:
        tc = st.number_input("Tipo de cambio (S/ por US$)", 1.0, 10.0, float(tipo_cambio["valor"]), 0.001, format="%.3f", key="tc")
        if tipo_cambio.get("fecha"):
            origen = "consultado ahora" if en_vivo else "copia guardada"
            st.caption(f"BCRP, venta del sistema bancario al {tipo_cambio['fecha']} ({origen}).")
    with izquierda:
        editado = st.data_editor(
            st.session_state["portafolio"],
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            key=f"ed_port{st.session_state.get('version', 0)}",
            column_config={
                "Tipo": st.column_config.SelectboxColumn(options=portafolio.TIPOS),
                "Mercado": st.column_config.SelectboxColumn(options=portafolio.MERCADOS),
                "Moneda": st.column_config.SelectboxColumn(options=portafolio.MONEDAS),
                "Invertido": st.column_config.NumberColumn(min_value=0, format="%.2f", help="En la moneda de la fila"),
                "Valor actual": st.column_config.NumberColumn(min_value=0, format="%.2f", help="Lo que vale hoy, según tu cuenta"),
            },
        )
        st.caption("Tú ingresas el valor actual que ves en tu cuenta. La app no consulta precios ni recomienda comprar o vender.")

    r = portafolio.resumen(editado, tc)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Valor actual", soles(r["valor"]))
    m2.metric("Invertido", soles(r["invertido"]))
    m3.metric("Ganancia o pérdida", soles(r["ganancia"]))
    m4.metric("Rentabilidad simple", f"{r['rentabilidad']:.1f} %", help="Ganancia sobre lo invertido. No está anualizada.")
    frases.mostrar(*frases.del_portafolio(r))

    if r["posiciones"]:
        d = portafolio.detalle(editado, tc)
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            st.markdown("**Peso de cada inversión en tu portafolio**")
            st.plotly_chart(
                barras_horizontales(list(d["Activo"]), list(d["Peso (%)"]), sufijo=" %"),
                width="stretch",
                config={"displayModeBar": False},
            )
        with b:
            st.markdown("**Lo que muestra tu portafolio**")
            for nota in portafolio.observaciones(r):
                st.markdown(f"- {nota}")
    return portafolio.limpiar(editado)
