import streamlit as st
import pandas as pd
import os
import io
import unicodedata
import streamlit_antd_components as sac

# 1. CONFIGURACION
st.set_page_config(page_title="Catalogo Hospital Clinic", layout="wide")

st.markdown("""
<style>
.main .block-container {
    max-width: 100% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1rem !important;
}
[data-testid="stSidebar"] {
    min-width: 200px !important;
    max-width: 200px !important;
}

/* --- ARBOL: TARGETS GRANDES PARA MOVIL --- */
.ant-tree .ant-tree-switcher {
    width: 42px !important;
    height: 42px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    background: rgba(0, 74, 153, 0.06) !important;
    border-radius: 8px !important;
    margin-right: 6px !important;
    transition: all 0.2s !important;
}
.ant-tree .ant-tree-switcher:hover {
    background: rgba(0, 74, 153, 0.20) !important;
    transform: scale(1.08);
}
.ant-tree .ant-tree-switcher svg,
.ant-tree .ant-tree-switcher i svg {
    width: 22px !important;
    height: 22px !important;
    fill: #004a99 !important;
}
.ant-tree .ant-tree-node-content-wrapper {
    min-height: 40px !important;
    line-height: 40px !important;
    font-size: 15px !important;
    padding: 0 10px !important;
    border-radius: 6px !important;
}
.ant-tree .ant-tree-node-content-wrapper:hover {
    background: rgba(0, 74, 153, 0.08) !important;
}
.ant-tree .ant-tree-treenode {
    padding: 3px 0 !important;
}
.ant-tree .ant-tree-iconEle {
    font-size: 18px !important;
}
</style>
""", unsafe_allow_html=True)


