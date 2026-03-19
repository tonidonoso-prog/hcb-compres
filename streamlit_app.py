import streamlit as st
import os
import sys
import base64

# 1. CONFIGURACIÓN GLOBAL
st.set_page_config(
    page_title="H. Clinic - DSG Compres",
    page_icon="🏥",
    layout="wide"
)

# 2. ESTILOS GLOBALES
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stAppDeployButton {display:none;}
.block-container {
    max-width: 95% !important;
    padding-top: 1rem !important;
    padding-right: 1rem !important;
    padding-left: 1rem !important;
}
[data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)


def get_logo_b64():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def main():
    # --- CABECERA CON LOGO ---
    logo = get_logo_b64()
    if logo:
        logo_html = '<img src="data:image/png;base64,' + logo + '" style="height:55px; margin-right:18px;">'
    else:
        logo_html = '<span style="font-size:28px; margin-right:12px;">🏥</span>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; background-color:#004a99;
                padding:16px 24px; border-radius:10px; margin-bottom:22px;">
        {logo_html}
        <div style="color:white; line-height:1.3;">
            <div style="font-size:19px; font-weight:700;">DSG Compres</div>
            <div style="font-size:13px; opacity:0.85;">Hospital Clínic Barcelona</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- NAVEGACIÓN EN PÁGINA PRINCIPAL (funciona en móvil) ---
    app_mode = st.selectbox(
        "Selecciona herramienta:",
        ["🪄 Limpiar Maravilloso", "📂 Catálogo Hospital",
         "🔍 Buscar material por referencia proveedor",
         "📄 Generador de Anexos", "📋 Extractor PCAP"]
    )

    st.divider()

    # --- LANZAMIENTO ---
    base = os.path.dirname(os.path.abspath(__file__))

    if app_mode == "🪄 Limpiar Maravilloso":
        run_app(os.path.join(base, "Varios Excel", "Limpiar Maravilloso"), "app_maravilloso.py")
    elif app_mode == "📂 Catálogo Hospital":
        run_app(os.path.join(base, "Cataleg"), "catalogo_app.py")
    elif app_mode == "🔍 Buscar material por referencia proveedor":
        run_app(os.path.join(base, "Cataleg"), "ref_search_app.py")
    elif app_mode == "📄 Generador de Anexos":
        run_app(os.path.join(base, "Annexes"), "app.py")
    elif app_mode == "📋 Extractor PCAP":
        run_app(os.path.join(base, "Varios PDF", "PCAP"), "app.py")


def run_app(dir_path, file_name):
    """Ejecuta un archivo de Streamlit silenciando st.set_page_config."""
    app_full_path = os.path.join(dir_path, file_name)
    old_cwd = os.getcwd()
    orig_set_page_config = st.set_page_config

    try:
        os.chdir(dir_path)
        if dir_path not in sys.path:
            sys.path.insert(0, dir_path)

        with open(file_name, encoding="utf-8") as f:
            code = f.read()

        def dummy_set_page_config(*args, **kwargs):
            pass
        st.set_page_config = dummy_set_page_config

        custom_globals = globals().copy()
        custom_globals["__file__"] = app_full_path

        try:
            exec(code, custom_globals)
        except Exception as e:
            st.error(f"❌ Error al ejecutar {file_name}: {e}")
            st.exception(e)
    except Exception as e:
        st.error(f"🚨 Error crítico al preparar {file_name}: {e}")
    finally:
        st.set_page_config = orig_set_page_config
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
