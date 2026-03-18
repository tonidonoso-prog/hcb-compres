import os
from pypdf import PdfReader

# Configuración básica de carpetas
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"

def setup_folders():
    """Crea las carpetas necesarias si no existen."""
    for folder in [INPUT_FOLDER, OUTPUT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Directorio creado: {folder}")

def extract_text_from_pdf(pdf_path):
    """Extrae el contenido de texto de un archivo PDF."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error al procesar {pdf_path}: {e}"

def process_pdfs():
    """Busca PDFs en la carpeta de entrada y guarda el texto en la de salida."""
    setup_folders()
    
    # Listar archivos PDF
    pdf_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No se encontraron archivos PDF en '{INPUT_FOLDER}'.")
        print("Copia tus archivos PDF a la carpeta 'input' y vuelve a ejecutar.")
        return

    print(f"Procesando {len(pdf_files)} archivo(s)...")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_FOLDER, pdf_file)
        print(f"Leyendo: {pdf_file}")
        
        text_content = extract_text_from_pdf(pdf_path)
        
        # Guardar en un archivo de texto con el mismo nombre
        output_filename = os.path.splitext(pdf_file)[0] + ".txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        
        print(f"Hecho: {output_filename} guardado en '{OUTPUT_FOLDER}'.")

if __name__ == "__main__":
    process_pdfs()
