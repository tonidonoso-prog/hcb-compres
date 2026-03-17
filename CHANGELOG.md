# Changelog

Historial de cambios del Orquestador de Compras Hospitalarias.

## [2.0.1] - 2026-03-17

### 🐛 Corregido
- **Bug Crítico Catálogo**: Los materiales ahora se muestran correctamente al usar filtros desplegables
- **Caché del Árbol**: Implementado sistema de caché con identificador único basado en filtros
- **Búsqueda de Materiales**: Optimizada búsqueda en dataframe filtrado en vez del completo

### ✨ Añadido
- **Contador de Resultados**: Muestra número de materiales en el título "Navegación (X materiales)"

### 🔧 Mejorado
- **Performance**: Conversión a JSON para caché más eficiente
- **Sort Hierarchy**: Ordenación alfabética en niveles de jerarquía del árbol

---

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
