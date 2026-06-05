import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def parsear_bios_lenovo(valor: pd.Series) -> str:
    if pd.isna(valor):
        return None
  
    valor = valor.strip()
    
    # Formato: CODIGO(X.XX) o CODIGO (X.XX )
    m = re.match(r'^([A-Z0-9]+)\s*\(\s*([\d.]+)\s*\)$', valor)
    if m:
        return f'{m.group(1)} {m.group(2)}'
        
    # Formato: CODIGO X.XX o CODIGO/X.XX
    m = re.match(r'^([A-Z0-9]+)[\s/](\d+\.\d{1,2})\s*$', valor)
    if m:
        return f'{m.group(1)} {m.group(2)}'
    return valor

    

def clean_text(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
    columns={
            'Number' : 'Numero',
            'Name' : 'Nombre',
            'Deployment State' : 'Estado Despliegue',
            'Incident State' : 'Estado Incidente',
            'DynamicField_TIPOPC' : 'Tipo',
            'DynamicField_FABRICANTE' : 'Fabricante',
            'DynamicField_MODELOPC' : 'Modelo',
            'DynamicField_NUMEROSERIE' : 'Numero Serie',
            'DynamicField_ENTIDAD' : 'Entidad',
            'DynamicField_CONTRATO' : 'Contrato',
            'DynamicField_ADENDUM' : 'Adendum',
            'DynamicField_USUARIO' : 'Usuario',
            'DynamicField_CAPACIDADMEMORIARAM' : 'Capacidad MemoriaRAM',
            'DynamicField_CAPACIDADDISCODURO' : 'Capacidad DiscoDuro',
            'DynamicField_PROCESADOR' : 'Procesador',
            'DynamicField_SOINSTALADO' : 'SO Instalado',
            'DynamicField_VERSIONBIOS' : 'Version BIOS',
            'DynamicField_FECHAPUBLICACIONBIOS' : 'Fecha Publicacion BIOS',
            'DynamicField_FECHAFINGARANTIA' : 'Fecha Fin Garantia',
            'DynamicField_FECHAULTIMAACTUALIZACION' : 'Fecha',
            'DynamicField_OBSERVACIONES' : 'Observaciones'
        }
    )
    for column in df.columns:
    # 1. Contamos cuántos valores nulos (NaN) tiene la columna actual
        nulos_afectados = df[column].isnull().sum()
        # 2. Si tiene al menos un nulo, informamos y rellenamos
        if nulos_afectados > 0:
            logger.info(f'Limpieza de nulos - Columna "{column}" - Valores afectados: {nulos_afectados}')
            df[column] = df[column].fillna("Sin novedades")
    try:
        valores_afectados = len(df[df['Modelo'].str.contains('TINKPAD', na=False)])
        df['Modelo'] = (
            df['Modelo'].str.replace(r'\bTINKPAD\b', 'THINKPAD', regex=True)
        )
        logger.info(f'Parseo de modelo valores afectados: {valores_afectados}')
        
        contratos_afectados = len(df[df['Contrato'].str.contains(r'CONTRATO\s+INC?I?IAL', regex=True, na=False)])
        df['Contrato'] = (
            df['Contrato'].str.strip().replace(r'CONTRATO\s+INC?I?IAL', 'CONTRATO INICIAL', regex=True)
        )
        logger.info(f'Parseo de contratos valores afectados: {contratos_afectados}')
        usuarios_afectados = len(df[df['Usuario'].str.contains(r'\bASIG?N[ADO]{2,4}\s+CL[EINT]{3,5}\b', regex=True, na=False)])
        df['Usuario'] = (
            df['Usuario'].str.replace(r'\bASIG?N[ADO]{2,4}\s+CL[EINT]{3,5}\b', 'ASIGNADO CLIENTE', regex=True, case = False)
        )
        logger.info(f'Parseo de modelo valores afectados: {usuarios_afectados}')

        return df
    except Exception as e:
        logger.error('Error en replace modelo ', e)
        raise

