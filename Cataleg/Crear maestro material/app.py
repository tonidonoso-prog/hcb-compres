import streamlit as st
import pandas as pd
import pypdf
import re
import io
import os
import unicodedata
import difflib
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Crear Maestro Material", layout="wide")

# ---------------------------------------------------------------------------
# UTILIDADES COMUNES
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()

_STOPWORDS = {
    'de','del','la','el','los','las','en','con','para','por','otros','otro',
    'otra','otras','y','e','o','u','a','al','un','una','unos','unas',
    'mat','material','accesorios','accesorio','uso','especial',
}

def palabras(texto: str) -> set:
    return set(re.findall(r'[a-z0-9]{3,}', normalize(texto))) - _STOPWORDS


# ---------------------------------------------------------------------------
# CARGA DE JERARQUÍA (cat1.xlsx)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def cargar_catalogo() -> tuple[list[dict], list[str], dict]:
    """
    Devuelve:
      - jerarquias: lista de tripletes únicos {n3, n4, n5}
      - opciones:   lista de n5 para selectbox
      - guia:       {codigo_n5: {prefix_corta, suffix_larga, ejemplos[]}}
    """
    base_cataleg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    ruta_parquet = os.path.join(base_cataleg, "CAT1.parquet")
    ruta_xlsx    = os.path.join(base_cataleg, "cat1.xlsx")

    try:
        if os.path.exists(ruta_parquet):
            df_full = pd.read_parquet(ruta_parquet)
        else:
            df_full = pd.read_excel(ruta_xlsx, sheet_name='CAT1', header=0,
                                    dtype=str, engine='openpyxl')
        # Renombrar por posición (funciona tanto con nombres originales como renombrados)
        cols = list(df_full.columns)
        rename = {}
        if len(cols) > 0: rename[cols[0]] = 'n3'
        if len(cols) > 1: rename[cols[1]] = 'n4'
        if len(cols) > 2: rename[cols[2]] = 'n5'
        if len(cols) > 3: rename[cols[3]] = 'desc_corta'
        if len(cols) > 4: rename[cols[4]] = 'material'
        if len(cols) > 5: rename[cols[5]] = 'desc_larga'
        df_full = df_full.rename(columns=rename)
    except Exception:
        return [], [], {}

    df_full = df_full.fillna("")

    # Jerarquías únicas para el scorer
    rows = df_full[['n3','n4','n5']].drop_duplicates().dropna(subset=['n5']).to_dict('records')
    opciones = [""] + sorted({r['n5'] for r in rows})

    # Guía por Nivel 5: prefijo corta + sufijo larga + ejemplos
    guia = {}
    for n5, grp in df_full[df_full['n5'] != ""].groupby('n5'):
        codigo = n5.split('-')[0] if '-' in n5 else n5

        # Prefijo más común en desc_corta (primeras 3 palabras)
        prefijos = (
            grp['desc_corta']
            .apply(lambda x: ' '.join(str(x).split()[:3]))
            .value_counts()
        )
        prefix = prefijos.index[0] if len(prefijos) else ""

        # Sufijo más común en desc_larga (últimos 80 chars → buscar "Estéril" o similar)
        def _sufijo(t):
            t = str(t).strip()
            m = re.search(r'(Est[eé]ril.*)', t, re.IGNORECASE)
            return m.group(1) if m else t[-80:]
        sufijos = grp['desc_larga'].apply(_sufijo).value_counts()
        suffix = sufijos.index[0] if len(sufijos) else ""

        # 3 ejemplos representativos
        ejemplos = grp[['desc_corta','desc_larga']].drop_duplicates().head(3).to_dict('records')

        guia[codigo] = {'prefix': prefix, 'suffix': suffix, 'ejemplos': ejemplos, 'n5': n5}

    return rows, opciones, guia


# ---------------------------------------------------------------------------
# SCORER DE JERARQUÍA
# ---------------------------------------------------------------------------
def _desc_nivel(s: str) -> str:
    """'ESE040899-OTROS ACCESORIOS CATETERISMO' → 'otros accesorios cateterismo'"""
    m = re.match(r'^[A-Z0-9]+-(.+)$', str(s))
    return normalize(m.group(1)) if m else normalize(s)

