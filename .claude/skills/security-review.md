---
name: security-review
description: "Revisión de seguridad del código: secretos, validación de inputs, exposición de datos sensibles, dependencias. Adaptado a proyectos Python/Streamlit."
risk: unknown
source: community (adaptado de cc-skill-security-review)
date_added: "2026-02-27"
---

# Security Review

Asegura que el código sigue buenas prácticas de seguridad e identifica vulnerabilidades potenciales.

## Cuándo usar
- Al añadir nuevas funcionalidades que lean/escriban archivos
- Al exponer datos al exterior (Streamlit Cloud, Docker)
- Al manejar uploads de PDF o Excel
- Al integrar APIs externas (SharePoint, traductores)

## Checklist de Seguridad

### 1. Gestión de Secretos
```python
# ❌ NUNCA hardcodear
password = "1234"
sharepoint_token = "eyJ0eX..."

# ✅ Usar variables de entorno o secrets de Streamlit
import os
password = os.environ.get("EXCEL_PASSWORD")
# o en .streamlit/secrets.toml (en .gitignore)
```
- [ ] Sin credenciales en el código fuente
- [ ] Sin secretos en el historial git
- [ ] `.streamlit/secrets.toml` en `.gitignore`
- [ ] `cat2.xlsx` (datos sensibles) en `.gitignore` y `.dockerignore`

### 2. Validación de Inputs
```python
# ❌ Peligroso: ejecutar input del usuario
exec(user_input)

# ✅ Validar y sanitizar siempre
def sanitize_search(text: str) -> str:
    # Solo permitir caracteres alfanuméricos, espacios y guiones
    return re.sub(r'[^\w\s\-]', '', text)[:200]
```
- [ ] Inputs de usuario validados antes de usarse
- [ ] Longitud máxima en campos de búsqueda
- [ ] No usar `eval()` ni `exec()` con datos del usuario

### 3. Exposición de Datos Sensibles
- [ ] Precios y datos contractuales NO en `cat2_refs.xlsx`
- [ ] Errores internos no expuestos al usuario (`st.error("Error")`, no el traceback completo)
- [ ] Logs no contienen datos personales en claro

### 4. Carga de Archivos (PDFs, Excel)
```python
# Validar tipo de archivo antes de procesar
ALLOWED_EXTENSIONS = {'.pdf', '.xlsx', '.docx'}

def validate_upload(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Tipo de archivo no permitido: {ext}")
    if file.size > 50 * 1024 * 1024:  # 50MB max
        raise ValueError("Archivo demasiado grande")
```
- [ ] Extensiones de archivo validadas
- [ ] Tamaño máximo de archivo limitado
- [ ] Archivos procesados en directorio temporal, no permanente

### 5. Dependencias
- [ ] `requirements.txt` con versiones mínimas especificadas
- [ ] Sin dependencias obsoletas con vulnerabilidades conocidas
- [ ] Revisar periódicamente con `pip audit`

## Errores comunes en Streamlit
```python
# ❌ Expone stack trace al usuario
st.error(traceback.format_exc())

# ✅ Error genérico al usuario, log interno
import logging
logging.error(traceback.format_exc())
st.error("Error al procesar el archivo. Contacta con el administrador.")
```

## Pre-deploy checklist
- [ ] Sin secretos en código ni en git
- [ ] Archivos sensibles en `.gitignore` y `.dockerignore`
- [ ] Inputs de usuario sanitizados
- [ ] Manejo de errores no expone internals
- [ ] Dependencias actualizadas

**Recuerda**: una vulnerabilidad puede comprometer datos de toda la organización.
