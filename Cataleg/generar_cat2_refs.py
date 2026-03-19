"""
Ejecuta este script UNA VEZ (o cada vez que actualices cat2.xlsx) para generar
cat2_refs.xlsx con solo los campos necesarios para la app (sin precios ni datos sensibles).

Uso: py -3 generar_cat2_refs.py
"""
import pandas as pd
import unicodedata
import os


def normalize(text):
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()


def col_match(col_name, *targets):
    cn = normalize(str(col_name).strip().rstrip('.'))
    for t in targets:
        if cn == normalize(t.rstrip('.')):
            return True
    return False


base = os.path.dirname(os.path.abspath(__file__))
ruta_in = os.path.join(base, 'cat2.xlsx')
ruta_out = os.path.join(base, 'cat2_refs.xlsx')

print(f"Leyendo {ruta_in} ...")
try:
    df = pd.read_excel(ruta_in, sheet_name='Sheet1', header=3, dtype=str, engine='calamine')
except Exception:
    df = pd.read_excel(ruta_in, sheet_name='Sheet1', header=3, dtype=str, engine='openpyxl')

keep = {}
for c in df.columns:
    if col_match(c, 'Cod.M', 'Cód.M'):
        keep[c] = 'Cód.M'
    elif col_match(c, 'Ref.Prov', 'Ref Prov'):
        keep[c] = 'Ref.Prov'
    elif col_match(c, 'Nom.Prov', 'Nom Prov', 'Nombre Proveedor'):
        keep[c] = 'Nom.Prov.'
    elif col_match(c, '/GpC', 'GpC', 'Grupo Compras'):
        keep[c] = '/GpC'
    elif col_match(c, '/P', 'P'):
        keep[c] = '/P'
    elif col_match(c, 'Prov.', 'Prov'):
        keep[c] = 'Prov.'

if not keep:
    print("ERROR: No se encontraron las columnas necesarias en cat2.xlsx.")
    exit(1)

df_out = df[list(keep.keys())].rename(columns=keep)
df_out.to_excel(ruta_out, index=False)
print(f"Generado: {ruta_out}  ({len(df_out)} filas, columnas: {list(df_out.columns)})")
