# Orquestador de Compras Hospitalarias 🏥

Sistema de automatización para la gestión de suministros, licitaciones y catálogo del Hospital Clínic Barcelona.

## 🚀 Módulos Disponibles

### 1. Catálogo (Cataleg)
*   **Descripción:** Navegador del maestro de materiales con búsqueda avanzada y jerarquía.
*   **Ejecución:** `streamlit run Cataleg/catalogo_app.py --server.port 8501`

### 2. Generador de Anexos (Annexes)
*   **Descripción:** Generación masiva de anexos (AM, OE, OT) a partir de un Fichero Inicial (HI).
*   **Ejecución:** `streamlit run Annexes/app.py --server.port 8502`

### 3. Varios Excel (Limpiar Maravilloso)
*   **Descripción:** Limpieza y normalización de exportaciones SAP (Proceso Maravilloso).
*   **Ejecución:** `streamlit run "Varios Excel/Limpiar Maravilloso/app_maravilloso.py" --server.port 8503`

---

## 🛠️ Instalación

1. Clonar el repositorio.
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar el módulo deseado.

## ✒️ Autor
Hospital Clínic Barcelona - DSG Compres
