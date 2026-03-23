FROM python:3.13-slim

WORKDIR /app

# Dependencias del sistema para pdfplumber/Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends ghostscript && \
    rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear un usuario de sistema (no-root) para mayor seguridad
RUN groupadd -r streamlit && useradd -r -g streamlit -d /app -s /sbin/nologin streamlit

# Configuración Streamlit
COPY --chown=streamlit:streamlit .streamlit/ ./.streamlit/

# App principal
COPY --chown=streamlit:streamlit streamlit_app.py .
COPY --chown=streamlit:streamlit logo.png .

# Módulos
COPY --chown=streamlit:streamlit Annexes/ ./Annexes/
COPY --chown=streamlit:streamlit Cataleg/ ./Cataleg/
COPY --chown=streamlit:streamlit ["Varios Excel/", "./Varios Excel/"]
COPY --chown=streamlit:streamlit ["Varios PDF/", "./Varios PDF/"]

# Directorio de datos persistente (copia inicial por defecto)
COPY --chown=streamlit:streamlit data/ ./data/

# Asegurar permisos finales para el usuario streamlit
RUN chown -R streamlit:streamlit /app

# Cambiar al usuario no privilegiado
USER streamlit

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
