# CLAUDE.md — Cataleg/

## ARCHIVOS
| Archivo | Rol |
|---|---|
| `catalogo_app.py` | Navegador catálogo: árbol Nivel3/4/5 + ficha material |
| `ref_search_app.py` | Buscador por referencia de proveedor |
| `Crear maestro material/app.py` | Generador de maestro desde fichas técnicas PDF |
| `cat1.xlsx` / `CAT1.parquet` | Maestro de materiales (27.797 filas, 6 cols) |
| `cat2_refs.xlsx` / `cat2_refs.parquet` | Referencias proveedor sin precios (público) |
| `fichas_index.json` | `{material-codprov: url_sharepoint}` — 22.360 fichas técnicas |
| `generar_cat2_refs.py` | Extrae cat2_refs.xlsx desde cat2.xlsx (privado, con precios) |
| `generar_fichas_index.py` | Indexa fichas técnicas de SharePoint |

## ESTRUCTURA cat1.xlsx (hoja CAT1)
```
col0: Jerarquia 3N   → Nivel 3 (Familia)
col1: Jerarquia 4N   → Nivel 4 (Subfamilia)
col2: Jerarquia 5N   → Nivel 5 (Grupo) — formato: ESE040402-CATÉTERES BALÓN ACTP...
col3: Descripción material  → desc corta SAP (≤40 chars, mayúsculas, sin acentos)
col4: Cód.M          → código material SAP
col5: Texto largo del material → desc larga SAP (≤250 chars)
```

## ESTRUCTURA cat2_refs.xlsx
```
Cód.M, Ref.Prov, Nom.Prov., /GpC, /P (X=preferente), Prov. (cod proveedor)
```
- `/P = X` → material aparece en el árbol del catálogo
- Parquet cache para ambos archivos

## FICHAS TÉCNICAS
- URL base SharePoint: `https://hospitalclinicdebarcelona.sharepoint.com/sites/GesDocDSGCompres/CoordinacioCompresCataleg/LOGARITME/FICHAS%20TEC-SEG%20UNIFICADO`
- Nombre fichero: `{material}-{cod_prov}-{referencia}.pdf`
- `fichas_index.json` clave: `"{material}-{cod_prov}"` → url

## CATALOGACIÓN SAP (guía de descripciones)
- **Corta** (≤40 chars): MAYÚSCULAS, sin acentos, sigue prefijo del Nivel 5 (ej: `CAT BALON ACTP NC PE 2,5X12 20AT`)
- **Larga ES** (≤250 chars): texto técnico + sufijo estándar del familia (ej: `Estéril. Un solo uso. Sin látex.`)
- **Larga CA** (≤250 chars): traducción al catalán de la larga ES
- Guía extraída de `cat1.xlsx` por Nivel 5 en `cargar_catalogo()`

## BUSCADOR REF PROVEEDOR
- Busca en `Ref Proveedor` + `Nombre Proveedor` de cat2_refs
- Multi-palabra, sin acentos, compacta (ignora espacios y guiones)
- Muestra ficha técnica via `fichas_index.json` como `LinkColumn`
