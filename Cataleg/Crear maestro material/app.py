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
def cargar_jerarquias() -> tuple[list[dict], list[str]]:
    """Devuelve (lista de tripletes únicos, lista de nombres Nivel5 para selectbox)."""
    base_cataleg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    ruta_parquet = os.path.join(base_cataleg, "CAT1.parquet")
    ruta_xlsx   = os.path.join(base_cataleg, "cat1.xlsx")

    try:
        if os.path.exists(ruta_parquet):
            df = pd.read_parquet(ruta_parquet)
        else:
            df = pd.read_excel(ruta_xlsx, sheet_name='CAT1', header=0,
                               dtype=str, usecols=[0, 1, 2], engine='openpyxl')
    except Exception:
        return [], []

    df.columns = ['n3', 'n4', 'n5']
    rows = df.drop_duplicates().dropna(subset=['n5']).fillna("").to_dict('records')
    opciones = [""] + sorted({r['n5'] for r in rows})
    return rows, opciones


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
def extraer_texto(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        return "\n\n".join(
            p.extract_text().strip()
            for p in reader.pages
            if p.extract_text() and p.extract_text().strip()
        )
    except Exception as e:
        return f"[Error al leer PDF: {e}]"


# ---------------------------------------------------------------------------
# FILTROS DE LÍNEAS BASURA (cabeceras, pies, direcciones)
# ---------------------------------------------------------------------------
_JUNK = re.compile(
    r'ctra\.|carretera|km\.|tfno|fax|tel[eé]f|\bwww\b|@|'
    r'rev\.\s*\d|\d{2}/\d{2}/\d{4}|'
    r'^\s*ficha\s+t[eé]cnica\s*$|'
    r'^\s*\d{5}\s',
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

def extraer_nombre_producto(texto: str) -> str:
    lines = texto.splitlines()
    despues_ficha = False
    candidatos = []
    for line in lines:
        l = re.sub(r'\s+', ' ', line).strip()
        if not l:
            continue
        if re.match(r'^\s*ficha\s+t[eé]cnica\s*$', l, re.IGNORECASE):
            despues_ficha = True
            continue
        if _es_basura(l):
            continue
        if despues_ficha and 5 < len(l) <= 80:
            candidatos.insert(0, l)
            despues_ficha = False
            continue
        if l.isupper() and 8 <= len(l) <= 80 and not re.match(r'^[\d\W]+$', l):
            candidatos.append(l)
    if candidatos:
        return candidatos[0][:40].upper()
    for l in lineas_limpias(texto):
        if 8 <= len(l) <= 80:
            return l[:40].upper()
    return ""

_CAMPOS_DESC = re.compile(
    r'^(PRODUCTO|DESCRIPCI[OÓ]N|INDICACIONES?|CARACTER[IÍ]STICAS?\s*T[EÉ]CNICAS?'
    r'|USO\s*PREVISTO|COMPOSICI[OÓ]N|MATERIA\s*PRIMA|MARCA|PRESENTACI[OÓ]N'
    r'|ESTERILIZACI[OÓ]N|PRECAUCIONES?|MODO\s*DE\s*USO)',
    re.IGNORECASE,
)

def extraer_descripcion_larga(texto: str) -> str:
    lines = lineas_limpias(texto)
    bloques = []
    capturando = False
    for l in lines:
        if _CAMPOS_DESC.match(l):
            capturando = True
        if capturando:
            bloques.append(l)
            if len(' '.join(bloques)) > 1200:
                break
    if bloques:
        return ' '.join(bloques)[:1200].strip()
    return ' '.join(lines)[:1000].strip()


# ---------------------------------------------------------------------------
# TRADUCCIÓN
# ---------------------------------------------------------------------------
def traducir(texto: str, destino: str) -> str:
    if not texto.strip():
        return ""
    try:
        return GoogleTranslator(source="auto", target=destino).translate(texto[:1500])
    except Exception:
        return texto


# ---------------------------------------------------------------------------
# PROCESADO COMPLETO DE UN PDF
# ---------------------------------------------------------------------------
def procesar_pdf(pdf_bytes: bytes, filename: str, jerarquias: list[dict]) -> dict:
    texto       = extraer_texto(pdf_bytes)
    ref         = extraer_referencia(filename, texto)
    nombre      = extraer_nombre_producto(texto)
    desc_raw    = extraer_descripcion_larga(texto)

    desc_corta_es = traducir(nombre, "es")[:40].upper() if nombre else ""
    desc_larga_es = traducir(desc_raw, "es")
    desc_larga_ca = traducir(desc_raw, "ca")

    jerar = asignar_jerarquia(desc_corta_es or nombre, desc_raw, jerarquias)

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
# CARGAR JERARQUÍA
# ---------------------------------------------------------------------------
jerarquias, opciones_n5 = cargar_jerarquias()
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
        resultado = procesar_pdf(archivo.read(), archivo.name, jerarquias)
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
st.markdown("#### Texto extraído de cada PDF")
for r in resultados:
    with st.expander(f"{r['Archivo']}  —  Confianza jerarquía: {r.get('_confianza', 0)}%"):
        texto = r.get("_texto", "")
        if texto:
            st.text_area("", value=texto, height=250,
                         key=f"txt_{r['Archivo']}", label_visibility="collapsed")
        else:
            st.warning("No se pudo extraer texto (puede ser imagen escaneada).")
