"""Motor financiero de Futuro Yo.

Todo se calcula mes a mes en soles nominales y al final se convierte a soles de
hoy (descontando la inflacion). Este modulo no usa IA ni guarda datos: recibe un
perfil y devuelve numeros reproducibles.
"""
from __future__ import annotations

from dataclasses import dataclass, field

APORTE_AFP = 0.10  # Aporte obligatorio sobre el sueldo bruto.


@dataclass
class Deuda:
    nombre: str
    saldo: float
    tcea: float  # Tasa anual en porcentaje, por ejemplo 65 para 65 %.
    cuota: float


@dataclass
class Inversion:
    nombre: str
    saldo: float
    aporte: float
    retorno: float  # Retorno anual nominal esperado, en porcentaje.


@dataclass
class Perfil:
    edad: int
    sueldo_bruto: float
    ingreso_neto: float
    gastos: float
    saldo_afp: float
    deudas: list[Deuda] = field(default_factory=list)
    inversiones: list[Inversion] = field(default_factory=list)
    edad_retiro: int = 65
    retorno_afp: float = 5.5
    inflacion: float = 2.5
    alza_sueldo: float = 3.0
    densidad_aportes: float = 100.0  # Porcentaje de meses con aporte a la AFP.
    retorno_rescate: float = 5.0  # Retorno del dinero liberado al pagar deudas.
    anos_retiro: int = 20
    retorno_real_retiro: float = 2.0


@dataclass
class Trayectoria:
    nombre: str
    edades: list[float]
    patrimonio_real: list[float]
    deuda_nominal: list[float]
    afp_real: float
    inversiones_real: float
    patrimonio_final_real: float
    intereses_pagados: float
    meses_sin_deuda: int | None
    deudas_sin_amortizar: list[str]


def tasa_mensual(anual_pct: float) -> float:
    """Convierte una tasa efectiva anual en porcentaje a tasa efectiva mensual."""
    return (1 + anual_pct / 100) ** (1 / 12) - 1


def ingreso_mensual_equivalente(fondo_real: float, anos: int, retorno_real_pct: float) -> float:
    """Ingreso mensual constante, en soles de hoy, que un fondo sostiene por `anos`."""
    n = anos * 12
    if n <= 0:
        return 0.0
    i = tasa_mensual(retorno_real_pct)
    if abs(i) < 1e-12:
        return fondo_real / n
    return fondo_real * i / (1 - (1 + i) ** -n)


def valor_futuro_real(aporte_mensual: float, meses: int, retorno_pct: float, inflacion_pct: float) -> float:
    """Valor en soles de hoy de apartar el mismo monto cada mes durante `meses`."""
    if meses <= 0:
        return 0.0
    i = tasa_mensual(retorno_pct)
    nominal = aporte_mensual * meses if abs(i) < 1e-12 else aporte_mensual * ((1 + i) ** meses - 1) / i
    return nominal / (1 + tasa_mensual(inflacion_pct)) ** meses


