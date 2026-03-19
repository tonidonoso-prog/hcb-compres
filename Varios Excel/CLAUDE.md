# CLAUDE.md — Varios Excel/

## MÓDULO: Limpiar Excel ABC (antes "Limpiar Maravilloso")

### Archivos
| Archivo | Rol |
|---|---|
| `Limpiar Maravilloso/app_maravilloso.py` | UI Streamlit |
| `Limpiar Maravilloso/maravilloso.py` | Lógica de limpieza |

### Qué hace
Limpia y normaliza exportaciones SAP en Excel:
- Detecta cabeceras automáticamente (fila variable)
- Elimina duplicados
- Normaliza fechas
- Elimina filas/columnas vacías
- Exporta Excel limpio para reimportar

### Convención de nombre
El botón en el portal se llama **"Limpiar Excel ABC"** (nombre interno de carpeta sigue siendo `Limpiar Maravilloso/`).
