import streamlit as st
import pandas as pd
from maravilloso import process_maravilloso
import io
import os

# Configuración de página
st.set_page_config(page_title="Limpiador Maravilloso", page_icon="🪄", layout="wide")

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .success-text {
        color: #28a745;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Encabezado
st.title("🪄 Limpiador Maravilloso")
st.markdown("### Automatización de limpieza de exportaciones SAP")
st.info("Sube tu archivo `f0.xlsx` sucio y obtén el `maravilloso.xlsx` limpio al instante.")

# Carga de archivos
uploaded_file = st.file_uploader("Elige el archivo Excel sucio (f0)", type=["xlsx"])

if uploaded_file is not None:
    st.success(f"Archivo '{uploaded_file.name}' cargado correctamente.")
    
    if st.button("✨ Procesar y Limpiar"):
        with st.spinner("Haciendo magia..."):
            try:
                # Leer bytes
                input_bytes = uploaded_file.read()
                
                # Procesar
                output_bytes = process_maravilloso(input_bytes)
                
                st.balloons()
                st.markdown("<p class='success-text'>¡Limpieza completada con éxito!</p>", unsafe_allow_html=True)
                
                # Botón de descarga
                st.download_button(
                    label="📥 Descargar maravilloso.xlsx",
                    data=output_bytes,
                    file_name="maravilloso.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                
            except Exception as e:
                st.error(f"Error procesando el archivo: {e}")

st.markdown("---")
st.caption("Hospital Clínic Barcelona - DSG Compres | v2.0 Standalone")
