import pandas as pd
import os

file_path = 'cat2.xlsx'
sheet_name = 'Sheet1'

try:
    # Read first 100 rows without header
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=100)
    
    found = False
    for i, row in df.iterrows():
        # Look for "Jerarquia 3N" or "Material" or any known column
        row_str = [str(x).strip() for x in row.values]
        if 'Jerarquia 3N' in row_str or 'Material' in row_str or 'Cód.M' in row_str:
            print(f"Header found at row index: {i}")
            print("Columns:", row.tolist())
            found = True
            break
            
    if not found:
        print("Header not found in first 100 rows.")
except Exception as e:
    print(f"Error: {e}")
