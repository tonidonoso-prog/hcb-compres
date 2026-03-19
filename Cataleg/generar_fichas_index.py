"""
Genera fichas_index.json con {material-codprov: url_sharepoint} para todos
los ficheros de la carpeta FICHAS TEC-SEG UNIFICADO.

Ejecutar cada vez que se añadan nuevas fichas:
    py -3 generar_fichas_index.py
"""
import os
import json
import urllib.parse

FICHAS_DIR = r"C:\Users\Toni\Clínic Barcelona\DSG - Compres - Coord. Compres - Catàleg\LOGARITME\FICHAS TEC-SEG UNIFICADO"
SHAREPOINT_BASE = "https://hospitalclinicdebarcelona.sharepoint.com/sites/GesDocDSGCompres/CoordinacioCompresCataleg/LOGARITME/FICHAS%20TEC-SEG%20UNIFICADO"

base = os.path.dirname(os.path.abspath(__file__))
ruta_out = os.path.join(base, "fichas_index.json")

if not os.path.isdir(FICHAS_DIR):
    print(f"ERROR: No se encuentra la carpeta:\n  {FICHAS_DIR}")
    exit(1)

indice = {}
sin_prov = 0

for fname in os.listdir(FICHAS_DIR):
    base_name, _ = os.path.splitext(fname)
    parts = base_name.split("-", 2)   # material, cod_prov, ref
    if len(parts) < 2:
        continue
    material = parts[0].strip()
    cod_prov = parts[1].strip()
    key = f"{material}-{cod_prov}"
    url = f"{SHAREPOINT_BASE}/{urllib.parse.quote(fname, safe='')}"
    indice[key] = url

with open(ruta_out, "w", encoding="utf-8") as f:
    json.dump(indice, f, ensure_ascii=False, indent=2)

print(f"Generado: {ruta_out}")
print(f"  {len(indice)} fichas indexadas")
print(f"  Ejemplo: {list(indice.items())[0]}")