# 2. UTILIDADES
def normalize(text):
    """Quita acentos y pasa a minusculas para busqueda."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()


# 3. CARGA DE DATOS

def _col_match(col_name, *targets):
    """Compara nombre de columna contra targets, ignorando acentos y mayusculas."""
    cn = normalize(str(col_name).strip().rstrip('.'))
    for t in targets:
        if cn == normalize(t.rstrip('.')):
            return True
    return False


def _leer_cat2_xlsx(ruta_cat2):
    """Lee cat2_refs.xlsx, extrae columnas relevantes y devuelve DataFrame limpio."""
    try:
        df2 = pd.read_excel(ruta_cat2, header=0, dtype=str, engine='calamine')
    except Exception:
        df2 = pd.read_excel(ruta_cat2, header=0, dtype=str, engine='openpyxl')

    keep = {}
    for c in df2.columns:
        if _col_match(c, 'Cod.M', 'Cód.M'):
            keep[c] = 'Material'
        elif _col_match(c, 'Ref.Prov', 'Ref Prov'):
            keep[c] = 'Ref Proveedor'
        elif _col_match(c, 'Nom.Prov', 'Nom Prov', 'Nombre Proveedor'):
            keep[c] = 'Nombre Proveedor'
        elif _col_match(c, '/GpC', 'GpC', 'Grupo Compras'):
            keep[c] = 'Grupo Compras'
        elif _col_match(c, '/P', 'P'):
            keep[c] = '/P'

    if 'Material' not in keep.values() or 'Ref Proveedor' not in keep.values():
        return pd.DataFrame()

    cols_needed = [k for k, v in keep.items() if v in ('Material', 'Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras', '/P')]
    df2 = df2[cols_needed].rename(columns=keep).fillna("").astype(str)
    for col in ('Nombre Proveedor', 'Grupo Compras', '/P'):
        if col not in df2.columns:
            df2[col] = ""
    df2['Material'] = df2['Material'].str.strip()
    return df2


@st.cache_data(ttl=3600)
def _cargar_refs_cat2(base):
    """Carga cat2_refs.xlsx (via parquet si disponible) y agrupa refs por material."""
    ruta_xlsx = os.path.join(base, 'cat2_refs.xlsx')
    ruta_parquet = os.path.join(base, 'cat2_refs.parquet')
    if not os.path.exists(ruta_xlsx):
        return pd.DataFrame()
    try:
        if (os.path.exists(ruta_parquet) and
                os.path.getmtime(ruta_parquet) >= os.path.getmtime(ruta_xlsx)):
            df2 = pd.read_parquet(ruta_parquet)
        else:
            df2 = _leer_cat2_xlsx(ruta_xlsx)
            if not df2.empty:
                df2.to_parquet(ruta_parquet, index=False)

        if df2.empty:
            return pd.DataFrame()

        # Solo materiales con al menos una X en /P
        if '/P' in df2.columns:
            materiales_p = df2[df2['/P'].str.strip().str.upper() == 'X']['Material'].unique()
            df2 = df2[df2['Material'].isin(materiales_p)]

        if df2.empty:
            return pd.DataFrame()

        agg = {
            'Ref Proveedor': lambda x: ' | '.join(sorted(set(v.strip() for v in x if v.strip()))),
            'Nombre Proveedor': lambda x: ' | '.join(sorted(set(v.strip() for v in x if v.strip()))),
            'Grupo Compras': lambda x: ' | '.join(sorted(set(v.strip() for v in x if v.strip()))),
        }
        return df2.groupby('Material').agg(agg).reset_index()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def cargar_datos():
    base = os.path.dirname(os.path.abspath(__file__))
    ruta_excel = os.path.join(base, 'cat1.xlsx')
    if not os.path.exists(ruta_excel):
        return pd.DataFrame()
    try:
        try:
            df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str,
                               usecols=[0, 1, 2, 3, 4, 5], engine='calamine')
        except Exception:
            df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str,
                               usecols=[0, 1, 2, 3, 4, 5], engine='openpyxl')

        cols = df.columns
        mapa = {}
        if len(cols) > 0: mapa[cols[0]] = 'Nivel 3'
        if len(cols) > 1: mapa[cols[1]] = 'Nivel 4'
        if len(cols) > 2: mapa[cols[2]] = 'Nivel 5'
        if len(cols) > 3: mapa[cols[3]] = 'Descripcion Corta'
        if len(cols) > 4: mapa[cols[4]] = 'Material'
        if len(cols) > 5: mapa[cols[5]] = 'Descripcion Larga'
        df = df.rename(columns=mapa)

        req = ['Nivel 3', 'Nivel 4', 'Nivel 5', 'Descripcion Corta', 'Material', 'Descripcion Larga']
        for c in req:
            if c not in df.columns:
                df[c] = ""
        df = df[req].fillna("").astype(str)

        # Enriquecer con Ref.Prov de cat2_refs.xlsx
        df_refs = _cargar_refs_cat2(base)
        if not df_refs.empty:
            df = df.merge(df_refs, on='Material', how='left')
            for col in ('Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras'):
                df[col] = df[col].fillna("") if col in df.columns else ""
        if 'Ref Proveedor' not in df.columns:
            df['Ref Proveedor'] = ""
            df['Nombre Proveedor'] = ""
        return df
    except Exception:
        return pd.DataFrame()


def to_excel(df_in):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_in.to_excel(writer, index=False)
    return out.getvalue()


df = cargar_datos()


# 4. CABECERA
col_logo, col_search = st.columns([0.12, 0.88])
with col_logo:
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logo.png')
    if os.path.exists(logo_path):
        st.image(logo_path, width=160)
with col_search:
    st.write("")
    busqueda_raw = st.text_input(
        "Buscador",
        placeholder="\U0001f50d Busca varias palabras: aguja 21g subcutanea (sin acentos vale)",
        label_visibility="collapsed",
    )

st.markdown("---")


# 5. BUSQUEDA MULTI-PALABRA + SIN ACENTOS
df_f = df.copy()
hay_busqueda = False

if busqueda_raw.strip():
    hay_busqueda = True
    words = normalize(busqueda_raw).split()
    search_fields = ['Material', 'Descripcion Corta', 'Nivel 3', 'Nivel 4', 'Nivel 5']

    df_norm = pd.DataFrame(index=df_f.index)
    for col in search_fields:
        df_norm[col] = df_f[col].apply(normalize)

    for word in words:
        mask = pd.Series(False, index=df_f.index)
        word_compact = word.replace(' ', '').replace('-', '')
        for col in search_fields:
            # Busqueda normal (con espacios)
            mask = mask | df_norm[col].str.contains(word, na=False, regex=False)
            # Busqueda compacta: ignora espacios y guiones en ambos lados
            # Permite "papeldina4" encontrar "Papel Din A4"
            field_compact = df_norm[col].str.replace(' ', '', regex=False).str.replace('-', '', regex=False)
            mask = mask | field_compact.str.contains(word_compact, na=False, regex=False)
        df_f = df_f[mask]
        df_norm = df_norm.loc[df_f.index]


# 6. FILTROS EN CASCADA
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
        st.download_button("EXPORTAR", to_excel(df_f), fname, "application/vnd.ms-excel", type="primary")


# 7. CONTROL DE CARGA
LIMITE = 1500
sin_filtro = sel_n3 == "Todas" and sel_n4 == "Todas" and sel_n5 == "Todos" and not hay_busqueda
demasiados = len(df_f) > LIMITE and sin_filtro

if demasiados:
    st.warning(f"{len(df_f)} materiales. Usa el buscador o selecciona una Familia para ver el arbol.")
    if not st.checkbox("Mostrar todo igualmente (puede ir lento)"):
        df_f_vista = pd.DataFrame()
    else:
        df_f_vista = df_f
else:
    df_f_vista = df_f


# 8. CONSTRUIR ARBOL
@st.cache_data(show_spinner=False)
def construir_arbol(datos_json, _key):
    df_temp = pd.read_json(io.StringIO(datos_json), orient='records')
    for col in df_temp.columns:
        df_temp[col] = df_temp[col].astype(str)
    arbol = []
    for n3, g3 in df_temp.groupby('Nivel 3', sort=True):
        hijos_n3 = []
        for n4, g4 in g3.groupby('Nivel 4', sort=True):
            hijos_n4 = []
            for n5, g5 in g4.groupby('Nivel 5', sort=True):
                hijos_n5 = []
                for _, row in g5.iterrows():
                    label = f"{row['Material']} - {row['Descripcion Corta']}"
                    hijos_n5.append(sac.TreeItem(label, icon='box-seam', tooltip=row['Descripcion Larga'][:100] + "..."))
                hijos_n4.append(sac.TreeItem(str(n5), icon='folder', children=hijos_n5))
            hijos_n3.append(sac.TreeItem(str(n4), icon='folder', children=hijos_n4))
        arbol.append(sac.TreeItem(str(n3), icon='folder-fill', children=hijos_n3))
    return arbol


# 9. INTERFAZ PRINCIPAL
c_tree, c_det = st.columns([0.42, 0.58])

seleccion_id = None

with c_tree:
    if demasiados and df_f_vista.empty:
        st.info("Filtra por Familia o busca un material para ver el arbol.")
    elif df_f_vista.empty:
        st.warning("No hay materiales que coincidan.")
    else:
        st.caption(f"{len(df_f_vista)} materiales  \u2014  pulsa  \u25b6  para abrir cada nivel")

        filtro_key = f"{sel_n3}|{sel_n4}|{sel_n5}|{busqueda_raw}|{len(df_f_vista)}"
        datos_json = df_f_vista.to_json(orient='records')
        items_arbol = construir_arbol(datos_json, filtro_key)

        abrir = hay_busqueda or len(df_f_vista) <= 50

        seleccion_id = sac.tree(
            items=items_arbol,
            label='Catalogo',
            index=None,
            format_func='title',
            size='md',
            icon='table',
            open_all=abrir,
            show_line=True,
        )

with c_det:
    if seleccion_id:
        if isinstance(seleccion_id, list):
            seleccion_id = seleccion_id[0] if seleccion_id else None

        if seleccion_id:
            df_busq = df_f_vista.copy()
            df_busq['_key'] = df_busq['Material'] + " - " + df_busq['Descripcion Corta']
            fila = df_busq[df_busq['_key'] == seleccion_id]

            if not fila.empty:
                item = fila.iloc[0]
                with st.container(border=True):
                    st.markdown(f"# {item['Material']}")
                    st.markdown(f"### {item['Descripcion Corta']}")
                    st.info(f"{item['Nivel 3']}  >  {item['Nivel 4']}  >  {item['Nivel 5']}")
                    st.divider()
                    st.markdown("### Descripcion Tecnica")
                    st.write(item['Descripcion Larga'])
                    if item.get('Ref Proveedor', '').strip():
                        st.divider()
                        st.markdown("### Referencia Proveedor")
                        st.write(item['Ref Proveedor'])
                        if item.get('Nombre Proveedor', '').strip():
                            st.caption(f"Proveedor: {item['Nombre Proveedor']}")
                    st.divider()
                    st.caption("Codigo de material:")
                    st.code(item['Material'], language=None)
            else:
                st.info(f"**{seleccion_id}**")
                st.caption("Pulsa \u25b6 para ver el contenido.")
    else:
        st.markdown(
            '<div style="text-align:center; color:#aaa; padding-top:80px;">'
            '<h3>Selecciona un material en el arbol</h3>'
            '</div>',
            unsafe_allow_html=True,
        )
