"""Descarga la inflacion de Lima desde la API publica del BCRP.

Uso: python -m backend.datos_bcrp
Guarda data/bcrp_inflacion.json, que la app lee como supuesto de inflacion.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests

SERIE = "PN01273PM"  # IPC Lima Metropolitana, variacion porcentual a 12 meses.
URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{serie}/json/{ini}/{fin}/esp"
DESTINO = Path(__file__).resolve().parents[1] / "data" / "bcrp_inflacion.json"
RESPALDO = {"serie": SERIE, "ultimo_periodo": None, "ultimo_valor": None, "promedio_10_anos": 2.5}


def descargar(anos: int = 10, timeout: int = 60) -> dict:
    hoy = date.today()
    url = URL.format(serie=SERIE, ini=f"{hoy.year - anos}-{hoy.month}", fin=f"{hoy.year}-{hoy.month}")
    respuesta = requests.get(url, timeout=timeout)
    respuesta.raise_for_status()
    periodos = respuesta.json()["periods"]

    datos = []
    for p in periodos:
        try:
            datos.append((p["name"], float(p["values"][0])))
        except (ValueError, IndexError, KeyError):
            continue  # El BCRP marca los meses sin dato como "n.d.".
    if not datos:
        raise ValueError("El BCRP no devolvio datos validos")

    valores = [v for _, v in datos]
    return {
        "serie": SERIE,
        "ultimo_periodo": datos[-1][0],
        "ultimo_valor": round(valores[-1], 2),
        "promedio_10_anos": round(sum(valores) / len(valores), 2),
        "observaciones": len(valores),
        "descargado": hoy.isoformat(),
        "fuente": "BCRP, API de series estadísticas",
    }


def cargar() -> dict:
    """Lee los datos guardados; si faltan, usa un supuesto marcado como respaldo."""
    try:
        return json.loads(DESTINO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(RESPALDO)


SERIE_TC = "PD04640PD"  # Tipo de cambio venta, sistema bancario SBS (S/ por US$).
DESTINO_TC = DESTINO.parent / "bcrp_tipo_cambio.json"
RESPALDO_TC = {"serie": SERIE_TC, "fecha": None, "valor": 3.45}


def descargar_tipo_cambio(timeout: int = 60) -> dict:
    hoy = date.today()
    url = URL.format(serie=SERIE_TC, ini=f"{hoy.year - 1}-{hoy.month}-1", fin=hoy.isoformat())
    respuesta = requests.get(url, timeout=timeout)
    respuesta.raise_for_status()
    for p in reversed(respuesta.json()["periods"]):
        try:
            return {"serie": SERIE_TC, "fecha": p["name"], "valor": round(float(p["values"][0]), 3)}
        except (ValueError, IndexError, KeyError):
            continue
    raise ValueError("El BCRP no devolvio tipo de cambio")


def obtener_tipo_cambio() -> tuple[dict, bool]:
    try:
        return descargar_tipo_cambio(timeout=6), True
    except (requests.RequestException, ValueError, KeyError):
        try:
            return json.loads(DESTINO_TC.read_text(encoding="utf-8")), False
        except (OSError, json.JSONDecodeError):
            return dict(RESPALDO_TC), False


def obtener() -> tuple[dict, bool]:
    """Consulta el BCRP en vivo con espera corta; si falla, usa la copia guardada."""
    try:
        return descargar(timeout=6), True
    except (requests.RequestException, ValueError, KeyError):
        return cargar(), False


if __name__ == "__main__":
    resultado = descargar()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(resultado)
    tc = descargar_tipo_cambio()
    DESTINO_TC.write_text(json.dumps(tc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(tc)
