# Day 4 — Incremental batch checkpoints

## Design
This milestone adds a **local SQLite reference implementation** for incremental CSV processing. It is intentionally separate from the Spark medallion pipeline; integrating it with distributed Parquet writes is a future task.

A caller supplies a stable `--batch-id` for each immutable source file. The SHA-256 fingerprint and accepted/rejected records are committed in one SQLite transaction. A repeated ID with the same content is skipped; reusing an ID for changed content raises an error. The unique `order_id` key prevents cross-batch duplication. Invalid rows and duplicates are audited with batch ID and source row number.

The `event_date_watermark` is the **maximum observed event date for reporting**, not a filtering threshold. Late-arriving valid orders are ingested, so no records are silently dropped due to their event date.

## Run

```bash
python -m pip install -e .
python -m retail_pipeline.incremental data/sample_orders.csv outputs/checkpoints.sqlite --batch-id sample-001
python -m retail_pipeline.incremental data/sample_orders.csv outputs/checkpoints.sqlite --batch-id sample-001
python -m unittest discover -s tests -v
```

The first run commits the batch; the second reports `skipped`. SQLite stores tables `batches`, `orders`, and `rejections`. Do not delete the database between runs if you want replay protection.

## Tradeoffs
- This implementation uses **insert-only, first-valid-order-wins** semantics, not CDC updates or deletes.
- The checkpoint is atomic with SQLite writes, but **not** with the existing Spark Parquet outputs.
- Concurrent writers are serialized using SQLite's `BEGIN IMMEDIATE`; SQLite is not intended as a distributed ingestion coordinator.
- SHA-256 fingerprints identify exact bytes; a semantically identical but differently formatted file is treated as changed.
- The event-date watermark is informational and should not be used to discard late data.

## Next
Integrate batch metadata into the Spark Bronze layer, then implement transactional lakehouse merges and Airflow scheduling.
