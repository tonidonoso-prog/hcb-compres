# Extractor Automático de Criterios PCAP

Este proyecto permite la extracción automática en tiempo real de los Criterios de Adjudicación de los Pliegos de Cláusulas Administrativas Particulares (PCAP).

## Estructura
*   `leer_pdf/`: Carpeta de entrada. **Arrastra aquí tus archivos PDF**.
*   `resultados_word/`: Aquí aparecerán automáticamente los **informes en Word (.docx)**.
*   `procesados/`: Los PDFs que ya se han leído se moverán aquí automáticamente.
*   `pcap_processor.py`: El script con el motor principal.
*   `requirements_pcap.txt`: Librerías necesarias.

## Instalación

Abre una terminal en esta carpeta (`PCAP/`) y ejecuta:
```bash
python -m pip install -r requirements_pcap.txt
```

## Uso de la Extracción Automática

1. Inicia el vigilante "Watchdog" de la carpeta ejecutando el script:
```bash
python pcap_processor.py
```
2. La terminal te dirá que está escuchando: `[✓] Esperando que se suelten archivos PDF...`
3. Abre la carpeta `leer_pdf/` y **suelta un documento PDF** dentro de ella.
4. El script detectará el archivo de inmediato, extraerá los criterios objetivos y subjetivos, y creará un archivo Word dentro de `resultados_word/`.

## Lógica Interna
La extracción se realiza de la siguiente manera:
1. Extrae el texto sucio del PDF de forma secuencial.
2. Compara bloques de texto con palabras clave propias de PCAP ("Criterio", "Adjudicación", "Juicio de Valor", "Fórmula", "Automático").
3. Lo clasifica en *Subjetivos / Juicios de Valor* y *Objetivos / Fórmulas*.
4. Redacta el informe Word utilizando de forma dinámica `python-docx`.
