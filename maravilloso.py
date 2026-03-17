import streamlit as st
import os
import sys

# Agregamos la ruta del módulo al sistema para que encuentre los archivos
dir_path = os.path.join(os.path.dirname(__file__), "Varios Excel", "Limpiar Maravilloso")
sys.path.append(dir_path)

# Importamos la lógica de la aplicación
try:
    with open(os.path.join(dir_path, "app_maravilloso.py"), encoding='utf-8') as f:
        code = f.read()
        exec(code)
except Exception as e:
    st.error(f"Error cargando la aplicación: {e}")
