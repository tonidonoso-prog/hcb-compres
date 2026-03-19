# CLAUDE.md — Cataleg/Crear maestro material/

## QUÉ HACE
Sube fichas técnicas PDF → extrae campos → asigna jerarquía → descarga Excel para SAP.

## FLUJO
1. Upload PDF(s) → `extraer_texto()` con `pdfplumber` (fallback `pypdf`) + `_clean_text()`
2. `extraer_referencia()` → del filename `{mat}-{prov}-{REF}.pdf` primero, luego regex en texto
3. `extraer_descripcion_larga()` → busca campos etiquetados (`PRODUCTO:`, `CARACTERÍSTICAS TÉCNICAS:`, etc.), para antes de `REFERENCIAS:` / tablas
4. `traducir(texto, 'es')` → si ya es castellano (detectado por `_es_castellano()`), no traduce
5. `traducir(texto, 'ca')` → siempre traduce al catalán via `deep-translator` (Google Translate, sin API key)
6. `generar_descripcion_corta()` → primeras palabras de la larga, sin acentos, ≤40 chars, sin conjunciones al final
7. `asignar_jerarquia()` → scorer Jaccard + difflib contra 890 tripletes de cat1 → devuelve n3/n4/n5 + confianza%
8. `aplicar_guia()` → prefijo corta y sufijo larga del Nivel 5 asignado (extraídos de cat1 en `cargar_catalogo()`)
9. UI: `st.data_editor` editable + ejemplos reales del Nivel 5 + texto PDF en expanders
10. Descarga Excel (Descripción corta, Descripción larga ES, Descripció llarga CA, referència, Nivel3/4/5)

## ARCHIVOS DE DATOS
- `../cat1.xlsx` / `../CAT1.parquet` → jerarquía y guía de catalogación
- `deep-translator` → Google Translate sin API key (instalado en requirements.txt)

## DETECCIÓN DE IDIOMA
```python
_es_castellano(texto):
    # True si contiene ñ/Ñ O si >8% palabras son del set de palabras funcionales ES
```

## GUÍA DE CATALOGACIÓN POR NIVEL 5
- `cargar_catalogo()` carga cat1 y por cada Nivel 5 extrae:
  - `prefix`: top 3 palabras más frecuentes en desc_corta del familia
  - `suffix`: fragmento "Estéril..." más frecuente en desc_larga del familia
  - `ejemplos`: 3 materiales reales para mostrar en UI
- `aplicar_guia()` antepone prefix a corta y añade suffix a larga si no está presente

## RESTRICCIONES
- desc_corta: ≤40 chars, MAYÚSCULAS, sin acentos (unicodedata NFD)
- desc_larga ES/CA: ≤250 chars, truncar en punto/coma si es posible
- No traducir al ES si el texto ya es castellano
- cat2.xlsx (con precios) NUNCA se sube al repo
