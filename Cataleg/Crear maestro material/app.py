import streamlit as st
import pandas as pd
import pypdf
import re
import io
import os
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Crear Maestro Material", layout="wide")

# ---------------------------------------------------------------------------
# EXTRACCIÓN DE TEXTO
# ---------------------------------------------------------------------------
def extraer_texto(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        paginas = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                paginas.append(t.strip())
        return "\n\n".join(paginas)
    except Exception as e:
        return f"[Error al leer PDF: {e}]"


# ---------------------------------------------------------------------------
# HEURÍSTICAS DE EXTRACCIÓN
# ---------------------------------------------------------------------------
REF_PATTERNS = [
    r"ref(?:erencia|erencia\.?|\.?\s*:?\s*)([A-Z0-9][A-Z0-9\-\.\/\s]{2,30})",
    r"c[oó]d(?:igo)?\.?\s*(?:art(?:ículo)?\.?)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\.\/]{3,25})",
    r"art(?:ículo)?\.?\s*n[oº°]?\.?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\.\/]{3,25})",
    r"\bref\b\.?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\.\/]{3,25})",
]

def _limpiar_linea(line: str) -> str:
    return re.sub(r'\s+', ' ', line).strip()

def extraer_referencia(texto: str) -> str:
    for pat in REF_PATTERNS:
        m = re.search(pat, texto, re.IGNORECASE)
        if m:
            val = m.group(1).strip().split()[0]
            if len(val) >= 3:
                return val
    return ""

def extraer_descripcion_corta(texto: str) -> str:
    for line in texto.splitlines():
        line = _limpiar_linea(line)
        if 8 <= len(line) <= 80 and not re.match(r'^[\d\W]+$', line):
            return line[:40].upper()
    return ""

def extraer_bloque_principal(texto: str) -> str:
    """Devuelve los primeros ~1500 chars de texto limpio para traducir."""
    lines = [_limpiar_linea(l) for l in texto.splitlines() if len(_limpiar_linea(l)) > 5]
    bloque = " ".join(lines)
    return bloque[:1500].strip()


# ---------------------------------------------------------------------------
# TRADUCCIÓN
# ---------------------------------------------------------------------------
def traducir(texto: str, destino: str) -> str:
    if not texto.strip():
        return ""
    try:
        # Google Translate limita a ~5000 chars; ya trabajamos con ≤1500
        return GoogleTranslator(source="auto", target=destino).translate(texto)
    except Exception:
        return texto  # Si falla, devuelve el original sin romper el flujo


# ---------------------------------------------------------------------------
# PROCESADO COMPLETO DE UN PDF
# ---------------------------------------------------------------------------
def procesar_pdf(pdf_bytes: bytes, filename: str) -> dict:
    texto = extraer_texto(pdf_bytes)
    ref = extraer_referencia(texto)
    desc_corta_raw = extraer_descripcion_corta(texto)
    bloque = extraer_bloque_principal(texto)

    desc_larga_es = traducir(bloque, "es")
    desc_larga_ca = traducir(bloque, "ca")
    desc_corta = traducir(desc_corta_raw, "es")[:40].upper() if desc_corta_raw else ""

    return {
        "Archivo": filename,
        "Descripción corta material": desc_corta,
        "Descripción larga material": desc_larga_es,
        "Descripció llarga material català": desc_larga_ca,
        "referència": ref,
        "_texto": texto,
    }


# ---------------------------------------------------------------------------
# EXPORT EXCEL
# ---------------------------------------------------------------------------
COLS_EXPORT = [
    "Descripción corta material",
    "Descripción larga material",
    "Descripció llarga material català",
    "referència",
]

def to_excel(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    df_exp = df[[c for c in COLS_EXPORT if c in df.columns]].copy()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df_exp.to_excel(writer, index=False, sheet_name="Maestro")
        ws = writer.sheets["Maestro"]
        ws.set_column(0, 0, 42)
        ws.set_column(1, 1, 70)
        ws.set_column(2, 2, 70)
        ws.set_column(3, 3, 28)
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
    st.caption("Sube fichas técnicas en PDF. Se extraen y traducen los campos automáticamente — edita lo que necesites y descarga el Excel.")

st.markdown("---")

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
# PROCESAR (solo pendientes, con spinner por PDF)
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
        resultado = procesar_pdf(archivo.read(), archivo.name)
        st.session_state[KEY][archivo.name] = resultado
    progress.progress(1.0, text="Listo")
    progress.empty()

resultados = list(st.session_state[KEY].values())

# ---------------------------------------------------------------------------
# TABLA EDITABLE
# ---------------------------------------------------------------------------
df_res = pd.DataFrame(resultados)
df_edit = df_res[["Archivo"] + COLS_EXPORT].copy()

st.markdown(f"### {len(df_edit)} material(es) — edita los campos y descarga el Excel")
st.caption("Descripciones traducidas automáticamente al castellano y catalán. Revisa y ajusta si es necesario.")

df_editado = st.data_editor(
    df_edit,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    disabled=["Archivo"],
    column_config={
        "Archivo": st.column_config.TextColumn("Archivo", width="medium"),
        "Descripción corta material": st.column_config.TextColumn(
            "Desc. corta ES (máx 40)", max_chars=40, width="medium"
        ),
        "Descripción larga material": st.column_config.TextColumn(
            "Desc. larga ES", width="large"
        ),
        "Descripció llarga material català": st.column_config.TextColumn(
            "Desc. llarga CA", width="large"
        ),
        "referència": st.column_config.TextColumn("Referència", width="small"),
    },
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
st.caption("Consulta el texto original para completar campos que la extracción automática no haya capturado.")

for r in resultados:
    with st.expander(r["Archivo"]):
        texto = r.get("_texto", "")
        if texto:
            st.text_area("", value=texto, height=300,
                         key=f"txt_{r['Archivo']}", label_visibility="collapsed")
        else:
            st.warning("No se pudo extraer texto de este PDF (puede ser una imagen escaneada).")
