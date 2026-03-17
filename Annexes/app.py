import streamlit as st
import pandas as pd
import os
import io
import time
from generator import generate_am, generate_oe, generate_ot

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Generador de Anexos - Hospital Clínic",
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
    if os.path.exists("logo.png"): st.image("logo.png", width=220)
    else: st.image("https://portalprofessional.clinic.cat/sap/bc/bsp/sap/zbsppubliclgn/imgs/brand_logo.jpg", width=220)

with c2:
    st.title("Orquestador de Compras: Generador de Anexos")
    st.write("Generación automatizada de PPT y PCAP a partir del Fichero Inicial (HI).")

st.divider()

# Sección de Carga
uploaded_file = st.file_uploader("Sube el Fichero Inicial (HI.xlsm)", type=["xlsm"])

if uploaded_file is not None:
    st.info(f"Archivo detectado: **{uploaded_file.name}**")
    input_bytes = uploaded_file.read()
    
    if st.button("🚀 GENERAR TODOS LOS ANEXOS"):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Generando ACO2_PPT_AM (Albarán de Muestras)...")
            st.session_state.outputs['am'] = generate_am(input_bytes)
            progress_bar.progress(33)
            
            status_text.text("Generando ACO3_PCAP_OE (Oferta Económica)...")
            st.session_state.outputs['oe'] = generate_oe(input_bytes)
            progress_bar.progress(66)
            
            status_text.text("Generando ACO1_PPT_OT (Oferta Técnica)...")
            st.session_state.outputs['ot'] = generate_ot(input_bytes)
            progress_bar.progress(100)
            
            status_text.success("¡Generación Completada!")
            st.balloons()
        except Exception as e:
            st.error(f"Error en la generación: {e}")

    # Mostrar resultados si existen
    if st.session_state.outputs:
        st.subheader("📦 Archivos Generados")
        res1, res2, res3 = st.columns(3)
        
        with res1:
            with st.container(border=True):
                st.write("### Anexo 1 (OT)")
                st.download_button("Descargar OT", st.session_state.outputs['ot'], "ACO1_PPT_OT.xlsx", type="primary")
                
        with res2:
            with st.container(border=True):
                st.write("### Anexo 2 (AM)")
                st.download_button("Descargar AM", st.session_state.outputs['am'], "ACO2_PPT_AM.xlsx", type="primary")
                
        with res3:
            with st.container(border=True):
                st.write("### Anexo 3 (OE)")
                st.download_button("Descargar OE", st.session_state.outputs['oe'], "ACO3_PCAP_OE.xlsx", type="primary")

else:
    st.session_state.outputs = {}
    st.warning("⚠️ Por favor, sube un archivo HI.xlsm para comenzar.")

st.markdown("---")
st.caption("© 2026 Hospital Clínic Barcelona - Gestión de Compras Hospitalarias")
