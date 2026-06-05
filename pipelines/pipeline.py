import argparse
import logging
import sys
from pathlib import Path
from src.etl.extract import extract_data
from src.etl.transform import parsear_bios_lenovo, clean_text
from src.etl.load import (
    generate_dim_contrato, generate_dim_estado, generate_dim_estado_ejecucion, 
    generate_dim_equipos, generate_dim_date, generate_dim_bios, 
    generate_dim_empresa, generate_dim_usuario
)
import pandas as pd

DIMS  = ["dim_equipos", "dim_empresa", "dim_usuario", "dim_estado_ejecucion", "dim_estado", "dim_contrato", "dim_date", "dim_bios"]
FACTS = ["fact_equipos"]

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def build_fact_equipos(df_clean: pd.DataFrame, maps: dict[str, dict]) -> pd.DataFrame:
    df_fact = df_clean.copy()
    df_fact["Contrato/adendum"] = df_fact["Contrato"] + "/" + df_fact["Adendum"]
    df_fact["Key estado ejecucion"] = df_fact["Estado Incidente"].map(maps["estado_ejecucion"])
    df_fact["Key estado"] = df_fact["Estado Despliegue"].map(maps["estado"])
    df_fact["Key contrato"] = df_fact["Contrato/adendum"].map(maps["contrato"])
    df_fact["Key equipo"] = df_fact["Numero Serie"].map(maps["equipos"])
    df_fact["Key date"] = pd.to_datetime(df_fact["Fecha"]).dt.strftime("%Y%m%d").astype(int)
    df_fact["Key bios"] = df_fact["Version BIOS"].map(maps["bios"])
    df_fact["Key empresa"] = df_fact["Entidad"].map(maps["empresa"])
    df_fact["Key usuario"] = df_fact["Usuario"].map(maps["usuario"])

    columnas_finales = ["Key estado ejecucion", "Key estado", "Key contrato", "Key equipo", 
                        "Key date", "Key bios", "Key empresa", "Key usuario", "Numero", "Nombre",
                        "SO Instalado", "Fecha Publicacion BIOS", "Fecha Fin Garantia", "Observaciones"]
    return df_fact[columnas_finales]

def load_existing(path: Path, force: bool = False) -> pd.DataFrame | None:
    # Si force es True, ignoramos el histórico y retornamos None
    if force:
        return None
        
    if path.exists():
        logger.info(f"  Cargando acumulado: {path.name}")
        # CORRECCIÓN: Cambiado de read_excel a read_csv para coincidir con la escritura
        return pd.read_csv(path) 
    return None

def run(data_dir: Path, output_dir: Path, force: bool = False) -> None:
    # -- 1. cargar datos
    df_raw = extract_data(data_dir)
    
    # -- 2. limpieza y transformación
    df_clean = clean_text(df_raw)
    df_clean["Version BIOS"] = df_clean["Version BIOS"].apply(parsear_bios_lenovo)
    
    # -- 3. Historicos acumulados
    if force:
        logger.info("Modo FORCE activado. Ignorando archivos previos...")
    else:
        logger.info("Cargando previos...")
        
    ex_estado_ejecucion = load_existing(output_dir / "dim_estado_ejecucion.csv", force)
    ex_estado = load_existing(output_dir / "dim_estado.csv", force)
    ex_contrato = load_existing(output_dir / "dim_contrato.csv", force)
    ex_equipos = load_existing(output_dir / "dim_equipos.csv", force)
    ex_date = load_existing(output_dir / "dim_date.csv", force)
    ex_bios = load_existing(output_dir / "dim_bios.csv", force)
    ex_empresa = load_existing(output_dir / "dim_empresa.csv", force)
    ex_usuario = load_existing(output_dir / "dim_usuario.csv", force)

    ex_fact_equipos = load_existing(output_dir / "fact_equipos.csv", force)

    # -- 4. Acumulación de dimensiones
    logger.info("Generando dimensiones...")
    dim_estado_ejecucion = generate_dim_estado_ejecucion(df_clean, ex_estado_ejecucion)
    dim_estado = generate_dim_estado(df_clean, ex_estado)
    dim_contrato = generate_dim_contrato(df_clean, ex_contrato)
    dim_equipos = generate_dim_equipos(df_clean, ex_equipos)
    dim_date = generate_dim_date(df_clean, ex_date)
    dim_bios = generate_dim_bios(df_clean, ex_bios)
    dim_empresa = generate_dim_empresa(df_clean, ex_empresa)
    dim_usuario = generate_dim_usuario(df_clean, ex_usuario)

    # -- 5. Mapas
    map_estado_ejecucion = dict(zip(dim_estado_ejecucion["Estado Incidente"], dim_estado_ejecucion["Key estado ejecucion"]))
    map_estado = dict(zip(dim_estado["Estado Despliegue"], dim_estado["Key estado"]))
    map_contrato = dict(zip(dim_contrato["Contrato/adendum"], dim_contrato["Key contrato"]))
    map_equipos = dict(zip(dim_equipos["Numero Serie"], dim_equipos["Key serie"]))
    map_date = dict(zip(dim_date["fecha"], dim_date["Key fecha"]))
    map_bios = dict(zip(dim_bios["Version BIOS"], dim_bios["Key bios"]))
    map_empresa = dict(zip(dim_empresa["Entidad"], dim_empresa["Key empresa"]))
    map_usuario = dict(zip(dim_usuario["Usuario"], dim_usuario["Key usuario"]))

    # -- 6. Generar hechos
    logger.info("Generando hechos...")
    fact_equipos = build_fact_equipos(df_clean, {
        "estado_ejecucion": map_estado_ejecucion,
        "estado": map_estado,
        "contrato": map_contrato,
        "equipos": map_equipos,
        "date": map_date,
        "bios": map_bios,
        "empresa": map_empresa,
        "usuario": map_usuario
    })

    # -- 7. Guardar resultados
    logger.info("Guardando resultados...")
    saves = {
        "dim_estado_ejecucion": dim_estado_ejecucion,
        "dim_estado": dim_estado,
        "dim_contrato": dim_contrato,
        "dim_equipos": dim_equipos,
        "dim_date": dim_date,
        "dim_bios": dim_bios,
        "dim_empresa": dim_empresa,
        "dim_usuario": dim_usuario,
        "fact_equipos": fact_equipos
    }

    for path, df in saves.items():
        output_path = output_dir / f"{path}.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"  → Guardado: {output_path.name} ({len(df)} registros)")

    logger.info("Pipeline finalizado exitosamente.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline ETL - inventariado"
    )
    parser.add_argument("--data",   default="data/02-silver",    help="Path de archivos")
    parser.add_argument("--output", default="data/03-gold",      help="Carpeta de salida")
    
    # NUEVO: Argumento flag --force
    parser.add_argument("--force", action="store_true", help="Ignorar históricos y regenerar datos desde cero")

    args = parser.parse_args()

    try:
        run(
            data_dir = Path(args.data),
            output_dir = Path(args.output),
            force = args.force # Pasamos el flag a la función principal
        )

    except (FileExistsError, ValueError, Exception) as e:
        logger.error(str(e))
        sys.exit(1)