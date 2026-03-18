import pandas as pd
import io
from openpyxl import load_workbook
from openpyxl.styles import Alignment, PatternFill, Font, Protection, Border, Side
from openpyxl.formatting.rule import FormulaRule
from openpyxl.drawing.image import Image
import os

def get_column_mapping(wb_in, annex_type):
    try:
        # En el contexto de generator.py, CABECERAS.xlsx debe estar en el mismo directorio
        cab_file = os.path.join(os.path.dirname(__file__), 'CABECERAS.xlsx')
        if not os.path.exists(cab_file):
            # Probar ruta relativa simple si el script se lanza desde el directorio base
            cab_file = 'CABECERAS.xlsx'
            if not os.path.exists(cab_file):
                print("CABECERAS.xlsx not found")
                return {}

        df_map = pd.read_excel(cab_file, sheet_name=annex_type, header=None)
        annex_headers = [str(h).strip() for h in df_map.iloc[0].fillna("").tolist()]
        hi_headers_to_find = [str(h).strip().upper() for h in df_map.iloc[1].fillna("").tolist()]
        
        ws_in = wb_in['Full Inici']
        mapping = {}
        
        # Scan headers in rows 5 and 6
        for r_idx in [5, 6]:
            row_vals = [str(ws_in.cell(row=r_idx, column=c).value).strip().upper() for c in range(1, 150)]
            for ah, htf in zip(annex_headers, hi_headers_to_find):
                if htf == "NAN" or htf == "": continue
                if htf in row_vals:
                    mapping[ah] = row_vals.index(htf) + 1 # 1-based column index
        return mapping
    except Exception as e:
        print(f"Error loading mapping: {e}")
        return {}

def apply_style(ws, rng, text=None, fill=None, font=None, align=None, border=None):
    if not align:
        align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    if ":" in rng: ws.merge_cells(rng)
    start_cell = ws[rng.split(":")[0]]
    if text is not None: start_cell.value = text
    start_coords, end_coords = rng.split(":") if ":" in rng else (rng, rng)
    for row in ws[start_coords:end_coords]:
        for cell in row:
            cell.alignment = align
            if border: cell.border = border
            if fill: cell.fill = fill
            if font: cell.font = font

