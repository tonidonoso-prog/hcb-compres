FROM python:3.13-slim

WORKDIR /app

# Dependencias del sistema para pdfplumber/Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends ghostscript && \
    rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Configuración Streamlit
COPY .streamlit/ ./.streamlit/

# App principal
COPY streamlit_app.py .
COPY logo.png .

# Módulos
COPY Annexes/ ./Annexes/
COPY Cataleg/ ./Cataleg/
COPY "Varios Excel/" "./Varios Excel/"
COPY "Varios PDF/" "./Varios PDF/"

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
