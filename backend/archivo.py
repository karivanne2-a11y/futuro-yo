"""Guardar y abrir el archivo personal de Futuro Yo.

Los datos nunca se guardan en el servidor: la persona descarga un archivo JSON
y lo vuelve a subir cuando quiera continuar.
"""
from __future__ import annotations

import json
import math

import pandas as pd

FORMATO = "futuro-yo/1"
CAMPOS_PERFIL = {
    "edad": (18, 64),
    "sueldo_bruto": (0, 200000),
    "ingreso_neto": (0, 200000),
    "gastos": (0, 200000),
    "saldo_afp": (0, 5000000),
    "densidad_aportes": (0, 100),
    "inflacion": (0, 20),
    "alza_sueldo": (0, 20),
    "retorno_afp": (-5, 20),
    "retorno_rescate": (-5, 20),
}
TABLAS = ("deudas", "inversiones", "diario", "portafolio")
TAMANO_MAXIMO = 2_000_000


def _registros(tabla: pd.DataFrame) -> list[dict]:
    t = tabla.copy()
    for col in t.columns:
        if pd.api.types.is_datetime64_any_dtype(t[col]):
            t[col] = t[col].dt.strftime("%Y-%m-%d")
    t = t.astype(object).where(t.notna(), None)
    return t.to_dict(orient="records")


def guardar(perfil: dict, tablas: dict[str, pd.DataFrame]) -> bytes:
    contenido = {
        "formato": FORMATO,
        "perfil": {k: perfil[k] for k in CAMPOS_PERFIL if k in perfil},
        **{nombre: _registros(tablas[nombre]) for nombre in TABLAS if nombre in tablas},
    }
    return json.dumps(contenido, ensure_ascii=False, indent=2).encode("utf-8")


def abrir(datos: bytes) -> dict:
    """Valida el archivo y devuelve perfil y tablas. Lanza ValueError si no sirve."""
    if len(datos) > TAMANO_MAXIMO:
        raise ValueError("El archivo es demasiado grande.")
    try:
        contenido = json.loads(datos.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("El archivo no es un JSON válido.") from error
    if not isinstance(contenido, dict) or contenido.get("formato") != FORMATO:
        raise ValueError("Este archivo no fue creado por Futuro Yo.")

    perfil = {}
    for campo, (minimo, maximo) in CAMPOS_PERFIL.items():
        valor = contenido.get("perfil", {}).get(campo)
        if isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor):
            perfil[campo] = min(max(valor, minimo), maximo)

    tablas = {}
    for nombre in TABLAS:
        filas = contenido.get(nombre, [])
        if isinstance(filas, list) and all(isinstance(f, dict) for f in filas):
            tablas[nombre] = pd.DataFrame(filas)
    return {"perfil": perfil, "tablas": tablas}
