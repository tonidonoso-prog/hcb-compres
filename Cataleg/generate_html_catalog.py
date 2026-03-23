import pandas as pd
import json
import os
import unicodedata
import base64

def normalize(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()

def construir_indice_fichas(base):
    fichas_path = os.path.join(base, "fichas_index.json")
    if not os.path.exists(fichas_path): return {}
    with open(fichas_path, encoding="utf-8") as f:
        flat = json.load(f)
    indice = {}
    for key, url in flat.items():
        parts = key.split("-", 1)
        if len(parts) == 2:
            mat, cod = parts
            if mat not in indice:
                indice[mat] = {}
            indice[mat][cod] = url
    return indice

def _col_match(col_name, *targets):
    cn = normalize(str(col_name).strip().rstrip('.'))
    for t in targets:
        if cn == normalize(t.rstrip('.')): return True
    return False

def _leer_cat2_xlsx(ruta_cat2):
    try:
        df2 = pd.read_excel(ruta_cat2, header=0, dtype=str, engine='calamine')
    except:
        df2 = pd.read_excel(ruta_cat2, header=0, dtype=str, engine='openpyxl')
        
    keep = {}
    for c in df2.columns:
        if _col_match(c, 'Cod.M', 'Cód.M'): keep[c] = 'Material'
        elif _col_match(c, 'Ref.Prov', 'Ref Prov'): keep[c] = 'Ref Proveedor'
        elif _col_match(c, 'Nom.Prov', 'Nom Prov', 'Nombre Proveedor'): keep[c] = 'Nombre Proveedor'
        elif _col_match(c, '/GpC', 'GpC', 'Grupo Compras'): keep[c] = 'Grupo Compras'
        elif _col_match(c, '/P', 'P'): keep[c] = '/P'
        elif _col_match(c, 'Prov.', 'Prov'): keep[c] = 'Cod Prov'

    if 'Material' not in keep.values() or 'Ref Proveedor' not in keep.values():
        return pd.DataFrame()

    cols_needed = [k for k, v in keep.items() if v in ('Material', 'Ref Proveedor', 'Nombre Proveedor', 'Grupo Compras', '/P', 'Cod Prov')]
    df2 = df2[cols_needed].rename(columns=keep).fillna("").astype(str)
    for col in ('Nombre Proveedor', 'Grupo Compras', '/P', 'Cod Prov'):
        if col not in df2.columns: df2[col] = ""
    df2['Material'] = df2['Material'].str.strip()
    df2['Cod Prov'] = df2['Cod Prov'].str.strip()
    return df2

def _cargar_cat2_completo(base):
    ruta_xlsx = os.path.join(base, 'cat2_refs.xlsx')
    ruta_parquet = os.path.join(base, 'cat2_refs.parquet')
    if not os.path.exists(ruta_xlsx): return pd.DataFrame(), set()

    try:
        if os.path.exists(ruta_parquet) and os.path.getmtime(ruta_parquet) >= os.path.getmtime(ruta_xlsx):
            df2 = pd.read_parquet(ruta_parquet)
        else:
            df2 = _leer_cat2_xlsx(ruta_xlsx)
            if not df2.empty: df2.to_parquet(ruta_parquet, index=False)

        if df2.empty: return pd.DataFrame(), set()

        if '/P' in df2.columns:
            materiales_con_p = set(df2[df2['/P'].str.strip().str.upper() == 'X']['Material'].unique())
            df2['_pref'] = df2['/P'].str.strip().str.upper() == 'X'
        else:
            materiales_con_p = set()
            df2['_pref'] = False

        def _join(vals):
            return ' | '.join(sorted(set(v.strip() for v in vals if v.strip())))

        rows = []
        def _pares(group):
            seen, result = set(), []
            for _, row in group.iterrows():
                ref = row['Ref Proveedor'].strip()
                prov = row['Nombre Proveedor'].strip()
                cod = row['Cod Prov'].strip() if 'Cod Prov' in row else ''
                key = (ref, prov, cod)
                if ref and key not in seen:
                    seen.add(key)
                    result.append(f"{ref}||{prov}||{cod}")
            return '\n'.join(result)

        for mat, g in df2.groupby('Material'):
            pref = g[g['_pref']]
            rows.append({
                'Material': mat,
                'Pares Pref': _pares(pref),
                'Pares Otros': _pares(g[~g['_pref']]),
                'Grupo Compras': _join(g['Grupo Compras']),
            })
        return pd.DataFrame(rows), materiales_con_p
    except Exception as e:
        print(f"Error cat2: {e}")
        return pd.DataFrame(), set()

def cargar_datos(base):
    ruta_excel = os.path.join(base, 'cat1.xlsx')
    ruta_parquet = os.path.join(base, 'cat1.parquet')
    if not os.path.exists(ruta_excel):
        print(f"No existe: {ruta_excel}")
        return pd.DataFrame()
    try:
        if os.path.exists(ruta_parquet) and os.path.getmtime(ruta_parquet) >= os.path.getmtime(ruta_excel):
            df = pd.read_parquet(ruta_parquet)
        else:
            try:
                df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str, usecols=[0, 1, 2, 3, 4, 5], engine='calamine')
            except:
                df = pd.read_excel(ruta_excel, sheet_name='CAT1', header=0, dtype=str, usecols=[0, 1, 2, 3, 4, 5], engine='openpyxl')
            try: df.to_parquet(ruta_parquet, index=False)
            except: pass

        cols = df.columns
        mapa = {}
        if len(cols) > 0: mapa[cols[0]] = 'Nivel 3'
        if len(cols) > 1: mapa[cols[1]] = 'Nivel 4'
        if len(cols) > 2: mapa[cols[2]] = 'Nivel 5'
        if len(cols) > 3: mapa[cols[3]] = 'Descripcion Corta'
        if len(cols) > 4: mapa[cols[4]] = 'Material'
        if len(cols) > 5: mapa[cols[5]] = 'Descripcion Larga'
        df = df.rename(columns=mapa)

        req = ['Nivel 3', 'Nivel 4', 'Nivel 5', 'Descripcion Corta', 'Material', 'Descripcion Larga']
        for c in req:
            if c not in df.columns: df[c] = ""
        df = df[req].fillna("").astype(str)

        df_refs, materiales_con_p = _cargar_cat2_completo(base)
        if not df_refs.empty:
            df = df.merge(df_refs, on='Material', how='left')
        for col in ('Pares Pref', 'Pares Otros', 'Grupo Compras'):
            if col not in df.columns: df[col] = ""
            df[col] = df[col].fillna("")
            
        # El usuario quiere ver todos los materiales, pero marcar solo los pref
        # No filtramos por materiales_con_p
        df = df.drop_duplicates(subset='Material')
        return df
    except Exception as e:
        print(f"Error cat1: {e}")
        return pd.DataFrame()

