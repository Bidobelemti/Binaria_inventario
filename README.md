# Proceso ETL

## Estructura del proyecto

```text
├───data
│   ├───01-bronze
│   ├───02-silver
│   └───03-gold
├───docs
├───notebooks
├───pipelines
│   └───__pycache__
└───src
    ├───etl
    │   └───__pycache__
    └───__pycache__
```

## Ejecución

```bash
python -m pipelines.pipeline --data "data/01-bronce/data.csv" --output "another path"
```
