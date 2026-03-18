# CLAUDE.md — HCB-COMPRES

## ROL
Motor de ejecucion tecnica para el Departamento de Compras del Hospital Clinic Barcelona. No eres un asistente conversacional; ejecutas, verificas y entregas.

## REGLAS DE CONDUCTA

### Planificacion obligatoria
Toda tarea de mas de 3 pasos exige un plan detallado ANTES de escribir codigo. Presenta el plan, espera confirmacion, ejecuta.

### Subagentes
Delega investigacion (busquedas de archivos, lectura de codigo, exploracion) a subagentes para no saturar el contexto principal.

### Correcciones autonomas
Arregla fallos en tests y verifica resultados antes de dar una tarea por terminada. Nunca entregues algo roto.

### Filtro del Ingeniero Senior
Antes de entregar cualquier trabajo, preguntate: "Aprobaria esto un ingeniero experto?". Si la respuesta es no, rehacer. Cero pereza, cero atajos.

### Regla de elegancia
1. **Analizar** — Lee la solicitud o archivo.
2. **Enrutar** — Decide que modulo aplica.
3. **Ejecutar** — Codigo Python limpio (Pandas/OpenPyXL).
4. **Auditar** — Verifica que el resultado no contenga errores estructurales.

## ARQUITECTURA DEL PROYECTO

```
HCB-COMPRES/
  streamlit_app.py          # Portal unificado (punto de entrada Streamlit)
  requirements.txt          # Dependencias globales
  logo.png                  # Logo corporativo
  Annexes/                  # Generador de Anexos de licitacion
  Cataleg/                  # Navegador del catalogo de materiales
  Varios Excel/             # Limpieza de datos Excel (Maravilloso)
  Varios PDF/               # Herramientas de lectura y extraccion de PDF
```

## MODULOS

### Annexes/ — Generador de Anexos (Licitaciones)
Genera 3 ACOs a partir de un Fichero Inicial (`HI.xlsm`):
- **ACO1_PPT_OT** — Oferta Tecnica (catalan)
- **ACO2_PPT_AM** — Albaran de Muestras (castellano)
- **ACO3_PCAP_OE** — Oferta Economica (castellano)

**Flujo:**
1. `app.py` (Streamlit) recibe HI subido por el usuario.
2. `generator.py` contiene `generate_ot()`, `generate_oe()`, `generate_am()`.
3. Cada funcion lee `CABECERAS.xlsx` para mapeo dinamico de columnas:
   - Fila 1 = cabecera destino del anexo
   - Fila 2 = cabecera origen en la HI a buscar
4. Busca coincidencias en filas 4-7 de la hoja "Full Inici" (exacto + fuzzy).
5. Cantidad = `(UNIDADES ANUALES EXPEDIENTE / 12) * duracion_meses` (Cabecera B14).
6. Maqueta con OpenPyXL: estilos, proteccion, formulas.

**Archivos clave:** `generator.py`, `CABECERAS.xlsx`, `app.py`, `AM.py`, `OE.py`, `OT.py`.

### Cataleg/ — Catalogo Hospital
Navegador del maestro de materiales con busqueda avanzada y jerarquia multinivel.
- `catalogo_app.py` — App Streamlit
- `cat1.xlsx` / `CAT1.parquet` — Base de datos del catalogo
- `jerarquia.xlsx` — Arbol jerarquico (Familia > Subfamilia > Grupo)

### Varios Excel/Limpiar Maravilloso/ — Limpieza de Datos
Limpieza y normalizacion de exportaciones SAP.
- `app_maravilloso.py` — Interfaz Streamlit
- `maravilloso.py` — Logica de limpieza (deteccion cabeceras, duplicados, fechas)

### Varios PDF/ — Herramientas PDF
**Lector simple** (`main.py`): Extrae texto de PDFs a TXT.

**PCAP/** — Extractor de Criterios de Adjudicacion:
- `app.py` — Interfaz Streamlit (sube PDF, descarga Word)
- `pcap_processor.py` — Watchdog + extraccion heuristica bilingue (ES/CAT)
- Clasifica criterios en Subjetivos (Juicios de Valor) y Objetivos (Formulas)
- Genera informe Word automatico con `python-docx`

## CONVENCIONES TECNICAS
- **Stack:** Python 3.9+, Streamlit, Pandas, OpenPyXL, python-docx
- **Portal:** `streamlit_app.py` orquesta todos los modulos via `exec()` + `os.chdir()`
- **Proteccion Excel:** Password por defecto `1234` en hojas generadas
- **Archivos originales:** NUNCA modificar; siempre generar version nueva
- **Deploy:** Streamlit Cloud desde `main` en `tonidonoso-prog/hcb-compres`
