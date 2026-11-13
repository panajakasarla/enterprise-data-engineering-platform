# Day 8 — Structured operational monitoring

## Objective

Provide machine-readable pipeline run events and read-only data quality metrics
without adding a monitoring server, cloud account, or external dependencies.

## Implementation

- `retail_pipeline.monitoring.monitored_run` wraps the existing incremental
  ingestion → quality gate → atomic warehouse publication workflow.
- A successful run emits one JSON line with UTC timestamp, elapsed milliseconds,
  committed batch count, accepted/rejected order counts, cumulative rejection
  ratio, and event-date watermark.
- A failed run emits one JSON line with the exception **class**, not the
  exception message or input data, and re-raises the original exception.
- `metrics_snapshot` opens SQLite read-only and does not initialize or mutate
  checkpoints. A missing database is an error.
- Replayed batches preserve cumulative counts and do not double-count metrics.

## Try it

```bash
python -m pip install -e .
python -m retail_pipeline.monitoring data/sample_orders.csv outputs/checkpoints.sqlite outputs/report.json --max-rejection-ratio 0.50
python -m unittest discover -s tests -p 'test_monitoring.py' -v
```

The sample contains two invalid rows out of five, so the demonstration uses a
50% threshold; the production-oriented default is 25%.

## Operational limitations

The metrics are cumulative snapshots, not per-run accepted/rejected counts.
JSON events go to stdout; shipping to CloudWatch, Azure Monitor, GCP Logging,
or OpenTelemetry is intentionally out of scope. The SQLite backend is a
single-writer local reference design. No distributed tracing, alert routing,
retention, or SLA guarantees are claimed. The wrapper does not automatically
instrument Airflow DAG tasks; an Airflow integration is a future milestone.

## Next

Add cloud-agnostic Terraform infrastructure and secret-free CI validation,
then integrate task-level Airflow metrics and alerting.
