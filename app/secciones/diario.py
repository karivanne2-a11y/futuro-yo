"""Seccion Mi diario: registrar movimientos y ver el resumen del mes."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from app.secciones import frases
from app.secciones.comunes import barras_horizontales, nombre_mes, soles
from backend import diario
from backend.motor import Perfil, valor_futuro_real


def mostrar(perfil: Perfil) -> pd.DataFrame:
    n = st.session_state.setdefault("n_diario", 0)

    st.subheader("Registra tu día")
    c1, c2, c3, c4, c5 = st.columns([1.1, 1.1, 1.4, 1, 1.6])
    fecha = c1.date_input("Fecha", value=date.today(), format="DD/MM/YYYY", key=f"d_fecha{n}")
    tipo = c2.selectbox("Tipo", diario.TIPOS, key=f"d_tipo{n}")
    categoria = c3.selectbox("Categoría", diario.CATEGORIAS[tipo], key=f"d_cat{n}_{tipo}")
    monto = c4.number_input("Monto (S/)", min_value=0.0, step=1.0, format="%.2f", key=f"d_monto{n}")
    nota = c5.text_input("Nota (opcional)", max_chars=80, key=f"d_nota{n}")
    agregar = st.button("Agregar movimiento", type="primary")

    resumen_caja = st.container()

    with st.expander("Ver y editar todos los movimientos"):
        editado = st.data_editor(
            st.session_state["diario"],
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            key=f"ed_diario{st.session_state.get('version', 0)}_{n}",
            column_config={
                "Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Tipo": st.column_config.SelectboxColumn(options=diario.TIPOS),
                "Categoría": st.column_config.SelectboxColumn(options=diario.TODAS_CATEGORIAS),
                "Monto (S/)": st.column_config.NumberColumn(min_value=0, format="%.2f"),
            },
        )
        st.caption("Para borrar, selecciona la fila a la izquierda y presiona Suprimir.")

    if agregar:
        if monto <= 0:
            st.warning("Ingresa un monto mayor que cero.")
        else:
            nueva = pd.DataFrame([{"Fecha": pd.Timestamp(fecha), "Tipo": tipo, "Categoría": categoria, "Monto (S/)": monto, "Nota": nota}])
            st.session_state["diario"] = diario.limpiar(pd.concat([editado, nueva], ignore_index=True))
            st.session_state["n_diario"] = n + 1
            st.toast(f"Registrado: {tipo.lower()} de {soles(monto)}")
            st.rerun()

    tabla = diario.limpiar(editado)
    with resumen_caja:
        _resumen(tabla, perfil)
    return tabla


def _resumen(tabla: pd.DataFrame, perfil: Perfil) -> None:
    meses = diario.meses_disponibles(tabla)
    if not meses:
        st.info("Aún no hay movimientos. Registra el primero arriba.")
        return

    st.subheader("Tu mes")
    mes = st.selectbox("Mes", meses, format_func=nombre_mes, label_visibility="collapsed")
    r = diario.resumen_mes(tabla, mes)
    if mes == date.today().strftime("%Y-%m"):
        st.caption("Mes en curso: las cifras cambian a medida que registras.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos", soles(r["ingresos"]))
    m2.metric("Gastos", soles(r["gastos"]))
    m3.metric("Pagos de deuda", soles(r["pagos_deuda"]))
    m4.metric("Invertido", soles(r["invertido"]))
    frases.mostrar(*frases.del_diario(r, diario.gastos_pequenos(tabla, mes)))

    izquierda, derecha = st.columns([1.3, 1], gap="large")
    with izquierda:
        categorias = diario.gastos_por_categoria(tabla, mes)
        if len(categorias):
            st.markdown("**En qué se fue tu dinero**")
            st.plotly_chart(
                barras_horizontales(list(categorias.index), list(categorias.values), prefijo="S/ "),
                width="stretch",
                config={"displayModeBar": False},
            )
    with derecha:
        anos = max(perfil.edad_retiro - perfil.edad, 0)
        if r["ahorro"] > 0:
            futuro = valor_futuro_real(r["ahorro"], anos * 12, perfil.retorno_rescate, perfil.inflacion)
            st.markdown(
                f'<div class="tarjeta destacada"><p class="etiqueta">Este mes no consumiste {soles(r["ahorro"])}, '
                f'el {r["tasa_ahorro"]:.0f} % de tus ingresos</p><p class="numero">{soles(futuro)}</p>'
                f'<p class="detalle">sería ese ahorro repetido cada mes hasta los 65, en soles de hoy</p></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="tarjeta"><p class="etiqueta">Este mes</p><p class="numero">{soles(r["ahorro"])}</p>'
                '<p class="detalle">Gastaste y pagaste más de lo que ingresó.</p></div>',
                unsafe_allow_html=True,
            )
        hormiga = diario.gastos_pequenos(tabla, mes)
        if hormiga["cantidad"]:
            st.markdown(
                f"**Gastos pequeños:** {hormiga['cantidad']:.0f} gastos de hasta S/ 30 suman {soles(hormiga['total'])} este mes."
            )
        if r["sin_asignar"] > 0:
            st.markdown(f"**Sin destino:** {soles(r['sin_asignar'])} no se registraron como inversión.")
