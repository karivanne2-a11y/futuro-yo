from datetime import date, datetime, timezone

import pandas as pd
import pytest

from backend import archivo, diario, noticias, portafolio
from backend.motor import valor_futuro_real


def tabla_diario():
    return pd.DataFrame(
        [
            ("2026-11-01", "Ingreso", "Sueldo", 3000, ""),
            ("2026-11-02", "Gasto", "Vivienda", 900, ""),
            ("2026-11-03", "Gasto", "Alimentación", 12, "café"),
            ("2026-11-03", "Pago de deuda", "Tarjeta de crédito", 400, ""),
            ("2026-11-04", "Inversión", "Fondo mutuo", 200, ""),
            ("2026-10-15", "Gasto", "Ocio", 50, ""),
            ("fecha mala", "Gasto", "Ocio", 50, ""),
            ("2026-11-05", "Tipo raro", "Ocio", 50, ""),
            ("2026-11-05", "Gasto", "Ocio", -5, ""),
        ],
        columns=diario.COLUMNAS,
    )


def test_diario_descarta_filas_invalidas():
    assert len(diario.limpiar(tabla_diario())) == 6


def test_resumen_del_mes():
    r = diario.resumen_mes(tabla_diario(), "2026-11")
    assert r["ingresos"] == 3000
    assert r["gastos"] == 912
    assert r["pagos_deuda"] == 400
    assert r["invertido"] == 200
    assert r["ahorro"] == 3000 - 912 - 400
    assert r["sin_asignar"] == r["ahorro"] - 200
    assert r["tasa_ahorro"] == pytest.approx(100 * 1688 / 3000)


def test_meses_y_categorias():
    assert diario.meses_disponibles(tabla_diario()) == ["2026-11", "2026-10"]
    cat = diario.gastos_por_categoria(tabla_diario(), "2026-11")
    assert cat.index[0] == "Vivienda" and cat["Alimentación"] == 12


def test_gastos_hormiga():
    assert diario.gastos_pequenos(tabla_diario(), "2026-11") == {"cantidad": 1, "total": 12}


def test_ejemplo_del_diario_es_valido_y_reproducible():
    a, b = diario.ejemplo(date(2026, 11, 11)), diario.ejemplo(date(2026, 11, 11))
    assert len(a) > 30 and a.equals(b)
    assert set(a["Tipo"]) <= set(diario.TIPOS)


def test_diario_vacio():
    assert diario.resumen_mes(diario.vacio(), "2026-11")["tasa_ahorro"] == 0


def test_portafolio_convierte_dolares_y_calcula_pesos():
    t = pd.DataFrame(
        [("A", "ETF", "Estados Unidos", "USD", 100, 110), ("B", "Fondo mutuo", "Perú", "PEN", 300, 270)],
        columns=portafolio.COLUMNAS,
    )
    d = portafolio.detalle(t, tipo_cambio=3.5)
    assert d.loc[d["Activo"] == "A", "Valor (S/)"].item() == pytest.approx(385)
    assert d["Peso (%)"].sum() == pytest.approx(100)
    r = portafolio.resumen(t, 3.5)
    assert r["invertido"] == pytest.approx(650)
    assert r["valor"] == pytest.approx(655)
    assert r["mayor_activo"] == "A"


def test_observaciones_son_descriptivas():
    t = pd.DataFrame([("BTC", "Cripto", "Otro", "USD", 100, 100)], columns=portafolio.COLUMNAS)
    notas = " ".join(portafolio.observaciones(portafolio.resumen(t, 3.5)))
    assert "100 %" in notas
    for palabra in ("compra", "vende", "recomend"):
        assert palabra not in notas.lower()


