"""Portada animada de Futuro Yo."""
from __future__ import annotations

import streamlit as st

from interfaz.comunes import soles

ESTILO = """
<style>
.hero {position: relative; overflow: hidden; border-radius: 22px; padding: 56px 44px 44px;
       background: #0B2726; color: #EAF6F3; margin-bottom: 8px; isolation: isolate;}
.hero .aurora {position: absolute; border-radius: 50%; filter: blur(60px); opacity: .55; z-index: -1;}
.hero .a1 {width: 520px; height: 520px; background: #12A594; top: -220px; left: -120px; animation: flotar1 16s ease-in-out infinite alternate;}
.hero .a2 {width: 460px; height: 460px; background: #2E6FD8; bottom: -260px; right: -80px; animation: flotar2 19s ease-in-out infinite alternate;}
.hero .a3 {width: 300px; height: 300px; background: #E2B33C; top: 30%; left: 55%; opacity: .28; animation: flotar1 23s ease-in-out infinite alternate-reverse;}
.hero .rejilla {position: absolute; inset: 0; z-index: -1; opacity: .12;
       background-image: linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px);
       background-size: 44px 44px; mask-image: radial-gradient(ellipse at 30% 40%, #000 20%, transparent 75%);}
.hero .kicker {font: 600 .78rem/1 ui-monospace, monospace; letter-spacing: .22em; color: #9FE3D6; margin: 0 0 16px;
       animation: subir .8s ease-out both;}
.hero .titular {font-size: clamp(2rem, 4.6vw, 3.4rem); font-weight: 760; line-height: 1.05; letter-spacing: -.025em;
       max-width: 17ch; margin: 0 0 16px; color: #FFFFFF; animation: subir .9s .1s ease-out both;}
.hero .titular em {font-style: normal; color: #7FE0CC;}
.hero .bajada {font-size: 1.12rem; line-height: 1.5; max-width: 54ch; color: #C9E4DE; margin: 0 0 30px; animation: subir .9s .2s ease-out both;}
.hero .chips {display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px;}
.hero .chip {background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.16); border-radius: 16px; padding: 16px 18px;
       backdrop-filter: blur(6px); animation: subir .9s ease-out both, mecer 6s ease-in-out infinite;}
.hero .chip:nth-child(1) {animation-delay: .3s, 1s;}
.hero .chip:nth-child(2) {animation-delay: .42s, 2s;}
.hero .chip:nth-child(3) {animation-delay: .54s, 3s;}
.hero .chip span {display: block; font-size: .88rem; color: #B7D6CF;}
.hero .chip b {display: block; font-size: clamp(1.4rem, 2.6vw, 2rem); font-weight: 750; color: #FFFFFF; margin-top: 4px;}
.hero .chip.luz {background: rgba(127,224,204,.18); border-color: rgba(127,224,204,.55);}
.hero .pie {margin: 18px 0 0; font-size: .82rem; color: #9DBDB6;}
.hero .marca {display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; margin: 0 0 22px; animation: subir .7s ease-out both;}
.hero .logo {font-size: 1.15rem; font-weight: 800; letter-spacing: .06em; color: #FFFFFF;
       padding: 6px 12px; border-radius: 10px; background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.22);}
.hero .lema {font-size: .95rem; color: #F7E7B4; font-style: italic;}
@keyframes flotar1 {from {transform: translate(0,0) scale(1);} to {transform: translate(120px,60px) scale(1.15);}}
@keyframes flotar2 {from {transform: translate(0,0) scale(1.1);} to {transform: translate(-140px,-50px) scale(.95);}}
@keyframes subir {from {opacity: 0; transform: translateY(18px);} to {opacity: 1; transform: none;}}
@keyframes mecer {0%,100% {transform: translateY(0);} 50% {transform: translateY(-4px);}}
@media (max-width: 720px) {.hero {padding: 36px 22px 26px;} .hero .chips {grid-template-columns: 1fr;}}
@media (prefers-reduced-motion: reduce) {.hero *, .hero {animation: none !important;}}
</style>
"""


def mostrar(patrimonio_hoy: float, igual_65: float, plan_65: float) -> None:
    st.markdown(
        ESTILO
        + f"""
<section class="hero">
  <div class="aurora a1"></div><div class="aurora a2"></div><div class="aurora a3"></div><div class="rejilla"></div>
  <div class="marca"><span class="logo">FINANFUNN’NT</span><span class="lema">Las finanzas no son divertidas. Pero son inevitables.</span></div>
  <p class="kicker">FUTURO YO</p>
  <div class="titular">Tu yo de 65 ya está viviendo <em>lo que decides hoy</em>.</div>
  <p class="bajada">Registra tu día, ordena tus deudas e inversiones, sigue la bolsa y mira en soles de hoy adónde te llevan.</p>
  <div class="chips">
    <div class="chip"><span>Tu patrimonio hoy</span><b>{soles(patrimonio_hoy)}</b></div>
    <div class="chip"><span>A los 65 si sigues igual</span><b>{soles(igual_65)}</b></div>
    <div class="chip luz"><span>A los 65 con tu plan</span><b>{soles(plan_65)}</b></div>
  </div>
  <p class="pie">Simulador educativo con supuestos editables. No es asesoría financiera, previsional ni de inversión.</p>
</section>
""",
        unsafe_allow_html=True,
    )
