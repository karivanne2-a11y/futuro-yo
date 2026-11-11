"""Calcula el detalle del portafolio de Futuro Yo e imprime JSON."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ))

from backend import archivo, portafolio  # noqa: E402


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        sys.exit("Uso: revisar.py <archivo.json> <tipo_de_cambio>")
    datos = archivo.abrir(Path(sys.argv[1]).read_bytes())
    tabla = datos["tablas"].get("portafolio")
    tc = float(sys.argv[2])
    r = portafolio.resumen(tabla, tc)
    detalle = portafolio.detalle(tabla, tc).round(2)
    print(json.dumps({
        "tipo_de_cambio": tc,
        "resumen": r,
        "observaciones": portafolio.observaciones(r),
        "posiciones": detalle.to_dict(orient="records"),
    }, ensure_ascii=False, indent=2, default=float))


if __name__ == "__main__":
    main()
