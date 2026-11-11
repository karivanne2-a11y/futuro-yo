"""Portafolio de inversiones registradas por la persona.

Los valores actuales los ingresa la persona: la app no consulta precios ni
recomienda comprar o vender. Solo ordena y describe.
"""
from __future__ import annotations

import pandas as pd

TIPOS = ["Acción", "ETF", "Fondo mutuo", "Depósito a plazo", "Bono", "Cripto", "Otro"]
MERCADOS = ["Perú", "Estados Unidos", "Otro"]
MONEDAS = ["PEN", "USD"]
COLUMNAS = ["Activo", "Tipo", "Mercado", "Moneda", "Invertido", "Valor actual"]


def vacio() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS)


def limpiar(tabla: pd.DataFrame) -> pd.DataFrame:
    if tabla is None or tabla.empty:
        return vacio()
    t = tabla.reindex(columns=COLUMNAS).copy()
    for col in ("Invertido", "Valor actual"):
        t[col] = pd.to_numeric(t[col], errors="coerce")
    t["Activo"] = t["Activo"].fillna("").astype(str).str.strip()
    t["Tipo"] = t["Tipo"].where(t["Tipo"].isin(TIPOS), "Otro")
    t["Mercado"] = t["Mercado"].where(t["Mercado"].isin(MERCADOS), "Otro")
    t["Moneda"] = t["Moneda"].where(t["Moneda"].isin(MONEDAS), "PEN")
    validas = (t["Activo"] != "") & (t["Invertido"] >= 0) & (t["Valor actual"] >= 0) & ((t["Invertido"] > 0) | (t["Valor actual"] > 0))
    return t[validas].reset_index(drop=True)


def detalle(tabla: pd.DataFrame, tipo_cambio: float) -> pd.DataFrame:
    """Agrega montos en soles, ganancia, rentabilidad simple y peso."""
    t = limpiar(tabla)
    factor = t["Moneda"].map({"PEN": 1.0, "USD": float(tipo_cambio)})
    t["Invertido (S/)"] = t["Invertido"] * factor
    t["Valor (S/)"] = t["Valor actual"] * factor
    t["Ganancia (S/)"] = t["Valor (S/)"] - t["Invertido (S/)"]
    t["Rentabilidad (%)"] = (100 * t["Ganancia (S/)"] / t["Invertido (S/)"]).where(t["Invertido (S/)"] > 0)
    total = t["Valor (S/)"].sum()
    t["Peso (%)"] = 100 * t["Valor (S/)"] / total if total > 0 else 0.0
    return t.sort_values("Valor (S/)", ascending=False).reset_index(drop=True)


def resumen(tabla: pd.DataFrame, tipo_cambio: float) -> dict:
    d = detalle(tabla, tipo_cambio)
    invertido, valor = float(d["Invertido (S/)"].sum()), float(d["Valor (S/)"].sum())
    mayor = d.iloc[0] if len(d) else None
    return {
        "posiciones": len(d),
        "invertido": invertido,
        "valor": valor,
        "ganancia": valor - invertido,
        "rentabilidad": 100 * (valor - invertido) / invertido if invertido > 0 else 0.0,
        "mayor_activo": mayor["Activo"] if mayor is not None else "",
        "mayor_peso": float(mayor["Peso (%)"]) if mayor is not None else 0.0,
        "peso_usd": float(d.loc[d["Moneda"] == "USD", "Peso (%)"].sum()) if len(d) else 0.0,
        "peso_por_tipo": d.groupby("Tipo")["Peso (%)"].sum().sort_values(ascending=False).to_dict() if len(d) else {},
    }


def observaciones(r: dict) -> list[str]:
    """Descripciones neutrales del portafolio. No son recomendaciones."""
    notas = []
    if r["posiciones"] == 0:
        return ["Aún no registras inversiones."]
    if r["mayor_peso"] >= 40:
        notas.append(f"{r['mayor_activo']} representa {r['mayor_peso']:.0f} % del valor total: tu resultado depende mucho de esa posición.")
    if r["peso_usd"] >= 50:
        notas.append(f"{r['peso_usd']:.0f} % está en dólares: el tipo de cambio mueve tu valor en soles.")
    cripto = r["peso_por_tipo"].get("Cripto", 0.0)
    if cripto >= 10:
        notas.append(f"Las criptomonedas pesan {cripto:.0f} %: es la parte que más puede variar.")
    if r["posiciones"] == 1:
        notas.append("Todo está en una sola posición.")
    if not notas:
        notas.append("Ninguna posición supera 40 % del total.")
    return notas


def ejemplo() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("Fondo mutuo conservador", "Fondo mutuo", "Perú", "PEN", 3000, 3120),
            ("ETF índice amplio de EE. UU.", "ETF", "Estados Unidos", "USD", 400, 452),
            ("Depósito a plazo 12 meses", "Depósito a plazo", "Perú", "PEN", 1500, 1560),
        ],
        columns=COLUMNAS,
    )