def simular(perfil: Perfil, rescate: bool = False, extra: float = 0.0) -> Trayectoria:
    """Proyecta el patrimonio hasta la edad de retiro.

    Sin rescate, cada deuda paga solo su cuota y lo que se libera se gasta.
    Con rescate, se suma `extra`, el dinero disponible se dirige a la deuda de
    mayor TCEA y, al terminar las deudas, ese flujo se invierte.
    """
    meses = max((perfil.edad_retiro - perfil.edad) * 12, 0)
    deudas = [Deuda(d.nombre, d.saldo, d.tcea, d.cuota) for d in perfil.deudas if d.saldo > 0]
    inversiones = [Inversion(i.nombre, i.saldo, i.aporte, i.retorno) for i in perfil.inversiones]
    afp = perfil.saldo_afp
    fondo_rescate = 0.0

    r_afp = tasa_mensual(perfil.retorno_afp)
    r_rescate = tasa_mensual(perfil.retorno_rescate)
    r_inv = [tasa_mensual(i.retorno) for i in inversiones]
    inflacion = tasa_mensual(perfil.inflacion)
    alza = tasa_mensual(perfil.alza_sueldo)

    presupuesto = sum(d.cuota for d in deudas) + (extra if rescate else 0.0)
    # Si hoy se gasta mas de lo que entra, el dinero liberado cubre primero ese faltante.
    deficit = max(-foto_hoy(perfil).flujo_libre, 0.0)
    sin_amortizar = [d.nombre for d in deudas if d.cuota <= d.saldo * tasa_mensual(d.tcea)]

    intereses = 0.0
    sin_deuda = 0 if not deudas else None
    edades = [float(perfil.edad)]

    def patrimonio_nominal() -> float:
        return afp + fondo_rescate + sum(i.saldo for i in inversiones) - sum(d.saldo for d in deudas)

    patrimonio = [patrimonio_nominal()]
    deuda_total = [sum(d.saldo for d in deudas)]
    deflactor = 1.0
    sueldo = perfil.sueldo_bruto
    factor_aportes = 1.0

    for mes in range(1, meses + 1):
        for d in deudas:
            interes = d.saldo * tasa_mensual(d.tcea)
            d.saldo += interes
            intereses += interes

        if rescate:
            disponible = presupuesto
            for d in deudas:
                pago = min(d.cuota, d.saldo, disponible)
                d.saldo -= pago
                disponible -= pago
            for d in sorted(deudas, key=lambda x: x.tcea, reverse=True):
                pago = min(d.saldo, disponible)
                d.saldo -= pago
                disponible -= pago
            fondo_rescate += max(disponible - deficit, 0.0)
        else:
            for d in deudas:
                d.saldo -= min(d.cuota, d.saldo)

        for d in deudas:
            if d.saldo < 0.005:
                d.saldo = 0.0

        if sin_deuda is None and sum(d.saldo for d in deudas) == 0:
            sin_deuda = mes

        afp = afp * (1 + r_afp) + sueldo * APORTE_AFP * perfil.densidad_aportes / 100
        fondo_rescate *= 1 + r_rescate
        for i, r in zip(inversiones, r_inv):
            i.saldo = i.saldo * (1 + r) + i.aporte * factor_aportes

        sueldo *= 1 + alza
        factor_aportes *= 1 + alza
        deflactor *= 1 + inflacion

        if mes % 12 == 0 or mes == meses:
            edades.append(perfil.edad + mes / 12)
            patrimonio.append(patrimonio_nominal() / deflactor)
            deuda_total.append(sum(d.saldo for d in deudas))

    inv_nominal = fondo_rescate + sum(i.saldo for i in inversiones)
    return Trayectoria(
        nombre="Con rescate" if rescate else "Seguir igual",
        edades=edades,
        patrimonio_real=patrimonio,
        deuda_nominal=deuda_total,
        afp_real=afp / deflactor,
        inversiones_real=inv_nominal / deflactor,
        patrimonio_final_real=patrimonio[-1],
        intereses_pagados=intereses,
        meses_sin_deuda=sin_deuda,
        deudas_sin_amortizar=sin_amortizar,
    )


@dataclass
class FotoHoy:
    deuda_total: float
    activos_total: float
    patrimonio_neto: float
    cuotas: float
    aportes: float
    flujo_libre: float
    carga_deuda_pct: float
    tcea_mayor: float


def foto_hoy(perfil: Perfil) -> FotoHoy:
    deuda = sum(d.saldo for d in perfil.deudas)
    activos = perfil.saldo_afp + sum(i.saldo for i in perfil.inversiones)
    cuotas = sum(d.cuota for d in perfil.deudas if d.saldo > 0)
    aportes = sum(i.aporte for i in perfil.inversiones)
    return FotoHoy(
        deuda_total=deuda,
        activos_total=activos,
        patrimonio_neto=activos - deuda,
        cuotas=cuotas,
        aportes=aportes,
        flujo_libre=perfil.ingreso_neto - perfil.gastos - cuotas - aportes,
        carga_deuda_pct=100 * cuotas / perfil.ingreso_neto if perfil.ingreso_neto > 0 else 0.0,
        tcea_mayor=max((d.tcea for d in perfil.deudas if d.saldo > 0), default=0.0),
    )


def perfil_ejemplo() -> Perfil:
    """Persona ficticia para el demo. No corresponde a nadie real."""
    return Perfil(
        edad=32,
        sueldo_bruto=4200,
        ingreso_neto=3550,
        gastos=2200,
        saldo_afp=38000,
        densidad_aportes=80,
        deudas=[
            Deuda("Tarjeta de crédito", 9500, 78, 480),
            Deuda("Préstamo personal", 14000, 38, 560),
        ],
        inversiones=[
            Inversion("Cuenta de ahorros", 2500, 0, 2.5),
            Inversion("Fondo mutuo", 3000, 60, 5.0),
        ],
    )
