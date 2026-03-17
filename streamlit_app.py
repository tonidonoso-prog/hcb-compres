import streamlit as st
import os
import sys

# --- CONFIGURACIÓN GLOBAL DEL PORTAL ---
st.set_page_config(
    page_title="H. Clinic - Orquestador de Compras",
    page_icon="🏥",
    layout="wide"
)

# --- ESTILOS ---
st.markdown("""
<style>
    .stSelectbox label { font-size: 20px !important; font-weight: bold; color: #004a99; }
    .portal-header { background-color: #004a99; padding: 20px; border-radius: 10px; color: white; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.markdown("### 🛠️ Panel de Herramientas")
        app_mode = st.selectbox(
            "Selecciona Aplicación:",
            ["🪄 Limpiar Maravilloso", "📂 Catálogo Hospital", "📄 Generador de Anexos"]
        )
        st.divider()
        st.info(" DSG Compres - Hospital Clínic Barcelona")

    # --- LÓGICA DE LANZAMIENTO ---
    
    if app_mode == "🪄 Limpiar Maravilloso":
        dir_path = os.path.join(os.path.dirname(__file__), "Varios Excel", "Limpiar Maravilloso")
        run_app(dir_path, "app_maravilloso.py")

    elif app_mode == "📂 Catálogo Hospital":
        dir_path = os.path.join(os.path.dirname(__file__), "Cataleg")
        run_app(dir_path, "catalogo_app.py")

    elif app_mode == "📄 Generador de Anexos":
        dir_path = os.path.join(os.path.dirname(__file__), "Annexes")
        run_app(dir_path, "app.py")

def run_app(dir_path, file_name):
    """Ejecuta un archivo de streamlit dentro del contexto actual."""
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    
    app_full_path = os.path.join(dir_path, file_name)
    
    try:
        with open(app_full_path, encoding='utf-8') as f:
            code = f.read()
            # Limpiamos set_page_config para evitar errores de Streamlit
            clean_code = code.replace("st.set_page_config", "# st.set_page_config")
            exec(clean_code, globals())
    except Exception as e:
        st.error(f"Error al cargar {file_name}: {e}")
        st.info(f"Ruta: {app_full_path}")

if __name__ == "__main__":
    main()
