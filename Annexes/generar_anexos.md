---
name: Generar Anexos
description: Automatización de la creación de anexos de licitación (PPT, PCAP) partiendo de un Fichero Inicial.
---

# SKILL: Generar Anexos (Módulo B - Contract Manager)

Este procedimiento automatiza la fragmentación y maquetación de un listado maestro de materiales (`HI.xlsm`) en múltiples archivos de anexos técnicos y administrativos.

## 1. OBJETIVO
Generar de forma masiva los archivos Excel necesarios para una licitación, aplicando formatos corporativos, protección de celdas y validación de datos automáticamente.

## 2. INSUMOS (Inputs)
*   **Fichero Inicial (`HI.xlsm`):** Contiene la base de datos de materiales, CPVs, lotes y presupuestos.
*   **Plantillas:** Archivos base con estilos predefinidos (v7-CAT, v2-ES, etc.).

## 3. FLUJO DE TRABAJO
1.  **Extracción (Pandas):** Lectura del `HI.xlsm` para segmentar los datos por lotes o tipos de anexo.
2.  **Maquetación (OpenPyXL):** 
    *   Inyección de datos en celdas específicas de las plantillas.
    *   Aplicación de estilos (negritas, bordes, colores) a las cabeceras.
    *   Ajuste automático de ancho de columnas y protección de hojas.
3.  **Generación:** Exportación de N archivos con nomenclatura estandarizada.

## 4. SCRIPTS ASOCIADOS
*   `AM.py`: Generación de anexos para Acuerdos Marco (PPT Albarán de Muestras).
*   `OE.py`: Generación de anexos para Ofertas Económicas (PCAP Oferta Económica).
*   `OT.py`: Procesamiento de Ofertas Técnicas (PPT Oferta Técnica).
*   *Nota: Se pueden añadir nuevos scripts siguiendo el mismo patrón de maquetación OpenPyXL.*

## 5. REGLAS DE ELEGANCIA
*   NUNCA usar cabeceras planas; usar siempre el formato de la plantilla.
*   Verificar integridad de fórmulas tras la inyección de datos.
*   Registrar cada set de archivos generados en el log de auditoría.
