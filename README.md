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

## Milestone 4 — Incremental checkpoints and replay protection

A local SQLite reference implementation adds **transactional batch checkpoints**, SHA-256 source fingerprints, cross-batch order deduplication, rejection auditing, and an informational event-date watermark. It accepts late-arriving orders instead of dropping events older than the watermark. This milestone does **not** yet provide distributed Spark/Parquet transactional writes.

```bash
python -m retail_pipeline.incremental data/sample_orders.csv outputs/checkpoints.sqlite --batch-id sample-001
python -m retail_pipeline.incremental data/sample_orders.csv outputs/checkpoints.sqlite --batch-id sample-001
python -m unittest discover -s tests -v
```

The first command commits the batch; the second skips the identical replay. See [Day 4 notes](docs/day4-incremental-checkpoints.md).

## Milestone 5 — SQL warehouse models and daily revenue

Build SQL views for order facts, customer and product dimensions, and daily
product activity on top of the committed SQLite ingestion database. Generate
daily product revenue with exact decimal arithmetic, and report accepted,
rejected, and batch counts without double-counting replays.

```bash
python -m retail_pipeline.warehouse outputs/checkpoints.sqlite
python -m unittest discover -s tests -p 'test_warehouse.py' -v
```

See [Day 5 notes](docs/day5-sql-warehouse.md) for architecture, validation,
limitations, and the next Airflow orchestration milestone.

## Milestone 6 — Airflow orchestration and quality gates

The optional Airflow DAG (`dags/retail_daily.py`) schedules a replay-safe
ingestion task, a data-quality gate, and atomic JSON warehouse report
publication. The task functions can also run locally without Airflow:

```bash
python -m retail_pipeline.orchestration data/sample_orders.csv outputs/checkpoints.sqlite outputs/warehouse_report.json --max-rejection-ratio 0.50
python -m unittest discover -s tests -p 'test_orchestration.py' -v
```

The sample input rejects 2 of 5 rows, so its 40% rejection ratio intentionally
fails the production-oriented default gate of 25%; use 50% for the demo.
See [Day 6 notes](docs/day6-airflow-orchestration.md) for deployment,
retries, configuration, and single-writer SQLite limitations.

## Milestone 7 — Dockerized local Airflow

Run the retail DAG using a pinned Airflow 2.10.5 / Python 3.11 image
without installing Airflow into your host Python environment:

```bash
docker compose build airflow
bash scripts/check_airflow_dag.sh
docker compose up -d airflow
```

The web UI is available at http://localhost:8080 (loopback only). The sample
quality threshold is set to 50% because 2/5 fixture rows are rejected. Named
volumes persist metadata, logs, and pipeline checkpoints; the input fixture is
read-only. This single-container SequentialExecutor setup is **not production
infrastructure**. See [Day 7 notes](docs/day7-docker-airflow.md) for verification,
security limits, and cleanup instructions.

## Roadmap

1. CSV ingestion and data quality
2. PySpark medallion layers
3. Deterministic deduplication and rejection audit
4. Incremental watermark/checkpoint processing (SQLite reference implementation)
5. SQL warehouse models and analytics (SQLite views)
6. Airflow orchestration and data quality gates
7. Dockerized local Airflow and DAG smoke checks
8. Structured operational monitoring and quality metrics
9. Read-only operational alert rules
10. Cloud infrastructure as code and alert delivery

## Milestone 8 — Structured monitoring

Run the existing replay-safe pipeline through a lightweight observability wrapper.
It emits one JSON event per run, including elapsed time, cumulative accepted/rejected
counts, committed batches, rejection ratio, and event-date watermark on success.
Failures log only the exception class and are re-raised; customer/order data and
raw exception messages are not included in the event.

```bash
python -m retail_pipeline.monitoring data/sample_orders.csv outputs/checkpoints.sqlite outputs/report.json --max-rejection-ratio 0.50
python -m unittest discover -s tests -p 'test_monitoring.py' -v
```

This is local structured logging, **not** a hosted monitoring/alerting stack,
and it does not yet instrument Airflow tasks. See [Day 8 notes](docs/day8-observability.md).

## Milestone 9 — Read-only operational alert rules

Evaluate committed checkpoint metrics with deterministic severity-coded alert rules
for empty batches, missing accepted orders, excessive rejection ratio, missing
event-date watermark, and stale event dates.

```bash
python -m retail_pipeline.alerts outputs/checkpoints.sqlite --max-rejection-ratio 0.50 --max-watermark-age-days 30
python -m unittest discover -s tests -p 'test_alerts.py' -v
```

The CLI prints JSON and exits 2 when alerts are present (0 if healthy). This
local reference has no cloud deployment or notification transport. See
[Day 9 notes](docs/day9-alert-rules.md) for thresholds and limitations.

## Milestone 10 — Terraform private artifact storage

A minimal AWS Terraform module provisions a private, encrypted, versioned S3
artifact bucket with TLS-only access, public-access blocks, and non-destructive
deletion defaults. **Nothing is deployed automatically.** No credentials or
Terraform state are stored in this repository.

```bash
python -m unittest discover -s tests -p 'test_terraform_security.py' -v
cd infra/terraform
terraform init -backend=false
terraform fmt -check
terraform validate
```

See [Day 10 notes](docs/day10-terraform-artifacts.md) for AWS planning,
costs, IAM prerequisites, and deployment limitations.

## Milestone 11 — Least-privilege GitHub OIDC IAM and Terraform CI

Terraform adds a GitHub Actions OIDC role with exact repository and branch trust,
no static access keys, and S3 read/write limited to a configurable artifact prefix.
A separate GitHub Actions workflow checks Terraform formatting, initialization,
validation, and offline IAM regression tests. It does **not** deploy AWS resources.

```bash
python -m unittest discover -s tests -p 'test_terraform_iam.py' -v
terraform -chdir=infra/terraform init -backend=false
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform validate
```

The module requires the ARN of an **existing** AWS GitHub OIDC provider before
planning or applying. See [Day 11 notes](docs/day11-iam-oidc.md) for manual
setup, security limitations, and the next deployment milestone.
