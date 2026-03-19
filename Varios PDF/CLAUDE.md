# CLAUDE.md — Varios PDF/

## MÓDULO: Extractor PCAP

### Archivos
| Archivo | Rol |
|---|---|
| `PCAP/app.py` | UI Streamlit: sube PDF, descarga Word |
| `PCAP/pcap_processor.py` | Extracción heurística + generación Word |

### Qué hace
Extrae criterios de adjudicación de Pliegos de Condiciones (PCAP) en PDF:
1. Lee PDF con `pdfplumber` (fallback `pypdf`) + `clean_text()` para artefactos ES/CA
2. Clasifica criterios en:
   - **Subjetivos** (Juicios de Valor)
   - **Objetivos** (Fórmulas)
3. Genera informe Word con `python-docx`
4. Bilingüe: detecta castellano y catalán

### Extracción de texto
```python
clean_text(text):  # en pcap_processor.py
    # Tabla de reemplazos de artefactos PDF catalán/castellano
    # ('dÆ' → "d'"), ('Ú' → 'é'), ('¾' → 'ó'), etc.
```
- `pdfplumber` es el extractor principal (mejor orden de texto, filtra headers flotantes)
- `pypdf` como fallback

### Leer PDF simple
- `main.py` — extrae texto de PDFs a TXT (herramienta auxiliar, no en portal)