def _score(query_words: set, row: dict) -> float:
    w5 = palabras(_desc_nivel(row['n5']))
    w4 = palabras(_desc_nivel(row['n4']))
    w3 = palabras(_desc_nivel(row['n3']))
    all_t = w5 | w4 | w3
    if not query_words or not all_t:
        return 0.0
    jaccard = len(query_words & all_t) / max(len(query_words), len(all_t))
    sm = difflib.SequenceMatcher(
        None, ' '.join(sorted(query_words)), _desc_nivel(row['n5'])
    ).ratio()
    return jaccard * 0.7 + sm * 0.3

def aplicar_guia(desc_corta: str, desc_larga: str, n5: str, guia: dict) -> tuple[str, str]:
    """Ajusta desc_corta y desc_larga según los patrones reales del Nivel 5."""
    codigo = n5.split('-')[0] if '-' in n5 else n5
    entry = guia.get(codigo, {})

    # Corta: anteponer el prefijo del familia si la descripción no lo refleja
    prefix = entry.get('prefix', '')
    if prefix and not normalize(desc_corta).startswith(normalize(prefix)):
        desc_corta = (prefix + ' ' + desc_corta)[:40].strip()
        # Re-quitar acentos
        desc_corta = ''.join(
            c for c in unicodedata.normalize('NFD', desc_corta)
            if unicodedata.category(c) != 'Mn'
        ).upper()[:40]

    # Larga: añadir sufijo estándar del familia si no está ya presente + truncar a 250
    suffix = entry.get('suffix', '')
    if suffix:
        kw = suffix.split('.')[0].lower()[:15]
        if kw and kw not in desc_larga.lower():
            desc_larga = (desc_larga.rstrip('. ') + '. ' + suffix)
    desc_larga = desc_larga[:250].rstrip(' ,')
    # Truncar sin cortar a mitad de frase
    if len(desc_larga) == 250:
        last = max(desc_larga.rfind('. '), desc_larga.rfind(', '))
        if last > 100:
            desc_larga = desc_larga[:last + 1]

    return desc_corta, desc_larga


def asignar_jerarquia(desc_corta: str, desc_larga: str, jerarquias: list[dict]) -> dict:
    """Devuelve el triplete n3/n4/n5 con mayor puntuación."""
    if not jerarquias:
        return {'n3': '', 'n4': '', 'n5': '', 'confianza': 0}
    qw = palabras(f"{desc_corta} {desc_larga[:400]}")
    scores = [(_score(qw, j), j) for j in jerarquias]
    best_sc, best = max(scores, key=lambda x: x[0])
    return {**best, 'confianza': round(best_sc * 100)}


