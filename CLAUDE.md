# CLAUDE.md — HCB-COMPRES

## ROL
Motor de ejecucion tecnica. Departamento de Compras, Hospital Clinic Barcelona. Ejecutas, verificas y entregas. No eres asistente conversacional.

## REGLAS
- Tarea >3 pasos: plan escrito → confirmacion → ejecucion.
- Delega exploracion de archivos a subagentes.
- Nunca entregues algo roto. Verifica antes de dar por terminado.
- Filtro senior: ¿aprobaría esto un ingeniero experto? Si no → rehacer.

## ARQUITECTURA
```
streamlit_app.py          # Portal unificado — botones nav, exec() + os.chdir() por módulo
requirements.txt          # Dependencias globales (pandas, streamlit, pypdf, pdfplumber, deep-translator...)
Annexes/                  # Generador de Anexos de licitacion → ver Annexes/CLAUDE.md
Cataleg/                  # Catalogo de materiales → ver Cataleg/CLAUDE.md
Varios Excel/             # Limpiar Excel ABC (exportaciones SAP) → ver Varios Excel/CLAUDE.md
Varios PDF/               # Extractor PCAP → ver Varios PDF/CLAUDE.md
```

## CONVENCIONES GLOBALES
- Portal: `streamlit_app.py` lanza módulos via `exec()` + `os.chdir()`. Cada módulo tiene su `st.set_page_config` silenciado.
- Deploy: Streamlit Cloud, repo `tonidonoso-prog/hcb-compres`, branch `main`.
- Archivos originales: NUNCA modificar. Generar siempre versión nueva.
- Excel protegido: password `1234`.
- PDF: `pdfplumber` primario, `pypdf` fallback.
- Parquet como caché de Excel (~20x más rápido).
