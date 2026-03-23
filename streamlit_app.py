import streamlit as st
import os
import sys
import base64
import time
# Prototipo para futura integración con MSAL
# import msal 

# 1. CONFIGURACIÓN GLOBAL
st.set_page_config(
    page_title="DSG - Compres",
    page_icon="📦",
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

/* Nav buttons — todos */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 70px !important;
}
/* Nav button activo → azul */
div[data-testid="stHorizontalBlock"] button[kind="primary"] {
    background-color: #004a99 !important;
    border-color: #004a99 !important;
    color: white !important;
}
div[data-testid="stHorizontalBlock"] button[kind="primary"]:hover {
    background-color: #003880 !important;
    border-color: #003880 !important;
}
</style>
""", unsafe_allow_html=True)


def get_logo_b64():
    # Desactivado temporalmente por petición del usuario (Anonimización Streamlit Cloud)
    return None


def main():
    # --- CONTROL DE ACCESO (SAML/OAuth2) ---
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        show_login_page()
        st.stop()

    # --- CABECERA CON LOGO ---
    logo = get_logo_b64()
    if logo:
        logo_html = '<img src="data:image/png;base64,' + logo + '" style="height:55px; margin-right:18px;">'
    else:
        logo_html = '<span style="font-size:28px; margin-right:12px;">🏥</span>'

    st.markdown(f"""
        <div style="color:white; line-height:1.3; flex-grow: 1;">
            <div style="font-size:19px; font-weight:700;">DSG Compres</div>
            <div style="font-size:13px; opacity:0.85;">Gestión de Compras</div>
        </div>
        <div style="color:white; text-align:right;">
            <div style="font-size:14px; font-weight:600;">{st.session_state.get('user_name', 'Usuario')}</div>
            <a href="?logout=true" style="color:#ff4b4b; font-size:12px; text-decoration:none; font-weight:bold;">Cerrar Sesión</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.query_params.get("logout") == "true":
        st.session_state["authenticated"] = False
        st.query_params.clear()
        st.rerun()

    # --- NAVEGACIÓN CON BOTONES ---
    TOOLS = [
        ("📂", "Catálogo Hospital",          "Cataleg",                              "catalogo_app.py"),
        ("🔍", "Buscar material por referencia", "Cataleg",                           "ref_search_app.py"),
        ("🧬", "Crear Maestro Material (Beta)", "Cataleg/Crear maestro material",      "app.py"),
        ("📄", "Generador de Anexos",        "Annexes",                              "app.py"),
        ("📋", "Extractor PCAP",             "Varios PDF/PCAP",                      "app.py"),
        ("🪄", "Limpiar Excel ABC",           "Varios Excel/Limpiar Maravilloso",     "app_maravilloso.py"),
    ]

    if "nav_tool" not in st.session_state:
        st.session_state["nav_tool"] = TOOLS[1][1]  # "Buscar por Ref. Proveedor"

    cols = st.columns(len(TOOLS))
    for col, (icon, label, _, _f) in zip(cols, TOOLS):
        selected = st.session_state["nav_tool"] == label
        with col:
            # Highlight active button with primary type
            btn_type = "primary" if selected else "secondary"
            if st.button(f"{icon}\n{label}", key=f"nav_{label}", use_container_width=True, type=btn_type):
                st.session_state["nav_tool"] = label
                st.rerun()

    st.divider()

    # --- LANZAMIENTO ---
    base = os.path.dirname(os.path.abspath(__file__))
    active = next((t for t in TOOLS if t[1] == st.session_state["nav_tool"]), TOOLS[0])
    run_app(os.path.join(base, active[2]), active[3])


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


def show_login_page():
    """Muestra una pantalla de login atractiva (Placeholder hasta tener ClientID)."""
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("")
        st.write("")
        logo = get_logo_b64()
        if logo:
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{logo}" width="250"></div>', unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; color: #004a99;'>Acceso Restringido</h1>", unsafe_allow_html=True)
        st.info("Esta aplicación es de uso exclusivo para el personal autorizado de DSG Compres.")
        
        with st.container(border=True):
            st.write("### Identificación Institucional")
            st.write("Para acceder, utiliza tu cuenta corporativa del hospital.")
            
            if st.button("🔐 Iniciar Sesión con cuenta corporativa", type="primary", use_container_width=True):
                # --- MOCK LOGIN (PARA PRUEBAS HASTA TENER EL TICKET) ---
                st.session_state["authenticated"] = True
                st.session_state["user_name"] = "Usuario Pruebas"
                st.success("Acceso concedido (Modo Pruebas)")
                time.sleep(1)
                st.rerun()

    st.markdown("""
    <div style="position: fixed; bottom: 20px; width: 100%; text-align: center; color: #666; font-size: 12px;">
        © 2026 DSG Compres - Dirección de Servicios Generales
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
