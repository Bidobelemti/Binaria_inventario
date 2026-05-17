import re
import pandas as pd

def parsear_bios_lenovo(valor: pd.Series) -> str:
    if pd.isna(valor):
        return None
    valor = valor.strip()
    
    # Formato: CODIGO(X.XX) o CODIGO (X.XX )
    m = re.match(r'^([A-Z0-9]+)\s*\(\s*([\d.]+)\s*\)$', valor)
    if m:
        return f'{m.group(1)} {m.group(2)}'
    
    # Formato: CODIGO X.XX o CODIGO/X.XX
    #m = re.match(r'^([A-Z0-9]+)[\s/]([\d.]+)', valor)
    m = re.match(r'^([A-Z0-9]+)[\s/](\d+\.\d{1,2})\s*$', valor)

    if m:
        return f'{m.group(1)} {m.group(2)}'
    
    # Solo código sin versión numérica
    return valor