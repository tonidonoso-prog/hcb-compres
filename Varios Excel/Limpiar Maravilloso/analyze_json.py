import pandas as pd
import json

def get_info(path):
    df = pd.read_excel(path, nrows=5)
    return {
        "columns": df.columns.tolist(),
        "rows": df.head(5).to_dict(orient='records')
    }

f0_path = r'c:\Users\adonoso\Documents\CLAUDE\COMPRES\Varios Excel\Limpiar Maravilloso\f0.xlsx'
f1_path = r'c:\Users\adonoso\Documents\CLAUDE\COMPRES\Varios Excel\Limpiar Maravilloso\f1.xlsx'

result = {
    "f0": get_info(f0_path),
    "f1": get_info(f1_path)
}

with open("analysis_result.json", "w", encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("Analysis saved to analysis_result.json")
