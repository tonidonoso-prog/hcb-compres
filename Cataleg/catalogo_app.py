import streamlit as st
import pandas as pd
import os
import io
import streamlit_antd_components as sac 

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Catálogo Hospital Clínic", layout="wide")

# --- CSS: MAXIMIZAR ESPACIO DISPONIBLE ---
st.markdown("""
<style>
    /* Expandir contenido principal al máximo sin ocultar sidebar */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
    }
    
    /* Reducir ancho del sidebar para dar más espacio al contenido */
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 200px !important;
    }
    
    /* Triángulos grandes para facilitar el clic */
    .ant-tree-switcher {
        width: 40px !important; 
        height: 40px !important; 
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }
    .ant-tree-switcher i svg {
        width: 25px !important;
        height: 25px !important;
        fill: #555 !important;
    }
    .ant-tree-node-content-wrapper {
        min-height: 32px !important;
        font-size: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS
@st.cache_data(ttl=3600)
def cargar_datos():
    ruta_excel = 'cat1.xlsx'
    ruta_parquet = 'CAT1.parquet'
    
    # Intento 1: Parquet (Super rápido)
    if os.path.exists(ruta_parquet):
        try:
            return pd.read_parquet(ruta_parquet)
        except:
            pass
            
    # Intento 2: Excel con motor Calamine (Muy rápido)
    if os.path.exists(ruta_excel):
        try:
            # Usamos calamine si está disponible, si no openpyxl
            try:
                df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str, engine='calamine')
            except:
                df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str, engine='openpyxl')
            
            # Mapeo de columnas
            cols = df.columns
            mapa = {}
            if len(cols) > 0: mapa[cols[0]] = 'Nivel 3'
            if len(cols) > 1: mapa[cols[1]] = 'Nivel 4'
            if len(cols) > 2: mapa[cols[2]] = 'Nivel 5'
            if len(cols) > 3: mapa[cols[3]] = 'Descripción Corta'
            if len(cols) > 4: mapa[cols[4]] = 'Material'
            if len(cols) > 5: mapa[cols[5]] = 'Descripción Larga'
            
            df = df.rename(columns=mapa)
            
            # Limpieza
            req = ['Nivel 3', 'Nivel 4', 'Nivel 5', 'Descripción Corta', 'Material', 'Descripción Larga']
            for c in req: 
                if c not in df.columns: df[c] = ""
            
            df = df[req].fillna("").astype(str)
            
            # Guardamos en parquet para la próxima vez
            df.to_parquet(ruta_parquet, index=False)
            return df
        except: return pd.DataFrame()
    else: return pd.DataFrame()

df = cargar_datos()

def to_excel(df_in):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_in.to_excel(writer, index=False)
    return out.getvalue()

# --- CABECERA ---
col_logo, col_search = st.columns([0.15, 0.85])
with col_logo:
    st.image("https://portalprofessional.clinic.cat/sap/bc/bsp/sap/zbsppubliclgn/imgs/brand_logo.jpg", width=180)
with col_search:
    st.write("")
    busqueda = st.text_input("Buscador", placeholder="🔍 Buscar material...", label_visibility="collapsed").lower()

st.markdown("---")

# --- FILTROS OPCIONALES (Ya no son obligatorios, pero ayudan a exportar) ---
cf1, cf2, cf3, c_exp = st.columns([1.5, 1.5, 1.5, 1])

df_f = df.copy()

# Lógica del Buscador de Texto (Optimizada)
if busqueda:
    mask = (df_f['Material'].str.contains(busqueda, case=False, na=False) | 
            df_f['Descripción Corta'].str.contains(busqueda, case=False, na=False) | 
            df_f['Descripción Larga'].str.contains(busqueda, case=False, na=False))
    df_f = df_f[mask]

# Lógica de los desplegables (Ahora son opcionales)
with cf1:
    fam = sorted(df_f['Nivel 3'].unique())
    sel_n3 = st.selectbox("Familia", ["Todas"] + fam)
    if sel_n3 != "Todas": df_f = df_f[df_f['Nivel 3'] == sel_n3]

with cf2:
    sub = sorted(df_f['Nivel 4'].unique())
    sel_n4 = st.selectbox("Subfamilia", ["Todas"] + sub)
    if sel_n4 != "Todas": df_f = df_f[df_f['Nivel 4'] == sel_n4]

with cf3:
    grup = sorted(df_f['Nivel 5'].unique())
    sel_n5 = st.selectbox("Grupo", ["Todos"] + grup)
    if sel_n5 != "Todos": df_f = df_f[df_f['Nivel 5'] == sel_n5]

with c_exp:
    st.write("")
    st.write("")
    if not df_f.empty:
        fname = f"{sel_n3}.xlsx" if sel_n3 != "Todas" else "catalogo.xlsx"
        st.download_button("📥 EXPORTAR", to_excel(df_f), fname, "application/vnd.ms-excel", type="primary")

# --- CONTROL DE CARGA PESADA ---
LIMITE_ARBOL = 1500
demasiados_datos = len(df_f) > LIMITE_ARBOL

if demasiados_datos and not busqueda and sel_n3 == "Todas":
    st.warning(f"⚠️ El catálogo completo tiene {len(df_f)} materiales. Para evitar que la web vaya lenta, por favor usa el buscador o selecciona una Familia.")
    if not st.checkbox("Mostrar todo de todas formas (puede colgar el navegador)"):
        df_f_vista = pd.DataFrame() 
    else:
        df_f_vista = df_f
else:
    df_f_vista = df_f

# --- CONSTRUCCIÓN DEL ÁRBOL ---
# Usamos caché con un identificador único basado en los filtros aplicados
@st.cache_data(show_spinner=False)
def construir_arbol_cacheado(datos_json, filtro_key):
    """
    Construye el árbol desde datos serializados.
    datos_json: JSON string del dataframe filtrado
    filtro_key: String único que identifica la combinación de filtros
    """
    df_temp = pd.read_json(io.StringIO(datos_json), orient='records')
    # Asegurar que todas las columnas son string para evitar errores con el componente tree
    for col in df_temp.columns:
        df_temp[col] = df_temp[col].astype(str)
    
    arbol = []
    
    # Agrupamos por jerarquía
    for n3, g3 in df_temp.groupby('Nivel 3', sort=True):
        hijos_n3 = []
        for n4, g4 in g3.groupby('Nivel 4', sort=True):
            hijos_n4 = []
            for n5, g5 in g4.groupby('Nivel 5', sort=True):
                hijos_n5 = []
                # Materiales
                for _, row in g5.iterrows():
                    # Convertir explícitamente a string para evitar errores
                    material_str = str(row['Material'])
                    desc_str = str(row['Descripción Corta'])
                    label = f"{material_str} - {desc_str}"
                    
                    item = sac.TreeItem(
                        label, 
                        icon='box-seam'
                    )
                    hijos_n5.append(item)
                hijos_n4.append(sac.TreeItem(str(n5), icon='folder', children=hijos_n5))
            hijos_n3.append(sac.TreeItem(str(n4), icon='folder', children=hijos_n4))
        arbol.append(sac.TreeItem(str(n3), icon='folder-fill', children=hijos_n3))
    return arbol

# --- INTERFAZ PRINCIPAL ---
# Ajustar proporciones para aprovechar el ancho completo
c_tree, c_det = st.columns([0.40, 0.60])

seleccion_id = None 

with c_tree:
    # Mostrar contador de resultados
    if not df_f_vista.empty:
        st.subheader(f"Navegación ({len(df_f_vista)} materiales)")
    else:
        st.subheader("Navegación")
    
    # 1. Construimos el árbol con los datos filtrados
    if df_f_vista.empty and demasiados_datos:
        st.info("💡 Filtra por Familia o busca un material para ver el árbol.")
    elif df_f_vista.empty:
        st.warning("No hay datos que coincidan.")
    else:
        # Crear clave única para el caché basada en los filtros
        filtro_key = f"{sel_n3}|{sel_n4}|{sel_n5}|{busqueda}|{len(df_f_vista)}"
        
        # Convertir dataframe a JSON para el caché (más eficiente que pasar el objeto)
        datos_json = df_f_vista.to_json(orient='records')
        items_arbol = construir_arbol_cacheado(datos_json, filtro_key)
        
        # 2. Lógica de apertura automática
        # Si hay búsqueda de texto -> Abrir todo para ver resultados
        # Si NO hay búsqueda -> Cerrar todo (collapse) para que no vaya lento
        abrir_todo = True if busqueda else False

        # 3. Dibujamos el árbol (Sin restricciones de cantidad)
        seleccion_id = sac.tree(
            items=items_arbol,
            label='Catálogo Completo',
            index=None, 
            format_func='title',
            size='sm',
            icon='table',
            open_all=abrir_todo 
        )

with c_det:
    if seleccion_id:
        # Corrección de lista vs string
        if isinstance(seleccion_id, list):
            seleccion_id = seleccion_id[0] if len(seleccion_id) > 0 else None

        if seleccion_id:
            # Buscamos la fila en el dataframe FILTRADO (df_f_vista en vez de df_f)
            # Esto asegura que solo buscamos en los materiales que están visibles en el árbol
            df_busqueda = df_f_vista.copy()
            df_busqueda['match_key'] = df_busqueda['Material'] + " - " + df_busqueda['Descripción Corta']
            fila = df_busqueda[df_busqueda['match_key'] == seleccion_id]
            
            if not fila.empty:
                item = fila.iloc[0]
                with st.container(border=True):
                    # TÍTULO GRANDE CON CÓDIGO
                    st.markdown(f"# 📦 {item['Material']}")
                    st.markdown(f"### {item['Descripción Corta']}")
                    
                    # Ruta del material (Breadcrumb)
                    st.info(f"📂 {item['Nivel 3']}  ➜  📂 {item['Nivel 4']}  ➜  📂 {item['Nivel 5']}")
                    
                    st.divider()
                    st.markdown("### 📝 Descripción Técnica")
                    st.write(item['Descripción Larga'])
                    
                    st.divider()
                    if st.button("Copiar Código"):
                        st.toast(f"Copiado al portapapeles: {item['Material']}")
            else:
                # Si es una carpeta
                st.info(f"📂 Carpeta seleccionada: **{seleccion_id}**")
                st.caption("Pulsa en el triángulo ▷ a la izquierda para ver el contenido.")
    else:
        st.markdown(
            """
            <div style="text-align: center; color: #aaa; padding-top: 100px;">
                <h1>👈</h1>
                <h3>Selecciona un material en el árbol</h3>
                <p>Todas las familias están cargadas a la izquierda.</p>
            </div>
            """, unsafe_allow_html=True
        )