import pandas as pd
import logging

logger = logging.getLogger(__name__)

def _validate_no_nulls(df: pd.DataFrame, columns: list[str], table_name: str) -> None:
    """Lanza un error si alguna columna clave contiene nulos."""
    for col in columns:
        nulls = df[col].isna().sum()
        if nulls > 0:
            raise ValueError(
                f"[{table_name}] La columna '{col}' tiene {nulls} valor(es) nulo(s). "
                "Revisar datos fuente antes de continuar."
            )

def _upsert_dim(existing: pd.DataFrame | None,
                nuevos: pd.DataFrame,
                pk_col: str,
                llave_negocio: str) -> pd.DataFrame:
    """
    Fusiona una dimensión existente con registros nuevos del mes.
    """
    if existing is None or existing.empty:
        resultado = nuevos.drop_duplicates(subset=llave_negocio).reset_index(drop=True).copy()
        resultado[pk_col] = resultado.index
        return resultado
 
    candidatos = nuevos.drop_duplicates(subset=llave_negocio).copy()
 
    mask_nuevo = ~candidatos[llave_negocio].isin(existing[llave_negocio])
    solo_nuevos = candidatos[mask_nuevo].copy()
 
    nuevos_count = len(solo_nuevos)
    if nuevos_count == 0:
        logger.info(f"  → Sin registros nuevos en '{llave_negocio}'.")
        return existing
 
    pk_max = int(existing[pk_col].max())
    solo_nuevos = solo_nuevos.reset_index(drop=True)
    solo_nuevos[pk_col] = range(pk_max + 1, pk_max + 1 + nuevos_count)
 
    resultado = pd.concat([existing, solo_nuevos], ignore_index=True)
    logger.info(f"  → {nuevos_count} registro(s) nuevo(s) en '{llave_negocio}'.")
    return resultado

def generate_dim_estado_ejecucion (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    cols = ["Estado Incidente"]
    df_prep = df_raw[cols].drop_duplicates().copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key estado ejecucion", llave_negocio="Estado Incidente")
    logger.info(f"[dim_estado_ejecucion] Total acumulado: {len(resultado)} estados de ejecucion.")
    return resultado

def generate_dim_estado (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    cols = ["Estado Despliegue"]
    df_prep = df_raw[cols].drop_duplicates().copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key estado", llave_negocio="Estado Despliegue")
    logger.info(f"[dim_estado] Total acumulado: {len(resultado)} estados.")
    return resultado

def generate_dim_contrato (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    cols = ["Contrato", "Adendum"]
    _validate_no_nulls(df_raw, ["Contrato"], "dim_contrato")

    df_prep = df_raw[cols].drop_duplicates().copy()
    df_prep["Contrato/adendum"] = df_raw["Contrato"]+ "/" + df_raw["Adendum"]
    df_prep = df_prep.drop_duplicates(subset="Contrato/adendum").copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key contrato", llave_negocio="Contrato/adendum")
    logger.info(f"[dim_contrato] Total acumulado: {len(resultado)} contratos.")
    return resultado

def generate_dim_equipos (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    """
    dim_equipos
    """
    cols = ["Numero Serie","Capacidad MemoriaRAM","Capacidad DiscoDuro", "Procesador","Tipo", "Fabricante", "Modelo"]
    _validate_no_nulls(df_raw, ["Numero Serie"], "dim_equipos")

    df_prep = df_raw[cols].drop_duplicates(subset="Numero Serie").copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key serie", llave_negocio="Numero Serie")
    logger.info(f"[dim_equipos] Total acumulado: {len(resultado)} equipos.")
    return resultado


def generate_dim_date (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    """
    dim_date: PK = YYYYMMDD
    """
    nuevas = pd.DataFrame({"fecha":pd.to_datetime(df_raw["Fecha"].drop_duplicates(), format="%d/%m/%Y %H:%M", dayfirst=True)})
    nuevas["Key fecha"] = nuevas["fecha"].dt.strftime("%Y%m%d").astype(int)

    if existing is not None and not existing.empty:
        combined = pd.concat([existing, nuevas]).drop_duplicates(subset="Key fecha")
    else:
        combined = nuevas
    resultado = combined.sort_values("fecha").reset_index(drop=True)
    logger.info(f"[dim_date] Total acumulado: {len(resultado)} fechas.")
    return resultado

def generate_dim_bios (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    cols = ["Version BIOS"]
    _validate_no_nulls(df_raw, ["Version BIOS"], "dim_bios")

    df_prep = df_raw[cols].drop_duplicates().copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key bios", llave_negocio="Version BIOS")
    logger.info(f"[dim_bios] Total acumulado: {len(resultado)} versiones de bios.")
    return resultado

def generate_dim_empresa (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    cols = ["Entidad"]
    _validate_no_nulls(df_raw, ["Entidad"], "dim_empresa")

    df_prep = df_raw[cols].drop_duplicates().copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key empresa", llave_negocio="Entidad")
    logger.info(f"[dim_empresa] Total acumulado: {len(resultado)} empresas.")
    return resultado

def generate_dim_usuario (df_raw:pd.DataFrame, existing:pd.DataFrame | None = None) -> pd.DataFrame :
    cols = ["Usuario"]
    _validate_no_nulls(df_raw, ["Usuario"], "dim_usuario")

    df_prep = df_raw[cols].drop_duplicates().copy()
    df_prep = df_prep.reset_index(drop=True)
    resultado = _upsert_dim(existing, df_prep, pk_col="Key usuario", llave_negocio="Usuario")
    logger.info(f"[dim_usuario] Total acumulado: {len(resultado)} usuarios.")
    return resultado