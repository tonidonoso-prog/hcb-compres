import streamlit as st
import pandas as pd
import os
import json
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
        elif _col_match(c, 'Prov.', 'Prov'):
            keep[c] = 'Cod Prov'
        elif _col_match(c, 'Resp.Cont.', 'Resp.Cont', 'Resp Cont'):
            keep[c] = 'Resp Cont'
        elif _col_match(c, 'Resp.Tec.', 'Resp.Tec', 'Resp Tec'):
            keep[c] = 'Resp Tec'

    if 'Material' not in keep.values() or 'Ref Proveedor' not in keep.values():
        return pd.DataFrame()

    cols_needed = [k for k, v in keep.items() if v in ('Material', 'Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras', 'Cod Prov', 'Resp Cont', 'Resp Tec')]
    df2 = df2[cols_needed].rename(columns=keep).fillna("").astype(str)
    for col in ('Nombre Proveedor', 'Grupo Compras', 'Cod Prov', 'Resp Cont', 'Resp Tec'):
        if col not in df2.columns:
            df2[col] = ""
    df2 = df2[df2['Ref Proveedor'].str.strip() != ""]
    df2['Material'] = df2['Material'].str.strip()
    return df2


@st.cache_data(ttl=3600)
def cargar_cat2(base):
    ruta_xlsx = os.path.join(base, 'cat2_refs.xlsx')
    ruta_parquet = os.path.join(base, 'cat2_refs.parquet')
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
    # Ocultado temporalmente por petición del usuario
    # if os.path.exists(logo_path):
    #     st.image(logo_path, width=160)
    st.write("📦") 
with col_title:
    st.write("")
    busqueda_raw = st.text_input(
        "Referencia",
        placeholder="\U0001f50d Busca por referencia de proveedor (varias palabras, sin acentos vale)",
        label_visibility="collapsed",
    )

st.markdown("---")

base = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(base), "data")

df_cat2 = cargar_cat2(DATA_DIR)
df_cat1 = cargar_cat1(DATA_DIR)

# Cargar indice de fichas tecnicas
_fichas_path = os.path.join(DATA_DIR, 'fichas_index.json')
fichas_index = {}
if os.path.exists(_fichas_path):
    try:
        fichas_index = json.load(open(_fichas_path, encoding='utf-8'))
    except Exception:
        pass

if df_cat2.empty:
    st.error("No se pudo cargar cat2_refs.xlsx o no contiene las columnas Cód.M / Ref.Prov.")
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

        # Añadir URL de ficha tecnica por fila (material + cod_prov)
        def _ficha_url(row):
            key = f"{row['Material']}-{row.get('Cod Prov', '').strip()}"
            return fichas_index.get(key, "")

        df_ref['Ficha'] = df_ref.apply(_ficha_url, axis=1)

        cols_show = ['Material', 'Descripcion Corta', 'Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras', 'Familia', 'Resp Cont', 'Resp Tec', 'Ficha']
        cols_show = [c for c in cols_show if c in df_ref.columns]
        df_show = df_ref[cols_show].drop_duplicates().copy()
        rename = {'Descripcion Corta': 'Descripcion', 'Nombre Proveedor': 'Proveedor', 'Grupo Compras': 'Grp Compras'}
        df_show.columns = [rename.get(c, c) for c in cols_show]
        st.caption(f"{len(df_show)} resultados encontrados")
        col_cfg = {}
        if 'Ficha' in df_show.columns:
            col_cfg['Ficha'] = st.column_config.LinkColumn("Ficha", display_text="Abrir ficha")
        st.dataframe(df_show, use_container_width=True, hide_index=True, column_config=col_cfg)
