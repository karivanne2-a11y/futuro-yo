"""Calcula el resumen de un mes del diario de Futuro Yo e imprime JSON."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ))

from backend import archivo, diario  # noqa: E402


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit("Uso: resumen.py <archivo.json> [AAAA-MM]")
    datos = archivo.abrir(Path(sys.argv[1]).read_bytes())
    tabla = diario.limpiar(datos["tablas"].get("diario"))
    meses = diario.meses_disponibles(tabla)
    if not meses:
        print(json.dumps({"error": "El archivo no tiene movimientos válidos."}, ensure_ascii=False))
        return
    mes = sys.argv[2] if len(sys.argv) > 2 else meses[0]
    salida = {"mes": mes, "resumen": diario.resumen_mes(tabla, mes),
              "gastos_por_categoria": diario.gastos_por_categoria(tabla, mes).round(2).to_dict(),
              "gastos_pequenos": diario.gastos_pequenos(tabla, mes)}
    anteriores = [m for m in meses if m < mes]
    if anteriores:
        salida["mes_anterior"] = {"mes": anteriores[0], "resumen": diario.resumen_mes(tabla, anteriores[0])}
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
