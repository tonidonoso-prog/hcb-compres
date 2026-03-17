import pandas as pd
import sys

def analyze_excel(path, name):
    try:
        print(f"\n=== ANALYZING {name}: {path} ===")
        # Read header only
        df_header = pd.read_excel(path, nrows=0)
        print(f"Columns: {df_header.columns.tolist()}")
        
        # Read first 10 rows
        df = pd.read_excel(path, nrows=10)
        print(f"Sample data (first 5 rows):\n{df.head(5)}")
        
        if name == "f0":
            # Check for the multi-line shifting
            print("\nChecking for multi-line shifting in f0...")
            df_full = pd.read_excel(path, nrows=20)
            for i in range(min(5, len(df_full)-1)):
                print(f"Row {i}: {df_full.iloc[i].to_dict()}")
                print(f"Row {i+1}: {df_full.iloc[i+1].to_dict()}")
                print("-" * 20)
                
    except Exception as e:
        print(f"Error analyzing {name}: {e}")

if __name__ == "__main__":
    f0_path = r'c:\Users\adonoso\Documents\CLAUDE\COMPRES\Varios Excel\Limpiar Maravilloso\f0.xlsx'
    f1_path = r'c:\Users\adonoso\Documents\CLAUDE\COMPRES\Varios Excel\Limpiar Maravilloso\f1.xlsx'
    analyze_excel(f0_path, "f0")
    analyze_excel(f1_path, "f1")
