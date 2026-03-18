import os
import time
import shutil
import re
from pypdf import PdfReader
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from docx import Document

# Directorios de trabajo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "leer_pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "resultados_word")
PROCESSED_DIR = os.path.join(BASE_DIR, "procesados")

def setup_directories():
    """Crea los directorios necesarios si no existen."""
    for folder in [INPUT_DIR, OUTPUT_DIR, PROCESSED_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[*] Directorio creado: {folder}")

def text_extraction(pdf_path):
    """Extrae el contenido de texto de un archivo PDF usando pypdf."""
    try:
        reader = PdfReader(pdf_path)
        text = []
        for page_num in range(len(reader.pages)):
            page_text = reader.pages[page_num].extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        print(f"[!] Error extrayendo texto de {pdf_path}: {e}")
        return ""

def analyze_pcap_criteria(text):
    """
    Analiza heurísticamente el PCAP buscando criterios de adjudicación.
    Esta función es una aproximación, que buscará palabras clave comunes
    en pliegos: "juicio de valor", "fórmulas", "automático".
    """
    # Expresiones regulares para capturar párrafos/oraciones relevantes.
    # Se recomienda a futuro afinar estas expresiones o usar Modelos de Lenguaje.
    
    # Criterios Subjetivos / No automáticos (Juicios de valor)
    subjetivos = []
    # Criterios Objetivos / Automáticos (Fórmulas)
    objetivos = []

    # Separar en párrafos simplificados
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) == 0:
        # Intento alternativo por saltos de línea simples
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 30]

    for p in paragraphs:
        p_lower = p.lower()
        if "adjudicación" in p_lower or "criterio" in p_lower:
            if "juicio de valor" in p_lower or "subjetivo" in p_lower:
                subjetivos.append(p)
            elif "fórmula" in p_lower or "automático" in p_lower or "objetivo" in p_lower:
                objetivos.append(p)

    # Si no encuentra específicamente en párrafos, puede devolver al menos las primeras menciones.
    if not subjetivos and not objetivos:
        return {"error": "No se encontraron secciones explícitas usando heurística básica. Revise el documento."}

    return {
        "Subjetivos / No Automáticos (Juicios de Valor)": subjetivos[:5],  # limitamos resultados para limpieza
        "Objetivos / Automáticos (Fórmulas)": objetivos[:5]
    }

def create_word_report(filename, analysis_results):
    """Acumula los resultados del análisis en un .docx estructurado."""
    doc = Document()
    doc.add_heading(f"Análisis PCAP: {filename}", 0)

    if "error" in analysis_results:
        doc.add_paragraph(analysis_results["error"])
    else:
        for title, criteria in analysis_results.items():
            doc.add_heading(title, level=1)
            if criteria:
                for c in criteria:
                    doc.add_paragraph(c, style='List Bullet')
            else:
                doc.add_paragraph("No se detectaron criterios explícitos en esta categoría con la heurística actual.")

    output_path = os.path.join(OUTPUT_DIR, f"{filename}.docx")
    doc.save(output_path)
    print(f"[+] Informe generado exitosamente: {output_path}")

def process_single_pdf(pdf_path):
    """Lógica integral para procesar un documento a su llegada."""
    filename = os.path.basename(pdf_path)
    name_only, _ = os.path.splitext(filename)
    
    print(f"\n[>] Procesando nuevo PDF: {filename}")
    
    # Pequeña espera para evitar leer un archivo a medio copiar (Race condition)
    time.sleep(2) 

    text = text_extraction(pdf_path)
    if not text:
        print(f"[!] El archivo no contiene texto legible: {filename}")
        return

    print("[*] Analizando criterios de adjudicación...")
    analysis = analyze_pcap_criteria(text)
    
    print("[*] Generando documento Word...")
    create_word_report(name_only, analysis)

    # Mover el pdf a la carpeta de procesados para limpiar la entrada
    try:
        dest_path = os.path.join(PROCESSED_DIR, filename)
        shutil.move(pdf_path, dest_path)
        print(f"[*] Archivo movido a procesados: {filename}")
    except Exception as e:
        print(f"[!] Hubo un error moviendo el archivo: {e}")

class PCAPHandler(FileSystemEventHandler):
    """Escucha la creación de archivos nuevos en el directorio mapeado."""
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            process_single_pdf(event.src_path)

def start_watching():
    """Incia el loop de Watchdog sobre el directorio INPUT_DIR."""
    setup_directories()
    
    # Comprobar si hay archivos residuales preexistentes al iniciar
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith(".pdf"):
            process_single_pdf(os.path.join(INPUT_DIR, file))

    event_handler = PCAPHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    
    print(f"\n[*] Modo 'Ingeniero Senior' activo.")
    print(f"[*] Carpeta de escucha activa: {INPUT_DIR}")
    print("[*] Esperando que se suelten archivos PDF... (Aplica Ctrl+C para detener)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[!] Deteniendo el proceso...")
    
    observer.join()

if __name__ == '__main__':
    start_watching()
