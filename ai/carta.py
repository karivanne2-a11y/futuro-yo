"""Carta del yo de 65 anos.

La IA solo redacta: todas las cifras salen del motor financiero. Una revision
final rechaza cualquier cifra que no venga de esos hechos y, si algo falla,
la app usa una plantilla sin IA. Al modelo nunca se le envian nombres ni el
detalle de las deudas, solo cifras agregadas.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

MODELO = os.getenv("FUTURO_YO_MODEL", "claude-opus-5-5")

SISTEMA = """Eres la voz de una persona de 65 años que le escribe a su yo actual en una app educativa de finanzas personales en Perú.
Escribe en español peruano claro, cálido y directo, en primera persona y tuteando.
Usa únicamente las cifras incluidas en HECHOS, copiadas tal como aparecen. No calcules ni inventes cifras nuevas.
Habla de escenarios posibles, nunca de resultados seguros.
No recomiendes bancos, AFP, fondos, acciones, criptomonedas ni otros productos. No des instrucciones de inversión.
Cada campo debe tener una o dos oraciones. "decisiones" debe tener tres frases cortas sobre hábitos: ordenar deudas, sostener un pago extra y revisar el plan."""


class Carta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    saludo: str
    lo_que_cambio: str
    decisiones: list[str]
    advertencia: str
    cierre: str

    def como_texto(self) -> str:
        decisiones = " ".join(self.decisiones)
        return " ".join([self.saludo, self.lo_que_cambio, decisiones, self.advertencia, self.cierre])


@dataclass
class ResultadoCarta:
    carta: Carta
    origen: str  # "ia" o "plantilla"
    nota: str = ""


def soles(valor: float) -> str:
    return f"S/ {valor:,.0f}"


def plazo(meses: int | None) -> str:
    if meses is None:
        return "sin fecha de término"
    if meses == 0:
        return "hoy mismo"
    anos, resto = divmod(meses, 12)
    partes = []
    if anos:
        partes.append(f"{anos} año" + ("s" if anos != 1 else ""))
    if resto:
        partes.append(f"{resto} mes" + ("es" if resto != 1 else ""))
    return " y ".join(partes)


def armar_hechos(edad, edad_retiro, igual, rescate, ingreso_igual, ingreso_rescate, extra) -> dict[str, str]:
    """Convierte los resultados del motor en los unicos datos que ve la IA."""
    return {
        "edad_actual": str(edad),
        "edad_retiro": str(edad_retiro),
        "pago_extra_mensual": soles(extra),
        "patrimonio_a_los_65_si_sigue_igual": soles(igual.patrimonio_final_real),
        "patrimonio_a_los_65_con_rescate": soles(rescate.patrimonio_final_real),
        "diferencia_de_patrimonio": soles(rescate.patrimonio_final_real - igual.patrimonio_final_real),
        "ingreso_mensual_estimado_si_sigue_igual": soles(ingreso_igual),
        "ingreso_mensual_estimado_con_rescate": soles(ingreso_rescate),
        "intereses_que_evita": soles(max(igual.intereses_pagados - rescate.intereses_pagados, 0)),
        "tiempo_sin_deudas_si_sigue_igual": plazo(igual.meses_sin_deuda),
        "tiempo_sin_deudas_con_rescate": plazo(rescate.meses_sin_deuda),
    }


def carta_plantilla(h: dict[str, str]) -> Carta:
    return Carta(
        saludo=f"Hola. Te escribo desde mis {h['edad_retiro']} años, a ti que hoy tienes {h['edad_actual']}.",
        lo_que_cambio=(
            f"Si seguimos igual, llegamos con cerca de {h['patrimonio_a_los_65_si_sigue_igual']} en soles de hoy. "
            f"Con el rescate podríamos llegar a {h['patrimonio_a_los_65_con_rescate']}, "
            f"porque salimos de deudas en {h['tiempo_sin_deudas_con_rescate']} y seguimos apartando ese dinero."
        ),
        decisiones=[
            "Mira primero la deuda que cobra más.",
            f"Sostén tu pago extra de {h['pago_extra_mensual']} aunque parezca poco.",
            "Revisa este plan cada vez que cambie tu sueldo.",
        ],
        advertencia="Nada de esto está garantizado: son escenarios que dependen de los supuestos que elegiste.",
        cierre="No necesitas hacerlo perfecto. Solo necesito que empieces.",
    )


def _digitos(texto: str) -> list[str]:
    return [re.sub(r"\D", "", n) for n in re.findall(r"\d[\d.,]*\d|\d", texto)]


def cifras_no_autorizadas(carta: Carta, hechos: dict[str, str]) -> list[str]:
    """Devuelve las cifras de la carta que no aparecen en los hechos."""
    permitidas = {n for valor in hechos.values() for n in _digitos(valor)}
    return [n for n in _digitos(carta.como_texto()) if n not in permitidas]


def _llamar_modelo(hechos: dict[str, str], cliente) -> Carta:
    respuesta = cliente.beta.messages.create(
        model=MODELO,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SISTEMA,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": Carta.model_json_schema()},
        },
        messages=[{"role": "user", "content": "HECHOS:\n" + json.dumps(hechos, ensure_ascii=False, indent=2)}],
    )
    if respuesta.stop_reason == "refusal":
        raise ValueError("El modelo declinó generar la carta")
    if respuesta.stop_reason == "max_tokens":
        raise ValueError("La respuesta quedó incompleta")
    texto = next(b.text for b in respuesta.content if b.type == "text")
    return Carta.model_validate_json(texto)


def generar_carta(hechos: dict[str, str], cliente=None) -> ResultadoCarta:
    """Intenta redactar con IA; si no se puede, devuelve la plantilla."""
    if cliente is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return ResultadoCarta(carta_plantilla(hechos), "plantilla", "Sin clave de IA configurada.")
        import anthropic

        cliente = anthropic.Anthropic(timeout=45.0, max_retries=1)

    try:
        carta = _llamar_modelo(hechos, cliente)
    except Exception as error:  # La demo nunca debe caerse por la IA.
        return ResultadoCarta(carta_plantilla(hechos), "plantilla", f"La IA no respondió ({type(error).__name__}).")

    extrañas = cifras_no_autorizadas(carta, hechos)
    if extrañas:
        return ResultadoCarta(carta_plantilla(hechos), "plantilla", "La IA usó cifras no calculadas y se descartó.")
    return ResultadoCarta(carta, "ia")
