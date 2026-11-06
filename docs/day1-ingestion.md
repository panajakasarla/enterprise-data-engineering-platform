# Day 1: Retail order ingestion

Validate retail CSV orders before downstream transformations. Invalid records are quarantined with rejection reasons.

## Run
```bash
python -m pip install -e .
python -m retail_pipeline.ingest data/sample_orders.csv outputs
python -m unittest discover -s tests -v
```

Outputs: `outputs/valid_orders.csv`, `outputs/rejected_orders.csv`, and `outputs/summary.json`.

Expected sample: 3 accepted, 2 rejected. Duplicate IDs are rejected after the first valid occurrence.

Next: PySpark Bronze/Silver/Gold transformations and Parquet storage.
