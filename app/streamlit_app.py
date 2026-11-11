"""Futuro Yo: registra tu dia, ordena deudas e inversiones y mira adonde te llevan a los 65."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.carta import armar_hechos, carta_plantilla, generar_carta, plazo  # noqa: E402
from app.secciones import diario as sec_diario  # noqa: E402
from app.secciones import noticias as sec_noticias  # noqa: E402
from app.secciones import frases, portada  # noqa: E402
from app.secciones import portafolio as sec_portafolio  # noqa: E402
from app.secciones.comunes import FONDO_GRAFICO, GRIS, LINEA, TEAL, TINTA, soles  # noqa: E402
from backend import archivo, datos_bcrp, diario, portafolio  # noqa: E402
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

st.set_page_config(page_title="Futuro Yo · FINANFUNN’NT", page_icon="🌱", layout="wide")

st.markdown(
    """
    <style>
    /* Fondo de toda la app: luces suaves en movimiento, como la portada */
    .stApp {background: #061A19;}
    .stApp::before {content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none;
        background:
          radial-gradient(38% 32% at 12% 18%, rgba(18,165,148,.34), transparent 70%),
          radial-gradient(34% 30% at 88% 72%, rgba(46,111,216,.26), transparent 70%),
          radial-gradient(24% 22% at 58% 38%, rgba(226,179,60,.10), transparent 70%);
        animation: deriva 34s ease-in-out infinite alternate;}
    .stApp::after {content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: .07;
        background-image: linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px);
        background-size: 48px 48px; mask-image: radial-gradient(ellipse at 50% 30%, #000 10%, transparent 70%);}
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {background: transparent;}
    .block-container {max-width: 1140px; padding-top: 3.2rem; position: relative; z-index: 1;}
    h1, h2, h3 {color: #F2FBF9 !important; letter-spacing: -.01em;}

    /* Pestanas como tarjetas deslizables */
    [role="tablist"] {gap: 12px; flex-wrap: nowrap; overflow-x: auto; scroll-snap-type: x mandatory;
        padding: 6px 2px 14px; scrollbar-width: thin; scrollbar-color: rgba(45,212,191,.5) transparent;}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display: none;}
    [data-testid="stTab"] {flex: 0 0 auto; min-width: 190px; height: auto; scroll-snap-align: start;
        justify-content: flex-start; padding: 16px 18px; border-radius: 18px;
        background: linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.02));
        border: 1px solid rgba(255,255,255,.12); transition: transform .25s, border-color .25s, box-shadow .25s, background .25s;}
    [data-testid="stTab"]:hover {transform: translateY(-3px); border-color: rgba(45,212,191,.45);}
    [data-testid="stTab"][aria-selected="true"] {background: linear-gradient(160deg, rgba(45,212,191,.28), rgba(46,111,216,.16));
        border-color: rgba(45,212,191,.8); box-shadow: 0 10px 30px rgba(45,212,191,.20);}
    [data-testid="stTab"] p {font-size: 1rem; font-weight: 650; white-space: nowrap;}
    [role="tabpanel"] {animation: aparecer .45s ease-out;}

    /* Superficies de vidrio */
    [data-testid="stMetric"], [data-testid="stPlotlyChart"], [data-testid="stExpander"] details, .tarjeta, .carta {
        background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.11); border-radius: 16px;
        backdrop-filter: blur(10px);}
    [data-testid="stMetric"] {padding: 14px 18px; transition: transform .2s, border-color .2s;}
    [data-testid="stMetric"]:hover {transform: translateY(-2px); border-color: rgba(45,212,191,.45);}
    [data-testid="stMetricValue"] {color: #FFFFFF;}
    [data-testid="stPlotlyChart"] {padding: 6px;}
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {border-radius: 12px; overflow: hidden;}

    .tarjeta {padding: 18px 20px; margin-bottom: 12px;}
    .tarjeta.destacada {border: 1px solid rgba(45,212,191,.7); background: rgba(45,212,191,.12);
        box-shadow: 0 0 40px rgba(45,212,191,.18);}
    .stMarkdown p.etiqueta {font-size: .92rem; color: #A9C7C0; margin: 0;}
    .stMarkdown p.numero {font-size: 2.3rem; font-weight: 750; color: #FFFFFF; line-height: 1.15; margin: .15rem 0;}
    .stMarkdown p.detalle {font-size: .95rem; color: #A9C7C0; margin: 0;}
    .carta {border-left: 4px solid #2DD4BF; padding: 16px 22px; font-size: 1.08rem; line-height: 1.55; color: #E6F4F1;}
    .carta p {margin: 0 0 .6rem;}

    @keyframes deriva {from {transform: translate(0,0) scale(1);} to {transform: translate(6%,4%) scale(1.08);}}
    @keyframes aparecer {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;}}
    @media (prefers-reduced-motion: reduce) {.stApp::before, [role="tabpanel"] {animation: none !important;}}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=86400, show_spinner="Consultando al BCRP...")
def inflacion_bcrp() -> tuple[dict, bool]:
    return datos_bcrp.obtener()


@st.cache_data(ttl=21600, show_spinner=False)
def tipo_cambio_bcrp() -> tuple[dict, bool]:
    return datos_bcrp.obtener_tipo_cambio()


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
    valor = pd.to_numeric(valor, errors="coerce")
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
    for t, color in ((igual, GRIS), (rescate, TEAL)):
        fig.add_scatter(
            x=t.edades,
            y=t.patrimonio_real,
            name=t.nombre,
            mode="lines",
            line={"color": color, "width": 2.5 if t is rescate else 2},
            hovertemplate="S/ %{y:,.0f}",
        )
        fig.add_annotation(
            x=t.edades[-1], y=t.patrimonio_real[-1], text=t.nombre, showarrow=False,
            xanchor="left", xshift=8, font={"size": 13, "color": TINTA},
        )
    fig.update_layout(
        height=350,
        margin={"l": 10, "r": 110, "t": 36, "b": 10},
        hovermode="x unified",
        plot_bgcolor=FONDO_GRAFICO,
        paper_bgcolor=FONDO_GRAFICO,
        legend={"orientation": "h", "y": 1.13, "x": 0},
        font={"color": TINTA},
        hoverlabel={"bgcolor": "#0B2726", "font": {"color": "#FFFFFF"}},
    )
    fig.update_xaxes(title="Edad", showgrid=False, ticksuffix=" años", showline=True, linecolor=LINEA)
    fig.update_yaxes(title="Patrimonio en soles de hoy", tickprefix="S/ ", tickformat=",.0f", gridcolor=LINEA, zeroline=True, zerolinecolor=LINEA)
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


def reiniciar(datos: dict | None) -> None:
    """Carga un archivo (o vuelve al ejemplo) y redibuja todo desde cero."""
    st.session_state["cargado"] = datos
    for clave in ("diario", "portafolio", "carta_ia"):
        st.session_state.pop(clave, None)
    st.session_state.version += 1
    st.rerun()


# ---------- Estado inicial ----------
if "version" not in st.session_state:
    st.session_state.version = 0
v = st.session_state.version
cargado = st.session_state.get("cargado") or {}
pdef, tdef = cargado.get("perfil", {}), cargado.get("tablas", {})
ejemplo = perfil_ejemplo()

if "diario" not in st.session_state:
    st.session_state["diario"] = diario.limpiar(tdef["diario"]) if "diario" in tdef else diario.ejemplo()
if "portafolio" not in st.session_state:
    st.session_state["portafolio"] = portafolio.limpiar(tdef["portafolio"]) if "portafolio" in tdef else portafolio.ejemplo()

bcrp, en_vivo = inflacion_bcrp()
tc_info, tc_en_vivo = tipo_cambio_bcrp()

caja_portada = st.container()
caja_archivo = st.container()
tab_orden, tab_diario, tab_port, tab_futuro, tab_noticias = st.tabs(
    [
        ":material/account_balance_wallet: Ordena tu dinero",
        ":material/edit_calendar: Mi diario",
        ":material/pie_chart: Portafolio",
        ":material/rocket_launch: Tu yo de 65",
        ":material/newspaper: Noticias de bolsa",
    ]
)

# ---------- 1. Ordena tu dinero ----------
with tab_orden:
    izquierda, derecha = st.columns([1, 2.1], gap="large")

    with izquierda:
        st.subheader("Tú hoy")
        edad = st.number_input("Edad", 18, 64, int(pdef.get("edad", ejemplo.edad)), key=f"edad{v}")
        sueldo = st.number_input("Sueldo bruto mensual (S/)", 0, 200000, int(pdef.get("sueldo_bruto", ejemplo.sueldo_bruto)), 100, key=f"sueldo{v}")
        neto = st.number_input("Ingreso neto mensual (S/)", 0, 200000, int(pdef.get("ingreso_neto", ejemplo.ingreso_neto)), 100, key=f"neto{v}")
        gastos = st.number_input("Gastos mensuales sin cuotas (S/)", 0, 200000, int(pdef.get("gastos", ejemplo.gastos)), 100, key=f"gastos{v}")
        saldo_afp = st.number_input("Saldo en tu AFP (S/)", 0, 5000000, int(pdef.get("saldo_afp", ejemplo.saldo_afp)), 500, key=f"afp{v}")
        densidad = st.slider(
            "Parte del tiempo en que aportas a tu AFP (%)", 0, 100, int(pdef.get("densidad_aportes", ejemplo.densidad_aportes)), 5,
            key=f"dens{v}", help="Si pasas temporadas sin empleo formal, tus aportes se interrumpen.",
        )
        if st.button("Volver al ejemplo"):
            reiniciar(None)

    with derecha:
        deudas_base, inversiones_base = tablas_ejemplo()
        if "deudas" in tdef:
            deudas_base = tdef["deudas"].reindex(columns=deudas_base.columns)
        if "inversiones" in tdef:
            inversiones_base = tdef["inversiones"].reindex(columns=inversiones_base.columns)
        st.subheader("Lo que debes")
        tabla_deudas = st.data_editor(
            deudas_base, num_rows="dynamic", hide_index=True, width="stretch", key=f"t_deudas{v}",
            column_config={
                "Saldo (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
                "TCEA (%)": st.column_config.NumberColumn(min_value=0, max_value=200, format="%.1f"),
                "Cuota mensual (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
            },
        )
        st.subheader("Lo que tienes")
        tabla_inversiones = st.data_editor(
            inversiones_base, num_rows="dynamic", hide_index=True, width="stretch", key=f"t_inv{v}",
            column_config={
                "Saldo (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
                "Aporte mensual (S/)": st.column_config.NumberColumn(min_value=0, format="%.0f"),
                "Retorno anual (%)": st.column_config.NumberColumn(min_value=-20, max_value=30, format="%.1f"),
            },
        )
        st.caption("Aquí van tus ahorros e inversiones con el retorno que supones para proyectar. El detalle de cada inversión va en Portafolio.")

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
        inflacion = c1.number_input("Inflación anual (%)", 0.0, 20.0, float(pdef.get("inflacion", bcrp["promedio_10_anos"])), 0.1, key=f"inf{v}")
        alza = c2.number_input("Alza anual de sueldo (%)", 0.0, 20.0, float(pdef.get("alza_sueldo", bcrp["promedio_10_anos"])), 0.1, key=f"alza{v}")
        retorno_afp = c3.number_input("Retorno anual AFP (%)", -5.0, 20.0, float(pdef.get("retorno_afp", ejemplo.retorno_afp)), 0.1, key=f"rafp{v}")
        retorno_rescate = c4.number_input(
            "Retorno del dinero liberado (%)", -5.0, 20.0, float(pdef.get("retorno_rescate", ejemplo.retorno_rescate)), 0.1, key=f"rres{v}"
        )
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

# ---------- 2. Mi diario ----------
with tab_diario:
    tabla_diario = sec_diario.mostrar(perfil)

# ---------- 3. Portafolio ----------
with tab_port:
    tabla_portafolio = sec_portafolio.mostrar(tc_info, tc_en_vivo)

# ---------- 4. Rescate y tu yo de 65 ----------
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
    frases.mostrar(*frases.del_futuro(igual.patrimonio_final_real, rescate.patrimonio_final_real))

    st.plotly_chart(grafico_futuro(igual, rescate), width="stretch", config={"displayModeBar": False})

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
        carta = resultado.carta
        nota = "Redactada con IA. Todas las cifras vienen del simulador." if resultado.origen == "ia" else resultado.nota + " Se muestra la versión sin IA."
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
            width="stretch",
        )

# ---------- 5. Noticias ----------
with tab_noticias:
    sec_noticias.mostrar()

# ---------- Portada y archivo (se dibujan arriba, con las cifras ya calculadas) ----------
with caja_portada:
    portada.mostrar(foto.patrimonio_neto, igual.patrimonio_final_real, rescate.patrimonio_final_real)
    frases.mostrar(*frases.del_dia())

with caja_archivo:
    with st.expander("Guarda o abre tu archivo personal"):
        g1, g2 = st.columns(2, gap="large")
        datos_perfil = {
            "edad": perfil.edad, "sueldo_bruto": perfil.sueldo_bruto, "ingreso_neto": perfil.ingreso_neto,
            "gastos": perfil.gastos, "saldo_afp": perfil.saldo_afp, "densidad_aportes": perfil.densidad_aportes,
            "inflacion": perfil.inflacion, "alza_sueldo": perfil.alza_sueldo,
            "retorno_afp": perfil.retorno_afp, "retorno_rescate": perfil.retorno_rescate,
        }
        tablas = {"deudas": tabla_deudas, "inversiones": tabla_inversiones, "diario": tabla_diario, "portafolio": tabla_portafolio}
        g1.download_button(
            "Descargar mi archivo",
            data=archivo.guardar(datos_perfil, tablas),
            file_name=f"futuro-yo-{date.today().isoformat()}.json",
            mime="application/json",
            type="primary",
        )
        g1.caption("Tus datos no se guardan en el servidor. Descarga tu archivo y súbelo otro día para continuar.")
        subido = g2.file_uploader("Abrir un archivo guardado", type=["json"], key=f"subir{v}")
    if subido is not None:
        try:
            reiniciar(archivo.abrir(subido.getvalue()))
        except ValueError as error:
            st.error(str(error))