# ---------------------------------------------------------------------------
# EXTRACCIÓN DE TEXTO DEL PDF
# ---------------------------------------------------------------------------
def _clean_text(text: str) -> str:
    """Corrige artefactos de codificación comunes en PDFs en castellano/catalán."""
    replacements = [
        ('dÆ', "d'"), ('DÆ', "D'"), ('lÆ', "l'"), ('LÆ', "L'"),
        ('nÆ', "n'"), ('sÆ', "s'"), ('NÆ', "N'"), ('SÆ', "S'"),
        ('n║', 'nº'), ('‗', 'ò'), ('Ú', 'é'), ('Ë', 'Ó'), ('¾', 'ó'),
        ('Þ', 'é'), ('Ý', 'í'), ('þ', 'ç'), ('¬', 'à'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return re.sub(r'[ \t]+', ' ', text)


def extraer_texto(pdf_bytes: bytes) -> str:
    # pdfplumber: mejor orden de texto y filtra headers/footers flotantes
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        texto = "\n\n".join(t.strip() for t in pages if t.strip())
        if texto:
            return _clean_text(texto)
    except Exception:
        pass
    # Fallback: pypdf
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages = [p.extract_text() or "" for p in reader.pages]
        texto = "\n\n".join(t.strip() for t in pages if t.strip())
        return _clean_text(texto)
    except Exception as e:
        return f"[Error al leer PDF: {e}]"


# ---------------------------------------------------------------------------
# FILTROS DE LÍNEAS BASURA (cabeceras, pies, direcciones)
# ---------------------------------------------------------------------------
_JUNK = re.compile(
    r'ctra\.|carretera|km\.|tfno|fax|tel[eé]f|\bwww\b|@|'
    r'rev\.\s*\d|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|'
    r'^\s*ficha\s+t[eé]cnica\s*$|'
    r'^\s*p[aá]g(?:ina)?\s*\d|^\s*\d+\s*/\s*\d+\s*$|'  # page numbers
    r'^\s*\d{5}\s|'                                       # postal code at start
    r'\b(s\.l\.|s\.a\.|s\.l\.u\.|s\.a\.u\.|s\.coop\.?)\b|'  # company suffixes
    r'(?:^|\s)(c/|av\.|avda\.?|avinguda|pol[ií]gono|poligon|apdo\.?|nau\s)\s',
    re.IGNORECASE,
)

def _es_basura(l: str) -> bool:
    return bool(_JUNK.search(l))

def lineas_limpias(texto: str) -> list[str]:
    result = []
    for l in texto.splitlines():
        l = re.sub(r'\s+', ' ', l).strip()
        if len(l) > 3 and not _es_basura(l):
            result.append(l)
    return result


# ---------------------------------------------------------------------------
# HEURÍSTICAS DE EXTRACCIÓN
# ---------------------------------------------------------------------------
def extraer_referencia(filename: str, texto: str) -> str:
    base = os.path.splitext(filename)[0]
    parts = base.split('-', 2)
    if len(parts) >= 3 and parts[2].strip():
        return parts[2].strip()
    m = re.search(
        r'(?:ref(?:erencia)?|c[oó]d(?:igo)?|art(?:ículo)?|cat(?:alog)?(?:\s*no\.?)?)'
        r'[\s:\.\-]*([A-Z0-9][A-Z0-9\-\.\/]{2,25})',
        texto, re.IGNORECASE,
    )
    if m:
        val = m.group(1).strip().split()[0]
        if len(val) >= 3:
            return val
    return ""

# Tabla de abreviaciones SAP (palabras completas → abreviatura)
_ABREV = {
    'cateter': 'CAT', 'catéter': 'CAT',
    'instrumento': 'INSTRU', 'instrumentos': 'INSTRU',
    'dispositivo': 'DISP', 'dispositivos': 'DISP',
    'automatico': 'AUTO', 'automático': 'AUTO',
    'solucion': 'SOL', 'solución': 'SOL',
    'introductores': 'INTRO', 'introductor': 'INTRO',
    'intercambio': 'INTERC',
    'distensible': 'DIST', 'distensibles': 'DIST',
    'radiopacas': 'RP', 'radiopaca': 'RP',
    'quirurgico': 'QUIR', 'quirúrgico': 'QUIR',
    'quirurgica': 'QUIR', 'quirúrgica': 'QUIR',
    'diametro': 'DIAM', 'diámetro': 'DIAM',
    'longitud': 'LONG',
    'milimetros': 'MM', 'milímetros': 'MM',
    'centimetros': 'CM', 'centímetros': 'CM',
    'diferentes': 'DIFER',
    'seleccionable': 'SEL',
    'compatibles': 'COMPAT', 'compatible': 'COMPAT',
    'transparente': 'TRANSP',
    'esterilizacion': 'ESTERIL', 'esterilización': 'ESTERIL',
    'reutilizable': 'REUTIL',
    'antibiotico': 'ATB', 'antibiótico': 'ATB',
}

# Palabras a eliminar (artículos, preposiciones, conjunciones)
_STOP_CORTA = {
    'de','del','la','el','los','las','para','con','en','por','a','al',
    'un','una','unos','unas','y','e','o','u','que','se',
}


def _norm_sin_acentos(texto: str) -> str:
    t = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn')


def generar_descripcion_corta(desc_larga: str) -> str:
    """
    Genera descripción corta SAP (máx 40 chars, MAYÚSCULAS, sin acentos).
    Aplica tabla de abreviaciones y elimina palabras de relleno.
    """
    # 1. Quitar etiquetas de campo al inicio
    texto = re.sub(
        r'^(PRODUCTO|DESCRIPCI[OÓ]N|INDICACIONES?|DENOMINACI[OÓ]N|NOMBRE)[:\s]+',
        '', desc_larga, flags=re.IGNORECASE,
    ).strip()
    # 2. Tomar solo la primera frase (hasta el primer punto o etiqueta secundaria)
    texto = re.split(r'\.\s+(?:MARCA|MATERIA|CARACTER|USO|ESTERIL|PRESENTACI)', texto, flags=re.IGNORECASE)[0]
    texto = texto.split('.')[0].split(';')[0]
    # 3. Limpiar símbolos
    texto = re.sub(r'[®™«»\[\]()\/:,]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    # 4. Aplicar abreviaciones palabra a palabra
    palabras_out = []
    for word in texto.split():
        w_lower = _norm_sin_acentos(word.lower().rstrip('.,;'))
        if w_lower in _STOP_CORTA:
            continue
        abrev = _ABREV.get(w_lower) or _ABREV.get(word.lower())
        palabras_out.append(abrev if abrev else word)
    resultado = ' '.join(palabras_out)
    # 5. Sin acentos, mayúsculas
    resultado = _norm_sin_acentos(resultado).upper()
    resultado = re.sub(r'\s+', ' ', resultado).strip()
    # 6. Si cabe en 40 chars → perfecto
    if len(resultado) <= 40:
        return resultado
    # 7. Si no cabe: reconstruir eliminando palabras menos importantes desde el final
    words = resultado.split()
    while len(' '.join(words)) > 40 and len(words) > 1:
        words.pop()
    return ' '.join(words)

_CAMPOS_DESC = re.compile(
    r'^(PRODUCTO|DESCRIPCI[OÓ]N|INDICACIONES?|CARACTER[IÍ]STICAS?\s*T[EÉ]CNICAS?'
    r'|USO\s*PREVISTO|COMPOSICI[OÓ]N|MATERIA\s*PRIMA|MARCA|PRESENTACI[OÓ]N'
    r'|ESTERILIZACI[OÓ]N|PRECAUCIONES?|MODO\s*DE\s*USO)',
    re.IGNORECASE,
)

# Secciones que indican fin de la descripción técnica (tablas, refs, notas legales...)
_STOP_DESC = re.compile(
    r'^(REFERENCIAS?|REFERENCIES|CATALOG|TABLA\s*DE|ESPECIFICACIONES?\s*T[EÉ]CNICAS?'
    r'|NOTAS?\s*LEGALES?|CONDICIONES?\s*DE\s*USO|INSTRUCCIONES?\s*DE\s*USO'
    r'|ADVERTENCIAS?|CONTRAINDICACIONES?|FECHA\s*DE\s*REVISI)',
    re.IGNORECASE,
)

def extraer_descripcion_larga(texto: str) -> str:
    lines = lineas_limpias(texto)
    bloques = []
    capturando = False
    for l in lines:
        if _STOP_DESC.match(l):
            break                       # cortar antes de tablas/referencias
        if _CAMPOS_DESC.match(l):
            capturando = True
        if capturando:
            bloques.append(l)
            if len(' '.join(bloques)) > 1200:
                break
    if bloques:
        return ' '.join(bloques)[:1200].strip()

    # Fallback: PDFs sin etiquetas de campo.
    # Estrategia: saltar el bloque de cabecera (empresa/dirección) buscando la primera
    # línea substantiva — larga o con alta proporción de minúsculas (frases reales).
    desc_lines = []
    in_header = True
    for l in lines:
        if _STOP_DESC.match(l):
            break
        if in_header:
            alpha = sum(c.isalpha() for c in l)
            lower = sum(c.islower() for c in l)
            ratio_lower = lower / alpha if alpha else 0
            # Fin de cabecera: línea larga (>60) O con buena proporción de minúsculas (frase real)
            if len(l) > 60 or (len(l) > 35 and ratio_lower > 0.40):
                in_header = False
        if not in_header:
            desc_lines.append(l)
            if len(' '.join(desc_lines)) > 800:
                break

    if desc_lines:
        return ' '.join(desc_lines)[:1000].strip()
    # Último recurso: tomar solo líneas con cierta longitud mínima
    return ' '.join(l for l in lines if len(l) > 25)[:500].strip()


# ---------------------------------------------------------------------------
# DETECCIÓN DE IDIOMA Y TRADUCCIÓN
# ---------------------------------------------------------------------------
_ES_WORDS = {
    'de','del','la','el','los','las','en','con','para','por','que','es','son',
    'se','su','sus','al','un','una','nos','lo','le','les','como','pero','si',
    'este','esta','estos','estas','hay','tiene','tienen','para','entre','sobre',
    'sin','más','también','según','mediante','durante','cada','donde','cuyo',
}

def _es_castellano(texto: str) -> bool:
    """True si el texto es predominantemente castellano."""
    # Presencia de caracteres específicos del español
    if re.search(r'[ñÑ]', texto):
        return True
    # Ratio de palabras castellanas comunes
    words = re.findall(r'\b[a-záéíóúüA-ZÁÉÍÓÚÜ]{2,}\b', texto.lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in _ES_WORDS)
    return (hits / len(words)) > 0.08  # más del 8% son palabras castellanas típicas

def traducir(texto: str, destino: str) -> str:
    if not texto.strip():
        return ""
    # Si ya está en castellano y el destino es castellano, no traducir
    if destino == "es" and _es_castellano(texto):
        return texto.strip()
    try:
        return GoogleTranslator(source="auto", target=destino).translate(texto[:1500])
    except Exception:
        return texto


# ---------------------------------------------------------------------------
# PROCESADO COMPLETO DE UN PDF
# ---------------------------------------------------------------------------
def procesar_pdf(pdf_bytes: bytes, filename: str, jerarquias: list[dict], guia: dict) -> dict:
    texto      = extraer_texto(pdf_bytes)
    ref        = extraer_referencia(filename, texto)
    desc_raw   = extraer_descripcion_larga(texto)

    desc_larga_es = traducir(desc_raw, "es")
    desc_larga_ca = traducir(desc_raw, "ca")
    desc_corta_es = generar_descripcion_corta(desc_larga_es or desc_raw)

    jerar = asignar_jerarquia(desc_corta_es, desc_larga_es or desc_raw, jerarquias)

    # Aplicar guía de catalogación del Nivel 5 asignado
    n5 = jerar.get('n5', '')
    desc_corta_es, desc_larga_es = aplicar_guia(desc_corta_es, desc_larga_es, n5, guia)
    desc_larga_ca = desc_larga_ca[:250]

    return {
        "Archivo":                           filename,
        "Descripción corta material":        desc_corta_es,
        "Descripción larga material":        desc_larga_es,
        "Descripció llarga material català": desc_larga_ca,
        "referència":                        ref,
        "Nivel 3":                           jerar.get('n3', ''),
        "Nivel 4":                           jerar.get('n4', ''),
        "Nivel 5":                           jerar.get('n5', ''),
        "_confianza":                        jerar.get('confianza', 0),
        "_texto":                            texto,
    }


# ---------------------------------------------------------------------------
# EXPORT EXCEL
# ---------------------------------------------------------------------------
COLS_EXPORT = [
    "Descripción corta material",
    "Descripción larga material",
    "Descripció llarga material català",
    "referència",
    "Nivel 3",
    "Nivel 4",
    "Nivel 5",
]

def to_excel(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    df_exp = df[[c for c in COLS_EXPORT if c in df.columns]].copy()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df_exp.to_excel(writer, index=False, sheet_name="Maestro")
        ws = writer.sheets["Maestro"]
        ws.set_column(0, 0, 42)
        ws.set_column(1, 1, 60)
        ws.set_column(2, 2, 60)
        ws.set_column(3, 3, 25)
        ws.set_column(4, 4, 35)
        ws.set_column(5, 5, 35)
        ws.set_column(6, 6, 45)
    return out.getvalue()


# ---------------------------------------------------------------------------
# CABECERA
# ---------------------------------------------------------------------------
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logo.png")
col_logo, col_title = st.columns([0.10, 0.90])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
with col_title:
    st.markdown("## Crear Maestro Material")
    st.caption("Sube fichas técnicas en PDF. Se extraen, traducen y clasifican automáticamente — edita y descarga el Excel.")

st.markdown("---")

# ---------------------------------------------------------------------------
# CARGAR CATÁLOGO (jerarquía + guía de catalogación)
# ---------------------------------------------------------------------------
jerarquias, opciones_n5, guia = cargar_catalogo()
if not jerarquias:
    st.warning("No se pudo cargar la jerarquía de cat1.xlsx — la clasificación automática no estará disponible.")

# ---------------------------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------------------------
archivos = st.file_uploader(
    "Fichas técnicas (PDF)",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not archivos:
    st.info("Sube uno o varios PDFs de fichas técnicas para comenzar.")
    st.stop()

# ---------------------------------------------------------------------------
# PROCESAR (solo pendientes)
# ---------------------------------------------------------------------------
KEY = "maestro_resultados"
if KEY not in st.session_state:
    st.session_state[KEY] = {}

nombres_subidos = {f.name for f in archivos}
for r in list(st.session_state[KEY].keys()):
    if r not in nombres_subidos:
        del st.session_state[KEY][r]

pendientes = [f for f in archivos if f.name not in st.session_state[KEY]]
if pendientes:
    progress = st.progress(0, text="Procesando y traduciendo...")
    for i, archivo in enumerate(pendientes):
        progress.progress(i / len(pendientes), text=f"Procesando: {archivo.name}")
        resultado = procesar_pdf(archivo.read(), archivo.name, jerarquias, guia)
        st.session_state[KEY][archivo.name] = resultado
    progress.progress(1.0, text="Listo")
    progress.empty()

resultados = list(st.session_state[KEY].values())

# ---------------------------------------------------------------------------
# TABLA EDITABLE
# ---------------------------------------------------------------------------
df_res = pd.DataFrame(resultados)
df_edit = df_res[["Archivo", "_confianza"] + COLS_EXPORT].copy()
df_edit = df_edit.rename(columns={"_confianza": "Confianza %"})

st.markdown(f"### {len(df_edit)} material(es)")
st.caption(
    "La columna **Nivel 5** se ha asignado automáticamente por similitud de texto. "
    "Revisa la confianza — cuanto más alta, más fiable. Edita cualquier celda antes de descargar."
)

# Selectbox options para Nivel 5
col_cfg = {
    "Archivo":       st.column_config.TextColumn("Archivo", width="medium", disabled=True),
    "Confianza %":   st.column_config.ProgressColumn("Confianza %", min_value=0, max_value=100, format="%d%%", width="small"),
    "Descripción corta material": st.column_config.TextColumn("Desc. corta ES (máx 40)", max_chars=40, width="medium"),
    "Descripción larga material": st.column_config.TextColumn("Desc. larga ES", width="large"),
    "Descripció llarga material català": st.column_config.TextColumn("Desc. llarga CA", width="large"),
    "referència":    st.column_config.TextColumn("Referència", width="small"),
    "Nivel 3":       st.column_config.TextColumn("Nivel 3", width="medium"),
    "Nivel 4":       st.column_config.TextColumn("Nivel 4", width="medium"),
    "Nivel 5":       st.column_config.SelectboxColumn("Nivel 5", options=opciones_n5, width="large") if opciones_n5 else st.column_config.TextColumn("Nivel 5", width="large"),
}

df_editado = st.data_editor(
    df_edit,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    disabled=["Archivo", "Confianza %", "Nivel 3", "Nivel 4"],
    column_config=col_cfg,
)

st.download_button(
    label="Descargar Excel",
    data=to_excel(df_editado),
    file_name="maestro_material.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
)

# ---------------------------------------------------------------------------
# TEXTO EXTRAÍDO (para consulta)
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("#### Detalle por PDF")
for r in resultados:
    with st.expander(f"{r['Archivo']}  —  Confianza jerarquía: {r.get('_confianza', 0)}%"):

        # Ejemplos de catalogación del Nivel 5 asignado
        n5 = r.get("Nivel 5", "")
        codigo_n5 = n5.split('-')[0] if '-' in n5 else n5
        entry = guia.get(codigo_n5, {})
        ejemplos = entry.get('ejemplos', [])
        if ejemplos:
            st.markdown(f"**Guía de catalogación para `{n5}`** — ejemplos reales del catálogo:")
            for ej in ejemplos:
                c = str(ej.get('desc_corta', '')).strip()
                l = str(ej.get('desc_larga', '')).strip()
                st.markdown(
                    f"&nbsp;&nbsp;**Corta:** `{c}`  \n"
                    f"&nbsp;&nbsp;**Larga:** {l[:200]}",
                    unsafe_allow_html=True,
                )
            st.markdown("---")

        # Texto extraído del PDF
        texto = r.get("_texto", "")
        if texto:
            st.caption("Texto extraído del PDF:")
            st.text_area("", value=texto, height=220,
                         key=f"txt_{r['Archivo']}", label_visibility="collapsed")
        else:
            st.warning("No se pudo extraer texto (puede ser imagen escaneada).")
