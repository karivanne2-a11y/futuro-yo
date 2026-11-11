---
name: resumen-mensual
description: Resume en español un mes del diario de Futuro Yo (ingresos, gastos, pagos de deuda, inversión y gastos pequeños) a partir del archivo JSON que descarga la app. Úsala cuando la persona pida revisar su mes, entender en qué se fue su dinero o comparar con el mes anterior.
---

# Resumen mensual del diario

## Cuándo usarla
La persona comparte un archivo `futuro-yo-*.json` descargado de la app Futuro Yo y pide entender un mes.

## Pasos
1. Calcula las cifras con el script. No las calcules a mano:
   `python .claude/skills/resumen-mensual/scripts/resumen.py <archivo.json> [AAAA-MM]`
   Sin mes, usa el más reciente. El script devuelve JSON con el mes pedido y el anterior.
2. Escribe un resumen de 150 a 250 palabras con esta estructura:
   - **Tu mes en una línea:** cuánto entró y cuánto no se consumió.
   - **En qué se fue:** las tres categorías de gasto más altas, con monto.
   - **Gastos pequeños:** cuántos y cuánto suman.
   - **Comparado con el mes anterior:** solo si existe en el JSON.
   - **Una pregunta para pensar:** sobre un hábito, no sobre un producto.
3. Copia cada cifra tal como sale del script, en soles con separador de miles.

## Reglas
- No recomiendes bancos, fondos, acciones, criptomonedas ni otros productos.
- No juzgues: describe y pregunta.
- Si el mes está en curso, dilo: las cifras están incompletas.
- Si el archivo no tiene movimientos válidos, dilo y no inventes datos.
