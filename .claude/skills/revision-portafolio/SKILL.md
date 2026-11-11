---
name: revision-portafolio
description: Describe en español el portafolio registrado en Futuro Yo (valor, ganancia, pesos, exposición al dólar y concentración) a partir del archivo JSON de la app. Úsala cuando la persona pida revisar o entender sus inversiones. No da recomendaciones de compra o venta.
---

# Revisión del portafolio

## Cuándo usarla
La persona comparte su archivo `futuro-yo-*.json` y pregunta cómo está su portafolio.

## Pasos
1. Calcula con el script, usando el tipo de cambio que indique la persona o el del BCRP:
   `python .claude/skills/revision-portafolio/scripts/revisar.py <archivo.json> <tipo_de_cambio>`
2. Escribe una revisión breve:
   - **Foto de hoy:** valor total, invertido, ganancia o pérdida y rentabilidad simple.
   - **Cómo está repartido:** pesos por inversión y por tipo de activo.
   - **Riesgos visibles:** usa las observaciones del script, como concentración, dólar o cripto.
   - **Qué conviene verificar:** comisiones, plazos y si el valor actual está al día.

## Reglas
- Nunca digas qué comprar, vender o mantener, ni des precios objetivo. Eso es asesoría de inversión.
- Si la persona lo pide, explica que una decisión personalizada requiere un asesor autorizado por la SMV.
- La rentabilidad es simple y no anualizada: dilo.
- Usa solo cifras del script.