def generate_am(input_bytes, logo_path='logo.png'):
    wb_in = load_workbook(io.BytesIO(input_bytes), data_only=True)
    
    # --- DADES DE CABECERA ---
    nom_pestanya_cab = next((s for s in wb_in.sheetnames if s.upper() == "CABECERA"), None)
    if not nom_pestanya_cab:
        raise ValueError("No s'ha trobat la pestanya 'cabecera' al fitxer original.")
    
    ws_cab = wb_in[nom_pestanya_cab]
    titol_expedient = ws_cab['B9'].value
    num_expedient = ws_cab['B5'].value

    # --- DADES DE PRODUCTES (Full Inici) ---
    ws_in = wb_in['Full Inici']
    
    mapping = get_column_mapping(wb_in, 'AM')
    col_lot = mapping.get("LOTE", 23)
    col_art = mapping.get("ARTÍCULO", 24)
    col_cod = mapping.get("CÓDIGO HCB", 1)
    col_tec = mapping.get("DENOMINACIÓN Y REQUISITOS TÉCNICOS", 32)
    col_req = mapping.get("CANTIDAD DE MUESTRAS\nREQUERIDAS", 79)

    dades_extretes = []
    fila_orig = 6
    while ws_in.cell(row=fila_orig, column=col_art).value is not None or ws_in.cell(row=fila_orig, column=col_cod).value is not None:
        val_w = ws_in.cell(row=fila_orig, column=col_lot).value 
        if val_w is not None and str(val_w).strip() != "" and str(val_w).upper() != "NUMERO":
            val_req_val = ws_in.cell(row=fila_orig, column=col_req).value
            try: val_req_val = float(val_req_val) if val_req_val is not None else 1.0
            except: val_req_val = 1.0
            
            dades_extretes.append({
                "lot": val_w, 
                "article": ws_in.cell(row=fila_orig, column=col_art).value,
                "codi_hcb": ws_in.cell(row=fila_orig, column=col_cod).value, 
                "tecnic": ws_in.cell(row=fila_orig, column=col_tec).value,
                "requerides": val_req_val
            })
        fila_orig += 1
        if fila_orig > 10000: break

    cols = ["LOTE", "ARTÍCULO", "CÓDIGO HCB", "DENOMINACIÓN Y REQUISITOS TÉCNICOS", 
            "DENOMINACIÓN ARTÍCULO LICITADOR", "REFERENCIA ARTÍCULO", 
            "CANTIDAD DE MUESTRAS REQUERIDAS", "CANTIDAD DE MUESTRAS PRESENTADAS"]

    df_final = pd.DataFrame(columns=cols)
    if dades_extretes:
        df_temp = pd.DataFrame(dades_extretes)
        df_final["LOTE"] = df_temp["lot"]
        df_final["ARTÍCULO"] = df_temp["article"]
        df_final["CÓDIGO HCB"] = df_temp["codi_hcb"]
        df_final["DENOMINACIÓN Y REQUISITOS TÉCNICOS"] = df_temp["tecnic"]
        df_final["CANTIDAD DE MUESTRAS REQUERIDAS"] = df_temp["requerides"]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, header=False, startrow=15, sheet_name='Plantilla Annex')
    
    output.seek(0)
    wb_out = load_workbook(output)
    ws = wb_out.active

    # --- ESTILS ---
    align_center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
    bold_9 = Font(bold=True, size=9)
    fill_verd = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
    fill_gris = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    fill_groc_inst = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    fill_blau = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # --- MAQUETACIÓ CABECERA ---
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path); img.width = 240; img.height = 100; ws.add_image(img, 'A1')
        except: pass

    ws.row_dimensions[1].height = 85
    apply_style(ws, "C1:H1", "ANEXO DE CUMPLIMENTACIÓN OBLIGATORIA 2 PPT ALBARÁN DE MUESTRAS", font=Font(bold=True, size=14), fill=fill_blau, border=border)
    
    txt_instr = ("Deberá presentar las muestras relacionadas en este albarán según se indique en los pliegos.\n"
                 "Rellene sólo las celdas en blanco o desprotegidas.")
    apply_style(ws, "A2:H2", txt_instr, font=Font(italic=True, size=10), fill=fill_groc_inst, border=border)
    ws.row_dimensions[2].height = 40

    apply_style(ws, "A4:B4", "TÍTULO DEL EXPEDIENTE:", font=bold_9, fill=fill_gris, border=border)
    apply_style(ws, "C4:H4", titol_expedient, align=align_left_wrap, border=border)
    
    apply_style(ws, "A5:B5", "NÚMERO DE EXPEDIENTE:", font=bold_9, fill=fill_gris, border=border)
    apply_style(ws, "C5:H5", num_expedient, align=align_left_wrap, border=border)

    apply_style(ws, "A7:H7", "LICITADOR E IDENTIFICACIÓN DEL RECEPTOR:", font=bold_9, fill=fill_gris, border=border)

    apply_style(ws, "A9:B9", "EMPRESA", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C9:D9", border=border)
    apply_style(ws, "A10:B10", "PERSONA DE CONTACTO", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C10:D10", border=border)
    apply_style(ws, "A11:B11", "TELÉFONO", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C11:D11", border=border)
    apply_style(ws, "A12:B12", "E-MAIL", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C12:D12", border=border)

    apply_style(ws, "E9:F9", "NOMBRE Y DNI/MATRICULA DEL RECEPTOR", fill=fill_gris, font=bold_9, align=align_left_wrap, border=border); apply_style(ws, "G9:H9", border=border)
    apply_style(ws, "E10:F10", "FECHA ENTREGA", fill=fill_gris, font=bold_9, align=align_left_wrap, border=border); apply_style(ws, "G10:H10", border=border)
    apply_style(ws, "E11:F11", "LUGAR ENTREGA", fill=fill_gris, font=bold_9, align=align_left_wrap, border=border); apply_style(ws, "G11:H11", border=border)

    apply_style(ws, "A14:D14", "IDENTIFICACIÓN ARTICULO LICITADO", fill=fill_verd, font=bold_9, border=border)
    apply_style(ws, "E14:H14", "IDENTIFICACIÓN ARTICULO DEL LICITADOR", fill=fill_gris, font=bold_9, border=border)
    
    for c in range(1, 9):
        cell = ws.cell(row=15, column=c)
        cell.font = bold_9; cell.alignment = align_center_wrap; cell.border = border
        if c <= 4 or c == 7: cell.fill = fill_verd
        elif c == 8: cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        else: cell.fill = fill_gris
    
    ws.cell(row=15, column=1, value="LOTE")
    ws.cell(row=15, column=2, value="ARTÍCULO")
    ws.cell(row=15, column=3, value="CÓDIGO HCB")
    ws.cell(row=15, column=4, value="DENOMINACIÓN Y REQUISITOS TÉCNICOS")
    ws.cell(row=15, column=5, value="DENOMINACIÓN ARTÍCULO LICITADOR")
    ws.cell(row=15, column=6, value="REFERENCIA ARTÍCULO")
    ws.cell(row=15, column=7, value="CANTIDAD DE MUESTRAS\nREQUERIDAS")
    ws.cell(row=15, column=8, value="CANTIDAD DE MUESTRAS\nPRESENTADAS")

    for r in range(4, 13): ws.row_dimensions[r].height = 25
    ws.row_dimensions[14].height = 30
    ws.row_dimensions[15].height = 65

    last_row = ws.max_row
    for r in range(16, last_row + 1):
        for c in range(1, 9):
            cell = ws.cell(row=r, column=c)
            cell.alignment = align_center_wrap; cell.border = border
            if c in [1, 2, 3, 4, 7]: cell.protection = Protection(locked=True)
            else: cell.protection = Protection(locked=False)

    for zona in ["C9:D12", "G9:H11"]:
        start, end = zona.split(":")
        for row in ws[start:end]:
            for cell in row: cell.protection = Protection(locked=False)

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 50
    ws.column_dimensions['E'].width = 40
    ws.column_dimensions['F'].width = 20
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    
    ws.protection.password = '1234'
    ws.protection.sheet = True
    
    final_output = io.BytesIO()
    wb_out.save(final_output)
    return final_output.getvalue()

def parse_num(val, default=0.0):
    if val is None: return default
    if isinstance(val, (int, float)): return float(val)
    try: return float(str(val).replace(',', '.').strip())
    except: return default

def generate_oe(input_bytes, logo_path='logo.png'):
    wb_in = load_workbook(io.BytesIO(input_bytes), data_only=True)
    nom_pestanya_cab = next((s for s in wb_in.sheetnames if s.upper() == "CABECERA"), None)
    if not nom_pestanya_cab: raise ValueError("No s'ha trobat la pestanya 'cabecera'.")
    
    ws_cab = wb_in[nom_pestanya_cab]
    titol_expedient = ws_cab['B9'].value
    num_expedient = ws_cab['B5'].value

    ws_in = wb_in['Full Inici']
    val_dh3 = ws_in['DH3'].value
    factor_dh3 = float(val_dh3) if val_dh3 is not None else 1.0
    
    mapping = get_column_mapping(wb_in, 'OE')
    col_lot = mapping.get("LOTE", 23)
    col_art = mapping.get("ARTÍCULO", 24)
    col_cod = mapping.get("CÓDIGO HCB", 1)
    col_tec = mapping.get("DENOMINACIÓN Y REQUISITOS TÉCNICOS", 32)
    col_uml = mapping.get("UNIDAD DE MEDIDA LICITADA (***)", 68)
    col_qty = mapping.get("CANTIDAD", 69)
    col_pre = mapping.get("BASE IMPONIBLE MÁXIMA DE LICITACIÓN UNITARIA(**) (***)", 70)
    col_iva = mapping.get("TIPO IVA", 71)

    dades_extretes = []
    fila_orig = 7
    while ws_in.cell(row=fila_orig, column=col_art).value is not None or ws_in.cell(row=fila_orig, column=col_cod).value is not None:
        val_w = ws_in.cell(row=fila_orig, column=col_lot).value 
        if val_w is not None and str(val_w).strip() != "" and str(val_w).upper() != "NUMERO":
            val_qty_val = parse_num(ws_in.cell(row=fila_orig, column=col_qty).value)
            preu_max = parse_num(ws_in.cell(row=fila_orig, column=col_pre).value)
            val_bs = ws_in.cell(row=fila_orig, column=col_iva).value
            try: 
                iva = float(val_bs) if isinstance(val_bs, (int, float)) else float(str(val_bs).replace('%', '').replace(',', '.').strip()) / 100.0
            except: iva = 0.0
            dades_extretes.append({
                "lot": val_w, "article": ws_in.cell(row=fila_orig, column=col_art).value,
                "codi_hcb": ws_in.cell(row=fila_orig, column=col_cod).value, 
                "tecnic": ws_in.cell(row=fila_orig, column=col_tec).value,
                "uml": ws_in.cell(row=fila_orig, column=col_uml).value, 
                "quantitat": (val_qty_val / 12) * factor_dh3,
                "preu_max": preu_max, "iva": iva
            })
        fila_orig += 1
        if fila_orig > 10000: break

    cols = ["LOTE", "ARTÍCULO", "DENOMINACIÓN Y REQUISITOS TÉCNICOS", "CÓDIGO HCB", "UNIDAD DE MEDIDA LICITADA (***)", "CANTIDAD", "BASE IMPONIBLE MÁXIMA DE LICITACIÓN UNITARIA(**) (***)", "TIPO IVA", "BASE IMPONIBLE MÁXIMA DE LICITACIÓN TOTAL (**)", "DENOMINACIÓN ARTÍCULO LICITADOR", "REFERENCIA ARTÍCULO LICITADOR", "BASE IMPONIBLE UNITARIA OFERTADA \n 2 DECIMALES\n (***)", " % IVA OFERTADO", "BASE IMPONIBLE TOTAL OFERTADA ", "IMPORTE TOTAL con descuento(IVA INCLUIDO)"]
    df_final = pd.DataFrame(columns=cols)
    if dades_extretes:
        df_temp = pd.DataFrame(dades_extretes)
        df_final["LOTE"] = df_temp["lot"]; df_final["ARTÍCULO"] = df_temp["article"]; df_final["DENOMINACIÓN Y REQUISITOS TÉCNICOS"] = df_temp["tecnic"]; df_final["CÓDIGO HCB"] = df_temp["codi_hcb"]; df_final["UNIDAD DE MEDIDA LICITADA (***)"] = df_temp["uml"]; df_final["CANTIDAD"] = df_temp["quantitat"]; df_final["BASE IMPONIBLE MÁXIMA DE LICITACIÓN UNITARIA(**) (***)"] = df_temp["preu_max"]; df_final["TIPO IVA"] = df_temp["iva"]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, header=False, startrow=16, sheet_name='ANNEX OFERTA')
    
    output.seek(0); wb_out = load_workbook(output); ws = wb_out.active

    align_center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
    bold_9 = Font(bold=True, size=9); bold_10 = Font(bold=True, size=10)
    fill_verd = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
    fill_blau = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    fill_gris = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    fill_taronja = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # --- CABECERA ---
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path); img.width = 240; img.height = 100; ws.add_image(img, 'A1')
        except: pass

    ws.row_dimensions[1].height = 85
    apply_style(ws, "C1:O1", "ANEXO DE CUMPLIMENTACIÓN OBLIGATORIA 3 PCAP OFERTA ECONÓMICA", font=Font(bold=True, size=14), fill=fill_blau, border=border)
    
    txt_instr = ("Los importes ofertados deberán incluir todos los tributos... Sólo escriba en las celdas en blanco.")
    apply_style(ws, "A2:O2", txt_instr, font=Font(italic=True, size=10), fill=fill_taronja, border=border)
    ws.row_dimensions[2].height = 40

    apply_style(ws, "A4:B4", "TÍTULO DEL EXPEDIENTE:", font=bold_9, fill=fill_gris, border=border)
    apply_style(ws, "C4:O4", titol_expedient, align=align_left_wrap, border=border)
    
    apply_style(ws, "A5:B5", "NÚMERO DE EXPEDIENTE:", font=bold_9, fill=fill_gris, border=border)
    apply_style(ws, "C5:O5", num_expedient, align=align_left_wrap, border=border)

    apply_style(ws, "A7:O7", "LICITADOR E IDENTIFICACIÓN DE LA OFERTA:", font=bold_9, fill=fill_gris, border=border)
    
    # Bloc Licitador
    apply_style(ws, "A9:B9", "EMPRESA", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C9:H9", border=border)
    apply_style(ws, "A10:B10", "E-MAIL", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C10:H10", border=border)
    apply_style(ws, "A11:B11", "PERSONA DE CONTACTO", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C11:H11", border=border)
    apply_style(ws, "A12:B12", "TELÉFONO", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C12:H12", border=border)
    
    apply_style(ws, "I9:K9", "FECHA", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "L9:O9", border=border)
    apply_style(ws, "I10:K10", "DURACIÓN OFERTA", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "L10:O10", border=border)

    apply_style(ws, "A15:I15", "IDENTIFICACIÓN ARTÍCULO Y PRECIO MÁX. LICITADO", fill=fill_verd, font=bold_9, border=border)
    apply_style(ws, "J15:O15", "OFERTA DEL LICITADOR", fill=fill_taronja, font=bold_9, border=border)
    
    for c_idx, h_text in enumerate(cols, start=1):
        cell = ws.cell(row=16, column=c_idx); cell.value = h_text; cell.font = bold_9; cell.alignment = align_center_wrap; cell.border = border
        if c_idx <= 9: cell.fill = fill_verd
        elif c_idx in [10, 11, 12, 13]: cell.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"); cell.font = Font(bold=True, size=9, color="FF0000")

    last_row = ws.max_row; format_milers = '#,##0.00'; format_iva = '0%'
    for r in range(17, last_row + 1):
        ws.cell(row=r, column=6).number_format = '#,##0'; ws.cell(row=r, column=7).number_format = format_milers; ws.cell(row=r, column=8).number_format = format_iva
        ws.cell(row=r, column=9).value = f"=F{r}*G{r}"; ws.cell(row=r, column=9).number_format = format_milers
        ws.cell(row=r, column=14).value = f'=IF(L{r}="","",F{r}*L{r})'; ws.cell(row=r, column=14).number_format = format_milers
        ws.cell(row=r, column=15).value = f'=IF(N{r}="","",N{r}*(1+M{r}))'; ws.cell(row=r, column=15).number_format = format_milers
        for c in range(1, 16):
            cell = ws.cell(row=r, column=c)
            if type(cell).__name__ != 'MergedCell':
                cell.alignment = align_center_wrap; cell.border = border
                cell.protection = Protection(locked=c not in [10, 11, 12, 13])

    fill_vermell = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    ws.conditional_formatting.add(f'N17:O{last_row}', FormulaRule(formula=[f'AND($N17<>"",$N17>$I17)'], fill=fill_vermell))

    row_total = last_row + 1
    for c in range(1, 16): ws.cell(row=row_total, column=c).border = border
    apply_style(ws, f"B{row_total}:F{row_total}", "TOTAL OFERTA ECONÓMICA:", font=bold_10, align=Alignment(horizontal='right'), border=border)
    ws.cell(row=row_total, column=9).value = f"=SUM(I17:I{last_row})"; ws.cell(row=row_total, column=9).number_format = format_milers; ws.cell(row=row_total, column=9).font = bold_10
    ws.cell(row=row_total, column=14).value = f"=SUM(N17:N{last_row})"; ws.cell(row=row_total, column=14).number_format = format_milers; ws.cell(row=row_total, column=14).font = bold_10
    ws.cell(row=row_total, column=15).value = f"=SUM(O17:O{last_row})"; ws.cell(row=row_total, column=15).number_format = format_milers; ws.cell(row=row_total, column=15).font = bold_10
    
    # --- ALÇADES I AMPLADES ---
    for r in range(4, 13): ws.row_dimensions[r].height = 25
    ws.row_dimensions[15].height = 40; ws.row_dimensions[16].height = 55; ws.row_dimensions[row_total].height = 30
    
    ws.column_dimensions['A'].width = 8; ws.column_dimensions['B'].width = 10; ws.column_dimensions['C'].width = 45; ws.column_dimensions['D'].width = 12; ws.column_dimensions['E'].width = 12; ws.column_dimensions['F'].width = 12; ws.column_dimensions['G'].width = 15; ws.column_dimensions['H'].width = 12; ws.column_dimensions['I'].width = 15; ws.column_dimensions['J'].width = 35; ws.column_dimensions['K'].width = 15; ws.column_dimensions['L'].width = 15; ws.column_dimensions['M'].width = 12; ws.column_dimensions['N'].width = 15; ws.column_dimensions['O'].width = 15

    # Desbloqueig campos
    for zona in ["C9:H12", "L9:O10"]:
        start, end = zona.split(":")
        for row in ws[start:end]:
            for cell in row: cell.protection = Protection(locked=False)

    ws.protection.password = '1234'; ws.protection.sheet = True
    final_output = io.BytesIO(); wb_out.save(final_output)
    return final_output.getvalue()

def generate_ot(input_bytes, logo_path='logo.png'):
    wb_in = load_workbook(io.BytesIO(input_bytes), data_only=True)
    nom_pestanya_cab = next((s for s in wb_in.sheetnames if s.upper() == "CABECERA"), None)
    if not nom_pestanya_cab: raise ValueError("No s'ha trobat la pestanya 'cabecera'.")
    
    ws_cab = wb_in[nom_pestanya_cab]
    titol_expedient = ws_cab['B9'].value
    num_expedient = ws_cab['B5'].value

    ws_in = wb_in['Full Inici']
    val_dh3 = ws_in['DH3'].value
    factor_dh3 = float(val_dh3) if val_dh3 is not None else 1.0
    
    mapping = get_column_mapping(wb_in, 'OT')
    col_lot = mapping.get("LOT", 23)
    col_art = mapping.get("ARTICLE", 24)
    col_cod = mapping.get("CODI HCB", 1)
    col_tec = mapping.get("DENOMINACIÓ I REQUERIMENTS TÈCNICS", 32)
    col_uml = mapping.get("UNITAT DE MESURA LICITADA (UML)", 68)
    col_qty = mapping.get("QUANTITAT", 69)

    dades_extretes = []
    fila_orig = 6
    while ws_in.cell(row=fila_orig, column=col_art).value is not None or ws_in.cell(row=fila_orig, column=col_cod).value is not None:
        # Evitar capturar la fila de capçalera si es detecta per paraules clau
        val_w = ws_in.cell(row=fila_orig, column=col_lot).value 
        if val_w is not None and str(val_w).strip() != "" and str(val_w).upper() != "NUMERO":
            val_qty_val = parse_num(ws_in.cell(row=fila_orig, column=col_qty).value)
            dades_extretes.append({
                "lot": val_w, "article": ws_in.cell(row=fila_orig, column=col_art).value,
                "codi_hcb": ws_in.cell(row=fila_orig, column=col_cod).value, 
                "tecnic": ws_in.cell(row=fila_orig, column=col_tec).value,
                "uml": ws_in.cell(row=fila_orig, column=col_uml).value, "quantitat": (val_qty_val / 12) * factor_dh3
            })
        fila_orig += 1
        if fila_orig > 10000: break

    cols = ["LOT", "ARTICLE", "CODI HCB", "DENOMINACIÓ I REQUERIMENTS TÈCNICS", 
            "QUANTITAT", "UNITAT DE MESURA LICITADA (UML)", "DENOMINACIÓ ARTICLE LICITADOR", 
            "DESCRIPCIÓ ARTICLE LICITADOR", "REFERÈNCIA MATERIAL LICITADOR (***)", 
            "FORMAT DE PRESENTACIÓ", "UNITATS UML EN PRESENTACIÓ (**)", 
            "FORMAT PRESENTACIÓ UNITAT MÍNIMA DE COMANDA", "UNITATS UML EN PRESENTACIÓ DE COMANDA (**)", 
            "ALTRE FORMAT DE PRESENTACIÓ MENOR CONTINGUTS (***)", "UNITATS UML EN ALTRE FORMAT MENOR (**)", 
            "NOM DEL FABRICANT", "MARCA", "REF. MATERIAL DEL FABRICANT"]

    df_final = pd.DataFrame(columns=cols)
    if dades_extretes:
        df_temp = pd.DataFrame(dades_extretes)
        df_final["LOT"] = df_temp["lot"]
        df_final["ARTICLE"] = df_temp["article"]
        df_final["CODI HCB"] = df_temp["codi_hcb"]
        df_final["DENOMINACIÓ I REQUERIMENTS TÈCNICS"] = df_temp["tecnic"]
        df_final["QUANTITAT"] = df_temp["quantitat"]
        df_final["UNITAT DE MESURA LICITADA (UML)"] = df_temp["uml"]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, startrow=15, sheet_name='Annex')

    output.seek(0); wb_out = load_workbook(output); ws = wb_out.active

    # --- ESTILS ---
    align_center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
    bold_9 = Font(bold=True, size=9)
    fill_verd = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
    fill_gris = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    fill_groc_inst = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # --- MAQUETACIÓ CABECERA ---
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path); img.width = 240; img.height = 100; ws.add_image(img, 'A1')
        except: pass

    ws.row_dimensions[1].height = 85
    apply_style(ws, "C1:R1", "ANNEX DE COMPLIMENTACIÓ OBLIGATÒRIA 1 PPT D'OFERTA TÈCNICA (ACO1_PPT_OT)", font=Font(bold=True, size=14))
    
    txt_instr = ("Ompli en aquest annex EN UN ÚNIC FITXER EXCEL, LES OFERTES A TOTS ELS LOTS A QUÈ ES PRESENTI.\n"
                 "En cas que la plataforma electrònica li requereixi pujar un fitxer d'oferta per cada lot...")
    apply_style(ws, "A2:R2", txt_instr, font=Font(italic=True, size=10), fill=fill_groc_inst, border=border)
    ws.row_dimensions[2].height = 65

    apply_style(ws, "A4:B4", "TÍTOL DE L´EXPEDIENT:", font=bold_9, fill=fill_gris, border=border)
    apply_style(ws, "C4:R4", titol_expedient, align=align_left_wrap, border=border)
    
    apply_style(ws, "A5:B5", "NÚMERO D´EXPEDIENT:", font=bold_9, fill=fill_gris, border=border)
    apply_style(ws, "C5:R5", num_expedient, align=align_left_wrap, border=border)

    apply_style(ws, "A7:R7", "LICITADOR I IDENTIFICACIÓ DE L'OFERTA:", font=bold_9, fill=fill_gris, border=border)

    # Bloc Esquerre Licitador
    apply_style(ws, "A9:B9", "EMPRESA", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C9:I9", border=border)
    apply_style(ws, "A10:B10", "MAIL", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C10:I10", border=border)
    apply_style(ws, "A11:B11", "PERSONA DE CONTACTE (COMERCIAL)", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C11:I11", border=border)
    apply_style(ws, "A12:B12", "TELÈFON", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "C12:I12", border=border)
    apply_style(ws, "A13:B13", "DIRECCIÓ MAIL CONTACTE (No comandes)", fill=fill_gris, font=bold_9, align=align_left_wrap, border=border); apply_style(ws, "C13:I13", border=border)

    # Bloc Dreta Licitador
    apply_style(ws, "J9:L9", "DATA", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "M9:N9", border=border)
    apply_style(ws, "J10:L10", "MAIL comandes", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "M10:N10", border=border)
    apply_style(ws, "J11:L11", "TELÈFON comandes", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "M11:N11", border=border)
    apply_style(ws, "J12:L12", "FAX COMANDES", fill=fill_gris, font=bold_9, border=border); apply_style(ws, "M12:N12", border=border)
    apply_style(ws, "O9:R13", "", fill=PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"), border=border)

    # Capçaleres Taula
    apply_style(ws, "A15:F15", "IDENTIFICACIÓ ARTICLE LICITAT", fill=fill_verd, font=bold_9, border=border)
    apply_style(ws, "G15:R15", "IDENTIFICACIÓ ARTICLE OFERTAT LICITADOR", fill=fill_gris, font=bold_9, border=border)
    for c in range(1, 19):
        cell = ws.cell(row=16, column=c)
        cell.font = bold_9; cell.alignment = align_center_wrap; cell.border = border
        if c <= 4 or c == 6: cell.fill = fill_verd
        elif c == 5: cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        else: cell.fill = fill_gris

    # --- PROTECCIÓ I ALÇADES ---
    for r in range(4, 14): ws.row_dimensions[r].height = 25
    ws.row_dimensions[16].height = 45

    last_row = ws.max_row
    for r in range(17, last_row + 1):
        ws.row_dimensions[r].height = None 
        val_cant = ws.cell(row=r, column=5).value
        # Si val_cant es 0, bloquegem tota la fila. Si no, bloquegem columnes de HCB (1-6)
        is_zero = False
        try: is_zero = float(val_cant) == 0
        except: pass
        
        for c in range(1, 19):
            cell = ws.cell(row=r, column=c)
            cell.alignment = align_center_wrap; cell.border = border
            if c == 5: cell.number_format = '#,##0'
            cell.protection = Protection(locked=True if is_zero else (c < 7))

    # Desbloqueig camps d'entrada superiors
    for zona in ["C9:I13", "M9:N12", "O9:R13"]:
        start, end = zona.split(":")
        for row in ws[start:end]:
            for cell in row: cell.protection = Protection(locked=False)

    ws.column_dimensions['D'].width = 55
    ws.protection.password = '1234'
    ws.protection.sheet = True
    
    final_output = io.BytesIO()
    wb_out.save(final_output)
    return final_output.getvalue()
