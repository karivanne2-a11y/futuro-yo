"""Diario de movimientos: ingresos, gastos, inversiones y pagos de deuda."""
from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd

TIPOS = ["Ingreso", "Gasto", "Inversión", "Pago de deuda"]
CATEGORIAS = {
    "Ingreso": ["Sueldo", "Ingreso extra", "Otros ingresos"],
    "Gasto": ["Alimentación", "Vivienda", "Transporte", "Servicios", "Salud", "Educación", "Ocio", "Compras", "Otros gastos"],
    "Inversión": ["Fondo mutuo", "Acciones o ETF", "Depósito a plazo", "Aporte voluntario AFP", "Otra inversión"],
    "Pago de deuda": ["Tarjeta de crédito", "Préstamo", "Otra deuda"],
}
TODAS_CATEGORIAS = [c for lista in CATEGORIAS.values() for c in lista]
COLUMNAS = ["Fecha", "Tipo", "Categoría", "Monto (S/)", "Nota"]


def vacio() -> pd.DataFrame:
    return pd.DataFrame({"Fecha": pd.Series(dtype="datetime64[ns]"), "Tipo": [], "Categoría": [], "Monto (S/)": [], "Nota": []})


def limpiar(tabla: pd.DataFrame) -> pd.DataFrame:
    """Deja solo filas validas: fecha, tipo conocido y monto positivo."""
    if tabla is None or tabla.empty:
        return vacio()
    t = tabla.reindex(columns=COLUMNAS).copy()
    t["Fecha"] = pd.to_datetime(t["Fecha"], errors="coerce").dt.normalize()
    t["Monto (S/)"] = pd.to_numeric(t["Monto (S/)"], errors="coerce")
    t["Nota"] = t["Nota"].fillna("").astype(str)
    t["Categoría"] = t["Categoría"].fillna("").astype(str)
    validas = t["Fecha"].notna() & t["Tipo"].isin(TIPOS) & (t["Monto (S/)"] > 0)
    return t[validas].sort_values("Fecha", ascending=False).reset_index(drop=True)


def meses_disponibles(tabla: pd.DataFrame) -> list[str]:
    t = limpiar(tabla)
    return sorted(t["Fecha"].dt.strftime("%Y-%m").unique(), reverse=True)


def del_mes(tabla: pd.DataFrame, mes: str) -> pd.DataFrame:
    t = limpiar(tabla)
    return t[t["Fecha"].dt.strftime("%Y-%m") == mes]


def resumen_mes(tabla: pd.DataFrame, mes: str) -> dict[str, float]:
    t = del_mes(tabla, mes)
    suma = {tipo: float(t.loc[t["Tipo"] == tipo, "Monto (S/)"].sum()) for tipo in TIPOS}
    ingresos, gastos = suma["Ingreso"], suma["Gasto"]
    pagos, invertido = suma["Pago de deuda"], suma["Inversión"]
    ahorro = ingresos - gastos - pagos  # Lo que no se consumio: incluye lo invertido.
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "pagos_deuda": pagos,
        "invertido": invertido,
        "ahorro": ahorro,
        "sin_asignar": ahorro - invertido,
        "tasa_ahorro": 100 * ahorro / ingresos if ingresos > 0 else 0.0,
        "movimientos": float(len(t)),
    }


def gastos_por_categoria(tabla: pd.DataFrame, mes: str) -> pd.Series:
    t = del_mes(tabla, mes)
    gastos = t[t["Tipo"] == "Gasto"]
    return gastos.groupby("Categoría")["Monto (S/)"].sum().sort_values(ascending=False)


def gastos_pequenos(tabla: pd.DataFrame, mes: str, tope: float = 30.0) -> dict[str, float]:
    """Gastos menores al tope: los llamados gastos hormiga."""
    t = del_mes(tabla, mes)
    chicos = t[(t["Tipo"] == "Gasto") & (t["Monto (S/)"] <= tope)]
    return {"cantidad": float(len(chicos)), "total": float(chicos["Monto (S/)"].sum())}


def ejemplo(hoy: date | None = None, semilla: int = 7) -> pd.DataFrame:
    """Movimientos ficticios de los ultimos dos meses para el demo."""
    hoy = hoy or date.today()
    azar = random.Random(semilla)
    filas = []
    inicio = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
    dia = inicio
    while dia <= hoy:
        if dia.day == 1:
            filas += [
                (dia, "Ingreso", "Sueldo", 3550, "Sueldo neto"),
                (dia, "Gasto", "Vivienda", 900, "Alquiler"),
                (dia, "Pago de deuda", "Tarjeta de crédito", 480, "Cuota"),
                (dia, "Pago de deuda", "Préstamo", 560, "Cuota"),
                (dia, "Inversión", "Fondo mutuo", 60, "Aporte mensual"),
            ]
        if dia.day == 5:
            filas.append((dia, "Gasto", "Servicios", 180, "Luz, agua e internet"))
        if dia.weekday() < 5:
            filas.append((dia, "Gasto", "Transporte", 8, "Pasajes"))
            if azar.random() < 0.55:
                filas.append((dia, "Gasto", "Alimentación", azar.choice([12, 15, 18]), "Almuerzo"))
            if azar.random() < 0.35:
                filas.append((dia, "Gasto", "Alimentación", azar.choice([6, 9, 11]), "Café o snack"))
        if dia.weekday() == 5:
            filas.append((dia, "Gasto", "Alimentación", azar.choice([120, 140, 165]), "Mercado"))
        if dia.weekday() == 6 and azar.random() < 0.5:
            filas.append((dia, "Gasto", "Ocio", azar.choice([35, 50, 70]), "Salida"))
        if dia.day == 20 and azar.random() < 0.6:
            filas.append((dia, "Ingreso", "Ingreso extra", 300, "Trabajo independiente"))
        dia += timedelta(days=1)
    return limpiar(pd.DataFrame(filas, columns=COLUMNAS))
