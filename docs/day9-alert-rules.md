# Milestone 9 — Read-only operational alert rules

The new alert evaluator reads committed SQLite checkpoint metrics, and reports `NO_BATCHES`, `NO_ACCEPTED_ORDERS`, `HIGH_REJECTION_RATIO`, `MISSING_WATERMARK`, or `STALE_WATERMARK`. Critical and warning severities are included. No customer IDs, order IDs, raw exceptions, or database paths are included in alerts.

```bash
python -m pip install -e .
python -m retail_pipeline.alerts outputs/checkpoints.sqlite --max-rejection-ratio 0.50 --max-watermark-age-days 30
python -m unittest discover -s tests -p 'test_alerts.py' -v
```

Exit code is 0 for healthy and 2 for alerts. Invalid threshold values or absent checkpoint database fail rather than reporting healthy. Alert rules use UTC calendar days; the watermark is the latest **event date**, not the last successful ingestion timestamp. Historical backfills can trigger freshness alerts even if recently processed.

This is a local JSON/CLI reference, **not** cloud infrastructure, hosted monitoring, notification delivery, or a stateful alert manager. A later milestone should add an ingestion-completion timestamp, persistent alert deduplication, alert routing, and Terraform-managed infrastructure. Never commit alert delivery credentials.
