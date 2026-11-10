"""Futuro Yo: ordena tus deudas e inversiones y mira adonde te llevan a los 65."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.carta import armar_hechos, carta_plantilla, generar_carta, plazo, soles  # noqa: E402
from backend import datos_bcrp  # noqa: E402
from backend.motor import (  # noqa: E402
    Deuda,
    Inversion,
    Perfil,
    foto_hoy,
    ingreso_mensual_equivalente,
    perfil_ejemplo,
    simular,
)

load_dotenv()
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:  # En local puede no existir el archivo de secretos.
    pass

st.set_page_config(page_title="Futuro Yo", page_icon="🌱", layout="wide")

COLOR_IGUAL = "#6B7780"
COLOR_RESCATE = "#0F766E"

st.markdown(
    """
    <style>
    .block-container {max-width: 1120px; padding-top: 4.5rem;}
    .stMarkdown p.marca {font-size: 2.8rem; font-weight: 750; letter-spacing: -.02em; line-height: 1.1; margin: 0; color: #12312F;}
    .stMarkdown p.lema {font-size: 1.15rem; color: #44545A; margin: .2rem 0 .4rem;}
    .stMarkdown p.aviso {font-size: .86rem; color: #5B6A70;}
    .tarjeta {border: 1px solid #DCE4E3; border-radius: 12px; padding: 18px 20px; background: #FFFFFF;}
    .tarjeta.destacada {border: 2px solid #0F766E; background: #F0F9F7;}
    .etiqueta {font-size: .9rem; color: #4C5C62; margin: 0;}
    .stMarkdown p.numero {font-size: 2.4rem; font-weight: 750; color: #12312F; line-height: 1.15; margin: .15rem 0;}
    .detalle {font-size: .95rem; color: #4C5C62; margin: 0;}
    .carta {border-left: 4px solid #0F766E; background: #F7FAF9; padding: 16px 22px; border-radius: 0 10px 10px 0;
            font-size: 1.08rem; line-height: 1.55; color: #1E3236;}
    .carta p {margin: 0 0 .6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=86400, show_spinner="Consultando al BCRP...")
def inflacion_bcrp() -> tuple[dict, bool]:
    return datos_bcrp.obtener()


def tablas_ejemplo() -> tuple[pd.DataFrame, pd.DataFrame]:
    p = perfil_ejemplo()
    deudas = pd.DataFrame(
        [{"Deuda": d.nombre, "Saldo (S/)": d.saldo, "TCEA (%)": d.tcea, "Cuota mensual (S/)": d.cuota} for d in p.deudas]
    )
    inversiones = pd.DataFrame(
        [
            {"Ahorro o inversión": i.nombre, "Saldo (S/)": i.saldo, "Aporte mensual (S/)": i.aporte, "Retorno anual (%)": i.retorno}
            for i in p.inversiones
        ]
    )
    return deudas, inversiones


def numero(valor, defecto: float = 0.0) -> float:
    return defecto if pd.isna(valor) else float(valor)


def leer_deudas(tabla: pd.DataFrame) -> list[Deuda]:
    filas = []
    for _, f in tabla.iterrows():
        saldo = numero(f["Saldo (S/)"])
        if saldo > 0:
            nombre = f["Deuda"] if isinstance(f["Deuda"], str) and f["Deuda"].strip() else "Deuda sin nombre"
            filas.append(Deuda(nombre, saldo, numero(f["TCEA (%)"]), numero(f["Cuota mensual (S/)"])))
    return filas


def leer_inversiones(tabla: pd.DataFrame) -> list[Inversion]:
    filas = []
    for _, f in tabla.iterrows():
        saldo, aporte = numero(f["Saldo (S/)"]), numero(f["Aporte mensual (S/)"])
        if saldo > 0 or aporte > 0:
            nombre = f["Ahorro o inversión"]
            nombre = nombre if isinstance(nombre, str) and nombre.strip() else "Sin nombre"
            filas.append(Inversion(nombre, saldo, aporte, numero(f["Retorno anual (%)"])))
    return filas


def con_retorno_ajustado(perfil: Perfil, puntos: float) -> Perfil:
    """Mueve todos los retornos para mostrar que la proyeccion es incierta."""
    return replace(
        perfil,
        retorno_afp=perfil.retorno_afp + puntos,
        retorno_rescate=perfil.retorno_rescate + puntos,
        inversiones=[replace(i, retorno=i.retorno + puntos) for i in perfil.inversiones],
    )


def tarjeta(etiqueta: str, valor: str, detalle: str, destacada: bool = False) -> None:
    clase = "tarjeta destacada" if destacada else "tarjeta"
    st.markdown(
        f'<div class="{clase}"><p class="etiqueta">{etiqueta}</p>'
        f'<p class="numero">{valor}</p><p class="detalle">{detalle}</p></div>',
        unsafe_allow_html=True,
    )


def grafico_futuro(igual, rescate) -> go.Figure:
    fig = go.Figure()
    for t, color in ((igual, COLOR_IGUAL), (rescate, COLOR_RESCATE)):
        fig.add_scatter(
            x=t.edades,
            y=t.patrimonio_real,
            name=t.nombre,
            mode="lines",
            line={"color": color, "width": 2.5 if t is rescate else 2},
            hovertemplate="S/ %{y:,.0f}",
        )
        fig.add_annotation(
            x=t.edades[-1],
            y=t.patrimonio_real[-1],
            text=t.nombre,
            showarrow=False,
            xanchor="left",
            xshift=8,
            font={"size": 13, "color": "#33474C"},
        )
    fig.update_layout(
        height=350,
        margin={"l": 10, "r": 110, "t": 36, "b": 10},
        hovermode="x unified",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend={"orientation": "h", "y": 1.13, "x": 0},
        font={"color": "#33474C"},
    )
    fig.update_xaxes(title="Edad", showgrid=False, ticksuffix=" años", showline=True, linecolor="#C9D3D2")
    fig.update_yaxes(title="Patrimonio en soles de hoy", tickprefix="S/ ", tickformat=",.0f", gridcolor="#EAEFEE", zeroline=True, zerolinecolor="#C9D3D2")
    return fig


def boton_voz(texto: str) -> None:
    seguro = json.dumps(texto, ensure_ascii=False).replace("</", "<\\/")
    components.html(
        f"""
        <button id="v" style="font:600 15px system-ui;padding:9px 16px;border-radius:8px;border:1px solid #0F766E;
                background:#0F766E;color:#fff;cursor:pointer">Escuchar a mi yo de 65</button>
        <span id="m" style="font:13px system-ui;color:#5B6A70;margin-left:10px"></span>
        <script>
        const b = document.getElementById("v"), m = document.getElementById("m"), s = window.speechSynthesis;
        b.onclick = () => {{
          if (!s) {{ m.textContent = "Tu navegador no tiene voz."; return; }}
          if (s.speaking) {{ s.cancel(); b.textContent = "Escuchar a mi yo de 65"; return; }}
          const u = new SpeechSynthesisUtterance({seguro});
          u.lang = "es-PE"; u.rate = 0.96;
          const voz = s.getVoices().find(v => v.lang.toLowerCase().startsWith("es"));
          if (voz) u.voice = voz;
          u.onend = () => b.textContent = "Escuchar a mi yo de 65";
          b.textContent = "Detener"; s.speak(u);
        }};
        </script>
        """,
        height=52,
    )


# ---------- Encabezado ----------
if "version" not in st.session_state:
    st.session_state.version = 0
v = st.session_state.version

st.markdown('<p class="marca">Futuro Yo</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="lema">Ordena tus deudas, ahorros e inversiones, y mira adónde te llevan a los 65 años.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="aviso">Simulador educativo: no es asesoría financiera, previsional ni de inversión. '
    "Tus datos solo viven en esta sesión y no se guardan. El ejemplo cargado es una persona ficticia.</p>",
    unsafe_allow_html=True,
)

bcrp, en_vivo = inflacion_bcrp()
tab_orden, tab_futuro = st.tabs(["1. Ordena tu dinero", "2. Rescate y tu yo de 65"])

# ---------- Paso 1: datos ----------
with tab_orden:
    ejemplo = perfil_ejemplo()
    izquierda, derecha = st.columns([1, 2.1], gap="large")

    with izquierda:
        st.subheader("Tú hoy")
        edad = st.number_input("Edad", 18, 64, ejemplo.edad, key=f"edad{v}")
        sueldo = st.number_input("Sueldo bruto mensual (S/)", 0, 200000, int(ejemplo.sueldo_bruto), 100, key=f"sueldo{v}")
        neto = st.number_input("Ingreso neto mensual (S/)", 0, 200000, int(ejemplo.ingreso_neto), 100, key=f"neto{v}")
        gastos = st.number_input("Gastos mensuales sin cuotas (S/)", 0, 200000, int(ejemplo.gastos), 100, key=f"gastos{v}")
        saldo_afp = st.number_input("Saldo en tu AFP (S/)", 0, 5000000, int(ejemplo.saldo_afp), 500, key=f"afp{v}")
        densidad = st.slider(
            "Parte del tiempo en que aportas a tu AFP (%)", 0, 100, int(ejemplo.densidad_aportes), 5, key=f"dens{v}",
            help="Si pasas temporadas sin empleo formal, tus aportes se interrumpen.",
        )
        if st.button("Restaurar ejemplo"):
            st.session_state.version += 1
            st.rerun()

    with derecha:
        deudas_base, inversiones_base = tablas_ejemplo()
        st.subheader("Lo que debes")
        tabla_deudas = st.data_editor(
            deudas_base, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"t_deudas{v}",
            column_config={
                "Saldo (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
                "TCEA (%)": st.column_config.NumberColumn(min_value=0, max_value=200, format="%.1f"),
                "Cuota mensual (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
            },
        )
        st.subheader("Lo que tienes")
        tabla_inversiones = st.data_editor(
            inversiones_base, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"t_inv{v}",
            column_config={
                "Saldo (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
                "Aporte mensual (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
                "Retorno anual (%)": st.column_config.NumberColumn(min_value=-20, max_value=30, format="%.1f"),
            },
        )

    with st.expander("Supuestos de la proyección"):
        origen = "consultado ahora" if en_vivo else "copia guardada"
        if bcrp.get("ultimo_periodo"):
            st.caption(
                f"Inflación de Lima según el BCRP ({origen}): {bcrp['ultimo_valor']:.2f} % a 12 meses en "
                f"{bcrp['ultimo_periodo']}. Promedio de los últimos 10 años: {bcrp['promedio_10_anos']:.2f} %."
            )
        else:
            st.caption("No se pudo leer el BCRP: se usa una inflación supuesta de 2.5 %.")
        c1, c2, c3, c4 = st.columns(4)
        inflacion = c1.number_input("Inflación anual (%)", 0.0, 20.0, float(bcrp["promedio_10_anos"]), 0.1, key=f"inf{v}")
        alza = c2.number_input("Alza anual de sueldo (%)", 0.0, 20.0, float(bcrp["promedio_10_anos"]), 0.1, key=f"alza{v}")
        retorno_afp = c3.number_input("Retorno anual AFP (%)", -5.0, 20.0, ejemplo.retorno_afp, 0.1, key=f"rafp{v}")
        retorno_rescate = c4.number_input("Retorno del dinero liberado (%)", -5.0, 20.0, ejemplo.retorno_rescate, 0.1, key=f"rres{v}")
        st.caption("Los retornos son supuestos que tú puedes cambiar. No son predicciones ni rentabilidades ofrecidas por nadie.")

    perfil = Perfil(
        edad=int(edad),
        sueldo_bruto=float(sueldo),
        ingreso_neto=float(neto),
        gastos=float(gastos),
        saldo_afp=float(saldo_afp),
        densidad_aportes=float(densidad),
        deudas=leer_deudas(tabla_deudas),
        inversiones=leer_inversiones(tabla_inversiones),
        inflacion=float(inflacion),
        alza_sueldo=float(alza),
        retorno_afp=float(retorno_afp),
        retorno_rescate=float(retorno_rescate),
    )
    foto = foto_hoy(perfil)

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Patrimonio neto", soles(foto.patrimonio_neto), help="Lo que tienes, incluida tu AFP, menos lo que debes.")
    m2.metric("Deuda total", soles(foto.deuda_total))
    m3.metric("Sueldo que va a cuotas", f"{foto.carga_deuda_pct:.0f} %")
    m4.metric("Te queda libre al mes", soles(foto.flujo_libre))

# ---------- Paso 2: rescate y futuro ----------
with tab_futuro:
    maximo = max(int(foto.flujo_libre), 0)
    clave_extra = f"extra{v}"
    if clave_extra in st.session_state and st.session_state[clave_extra] > maximo:
        st.session_state[clave_extra] = maximo

    if maximo >= 10:
        extra = st.slider(
            "¿Cuánto más podrías destinar cada mes a salir de deudas?", 0, maximo, min(150, maximo), 10,
            key=clave_extra, format="S/ %d",
        )
    else:
        extra = 0
        st.warning("Con estos datos no te queda dinero libre al mes. El rescate solo reordena tus cuotas actuales.")

    igual = simular(perfil)
    rescate = simular(perfil, rescate=True, extra=extra)

    if igual.deudas_sin_amortizar:
        st.error(
            "Estas cuotas no cubren ni los intereses, y la deuda seguiría creciendo: "
            + ", ".join(igual.deudas_sin_amortizar) + ". Revisa los datos o busca orientación sobre esa deuda."
        )

    ingreso_igual = ingreso_mensual_equivalente(igual.patrimonio_final_real, perfil.anos_retiro, perfil.retorno_real_retiro)
    ingreso_rescate = ingreso_mensual_equivalente(rescate.patrimonio_final_real, perfil.anos_retiro, perfil.retorno_real_retiro)
    bajo = simular(con_retorno_ajustado(perfil, -2), rescate=True, extra=extra).patrimonio_final_real
    alto = simular(con_retorno_ajustado(perfil, 2), rescate=True, extra=extra).patrimonio_final_real

    a, b = st.columns(2)
    with a:
        tarjeta("Si sigues igual, a los 65", soles(igual.patrimonio_final_real), f"Podría sostener cerca de {soles(ingreso_igual)} al mes por 20 años")
    with b:
        tarjeta(
            "Con el rescate, a los 65", soles(rescate.patrimonio_final_real),
            f"Podría sostener cerca de {soles(ingreso_rescate)} al mes por 20 años", destacada=True,
        )
    st.caption(
        f"En soles de hoy. Si los retornos fueran 2 puntos menores o mayores, el rescate daría entre {soles(bajo)} y {soles(alto)}. "
        "El rescate supone que, al terminar las deudas, sigues apartando ese dinero en lugar de gastarlo. No es una pensión oficial."
    )

    st.plotly_chart(grafico_futuro(igual, rescate), use_container_width=True, config={"displayModeBar": False})

    d1, d2, d3 = st.columns(3)
    d1.metric("Libre de deudas si sigues igual", plazo(igual.meses_sin_deuda))
    d2.metric("Libre de deudas con el rescate", plazo(rescate.meses_sin_deuda))
    d3.metric("Intereses que evitarías", soles(max(igual.intereses_pagados - rescate.intereses_pagados, 0)))

    if perfil.deudas:
        orden = sorted(perfil.deudas, key=lambda d: d.tcea, reverse=True)
        st.markdown(
            "**Orden que simula el rescate:** "
            + " → ".join(f"{i + 1}. {d.nombre} ({d.tcea:.0f} %)" for i, d in enumerate(orden))
            + ". Se mantiene la cuota de todas y el dinero adicional va a la de mayor costo."
        )

    st.subheader("Una carta de tu yo de 65")
    hechos = armar_hechos(perfil.edad, perfil.edad_retiro, igual, rescate, ingreso_igual, ingreso_rescate, extra)
    guardada = st.session_state.get("carta_ia")
    if guardada and guardada["hechos"] == hechos:
        resultado = guardada["resultado"]
        carta, nota = resultado.carta, (
            "Redactada con IA. Todas las cifras vienen del simulador." if resultado.origen == "ia" else resultado.nota + " Se muestra la versión sin IA."
        )
    else:
        carta, nota = carta_plantilla(hechos), "Escrita con tus cifras, sin IA."

    decisiones = "".join(f"<p>• {d}</p>" for d in carta.decisiones)
    st.markdown(
        f'<div class="carta"><p>{carta.saludo}</p><p>{carta.lo_que_cambio}</p>{decisiones}'
        f"<p>{carta.advertencia}</p><p><b>{carta.cierre}</b></p></div>",
        unsafe_allow_html=True,
    )
    st.caption(nota)

    voz, ia = st.columns([1, 1])
    with voz:
        boton_voz(carta.como_texto())
    with ia:
        if os.getenv("ANTHROPIC_API_KEY") and st.button("Reescribir la carta con IA"):
            with st.spinner("Tu yo de 65 está escribiendo..."):
                st.session_state["carta_ia"] = {"hechos": hechos, "resultado": generar_carta(hechos)}
            st.rerun()

    with st.expander("Ver los datos del gráfico en una tabla"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Edad": [int(e) for e in igual.edades],
                    "Seguir igual (S/ de hoy)": [round(x) for x in igual.patrimonio_real],
                    "Con rescate (S/ de hoy)": [round(x) for x in rescate.patrimonio_real],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
