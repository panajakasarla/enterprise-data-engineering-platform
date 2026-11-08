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

## Milestone 3 — Deterministic deduplication and rejection audit

Silver retains one valid record per order ID, using a stable ascending business-field sort to choose a winner. Rows that fail validation or lose deduplication are written to `silver/rejected_orders` with a `rejection_reason`. The same input can be safely rerun with overwrite mode without accumulating duplicates. This is **batch idempotence**, not yet incremental ingestion.

For the bundled sample, expect **5 Bronze, 3 Silver, 2 rejected, and 3 Gold rows**. Review [Day 3 notes](docs/day3-data-quality-audit.md).

CI runs Python and Spark tests on pull requests. Generated outputs are gitignored.

## Roadmap

1. CSV ingestion and data quality
2. PySpark medallion layers
3. Deterministic deduplication and rejection audit
4. Incremental watermark/checkpoint processing
5. SQL warehouse models and Airflow orchestration
6. Docker, IaC, and observability
