"""Descarga titulares de mercado de las fuentes de Futuro Yo e imprime JSON."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ))

from backend import noticias  # noqa: E402


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    lista, fallidas = noticias.descargar()
    salida = {
        "fuentes_sin_respuesta": fallidas,
        "titulares": [
            {"titulo": n.titulo, "fuente": n.fuente, "region": n.region,
             "fecha": n.fecha.isoformat() if n.fecha else None, "enlace": n.enlace}
            for n in lista if n.de_mercado
        ][:30],
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
