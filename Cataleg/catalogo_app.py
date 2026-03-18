import streamlit as st
import pandas as pd
import os
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Catálogo Hospital Clínic", layout="wide")

st.markdown("""
<style>
.main .block-container {
    max-width: 100% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS
@st.cache_data(ttl=3600)
def cargar_datos():
    ruta_excel = 'cat1.xlsx'
    if os.path.exists(ruta_excel):
        try:
            try:
                df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str, engine='calamine')
            except Exception:
                df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str, engine='openpyxl')

            cols = df.columns
            mapa = {}
            if len(cols) > 0: mapa[cols[0]] = 'Nivel 3'
            if len(cols) > 1: mapa[cols[1]] = 'Nivel 4'
            if len(cols) > 2: mapa[cols[2]] = 'Nivel 5'
            if len(cols) > 3: mapa[cols[3]] = 'Descripción Corta'
            if len(cols) > 4: mapa[cols[4]] = 'Material'
            if len(cols) > 5: mapa[cols[5]] = 'Descripción Larga'

            df = df.rename(columns=mapa)
            req = ['Nivel 3', 'Nivel 4', 'Nivel 5', 'Descripción Corta', 'Material', 'Descripción Larga']
            for c in req:
                if c not in df.columns: df[c] = ""
            return df[req].fillna("").astype(str)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def to_excel(df_in):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_in.to_excel(writer, index=False)
    return out.getvalue()

df = cargar_datos()

# 3. CABECERA
col_logo, col_search = st.columns([0.15, 0.85])
with col_logo:
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logo.png')
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
with col_search:
    st.write("")
    busqueda = st.text_input(
        "Buscador",
        placeholder="🔍 Buscar por código, descripción...",
        label_visibility="collapsed"
    ).lower()

st.markdown("---")

# 4. FILTROS EN CASCADA
df_f = df.copy()

if busqueda:
    mask = (
        df_f['Material'].str.contains(busqueda, case=False, na=False) |
        df_f['Descripción Corta'].str.contains(busqueda, case=False, na=False) |
        df_f['Descripción Larga'].str.contains(busqueda, case=False, na=False)
    )
    df_f = df_f[mask]

cf1, cf2, cf3, c_exp = st.columns([1.5, 1.5, 1.5, 1])

with cf1:
    sel_n3 = st.selectbox("Familia", ["Todas"] + sorted(df_f['Nivel 3'].unique()))
    if sel_n3 != "Todas":
        df_f = df_f[df_f['Nivel 3'] == sel_n3]

with cf2:
    sel_n4 = st.selectbox("Subfamilia", ["Todas"] + sorted(df_f['Nivel 4'].unique()))
    if sel_n4 != "Todas":
        df_f = df_f[df_f['Nivel 4'] == sel_n4]

with cf3:
    sel_n5 = st.selectbox("Grupo", ["Todos"] + sorted(df_f['Nivel 5'].unique()))
    if sel_n5 != "Todos":
        df_f = df_f[df_f['Nivel 5'] == sel_n5]

with c_exp:
    st.write("")
    st.write("")
    if not df_f.empty:
        fname = f"{sel_n3}.xlsx" if sel_n3 != "Todas" else "catalogo.xlsx"
        st.download_button("📥 EXPORTAR", to_excel(df_f), fname, "application/vnd.ms-excel", type="primary")

# 5. TABLA + DETALLE
sin_filtro = (sel_n3 == "Todas" and sel_n4 == "Todas" and sel_n5 == "Todos" and not busqueda)

selected_item = None
df_tabla = df_f.reset_index(drop=True)

c_tabla, c_det = st.columns([0.50, 0.50])

with c_tabla:
    if sin_filtro:
        st.info("Usa el buscador o selecciona una Familia para ver los materiales.")
    elif df_tabla.empty:
        st.warning("No hay materiales que coincidan con los filtros.")
    else:
        st.caption(f"{len(df_tabla)} materiales")
        event = st.dataframe(
            df_tabla[['Material', 'Descripción Corta', 'Nivel 5']],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Material":          st.column_config.TextColumn("Código",      width="small"),
                "Descripción Corta": st.column_config.TextColumn("Descripción", width="large"),
                "Nivel 5":           st.column_config.TextColumn("Grupo",       width="medium"),
            }
        )
        if event.selection.rows:
            selected_item = df_tabla.iloc[event.selection.rows[0]]

with c_det:
    if selected_item is not None:
        with st.container(border=True):
            st.markdown(f"# 📦 {selected_item['Material']}")
            st.markdown(f"### {selected_item['Descripción Corta']}")
            st.info(f"📂 {selected_item['Nivel 3']}  ➜  {selected_item['Nivel 4']}  ➜  {selected_item['Nivel 5']}")
            st.divider()
            st.markdown("### 📝 Descripción Técnica")
            st.write(selected_item['Descripción Larga'])
            st.divider()
            st.caption("Código de material:")
            st.code(selected_item['Material'], language=None)
    else:
        st.markdown(
            """
            <div style="text-align:center; color:#aaa; padding-top:80px;">
                <h1>👈</h1>
                <h3>Haz clic en un material de la tabla</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
