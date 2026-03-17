# Orquestador de Compras Hospitalarias 🏥

Sistema de automatización para la gestión de suministros, licitaciones y catálogo del Hospital Clínic Barcelona.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)

## 🌐 **Acceso Web**
👉 **[Acceder a la aplicación en Streamlit Cloud](https://share.streamlit.io)** (Desplegado automáticamente desde GitHub)

## 🚀 Módulos Disponibles

El portal integra 3 aplicaciones principales accesibles desde un menú lateral unificado:

### 1. 📂 Catálogo Hospital
*   **Descripción:** Navegador del maestro de materiales con búsqueda avanzada y jerarquía multinivel
*   **Features:** 
    - Búsqueda en tiempo real por código/descripción
    - Árbol jerárquico expandible (Familia → Subfamilia → Grupo)
    - Exportación Excel filtrada
    - Caché optimizado para rendimiento
*   **Ejecución local:** `streamlit run Cataleg/catalogo_app.py --server.port 8501`

### 2. 📄 Generador de Anexos
*   **Descripción:** Generación automatizada de anexos de licitación (AM, OE, OT) desde Fichero Inicial (HI)
*   **Features:**
    - Procesamiento batch de múltiples anexos
    - Validación automática de datos
    - Formateo según plantillas oficiales
    - Protección con contraseña de celdas
*   **Ejecución local:** `streamlit run Annexes/app.py --server.port 8502`

### 3. 🪄 Limpiar Maravilloso
*   **Descripción:** Limpieza y normalización de exportaciones SAP (Proceso Maravilloso)
*   **Features:**
    - Detección automática de cabeceras
    - Eliminación de duplicados y filas vacías
    - Formateo de fechas estandarizado
    - Consolidación de información dispersa
*   **Ejecución local:** `streamlit run "Varios Excel/Limpiar Maravilloso/app_maravilloso.py" --server.port 8503`

---

## 🛠️ Instalación Local

### Prerrequisitos
- Python 3.9 o superior
- pip (gestor de paquetes Python)

### Pasos

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tonidonoso-prog/limpiar-maravilloso.git
   cd limpiar-maravilloso
   ```

2. **Crear entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el portal unificado:**
   ```bash
   streamlit run streamlit_app.py
   ```
   
   O ejecutar módulos individuales (ver sección "Módulos Disponibles")

---

## 🚀 Desplegar en Streamlit Cloud

### Opción 1: Deploy Automático (Recomendado)

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu cuenta de GitHub
3. Selecciona este repositorio: `tonidonoso-prog/limpiar-maravilloso`
4. Branch: `main`
5. Main file: `streamlit_app.py`
6. ¡Listo! Tu URL será: `https://[tu-usuario]-limpiar-maravilloso-xxxxxx.streamlit.app`

### Opción 2: Deploy Manual

Hacer push al repositorio GitHub activa el deployment automático gracias a la configuración en `.streamlit/config.toml`.

---

## 📁 Estructura del Proyecto

```
COMPRES/
├── .streamlit/
│   └── config.toml           # Configuración de Streamlit Cloud
├── Annexes/
│   ├── app.py               # Interfaz principal de Anexos
│   ├── generator.py         # Lógica de generación
│   └── [AM.py, OE.py, OTcabecera.py]
├── Cataleg/
│   ├── catalogo_app.py      # Aplicación del catálogo
│   ├── CAT1.xlsx            # Base de datos del catálogo
│   └── CAT1.parquet         # Versión optimizada
├── Varios Excel/
│   └── Limpiar Maravilloso/
│       ├── app_maravilloso.py
│       └── maravilloso.py   # Lógica de limpieza
├── streamlit_app.py         # Portal unificado (punto de entrada)
├── requirements.txt         # Dependencias Python
└── README.md               # Este archivo
```

---

## 🔧 Configuración

### Variables de Entorno (Opcional)

Si necesitas configuraciones específicas, crea `.streamlit/secrets.toml`:

```toml
# Ejemplo de configuración de secretos
[database]
host = "your-host"
password = "your-password"
```

### Límites de Carga

Por defecto, el límite de carga de archivos es **200 MB** (configurado en `config.toml`).

---

## 🐛 Solución de Problemas

### Error: "streamlit.errors.StreamlitAPIException: set_page_config()"
✅ **Solucionado**: El portal usa monkey-patching para permitir múltiples apps.

### Error al cargar archivos Excel grandes
💡 **Solución**: El sistema usa `python-calamine` para optimización. Asegúrate de tener todas las dependencias instaladas.

### La aplicación va lenta con muchos registros
💡 **Solución**: Usa los filtros (Familia, Subfamilia) antes de expandir el árbol del catálogo.

---

## 📊 Tecnologías Utilizadas

- **[Streamlit](https://streamlit.io)** - Framework web
- **[Pandas](https://pandas.pydata.org)** - Procesamiento de datos
- **[OpenPyXL](https://openpyxl.readthedocs.io)** - Manipulación avanzada de Excel
- **[Streamlit Ant Design](https://github.com/nicedouble/StreamlitAntdComponents)** - Componentes UI avanzados

---

## ✒️ Autor

**Hospital Clínic Barcelona - DSG Compres**

📧 Contacto: [Añadir email si procede]  
🔗 GitHub: [@tonidonoso-prog](https://github.com/tonidonoso-prog)

---

## 📄 Licencia

Uso interno Hospital Clínic Barcelona. Todos los derechos reservados.
