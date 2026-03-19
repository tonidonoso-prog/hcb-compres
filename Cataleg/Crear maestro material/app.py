import streamlit as st
import pandas as pd
import anthropic
import base64
import io
import json
import os

st.set_page_config(page_title="Crear Maestro Material", layout="wide")

# ---------------------------------------------------------------------------
# PROMPT
# ---------------------------------------------------------------------------
PROMPT = """Eres un experto en compras hospitalarias. A partir de esta ficha técnica de producto sanitario, extrae los siguientes campos y devuelve SOLO un JSON válido, sin texto adicional:

{
  "descripcion_corta": "...",
  "descripcion_larga_es": "...",
  "descripcio_llarga_ca": "...",
  "referencia": "..."
}

Reglas estrictas:
- "descripcion_corta": máximo 40 caracteres, EN MAYÚSCULAS, sin artículos ni marca comercial. Ejemplo: "AGUJA SUBCUTANEA 21G 0.8X25MM"
- "descripcion_larga_es": descripción técnica completa en castellano. Incluye características, materiales, medidas, esterilidad, uso previsto, etc.
- "descripcio_llarga_ca": mateixa descripció tècnica però en català correcte.
- "referencia": código o referencia del fabricante/proveedor. Si hay varias, separa con " / ".
- Si no encuentras un campo, usa cadena vacía "".
- Devuelve SOLO el JSON, sin bloques de código ni texto adicional."""


# ---------------------------------------------------------------------------
# CLIENTE ANTHROPIC (cached para no reconectar en cada rerun)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_client():
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


# ---------------------------------------------------------------------------
# PROCESADO DE PDF
# ---------------------------------------------------------------------------
def procesar_pdf(client, pdf_bytes: bytes, filename: str) -> dict:
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
        raw = response.content[0].text.strip()
        # Limpiar posibles bloques ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return {
            "Archivo": filename,
            "Descripción corta material": data.get("descripcion_corta", ""),
            "Descripción larga material": data.get("descripcion_larga_es", ""),
            "Descripció llarga material català": data.get("descripcio_llarga_ca", ""),
            "referència": data.get("referencia", ""),
            "_error": "",
        }
    except json.JSONDecodeError:
        return {"Archivo": filename, "_error": f"JSON inválido: {raw[:300]}"}
    except Exception as e:
        return {"Archivo": filename, "_error": str(e)}


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
        ws.set_column(0, 0, 42)   # corta
        ws.set_column(1, 1, 70)   # larga ES
        ws.set_column(2, 2, 70)   # llarga CA
        ws.set_column(3, 3, 28)   # ref
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
    st.caption("Sube fichas técnicas en PDF y genera automáticamente las descripciones para SAP.")

st.markdown("---")

# ---------------------------------------------------------------------------
# VERIFICAR API KEY
# ---------------------------------------------------------------------------
client = get_client()
if client is None:
    st.error(
        "No se encontró la clave de API de Anthropic. "
        "Añade **ANTHROPIC_API_KEY** en los Secrets de Streamlit Cloud "
        "(Settings → Secrets)."
    )
    st.stop()

# ---------------------------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------------------------
archivos = st.file_uploader(
    "Sube una o varias fichas técnicas en PDF",
    type=["pdf"],
    accept_multiple_files=True,
    help="Puedes arrastrar varios PDFs a la vez.",
)

if not archivos:
    st.info("Sube al menos un PDF para comenzar.")
    st.stop()

# ---------------------------------------------------------------------------
# PROCESAR (solo los nuevos o si se pulsa reprocesar)
# ---------------------------------------------------------------------------
KEY = "maestro_resultados"
if KEY not in st.session_state:
    st.session_state[KEY] = {}

nombres_subidos = {f.name for f in archivos}
nombres_cached = set(st.session_state[KEY].keys())

pendientes = [f for f in archivos if f.name not in nombres_cached]
retirados = nombres_cached - nombres_subidos
for r in retirados:
    del st.session_state[KEY][r]

if pendientes:
    progress = st.progress(0, text="Procesando fichas...")
    for i, archivo in enumerate(pendientes):
        progress.progress((i) / len(pendientes), text=f"Procesando: {archivo.name}")
        resultado = procesar_pdf(client, archivo.read(), archivo.name)
        st.session_state[KEY][archivo.name] = resultado
    progress.progress(1.0, text="Listo")
    progress.empty()

# ---------------------------------------------------------------------------
# CONSTRUIR DATAFRAME DE RESULTADOS
# ---------------------------------------------------------------------------
resultados = list(st.session_state[KEY].values())
df_res = pd.DataFrame(resultados)

errores = df_res[df_res.get("_error", pd.Series(dtype=str)).fillna("") != ""] if "_error" in df_res.columns else pd.DataFrame()
if not errores.empty:
    with st.expander(f"⚠️ {len(errores)} error(es) al procesar", expanded=True):
        for _, row in errores.iterrows():
            st.error(f"**{row['Archivo']}**: {row.get('_error', '')}")

df_ok = df_res[df_res.get("_error", pd.Series(dtype=str)).fillna("") == ""].copy() if "_error" in df_res.columns else df_res.copy()
df_ok = df_ok.drop(columns=["_error", "Archivo"], errors="ignore")

if df_ok.empty:
    st.warning("No hay resultados válidos todavía.")
    st.stop()

# ---------------------------------------------------------------------------
# TABLA EDITABLE + DESCARGA
# ---------------------------------------------------------------------------
st.markdown(f"### {len(df_ok)} material(es) extraído(s)")
st.caption("Puedes editar cualquier celda antes de descargar el Excel.")

df_editado = st.data_editor(
    df_ok,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "Descripción corta material": st.column_config.TextColumn(
            "Descripción corta material", max_chars=40, width="medium"
        ),
        "Descripción larga material": st.column_config.TextColumn(
            "Descripción larga material", width="large"
        ),
        "Descripció llarga material català": st.column_config.TextColumn(
            "Descripció llarga material català", width="large"
        ),
        "referència": st.column_config.TextColumn("referència", width="small"),
    },
)

st.download_button(
    label="Descargar Excel",
    data=to_excel(df_editado),
    file_name="maestro_material.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    use_container_width=False,
)
