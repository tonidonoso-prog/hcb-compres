import streamlit as st
import os
import sys

# Ruta a la subcarpeta donde está la lógica real
SUBFOLDER_PATH = os.path.join(os.path.dirname(__file__), "Varios Excel", "Limpiar Maravilloso")

# Insertamos la subcarpeta al principio de sys.path para evitar conflictos
if SUBFOLDER_PATH not in sys.path:
    sys.path.insert(0, SUBFOLDER_PATH)

# Ejecutamos la aplicación real
app_file = os.path.join(SUBFOLDER_PATH, "app_maravilloso.py")

try:
    with open(app_file, encoding='utf-8') as f:
        code = f.read()
        exec(code, globals())
except Exception as e:
    st.error(f"Error cargando la aplicación real: {e}")
    st.info(f"Ruta intentada: {app_file}")
