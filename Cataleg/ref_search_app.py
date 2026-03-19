import streamlit as st
import pandas as pd
import os
import unicodedata


st.set_page_config(page_title="Buscar por Referencia Proveedor", layout="wide")


def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()


def _col_match(col_name, *targets):
    cn = normalize(str(col_name).strip().rstrip('.'))
    for t in targets:
        if cn == normalize(t.rstrip('.')):
            return True
    return False


def _leer_cat2_xlsx(ruta_cat2):
    """Lee cat2.xlsx, extrae columnas relevantes y devuelve DataFrame limpio."""
    try:
        df2 = pd.read_excel(ruta_cat2, sheet_name='Sheet1', header=3, dtype=str, engine='calamine')
    except Exception:
        df2 = pd.read_excel(ruta_cat2, sheet_name='Sheet1', header=3, dtype=str, engine='openpyxl')

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

    if 'Material' not in keep.values() or 'Ref Proveedor' not in keep.values():
        return pd.DataFrame()

    cols_needed = [k for k, v in keep.items() if v in ('Material', 'Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras')]
    df2 = df2[cols_needed].rename(columns=keep).fillna("").astype(str)
    for col in ('Nombre Proveedor', 'Grupo Compras'):
        if col not in df2.columns:
            df2[col] = ""
    df2 = df2[df2['Ref Proveedor'].str.strip() != ""]
    df2['Material'] = df2['Material'].str.strip()
    return df2


@st.cache_data(ttl=3600)
def cargar_cat2(base):
    ruta_xlsx = os.path.join(base, 'cat2.xlsx')
    ruta_parquet = os.path.join(base, 'cat2.parquet')
    if not os.path.exists(ruta_xlsx):
        return pd.DataFrame()
    try:
        # Usar parquet si existe y es mas reciente que el xlsx
        if (os.path.exists(ruta_parquet) and
                os.path.getmtime(ruta_parquet) >= os.path.getmtime(ruta_xlsx)):
            return pd.read_parquet(ruta_parquet)

        df2 = _leer_cat2_xlsx(ruta_xlsx)
        if not df2.empty:
            df2.to_parquet(ruta_parquet, index=False)
        return df2
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def cargar_cat1(base):
    ruta = os.path.join(base, 'cat1.xlsx')
    if not os.path.exists(ruta):
        return pd.DataFrame()
    try:
        try:
            df = pd.read_excel(ruta, sheet_name='CAT1', header=0, dtype=str, engine='calamine')
        except Exception:
            df = pd.read_excel(ruta, sheet_name='CAT1', header=0, dtype=str, engine='openpyxl')
        cols = df.columns
        mapa = {}
        if len(cols) > 4: mapa[cols[4]] = 'Material'
        if len(cols) > 3: mapa[cols[3]] = 'Descripcion Corta'
        if len(cols) > 0: mapa[cols[0]] = 'Familia'
        if len(cols) > 1: mapa[cols[1]] = 'Subfamilia'
        df = df.rename(columns=mapa)
        keep = [c for c in ('Material', 'Descripcion Corta', 'Familia', 'Subfamilia') if c in df.columns]
        return df[keep].fillna("").astype(str).drop_duplicates('Material')
    except Exception:
        return pd.DataFrame()


# --- CABECERA ---
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logo.png')
col_logo, col_title = st.columns([0.12, 0.88])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=160)
with col_title:
    st.write("")
    busqueda_raw = st.text_input(
        "Referencia",
        placeholder="\U0001f50d Busca por referencia de proveedor (varias palabras, sin acentos vale)",
        label_visibility="collapsed",
    )

st.markdown("---")

base = os.path.dirname(os.path.abspath(__file__))
df_cat2 = cargar_cat2(base)
df_cat1 = cargar_cat1(base)

if df_cat2.empty:
    st.error("No se pudo cargar cat2.xlsx o no contiene las columnas Cód.M / Ref.Prov.")
elif not busqueda_raw.strip():
    st.info("Introduce una referencia de proveedor para buscar el material correspondiente.")
else:
    words = normalize(busqueda_raw).split()
    df_ref = df_cat2.copy()
    ref_fields = ['Ref Proveedor', 'Nombre Proveedor']
    df_norm = pd.DataFrame(index=df_ref.index)
    for col in ref_fields:
        df_norm[col] = df_ref[col].apply(normalize)

    for word in words:
        mask = pd.Series(False, index=df_ref.index)
        word_compact = word.replace(' ', '').replace('-', '')
        for col in ref_fields:
            mask = mask | df_norm[col].str.contains(word, na=False, regex=False)
            field_compact = df_norm[col].str.replace(' ', '', regex=False).str.replace('-', '', regex=False)
            mask = mask | field_compact.str.contains(word_compact, na=False, regex=False)
        df_ref = df_ref[mask]
        df_norm = df_norm.loc[df_ref.index]

    if df_ref.empty:
        st.warning("No se encontraron materiales con esa referencia.")
    else:
        if not df_cat1.empty:
            df_ref = df_ref.merge(df_cat1, on='Material', how='left')
            for col in ('Descripcion Corta', 'Familia', 'Subfamilia'):
                if col in df_ref.columns:
                    df_ref[col] = df_ref[col].fillna("")
                else:
                    df_ref[col] = ""

        cols_show = ['Material', 'Descripcion Corta', 'Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras', 'Familia', 'Subfamilia']
        cols_show = [c for c in cols_show if c in df_ref.columns]
        df_show = df_ref[cols_show].drop_duplicates().copy()
        df_show.columns = [
            {'Descripcion Corta': 'Descripcion', 'Nombre Proveedor': 'Proveedor',
             'Grupo Compras': 'Grp Compras'}.get(c, c) for c in cols_show
        ]
        st.caption(f"{len(df_show)} resultados encontrados")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
