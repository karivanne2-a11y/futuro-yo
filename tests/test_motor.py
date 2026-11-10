import math

import pytest

from backend.motor import (
    Deuda,
    Inversion,
    Perfil,
    foto_hoy,
    ingreso_mensual_equivalente,
    perfil_ejemplo,
    simular,
    tasa_mensual,
)


def base(**cambios):
    datos = dict(
        edad=64,
        sueldo_bruto=0,
        ingreso_neto=3000,
        gastos=1000,
        saldo_afp=0,
        retorno_afp=0,
        inflacion=0,
        alza_sueldo=0,
        densidad_aportes=100,
        retorno_rescate=0,
    )
    datos.update(cambios)
    return Perfil(**datos)


def test_tasa_mensual_compone_a_la_tasa_anual():
    assert (1 + tasa_mensual(12)) ** 12 == pytest.approx(1.12)


def test_deuda_sin_interes_se_paga_en_los_meses_exactos():
    r = simular(base(deudas=[Deuda("a", 1000, 0, 100)]))
    assert r.meses_sin_deuda == 10
    assert r.intereses_pagados == 0
    assert r.deuda_nominal[-1] == 0


def test_rescate_ataca_primero_la_tasa_mas_alta():
    perfil = base(edad=60, deudas=[Deuda("barata", 5000, 10, 150), Deuda("cara", 5000, 80, 300)])
    igual = simular(perfil)
    rescate = simular(perfil, rescate=True, extra=200)
    assert rescate.intereses_pagados < igual.intereses_pagados
    assert rescate.meses_sin_deuda < igual.meses_sin_deuda


def test_rescate_sin_extra_no_paga_mas_intereses():
    perfil = perfil_ejemplo()
    assert simular(perfil, rescate=True).intereses_pagados <= simular(perfil).intereses_pagados


def test_el_rescate_no_crea_dinero_sin_intereses():
    perfil = base(edad=63, deudas=[Deuda("a", 1200, 0, 100)])
    r = simular(perfil, rescate=True)
    # Paga 1200 y sobran 12 meses de 100 invertidos a cero: patrimonio final 1200.
    assert r.patrimonio_final_real == pytest.approx(1200)


def test_con_deficit_el_dinero_liberado_no_se_invierte():
    perfil = base(edad=63, ingreso_neto=1000, gastos=1100, deudas=[Deuda("a", 1200, 0, 100)])
    # Faltan 200 al mes (100 de gastos y 100 de cuota): lo liberado cubre ese faltante.
    assert simular(perfil, rescate=True).patrimonio_final_real == pytest.approx(0)


def test_patrimonio_final_se_deflacta():
    perfil = base(edad=64, saldo_afp=1000, inflacion=10)
    assert simular(perfil).patrimonio_final_real == pytest.approx(1000 / 1.10)


def test_afp_acumula_aporte_segun_densidad():
    perfil = base(edad=64, sueldo_bruto=1000, densidad_aportes=50)
    assert simular(perfil).afp_real == pytest.approx(12 * 1000 * 0.10 * 0.5)


def test_avisa_si_la_cuota_no_cubre_el_interes():
    perfil = base(deudas=[Deuda("impagable", 10000, 100, 50)])
    assert simular(perfil).deudas_sin_amortizar == ["impagable"]


def test_ingreso_equivalente_sin_retorno_divide_en_meses():
    assert ingreso_mensual_equivalente(24000, 2, 0) == pytest.approx(1000)


def test_ingreso_equivalente_agota_el_fondo():
    fondo, anos, tasa = 100000, 20, 2
    pago = ingreso_mensual_equivalente(fondo, anos, tasa)
    i = tasa_mensual(tasa)
    saldo = fondo
    for _ in range(anos * 12):
        saldo = saldo * (1 + i) - pago
    assert math.isclose(saldo, 0, abs_tol=1e-6)


def test_foto_hoy():
    perfil = base(
        saldo_afp=500,
        deudas=[Deuda("a", 1000, 50, 100)],
        inversiones=[Inversion("b", 200, 50, 5)],
    )
    f = foto_hoy(perfil)
    assert f.deuda_total == 1000
    assert f.patrimonio_neto == -300
    assert f.flujo_libre == 3000 - 1000 - 100 - 50
    assert f.tcea_mayor == 50


def test_edad_igual_al_retiro_no_falla():
    r = simular(base(edad=65, saldo_afp=100))
    assert r.patrimonio_final_real == 100
