"""Frases con humor para acompañar las cifras. Nunca son recomendaciones."""
from __future__ import annotations

from datetime import date

import streamlit as st

from interfaz.comunes import soles

ESTILO = """
<style>
.frase {display: inline-flex; align-items: center; gap: 10px; margin: 6px 0 14px; padding: 10px 16px;
        border-radius: 999px; background: rgba(226,179,60,.12); border: 1px solid rgba(226,179,60,.45);
        color: #F7E7B4; font-weight: 600; font-size: .98rem; animation: brillar 3.5s ease-in-out infinite;}
.frase .emoji {font-size: 1.25rem;}
@keyframes brillar {0%,100% {box-shadow: 0 0 0 rgba(226,179,60,0);} 50% {box-shadow: 0 0 22px rgba(226,179,60,.25);}}
@media (prefers-reduced-motion: reduce) {.frase {animation: none;}}
</style>
"""

DEL_DIA = [
    ("👀", "Mirar tus cuentas no muerde. Bueno, a veces un poquito."),
    ("😉", "Tu yo de 65 no acepta excusas, pero sí planes."),
    ("☕", "Un cafecito al día no te arruina. Treinta cafecitos sin anotar, quién sabe."),
    ("🧭", "Sin plan, la plata se va de paseo sin avisar."),
    ("🐢", "Lento pero seguro: así también se llega a los 65."),
    ("🎯", "Hoy es buen día para ponerle nombre a cada sol."),
]


def mostrar(emoji: str, texto: str) -> None:
    st.markdown(ESTILO + f'<div class="frase"><span class="emoji">{emoji}</span><span>{texto}</span></div>', unsafe_allow_html=True)


def del_dia(hoy: date | None = None) -> tuple[str, str]:
    """La misma frase durante todo el día, para que no cambie con cada clic."""
    hoy = hoy or date.today()
    return DEL_DIA[hoy.toordinal() % len(DEL_DIA)]


def del_diario(r: dict, hormiga: dict) -> tuple[str, str]:
    if r["ingresos"] > 0 and r["ahorro"] <= 0:
        return "🆘", "Este mes la billetera pidió auxilio. Tranqui, el próximo se ajusta."
    if hormiga["total"] >= 100:
        return "🐜", f"Los gastos hormiga armaron su fiesta: {soles(hormiga['total'])} en cositas de hasta S/ 30."
    if r["tasa_ahorro"] >= 20:
        return "🐟", "¡Bien ahí! Tu yo de 65 ya está pidiendo un cevichito para celebrar."
    return "😎", "Vas bien. Un poquito más y tu yo de 65 llega con lentes de sol."


def del_portafolio(r: dict) -> tuple[str, str]:
    if r["posiciones"] == 0:
        return "🌱", "Tu portafolio está en modo semillita. Todo empieza por registrar."
    if r["mayor_peso"] >= 40:
        return "🥚", f"El {r['mayor_peso']:.0f} % de tus huevitos está en una sola canasta. Solo para que lo tengas en el radar."
    if r["ganancia"] < 0:
        return "😴", "Tu portafolio anda en modo lunes. Los mercados también tienen días así."
    return "💪", "Tu plata está chambeando por ti."


def del_futuro(igual: float, rescate: float) -> tuple[str, str]:
    if rescate > igual * 1.1:
        return "🙌", f"Tu yo de 65 ya te está agradeciendo: son {soles(rescate - igual)} más en soles de hoy."
    return "🧩", "Cada sol que mueves hoy es una pieza del rompecabezas de tus 65."


NOTICIAS = ("📰", "El chisme financiero del día, con fuente y sin humo.")
