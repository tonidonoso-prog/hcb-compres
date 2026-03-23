FROM python:3.13-slim

WORKDIR /app

# Dependencias del sistema para pdfplumber/Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends ghostscript && \
    rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear usuario no-root con UID/GID específicos
RUN groupadd -g 1100 hcb-user && \
    useradd -u 1100 -g 1100 -r -d /app -s /bin/bash hcb-user

# Configuración Streamlit
COPY --chown=hcb-user:hcb-user .streamlit/ ./.streamlit/

# App principal
COPY --chown=hcb-user:hcb-user streamlit_app.py .
COPY --chown=hcb-user:hcb-user logo.png .

# Módulos
COPY --chown=hcb-user:hcb-user Annexes/ ./Annexes/
COPY --chown=hcb-user:hcb-user Cataleg/ ./Cataleg/
COPY --chown=hcb-user:hcb-user ["Varios Excel/", "./Varios Excel/"]
COPY --chown=hcb-user:hcb-user ["Varios PDF/", "./Varios PDF/"]

# Asegurar permisos finales para el usuario hcb-user
RUN chown -R hcb-user:hcb-user /app

# Cambiar al usuario no privilegiado
USER hcb-user

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