def construir_arbol_json(df, indice_fichas):
    root = {"name": "Catálogo de Compras", "children": []}
    
    # Pre-calcular agrupaciones
    for n3, g3 in df.groupby('Nivel 3'):
        n3_name = str(n3).strip()
        if not n3_name or n3_name in ['0', 'nan', '0.0']: continue
        
        n3_node = {"name": n3_name, "children": []}
        for n4, g4 in g3.groupby('Nivel 4'):
            n4_name = str(n4).strip()
            if not n4_name or n4_name in ['0', 'nan', '0.0']: continue
            
            n4_node = {"name": n4_name, "children": []}
            for n5, g5 in g4.groupby('Nivel 5'):
                n5_name = str(n5).strip()
                if not n5_name or n5_name in ['0', 'nan', '0.0']: continue
                
                n5_node = {"name": n5_name, "children": []}
                for _, row in g5.iterrows():
                    mat = str(row['Material']).strip()
                    desc = str(row['Descripcion Corta']).strip()
                    item_name = f"{mat} - {desc}"
                    
                    mat_fichas = indice_fichas.get(mat, {})
                    
                    pares_pref = []
                    for p in row.get('Pares Pref', '').split('\n'):
                        if not p.strip(): continue
                        parts = (p.split('||') + ['', ''])[:3]
                        ref, prov, cod_prov = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        url = mat_fichas.get(cod_prov, "")
                        pares_pref.append([ref, prov, cod_prov, url])
                        
                    pares_otros = []
                    for p in row.get('Pares Otros', '').split('\n'):
                        if not p.strip(): continue
                        parts = (p.split('||') + ['', ''])[:3]
                        ref, prov, cod_prov = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        url = mat_fichas.get(cod_prov, "")
                        pares_otros.append([ref, prov, cod_prov, url])
                    
                    item_node = {
                        "name": item_name,
                        "material": mat,
                        "desc_corta": desc,
                        "desc_larga": str(row.get('Descripcion Larga', '')).strip(),
                        "refs_pref": pares_pref,
                        "refs_otros": pares_otros,
                        "grupo_compras": str(row.get('Grupo Compras', '')).strip(),
                        "n3": str(n3).strip(),
                        "n4": str(n4).strip(),
                        "n5": str(n5).strip()
                    }
                    n5_node["children"].append(item_node)
                if n5_node["children"]:
                    n4_node["children"].append(n5_node)
            if n4_node["children"]:
                n3_node["children"].append(n4_node)
        if n3_node["children"]:
            root["children"].append(n3_node)
            
    return root

