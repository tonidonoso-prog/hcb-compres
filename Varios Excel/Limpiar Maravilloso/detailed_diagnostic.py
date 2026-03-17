import pandas as pd
import sys

def analyze():
    f0_path = r'c:\Users\adonoso\Documents\CLAUDE\COMPRES\Varios Excel\Limpiar Maravilloso\f0.xlsx'
    
    # Based on previous output, header is likely around row 6
    # Let's read with header at 6
    df = pd.read_excel(f0_path, header=6, nrows=30)
    
    with open("f0_detailed_analysis.txt", "w", encoding='utf-8') as f:
        f.write(f"Columns found at row 6:\n{df.columns.tolist()}\n\n")
        
        for i in range(0, len(df)-1, 2):
            row_main = df.iloc[i]
            row_next = df.iloc[i+1]
            
            f.write(f"--- PAIR {i//2} ---\n")
            f.write(f"MAIN ROW {i} (Material: {row_main.get('Cód.M')}): \n")
            f.write(str({k:v for k,v in row_main.to_dict().items() if pd.notna(v)}) + "\n")
            
            f.write(f"SHIFTED ROW {i+1}: \n")
            # Look for values in the next row that might be the 'descripcion larga' and 'grupo portes'
            # The user says they are one line below.
            f.write(str({k:v for k,v in row_next.to_dict().items() if pd.notna(v)}) + "\n")
            f.write("\n")

if __name__ == "__main__":
    analyze()
