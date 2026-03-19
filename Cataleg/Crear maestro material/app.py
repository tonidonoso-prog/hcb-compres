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
# FILTROS DE LÍNEAS BASURA (cabeceras, pies, direcciones)
# ---------------------------------------------------------------------------
_JUNK = re.compile(
    r'ctra\.|carretera|km\.|tfno|fax|tel[eé]f|\bwww\b|@|'
    r'rev\.\s*\d|\d{2}/\d{2}/\d{4}|'          # revisiones y fechas
    r'^\s*ficha\s+t[eé]cnica\s*$|'            # etiqueta "FICHA TÉCNICA" sola
    r'^\s*\d{5}\s',                            # código postal
    re.IGNORECASE
)

def _es_basura(line: str) -> bool:
    return bool(_JUNK.search(line))

def lineas_limpias(texto: str) -> list[str]:
    result = []
    for l in texto.splitlines():
        l = re.sub(r'\s+', ' ', l).strip()
        if len(l) > 3 and not _es_basura(l):
            result.append(l)
    return result


# ---------------------------------------------------------------------------
# REFERENCIA: primero del filename, luego del texto
# ---------------------------------------------------------------------------
_REF_LABELED = re.compile(
    r'(?:ref(?:erencia)?|c[oó]d(?:igo)?|art(?:ículo)?|cat(?:alog)?(?:\s*no\.?)?)'
    r'[\s:\.\-]*([A-Z0-9][A-Z0-9\-\.\/]{2,25})',
    re.IGNORECASE
)

def extraer_referencia(filename: str, texto: str) -> str:
    # 1. Intentar sacar del nombre de fichero: mat-prov-REF.pdf
    base = os.path.splitext(filename)[0]
    parts = base.split('-', 2)
    if len(parts) >= 3 and parts[2].strip():
        return parts[2].strip()

    # 2. Buscar en el texto con patrones etiquetados
    m = _REF_LABELED.search(texto)
    if m:
        val = m.group(1).strip().split()[0]
        if len(val) >= 3:
            return val
    return ""


# ---------------------------------------------------------------------------
# NOMBRE DEL PRODUCTO (descripción corta)
# ---------------------------------------------------------------------------
def extraer_nombre_producto(texto: str) -> str:
    """
    Busca el nombre del producto después de 'FICHA TÉCNICA' o como línea
    destacada en mayúsculas que no sea basura.
    """
    lines = texto.splitlines()
    despues_ficha = False
    candidatos = []

    for line in lines:
        l = re.sub(r'\s+', ' ', line).strip()
        if not l:
            continue

        # Activar búsqueda tras "FICHA TÉCNICA"
        if re.match(r'^\s*ficha\s+t[eé]cnica\s*$', l, re.IGNORECASE):
            despues_ficha = True
            continue

        if _es_basura(l):
            continue

        # Línea inmediatamente tras "FICHA TÉCNICA" → candidato prioritario
        if despues_ficha and 5 < len(l) <= 80:
            candidatos.insert(0, l)
            despues_ficha = False
            continue

        # Líneas en mayúsculas significativas (nombre de producto típico)
        if l.isupper() and 8 <= len(l) <= 80 and not re.match(r'^[\d\W]+$', l):
            candidatos.append(l)

    if candidatos:
        return candidatos[0][:40].upper()

    # Fallback: primera línea limpia razonable
    for l in lineas_limpias(texto):
        if 8 <= len(l) <= 80:
            return l[:40].upper()
    return ""


# ---------------------------------------------------------------------------
# DESCRIPCIÓN LARGA: campos etiquetados + características técnicas
# ---------------------------------------------------------------------------
_CAMPOS_DESC = re.compile(
    r'^(PRODUCTO|DESCRIPCI[OÓ]N|INDICACIONES?|CARACTER[IÍ]STICAS?\s*T[EÉ]CNICAS?'
    r'|USO\s*PREVISTO|COMPOSICI[OÓ]N|MATERIA\s*PRIMA|MARCA|PRESENTACI[OÓ]N'
    r'|ESTERILIZACI[OÓ]N|PRECAUCIONES?|MODO\s*DE\s*USO)',
    re.IGNORECASE
)

def extraer_descripcion_larga(texto: str) -> str:
    """Recoge párrafos con etiquetas técnicas relevantes."""
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

    # Fallback: todo el texto limpio
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
# PROCESADO COMPLETO
# ---------------------------------------------------------------------------
def procesar_pdf(pdf_bytes: bytes, filename: str) -> dict:
    texto = extraer_texto(pdf_bytes)
    ref = extraer_referencia(filename, texto)
    nombre = extraer_nombre_producto(texto)
    desc_larga_raw = extraer_descripcion_larga(texto)

    desc_corta_es = traducir(nombre, "es")[:40].upper() if nombre else ""
    desc_larga_es = traducir(desc_larga_raw, "es")
    desc_larga_ca = traducir(desc_larga_raw, "ca")

    return {
        "Archivo": filename,
        "Descripción corta material": desc_corta_es,
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
    st.caption("Sube fichas técnicas en PDF. Se extraen y traducen los campos — edita lo que necesites y descarga el Excel.")

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
# TEXTO EXTRAÍDO (para consulta y copia)
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
