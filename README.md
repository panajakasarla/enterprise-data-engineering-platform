# Enterprise Data Engineering Platform

An incremental portfolio project demonstrating Python ETL, PySpark medallion architecture, data quality, automated tests, and GitHub Actions CI.

## Milestone 1 — CSV ingestion and data quality

Reads retail orders and separates accepted and rejected records with validation reasons.

```bash
python -m pip install -e .
python -m retail_pipeline.ingest data/sample_orders.csv outputs
```

Expected: 3 accepted and 2 rejected. See [Day 1 notes](docs/day1-ingestion.md).

## Milestone 2 — PySpark Bronze/Silver/Gold

Uses local PySpark and Parquet for raw Bronze, validated Silver, and daily product revenue Gold datasets.

Requires Python 3.10+, Java 17, and PySpark 3.5.x:

```bash
python -m pip install -e '.[spark]'
python -m retail_pipeline.spark_layers data/sample_orders.csv outputs/lakehouse
python -m unittest discover -s tests -v
```

Expected: 5 Bronze, 3 Silver, and 3 Gold rows. See [Day 2 notes](docs/day2-spark-medallion.md).

CI runs Python and Spark tests on pull requests. Output files are gitignored.

## Roadmap

1. CSV ingestion and data quality
2. PySpark medallion layers
3. Deterministic deduplication, rejection audit and incremental processing
4. SQL warehouse models
5. Airflow orchestration
6. Docker and IaC deployment
7. Observability and end-to-end integration tests
