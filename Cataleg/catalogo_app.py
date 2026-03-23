import streamlit as st
import streamlit.components.v1 as components
import os
import sys

# Añadir el path actual al sistema para importar el generador
base_path = os.path.dirname(os.path.abspath(__file__))
if base_path not in sys.path:
    sys.path.append(base_path)

try:
    import generate_html_catalog
except ImportError:
    st.error("Error: No se encontró el script 'generate_html_catalog.py' en la carpeta.")
    st.stop()

# 1. CONFIGURACIÓN DE PÁGINA (Sin barra lateral original)
st.set_page_config(
    page_title="Catálogo de Materiales", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. OCULTAR ELEMENTOS DE STREAMLIT Y AJUSTAR MARGENES
st.markdown("""
<style>
    /* Ocultar decoraciones de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    
    /* Eliminar paddings de la aplicación */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    /* Asegurar que el componente de iframe ocupe todo el espacio */
    .element-container iframe {
        border-radius: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. LÓGICA DE ACTUALIZACIÓN AUTOMÁTICA
html_file = os.path.join(base_path, "catalogo_interactivo.html")

def sync_catalog():
    """Detecta cambios en los Excel y regenera el HTML si es necesario."""
    xlsx_files = [
        os.path.join(base_path, "cat1.xlsx"), 
        os.path.join(base_path, "cat2_refs.xlsx"),
        os.path.join(base_path, "template.html")
    ]
    
    should_generate = False
    if not os.path.exists(html_file):
        should_generate = True
    else:
        html_mtime = os.path.getmtime(html_file)
        for f in xlsx_files:
            if os.path.exists(f) and os.path.getmtime(f) > html_mtime:
                should_generate = True
                break
                
    if should_generate:
        try:
            generate_html_catalog.main()
        except Exception as e:
            st.error(f"Error regenerando catálogo: {e}")

sync_catalog()

# 4. RENDERIZADO DEL HTML
if os.path.exists(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Renderizamos con un alto generoso. 
    # El HTML tiene su propio scroll interno para el árbol y la tabla.
    components.html(html_content, height=1000, scrolling=False)
else:
    st.error("No se encontró el archivo 'catalogo_interactivo.html'.")
    st.info("Asegúrate de que los archivos 'cat1.xlsx' y 'cat2_refs.xlsx' estén en la misma carpeta.")
