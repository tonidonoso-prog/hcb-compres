# CLAUDE.md — Annexes/

## QUÉ HACE
Genera 3 anexos Excel de licitación a partir de un Fichero Inicial (`HI.xlsm`):
- **ACO1_PPT_OT** — Oferta Técnica (catalán)
- **ACO2_PPT_AM** — Albarán de Muestras (castellano)
- **ACO3_PCAP_OE** — Oferta Económica (castellano)

## ARCHIVOS
| Archivo | Rol |
|---|---|
| `app.py` | UI Streamlit: sube HI, descarga ZIP con los 3 anexos |
| `generator.py` | `generate_ot()`, `generate_oe()`, `generate_am()` |
| `OT.py` / `OE.py` / `AM.py` | Lógica específica de cada anexo |
| `CABECERAS.xlsx` | Mapeo dinámico de columnas (fila1=destino, fila2=origen en HI) |

## FLUJO
1. Usuario sube `HI.xlsm`.
2. `generator.py` lee `CABECERAS.xlsx` para saber qué columna del HI va a qué columna del anexo.
3. Busca coincidencias en filas 4-7 de la hoja `Full Inici` (exacto + fuzzy con `difflib`).
4. **Cantidad** = `(UNIDADES ANUALES EXPEDIENTE / 12) * duracion_meses` — duración viene de Cabecera B14.
5. Maqueta con OpenPyXL: estilos, protección (pwd `1234`), fórmulas.
6. Devuelve ZIP con los 3 ficheros.

## REGLAS ESPECÍFICAS
- CABECERAS.xlsx es el corazón del mapeo — no hardcodear nombres de columnas.
- Fuzzy matching con `difflib.SequenceMatcher`, umbral 0.7.
- Nunca modificar el HI original.
