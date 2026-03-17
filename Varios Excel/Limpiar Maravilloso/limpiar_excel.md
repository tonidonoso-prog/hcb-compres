---
name: Limpiar Excel
description: Automatización de la limpieza y normalización de datos Excel para el proceso Maravilloso.
---

# SKILL: Limpiar Excel (Proceso Limpiar Excel)

Este documento define el procedimiento para transformar un archivo Excel crudo (`f0.xlsx`) en un archivo final procesado, siguiendo un modelo de referencia (`f1.xlsx`).

## 1. OBJETIVO
Convertir datos heterogéneos y "sucios" en información estructurada lista para su uso en SAP o Logística, eliminando la necesidad de correcciones manuales recurrentes.

## 2. FLUJO DE TRABAJO
1.  **Entrada:** Se deposita el archivo `f0.xlsx` en la carpeta `Limpiar Maravilloso`.
2.  **Análisis:** El script `limpiar_excel.py` compara la estructura actual con las reglas de negocio.
3.  **Ejecución:**
    *   Eliminación de filas/columnas vacías.
    *   Filtrado de datos irrelevantes.
    *   Reorganización de columnas según el orden de `f1`.
    *   Normalización de tipos de datos (SKU, Precios, Fechas).
4.  **Salida:** Generación del archivo final limpio.

## 3. REGLAS DE NEGOCIO (A definir tras analizar f1)
*   *Pendiente: Mapeo de columnas.*
*   *Pendiente: Filtros específicos.*

## 4. COMANDO DE EJECUCIÓN
`python limpiar_excel.py`
