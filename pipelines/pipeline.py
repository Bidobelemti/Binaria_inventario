import argparse
import logging
import sys
from pathlib import Path
from src.etl.extract import extract_data
from src.etl.transform import parsear_bios_lenovo, clean_text
import pandas as pd


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline ETL - inventariado"
    )
    parser.add_argument("--data",   default="../data/02-silver",    help="Path de archivos")
    parser.add_argument("--output", default="../data/03-gold",       help="Carpeta de salida")

    args = parser.parse_args()

    try:
        df_raw = extract_data(args.data)
        try:
            df_raw['Prueba BIOS'] = pd.DataFrame(
                df_raw['DynamicField_FECHAPUBLICACIONBIOS'].apply(parsear_bios_lenovo).tolist(),
                index=df_raw.index
            )
            logger.info(f"Se han procesado {len(df_raw)} valores")
        except Exception as e:
            logger.error('Error al parseas BIOS')
            raise
        df_pro = clean_text(df_raw)
    except (FileExistsError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)