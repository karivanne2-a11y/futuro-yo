from types import SimpleNamespace

import pytest

from ai import carta as modulo
from ai.carta import Carta, armar_hechos, carta_plantilla, cifras_no_autorizadas, generar_carta, plazo
from backend.motor import perfil_ejemplo, simular


@pytest.fixture
def hechos():
    p = perfil_ejemplo()
    return armar_hechos(p.edad, p.edad_retiro, simular(p), simular(p, True, 150), 1500, 2500, 150)


def falso_cliente(texto=None, stop_reason="end_turn", error=None):
    def crear(**kwargs):
        if error:
            raise error
        return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=texto)])

    return SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=crear)))


def json_carta(cifra):
    return Carta(saludo="Hola", lo_que_cambio=cifra, decisiones=["a"], advertencia="b", cierre="c").model_dump_json()


def test_la_plantilla_solo_usa_cifras_autorizadas(hechos):
    assert cifras_no_autorizadas(carta_plantilla(hechos), hechos) == []


def test_acepta_cifra_de_los_hechos(hechos):
    cifra = hechos["patrimonio_a_los_65_con_rescate"]
    r = generar_carta(hechos, falso_cliente(json_carta(f"Llegamos con {cifra}")))
    assert r.origen == "ia"


def test_rechaza_cifra_inventada(hechos):
    r = generar_carta(hechos, falso_cliente(json_carta("Llegamos con S/ 9,999,999")))
    assert r.origen == "plantilla"


def test_error_de_api_usa_plantilla(hechos):
    r = generar_carta(hechos, falso_cliente(error=RuntimeError("caida")))
    assert r.origen == "plantilla"


def test_rechazo_del_modelo_usa_plantilla(hechos):
    r = generar_carta(hechos, falso_cliente(json_carta("x"), stop_reason="refusal"))
    assert r.origen == "plantilla"


def test_json_invalido_usa_plantilla(hechos):
    r = generar_carta(hechos, falso_cliente("no es json"))
    assert r.origen == "plantilla"


def test_sin_clave_usa_plantilla(hechos, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert generar_carta(hechos).origen == "plantilla"


def test_no_envia_nombres_de_deudas(hechos):
    texto = " ".join(hechos.values()) + " ".join(hechos)
    assert "Tarjeta" not in texto and "Préstamo" not in texto


@pytest.mark.parametrize(
    "meses,esperado",
    [(None, "sin fecha de término"), (0, "hoy mismo"), (13, "1 año y 1 mes"), (24, "2 años"), (5, "5 meses")],
)
def test_plazo(meses, esperado):
    assert plazo(meses) == esperado


def test_schema_prohibe_campos_extra():
    assert Carta.model_json_schema()["additionalProperties"] is False
    assert modulo.MODELO
