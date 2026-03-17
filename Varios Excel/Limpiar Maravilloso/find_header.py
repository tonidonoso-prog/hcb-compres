import pandas as pd

def find_header_and_sample(path):
    print(f"Scanning {path}...")
    # Try different starting rows to find something with many columns or specific keywords
    for skip in range(20):
        df = pd.read_excel(path, skiprows=skip, nrows=10)
        cols = [str(c) for c in df.columns]
        if any('material' in c.lower() or 'Cód' in c for c in cols):
            print(f"Potential header found at row {skip}:")
            print(f"Columns: {cols}")
            print("First 5 rows of data:")
            print(df.head(5))
            
            # Investigate the "one line below" rule
            print("\nInvestigating row shifting:")
            for i in range(len(df)-1):
                row1 = df.iloc[i].to_dict()
                row2 = df.iloc[i+1].to_dict()
                print(f"Row {i} (Material?): {row1.get('Cód.M') or row1.get('Material')}")
                # Look for what might be 'descripcion larga' or 'grupo portes' in row2
                # In f1 they are "Texto largo de material" and "GrPt"
                print(f"Row {i+1} might contain extra info for Row {i}")
                print(f"Row {i+1} values: { {k:v for k,v in row2.items() if pd.notna(v)} }")
                print("-" * 10)
            return

f0_path = r'c:\Users\adonoso\Documents\CLAUDE\COMPRES\Varios Excel\Limpiar Maravilloso\f0.xlsx'
find_header_and_sample(f0_path)