def test_portafolio_vacio_y_filas_invalidas():
    t = pd.DataFrame([("", "ETF", "Perú", "PEN", 10, 10), ("X", "Raro", "Marte", "EUR", 10, 12)], columns=portafolio.COLUMNAS)
    limpio = portafolio.limpiar(t)
    assert len(limpio) == 1 and limpio.loc[0, "Tipo"] == "Otro" and limpio.loc[0, "Moneda"] == "PEN"
    assert portafolio.observaciones(portafolio.resumen(portafolio.vacio(), 3.5)) == ["Aún no registras inversiones."]


RSS = b"""<?xml version="1.0"?><rss><channel>
<item><title>BVL sube por el cobre</title><link>https://ejemplo.pe/a</link><pubDate>Tue, 10 Nov 2026 15:00:00 GMT</pubDate></item>
<item><title>Receta de causa</title><link>https://ejemplo.pe/b</link></item>
<item><title>Enlace peligroso</title><link>javascript:alert(1)</link></item>
</channel></rss>"""

ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Stocks rally</title>
<link href="https://ejemplo.com/c"/><updated>2026-11-10T12:00:00Z</updated></entry></feed>"""


def test_parsea_rss_y_filtra_enlaces():
    n = noticias.parsear(RSS, "Prueba", "Perú")
    assert [x.titulo for x in n] == ["BVL sube por el cobre", "Receta de causa"]
    assert n[0].de_mercado and not n[1].de_mercado
    assert n[0].fecha == datetime(2026, 11, 10, 15, tzinfo=timezone.utc)


def test_parsea_atom():
    n = noticias.parsear(ATOM, "Prueba", "Internacional")
    assert n[0].enlace == "https://ejemplo.com/c" and n[0].de_mercado


def test_descarga_tolera_fuentes_caidas(monkeypatch):
    def falsa(fuente, timeout):
        if fuente[0] == "mala":
            raise RuntimeError("caída")
        return noticias.parsear(RSS, fuente[0], fuente[1])

    monkeypatch.setattr(noticias, "_descargar_una", falsa)
    lista, fallidas = noticias.descargar([("buena", "Perú", "u"), ("mala", "Perú", "u")])
    assert fallidas == ["mala"] and len(lista) == 2


def test_hace_cuanto():
    ahora = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    assert noticias.hace_cuanto(datetime(2026, 11, 11, 11, 30, tzinfo=timezone.utc), ahora) == "hace 30 min"
    assert noticias.hace_cuanto(datetime(2026, 11, 9, 12, tzinfo=timezone.utc), ahora) == "hace 2 d"


def test_archivo_ida_y_vuelta():
    perfil = {"edad": 32, "gastos": 2200, "inflacion": 3.38, "otro": "x"}
    tablas = {"diario": diario.limpiar(tabla_diario()), "portafolio": portafolio.ejemplo()}
    abierto = archivo.abrir(archivo.guardar(perfil, tablas))
    assert abierto["perfil"] == {"edad": 32, "gastos": 2200, "inflacion": 3.38}
    assert len(diario.limpiar(abierto["tablas"]["diario"])) == 6
    assert len(portafolio.limpiar(abierto["tablas"]["portafolio"])) == 3


@pytest.mark.parametrize("datos", [b"no json", b'{"formato": "otro"}', b"[1, 2]"])
def test_archivo_rechaza_datos_ajenos(datos):
    with pytest.raises(ValueError):
        archivo.abrir(datos)


def test_archivo_acota_valores_extremos():
    datos = b'{"formato": "futuro-yo/1", "perfil": {"edad": 500, "gastos": true, "inflacion": -9}}'
    assert archivo.abrir(datos)["perfil"] == {"edad": 64, "inflacion": 0}


def test_valor_futuro_real():
    assert valor_futuro_real(100, 12, 0, 0) == pytest.approx(1200)
    assert valor_futuro_real(100, 0, 5, 3) == 0
    # Si el retorno iguala a la inflacion, cada aporte conserva su valor real del dia en que se hizo.
    assert 1150 < valor_futuro_real(100, 12, 5, 5) < 1200
    assert valor_futuro_real(100, 120, 5, 3) > valor_futuro_real(100, 120, 3, 3)
