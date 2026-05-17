import pandas as pd
import logging

logger = logging.getLogger(__name__)

def extract_data(file_path: str) -> pd.DataFrame:
    """
    Extract data from a CSV file.

    Parameters:
    file_path (str): The path to the CSV file.

    Returns:
    pd.DataFrame: The extracted data as a DataFrame.
    """
    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8")
        logger.info(f"Data cargada correctamente desde {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error cargando datos desde {file_path}: {e}")
        raise