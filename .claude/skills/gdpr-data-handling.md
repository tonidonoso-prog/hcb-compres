---
name: gdpr-data-handling
description: "Guía práctica GDPR/LOPD para sistemas que procesan datos personales de la UE. Especialmente relevante para datos hospitalarios y de proveedores."
risk: unknown
source: community
date_added: "2026-02-27"
---

# GDPR / LOPD — Gestión de Datos

Guía práctica para tratamiento de datos conforme al Reglamento General de Protección de Datos (RGPD) y la LOPD-GDD española. Contexto: Hospital Clínic Barcelona — datos de proveedores, contratos y materiales.

## Datos presentes en este proyecto

| Dato | Categoría | Riesgo |
|------|-----------|--------|
| Precios de contratos (`cat2.xlsx`) | Confidencial comercial | Alto — no publicar |
| Responsable contrato / técnico | Datos personales laborales | Medio |
| Códigos de proveedor | Datos de empresa | Bajo |
| Fichas técnicas de materiales | Datos técnicos | Bajo |

## Principios a aplicar

### 1. Minimización de datos
- `cat2_refs.xlsx` (público) **no debe contener precios** — ya implementado con `generar_cat2_refs.py`
- Solo exportar al frontend los campos estrictamente necesarios

### 2. Separación público / privado
```
cat2.xlsx        ← PRIVADO (precios, datos sensibles) — en .gitignore
cat2_refs.xlsx   ← PÚBLICO (solo referencias, sin precios) — en repo
```

### 3. Datos personales (Resp.Cont., Resp.Tec.)
- Son datos laborales de empleados del hospital
- No mostrar en interfaces públicas externas
- Solo visible para usuarios autenticados del portal interno

### 4. Logs y auditoría
- No registrar en logs datos de precios ni identificadores personales en claro
- Si se implementa log de accesos: anonimizar o pseudonimizar

## Checklist de revisión GDPR

- [ ] `cat2.xlsx` está en `.gitignore` y no se sube al repo
- [ ] `cat2_refs.xlsx` no contiene columnas de precio
- [ ] Datos de responsables (Resp.Cont., Resp.Tec.) solo accesibles en red interna
- [ ] No hay credenciales ni datos personales en el código fuente
- [ ] `.streamlit/secrets.toml` en `.gitignore`
- [ ] El contenedor Docker no incluye `cat2.xlsx` (ya en `.dockerignore`)

## Base legal para el tratamiento
- **Interés legítimo**: gestión de contratos y compras del hospital
- **Relación contractual**: datos de proveedores necesarios para ejecutar contratos
- **Obligación legal**: conservación de documentación según normativa de contratos públicos (Ley 9/2017 LCSP)

## Derechos de los interesados
Si algún proveedor o empleado ejerce derechos ARCO (Acceso, Rectificación, Cancelación, Oposición), los datos deben poder identificarse y eliminarse del sistema. Documentar dónde están almacenados.
