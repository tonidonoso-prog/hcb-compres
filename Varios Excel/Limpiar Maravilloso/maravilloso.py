import pandas as pd
import numpy as np
import os
import io

def process_maravilloso(input_bytes):
    """
    Recibe bytes de un Excel (f0), limpia y procesa según las reglas de Maravilloso,
    y retorna los bytes del archivo resultante.
    """
    # Esquema fijo de columnas
    target_cols = [
        "Cód.M", "Descripción material", "Cód M Ant", "Cod.Agr", "Descripción Agrupador",
        "Grup.Art.", "Descripción Gr.Art.", "B", "GpC", "Cntr", "Alm.", "UMB", "TMat",
        "CatV", "Cat. Valoración", "Cta.gasto", "Descrip.Cta.gasto", "QConsumoPeriodo",
        "QConsÚlt12meses", "Importe según ABC", "NºMovAlmacén", "Unidades estoc",
        "F.ÚltMovAl", "F.últ.ped.", "g", "Prov.UP", "Nom.Prov.ÚltPed", "Ref.Prov-UP",
        "Precio-BI-UP", "  QB-UP", "I-UP", "Prov.PF", "Nom.Prov.Prefer", "Ref.Prov-PF",
        "    QStd", "    QMín", "UMP", "Precio-BI-PF", "  QB-PF", "I-PF", "NºC.Marco",
        "G2", "T.CM", "+", "W", "Txt.Orden Ent.CM", "Prov.CM", "Nom.Prov.Cmarco",
        "Ref.prov-CM", "Precio-BI-CM", "  QB-CM", "I-CM", "F.Inic.CM", "F.Fin CM",
        "Nº Sol Ex", "TSol", "Año", "Nº Ex", "Denomin.Expediente", "DEx", "PEx",
        "PPEx", "F Inic Ex", "F Fin Exp.", "F FinMaxEx", "NSolExPd", "AÑ", "ExPdt",
        "FIniExpPdt", "FFinExpPdt", "DPd", "PPd", "Último Status  Liberado",
        "FLibÚltSts", "+_1", "QExpPdt", "F.Fin LP", "Prov-LP", "Nom.Prov LP",
        "Promot", "Resp.Técnico", "CeCo1", "0,01", "Ins1", "CeCo2", "0,02",
        "Ins2", "CeCo3", "0,03", "Ins3", "FeCreacMat", "Texto largo de material", "GrPt"
    ]

    # 1. Detectar cabecera dinámicamente y cargar F0
    try:
        df_raw = pd.read_excel(io.BytesIO(input_bytes), header=None)
        header_idx = None
        for i in range(min(50, len(df_raw))):
            row_vals = df_raw.iloc[i].astype(str).values
            if any('Cód.M' in v for v in row_vals) or any('Descripción material' in v for v in row_vals):
                header_idx = i
                break
                
        if header_idx is None:
            raise ValueError("No se pudo detectar la fila de cabeceras (búsqueda de 'Cód.M' o 'Descripción material' fallida).")
            
        df_f0 = pd.read_excel(io.BytesIO(input_bytes), header=header_idx)
    except Exception as e:
        raise ValueError(f"Error cargando Excel: {e}")

    # Limpiar nombres de columnas
    df_f0.columns = df_f0.columns.astype(str).str.strip()
    target_cols_clean = [c.strip() for c in target_cols]

    # 2. Procesar las parejas de filas (Main row -> Info row shifted)
    material_rows = df_f0.iloc[::2].copy()
    info_rows = df_f0.iloc[1::2].copy()

    material_rows.reset_index(drop=True, inplace=True)
    info_rows.reset_index(drop=True, inplace=True)

    # Fusionar info extra de la fila de abajo
    if 'Unnamed: 0' in info_rows.columns:
        material_rows['Texto largo de material'] = info_rows['Unnamed: 0']
    
    if 'Unnamed: 22' in info_rows.columns:
        material_rows['GrPt'] = info_rows['Unnamed: 22']

    # 3. Mapear al esquema destino
    df_final = pd.DataFrame(columns=target_cols_clean)
    common_cols = [c for c in target_cols_clean if c in material_rows.columns]
    
    if not common_cols:
        raise ValueError("Error crítico: No se encontró coincidencia entre las columnas de SAP y el esquema previsto.")

    for col in common_cols:
        df_final[col] = material_rows[col]
    
    # Asegurar Texto Largo y GrPt
    if 'Texto largo de material' in material_rows.columns:
        df_final['Texto largo de material'] = material_rows['Texto largo de material']
    if 'GrPt' in material_rows.columns:
        df_final['GrPt'] = material_rows['GrPt']

    # 4. LIMPIEZA
    # A. Eliminar filas vacías
    df_final.dropna(how='all', inplace=True)
    
    # B. Eliminar cabeceras repetidas
    if 'Cód.M' in df_final.columns:
        df_final = df_final[df_final['Cód.M'].astype(str).str.strip() != 'Cód.M']
        df_final.dropna(subset=['Cód.M'], inplace=True)

    # C. Formatear fechas: de . a /
    for col in df_final.columns:
        if col.startswith('F') or 'Fe' in col or 'Date' in col:
            df_final[col] = df_final[col].astype(str).replace(r'\.', '/', regex=True).replace('nan', '')
            df_final[col] = df_final[col].str.replace(r'/0$', '', regex=True)

    # 5. Generar output
    output = io.BytesIO()
    df_final.to_excel(output, index=False)
    return output.getvalue()

def clean_excel_cli():
    f0_path = 'f0.xlsx'
    output_path = 'maravilloso.xlsx'
    if not os.path.exists(f0_path):
        return
    with open(f0_path, 'rb') as f:
        res = process_maravilloso(f.read())
    with open(output_path, 'wb') as f:
        f.write(res)
    print(f"¡Éxito! Generado {output_path}")

if __name__ == "__main__":
    clean_excel_cli()
