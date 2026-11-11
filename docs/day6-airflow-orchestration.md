# Day 6 — Airflow orchestration and data-quality gates

## Architecture
The Airflow DAG `dags/retail_daily.py` runs three PythonOperator tasks in order:
`ingest_orders >> check_quality >> publish_warehouse`. The Python functions
live in `retail_pipeline.orchestration` and can run without Airflow.

Ingestion uses a SHA-256-derived batch ID, so identical source bytes are
replay-safe. New source content produces a new batch ID. A transactional SQLite
checkpoint prevents duplicate orders across batches.

The quality gate fails if there are no accepted orders or if the **cumulative**
rejected-row ratio exceeds the configured limit (default 25%). Failed gates
prevent publishing a new report, but do not undo already committed ingestion.
The warehouse JSON report is written by atomic replacement.

## Local run
```bash
python -m pip install -e .
python -m retail_pipeline.orchestration data/sample_orders.csv outputs/checkpoints.sqlite outputs/warehouse_report.json --max-rejection-ratio 0.50
python -m unittest discover -s tests -p 'test_orchestration.py' -v
```
The bundled sample has 3 valid and 2 rejected rows (40% rejection), so the
default 25% gate **intentionally fails**; use 0.50 for this demo.

## Airflow deployment
Install Airflow 2.8+ in a separate environment using the official
version-specific constraints, install this package, and put the `dags/`
directory on Airflow's DAG path. Configure these worker environment variables:
`RETAIL_SOURCE`, `RETAIL_DB`, `RETAIL_REPORT`, and
`RETAIL_MAX_REJECTION_RATIO`. The DAG schedules daily at 06:00 UTC, disables
catchup, allows one active run, and retries failures twice after five minutes.
Airflow itself is deliberately not installed in lightweight unit-test CI.

## Limitations
SQLite is appropriate for local single-writer demonstration, not distributed
Airflow workers or cloud scale. All workers need shared filesystem access.
The cumulative gate can stay failed after a bad batch until the data is
remediated. Replacing a source file during ingestion is not supported: stage
immutable input snapshots before triggering a run. A SHA-256 prefix is used
for convenient batch IDs; full digests remain in checkpoint records.
Airflow scheduler/DAG parsing has not been exercised in this milestone.

## Next
Add containerized local Airflow deployment, structured task metrics, and
CI smoke tests for DAG parsing.
