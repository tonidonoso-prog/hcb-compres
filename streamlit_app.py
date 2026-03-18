import streamlit as st
import os
import sys

# 1. CONFIGURACIÓN GLOBAL (Debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="H. Clinic - Orquestador",
    page_icon="🏥",
    layout="wide"
)

# 2. EL CAMUFLAJE CSS Y ESTILOS GLOBALES UNIFICADOS
estilos_globales = """
    <style>
    /* Ocultar menú de Streamlit y botón de GitHub */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Maximizar ancho disponible */
    .block-container {
        max-width: 95% !important;
        padding-top: 1rem !important;
        padding-right: 1rem !important;
        padding-left: 1rem !important;
    }
    .stSelectbox label { font-size: 20px !important; font-weight: bold; color: #004a99; }
    .portal-header { background-color: #004a99; padding: 20px; border-radius: 10px; color: white; margin-bottom: 25px; }
    </style>
    """
st.markdown(estilos_globales, unsafe_allow_html=True)

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
    """Ejecuta un archivo de streamlit silenciando st.set_page_config para evitar errores."""
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    
    # Preparamos el entorno para la app hija
    app_full_path = os.path.join(dir_path, file_name)
    old_cwd = os.getcwd()
    
    # Guardamos la función original para restaurarla pase lo que pase
    orig_set_page_config = st.set_page_config
    
    try:
        os.chdir(dir_path)
        if dir_path not in sys.path:
            sys.path.insert(0, dir_path)
            
        with open(file_name, encoding='utf-8') as f:
            code = f.read()
            
            # Monkey-patch st.set_page_config
            def dummy_set_page_config(*args, **kwargs):
                pass
            st.set_page_config = dummy_set_page_config
            
            # Inyectamos contexto
            custom_globals = globals().copy()
            custom_globals['__file__'] = app_full_path
            
            try:
                exec(code, custom_globals)
            except Exception as e:
                st.error(f"❌ Error al ejecutar {file_name}: {e}")
                st.exception(e) # Mostrar traceback para depuración en Cloud
    except Exception as e:
        st.error(f"🚨 Error crítico al preparar {file_name}: {e}")
    finally:
        st.set_page_config = orig_set_page_config
        os.chdir(old_cwd)

if __name__ == "__main__":
    main()
