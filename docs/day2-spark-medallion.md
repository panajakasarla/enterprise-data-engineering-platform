# Milestone 2 — PySpark medallion lakehouse

Extends the CSV ingestion milestone with three local Parquet datasets:

- **Bronze**: raw CSV fields, preserving original string values.
- **Silver**: validated typed orders; requires nonblank identifiers, valid dates, positive integer quantities, nonnegative decimal prices, and unique order IDs.
- **Gold**: daily product sales aggregates with order count, units sold, and revenue.

## Run

Requires Python 3.10+, Java, and PySpark 3.5.x:

```bash
python -m pip install -e '.[spark]'
python -m retail_pipeline.spark_layers data/sample_orders.csv outputs/lakehouse
python -m unittest discover -s tests -v
```

Expected sample: 5 Bronze rows, 3 Silver rows, 3 Gold aggregates.

## Limitations and next steps

This is local Parquet, not Delta Lake. `dropDuplicates` has nondeterministic survivor selection for conflicting duplicates; production processing needs event-time precedence and a rejection audit table. Next milestone: deterministic deduplication, quarantined rows, and incremental loads.
