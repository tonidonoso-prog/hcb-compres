# Changelog

Historial de cambios del Orquestador de Compras Hospitalarias.

## [2.0.0] - 2026-03-17

### ✨ Añadido
- **Portal Unificado**: `streamlit_app.py` que integra las 3 aplicaciones en una interfaz única
- **Configuración Streamlit Cloud**: Archivo `.streamlit/config.toml` con tema corporativo
- **README Mejorado**: Documentación completa con instrucciones de deployment
- **Dependencias Versionadas**: `requirements.txt` actualizado con versiones específicas
- **Badges**: Indicadores visuales de tecnologías usadas

### 🔧 Mejorado
- **Optimización de Performance**: Uso de `python-calamine` para lectura rápida de Excel
- **Caché Inteligente**: Sistema de caché en Catálogo con archivos `.parquet`
- **Gestión de Errores**: Monkey-patching para permitir múltiples `st.set_page_config()`
- **.gitignore**: Añadidos archivos temporales, secretos y configuraciones OS

### 🐛 Corregido
- Error de `st.set_page_config()` duplicado en portal multi-app
- Rutas relativas para compatibilidad con Streamlit Cloud
- Contexto de ejecución de aplicaciones hijas

### 📝 Documentación
- Guía completa de instalación local
- Instrucciones de deployment en Streamlit Cloud
- Estructura del proyecto documentada
- Sección de troubleshooting

---

## [1.0.0] - 2026-03-XX

### ✨ Versión Inicial
- **Catálogo Hospital**: Navegador de materiales con árbol jerárquico
- **Generador de Anexos**: Creación automatizada de ACO1, ACO2, ACO3
- **Limpiar Maravilloso**: Procesamiento de exportaciones SAP
- Aplicaciones independientes funcionales
