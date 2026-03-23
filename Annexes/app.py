import streamlit as st
import pandas as pd
import os
import io
from generator import generate_am, generate_oe, generate_ot

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Generador de Anexos",
    page_icon="📄",
    layout="wide"
)

# --- ESTILOS PERSONALIZADOS (ELEGANCIA SENIOR) ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3em;
        background-color: #004a99; color: white; font-weight: bold;
        border: none; transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .success-card {
        padding: 20px; border-radius: 8px;
        background-color: #d4edda; border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    h1, h2, h3 { color: #004a99; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO DE LA SESIÓN ---
if 'outputs' not in st.session_state:
    st.session_state.outputs = {}

# --- CABECERA ---
c1, c2 = st.columns([1, 4])
with c1:
    # Ocultado por petición del usuario
    # if os.path.exists("logo.png"): st.image("logo.png", width=220)
    # else: st.image("https://portalprofessional.clinic.cat/sap/bc/bsp/sap/zbsppubliclgn/imgs/brand_logo.jpg", width=220)
    st.write("📦")

with c2:
    st.title("Generador de Anexos")
    st.write("Generación automatizada de ACO1, ACO2 y ACO3 a partir del Fichero Inicial.")

st.divider()

# Sección de Carga
uploaded_file = st.file_uploader("Sube el Fichero Inicial (HI.xlsm)", type=["xlsm"])

if uploaded_file is not None:
    st.info(f"Archivo detectado: **{uploaded_file.name}**")
    input_bytes = uploaded_file.read()

    if st.button("🚀 GENERAR TODOS LOS ANEXOS (Castellano + Català)"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        st.session_state.outputs = {}
        st.session_state.warnings = {}

        tasks = [
            ('am_es',  "Generando ACO2_PPT_AM — Castellano...",  lambda: generate_am(input_bytes, lang='es')),
            ('oe_es',  "Generando ACO3_PCAP_OE — Castellano...", lambda: generate_oe(input_bytes, lang='es')),
            ('ot_es',  "Generando ACO1_PPT_OT — Castellano...",  lambda: generate_ot(input_bytes, lang='es')),
            ('am_cat', "Generant ACO2_PPT_AM — Català...",       lambda: generate_am(input_bytes, lang='cat')),
            ('oe_cat', "Generant ACO3_PCAP_OE — Català...",      lambda: generate_oe(input_bytes, lang='cat')),
            ('ot_cat', "Generant ACO1_PPT_OT — Català...",       lambda: generate_ot(input_bytes, lang='cat')),
        ]

        for i, (key, msg, gen_fn) in enumerate(tasks):
            status_text.text(msg)
            try:
                st.session_state.outputs[key] = gen_fn()
            except Exception as e:
                st.session_state.warnings[key] = str(e)
            progress_bar.progress(int((i + 1) / len(tasks) * 100))

        if st.session_state.warnings:
            status_text.warning("Generación completada con avisos — revisa los anexos marcados.")
        else:
            status_text.success("¡Generación Completada! / Generació Completada!")
            st.balloons()

    # Mostrar resultados si existen
    if st.session_state.outputs or st.session_state.get('warnings'):
        outputs = st.session_state.outputs
        warns = st.session_state.get('warnings', {})

        # --- CASTELLANO ---
        st.subheader("📦 Archivos Generados — Castellano")
        res1, res2, res3 = st.columns(3)

        with res1:
            with st.container(border=True):
                st.write("### Anexo 1 (OT)")
                if 'ot_es' in outputs:
                    st.download_button("Descargar OT (ES)", outputs['ot_es'], "ACO1_PPT_OT_ES.xlsx", type="primary", key="dl_ot_es")
                elif 'ot_es' in warns:
                    st.warning(f"⚠️ Requiere revisión:\n\n{warns['ot_es']}")

        with res2:
            with st.container(border=True):
                st.write("### Anexo 2 (AM)")
                if 'am_es' in outputs:
                    st.download_button("Descargar AM (ES)", outputs['am_es'], "ACO2_PPT_AM_ES.xlsx", type="primary", key="dl_am_es")
                elif 'am_es' in warns:
                    st.warning(f"⚠️ Requiere revisión:\n\n{warns['am_es']}")

        with res3:
            with st.container(border=True):
                st.write("### Anexo 3 (OE)")
                if 'oe_es' in outputs:
                    st.download_button("Descargar OE (ES)", outputs['oe_es'], "ACO3_PCAP_OE_ES.xlsx", type="primary", key="dl_oe_es")
                elif 'oe_es' in warns:
                    st.warning(f"⚠️ Requiere revisión:\n\n{warns['oe_es']}")

        # --- CATALÀ ---
        st.subheader("📦 Fitxers Generats — Català")
        res4, res5, res6 = st.columns(3)

        with res4:
            with st.container(border=True):
                st.write("### Annex 1 (OT)")
                if 'ot_cat' in outputs:
                    st.download_button("Descarregar OT (CAT)", outputs['ot_cat'], "ACO1_PPT_OT_CAT.xlsx", type="primary", key="dl_ot_cat")
                elif 'ot_cat' in warns:
                    st.warning(f"⚠️ Cal revisió:\n\n{warns['ot_cat']}")

        with res5:
            with st.container(border=True):
                st.write("### Annex 2 (AM)")
                if 'am_cat' in outputs:
                    st.download_button("Descarregar AM (CAT)", outputs['am_cat'], "ACO2_PPT_AM_CAT.xlsx", type="primary", key="dl_am_cat")
                elif 'am_cat' in warns:
                    st.warning(f"⚠️ Cal revisió:\n\n{warns['am_cat']}")

        with res6:
            with st.container(border=True):
                st.write("### Annex 3 (OE)")
                if 'oe_cat' in outputs:
                    st.download_button("Descarregar OE (CAT)", outputs['oe_cat'], "ACO3_PCAP_OE_CAT.xlsx", type="primary", key="dl_oe_cat")
                elif 'oe_cat' in warns:
                    st.warning(f"⚠️ Cal revisió:\n\n{warns['oe_cat']}")

else:
    st.session_state.outputs = {}
    st.warning("⚠️ Por favor, sube un archivo HI.xlsm para comenzar.")

st.markdown("---")
st.caption("© 2026 DSG Compres - Gestión de Compras")
