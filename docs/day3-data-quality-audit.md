# Day 3 — Deterministic deduplication and rejected-record audit

## Why this matters

Spark's `dropDuplicates(["order_id"])` does not specify which conflicting record survives. This milestone uses a window ordered by normalized customer, product, date, quantity, and price. This produces a reproducible winner for each valid order ID. Identical duplicates are interchangeable.

## Validation rules and precedence

Rows are rejected in this order: missing order ID, missing customer ID, missing product ID, invalid date, invalid/nonpositive quantity, invalid/negative price. Only valid rows participate in deduplication; duplicate valid rows receive `duplicate_order_id`.

## Outputs

- `bronze/orders`: raw records
- `silver/orders`: accepted typed records
- `silver/rejected_orders`: raw input fields plus `rejection_reason`
- `gold/daily_product_sales`: daily revenue and units

All paths are Parquet directories. The pipeline overwrites output on each batch run, so rerunning an identical input is idempotent. It does not yet support merging multiple batches or persisting checkpoints.

## Verify

```bash
python -m pip install -e '.[spark]'
python -m unittest discover -s tests -v
python -m retail_pipeline.spark_layers data/sample_orders.csv outputs/lakehouse
```

The Spark integration test checks stable duplicate selection, three rejection categories, revenue totals, and repeat execution. The sample CLI should return `{'bronze': 5, 'silver': 3, 'rejected': 2, 'gold': 3}`.

## Next

Introduce source-file batch IDs, watermarks, and merge semantics for incremental loads.