def main():
    print("Iniciando generación de catálogo HTML...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(os.path.dirname(base_dir), "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    file_cat1 = os.path.join(DATA_DIR, 'cat1.xlsx')
    file_cat2 = os.path.join(DATA_DIR, 'cat2_refs.xlsx')
    template_path = os.path.join(base_dir, 'template.html')
    output_path = os.path.join(DATA_DIR, 'catalogo_interactivo.html')
    
    df = cargar_datos(DATA_DIR) # Pass DATA_DIR to cargar_datos
    indice_fichas = construir_indice_fichas(DATA_DIR) # Pass DATA_DIR to construir_indice_fichas
    
    if df.empty:
        print("Error: No se pudieron cargar los datos.")
        return
        
    print(f"Datos cargados: {len(df)} materiales.")
    arbol_data = construir_arbol_json(df, indice_fichas)
    json_str = json.dumps(arbol_data, ensure_ascii=False)
    
    template_path = os.path.join(base_dir, "template.html")
    if not os.path.exists(template_path):
        print(f"Error: Plantilla HTML no encontrada en {template_path}")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Inyectar logo (Desactivado por petición del usuario para Streamlit Cloud)
    # logo_path = os.path.join(os.path.dirname(base_dir), "logo.png")
    # if os.path.exists(logo_path):
    #     with open(logo_path, "rb") as img_f:
    #         b64_logo = base64.b64encode(img_f.read()).decode()
    #         logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:40px; margin-right:8px;">'
    #         html_content = html_content.replace('/*INYECTAR_LOGO_AQUI*/', logo_html)
    # else:
    #     html_content = html_content.replace('/*INYECTAR_LOGO_AQUI*/', '<span style="font-size:24px; margin-right:8px;">📦</span>')
    
    html_content = html_content.replace('/*INYECTAR_LOGO_AQUI*/', '<span style="font-size:24px; margin-right:8px;">📦</span>')

    # Inyectar datos
    # Buscaremos la cadena const DATA = {}; y la reemplazaremos
    if "const DATA = {};" in html_content:
        html_content = html_content.replace("const DATA = {};", f"const DATA = {json_str};")
    else:
        print("Aviso: No se encontró 'const DATA = {};' en la plantilla. Buscando inyección genérica.")
        # Reemplazo de fallback por si acaso
        html_content = html_content.replace("/*INYECTAR_DATOS_AQUI*/", f"const DATA = {json_str};")
        
    out_path = os.path.join(base_dir, "catalogo_interactivo.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"¡Catálogo generado exitosamente en: {out_path}!")

if __name__ == "__main__":
    main()
