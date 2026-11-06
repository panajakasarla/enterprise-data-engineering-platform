# Enterprise Data Engineering Platform

A portfolio project building a production-style retail analytics platform incrementally, with data quality, orchestration, Spark processing, SQL models, and DevOps automation.

## Milestone 1: Python retail order ingestion

The ingestion module reads order CSV files, validates order identifiers, required fields, ISO dates, quantities, and prices, then separates valid and rejected records with audit reasons.

### Quick start

Requires Python 3.10+.

```bash
python -m pip install -e .
python -m retail_pipeline.ingest data/sample_orders.csv outputs
python -m unittest discover -s tests -v
```

Expected sample summary: **3 accepted / 2 rejected**.

Outputs are `outputs/valid_orders.csv`, `outputs/rejected_orders.csv`, and `outputs/summary.json`. Generated outputs are excluded from Git.

### CI

GitHub Actions runs the Python unit tests on pushes and pull requests.

### Repository layout

- `src/retail_pipeline/ingest.py` — validation and ingestion
- `tests/test_ingest.py` — five unit/integration tests
- `data/sample_orders.csv` — synthetic retail orders
- `docs/day1-ingestion.md` — milestone documentation
- `.github/workflows/tests.yml` — CI test workflow

## Roadmap

1. Python ingestion and data quality
2. PySpark Bronze/Silver/Gold transformations and Parquet storage
3. SQL warehouse models and analytics
4. Airflow DAG orchestration
5. Dockerized reproducible execution
6. Infrastructure automation and observability
7. End-to-end tests and production-style documentation
