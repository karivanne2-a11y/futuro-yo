---
name: pulso-bolsa
description: Resume en español los titulares recientes de economía y bolsa de Perú y del mundo que usa Futuro Yo, con enlace a cada fuente. Úsala cuando la persona pregunte qué está pasando en la bolsa, con el dólar o con la economía hoy.
---

# Pulso de la bolsa

## Pasos
1. Descarga los titulares con el script:
   `python .claude/skills/pulso-bolsa/scripts/titulares.py`
   Devuelve JSON con título, fuente, región, fecha y enlace, solo de temas de mercado.
2. Escribe un resumen de 150 a 250 palabras:
   - **Perú:** tres a cinco temas, como dólar, BCRP, BVL y metales.
   - **Mundo:** tres a cinco temas, como Wall Street, tasas, petróleo y empresas.
   - **Cómo leer esto:** una línea que recuerde que un titular no es una señal de compra o venta.
3. Cita cada tema con su enlace en formato Markdown.

## Reglas
- Resume solo lo que dicen los titulares. No inventes cifras ni causas.
- No hagas predicciones ni recomiendes productos.
- Traduce al español los titulares internacionales y deja el enlace original.
- Si alguna fuente no respondió, menciónalo.
