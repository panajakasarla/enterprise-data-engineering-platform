# Day 5 — SQL warehouse models and analytics

## Architecture
The incremental SQLite checkpoint database is the source of truth. The warehouse
module creates four **idempotent SQL views**: `fact_order_lines`,
`dim_customers`, `dim_products`, and `mart_daily_product_activity`.
No records are copied into a second database. Accepted orders flow into views;
rejected orders are counted for observability but excluded from revenue.

## Reproducibility
Run from a Python 3.10+ environment:

```bash
python -m pip install -e .
python -m retail_pipeline.incremental data/sample_orders.csv outputs/checkpoints.sqlite --batch-id sample-001
python -m retail_pipeline.warehouse outputs/checkpoints.sqlite
python -m unittest discover -s tests -p 'test_warehouse.py' -v
```

Daily product revenue uses Python `Decimal` to avoid SQLite floating-point
rounding. Output is a deterministic JSON list ordered by date and product.
Late-arriving orders update historical reporting automatically. Replayed batches
do not double-count because the ingestion checkpoint is transactional.

## Limitations
SQLite views are a local reference model, not a cloud data warehouse.
There is no incremental materialized view refresh, slowly changing dimensions,
or distributed transactional Spark writes. Product and customer dimensions are
derived from orders, so they do not include entities without purchases.

## Next
Orchestrate ingestion and warehouse reporting with Airflow, including retries,
scheduling, data-quality gates, and observable task logs.
