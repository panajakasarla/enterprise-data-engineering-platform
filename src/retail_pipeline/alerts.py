"""Read-only alert rules for checkpointed retail ingestion."""
import argparse
import json
import math
from datetime import date, datetime, timezone
from retail_pipeline.monitoring import metrics_snapshot


def evaluate_alerts(metrics, *, max_rejection_ratio=0.25, max_watermark_age_days=2, today=None):
    """Return stable alert codes; never include customer or order identifiers."""
    if isinstance(max_rejection_ratio, bool) or not isinstance(max_rejection_ratio, (float, int)) or not math.isfinite(max_rejection_ratio) or not 0 <= max_rejection_ratio <= 1:
        raise ValueError("max_rejection_ratio must be finite and between zero and one")
    if isinstance(max_watermark_age_days, bool) or not isinstance(max_watermark_age_days, int) or max_watermark_age_days < 0:
        raise ValueError("max_watermark_age_days must be a nonnegative integer")
    today = today or datetime.now(timezone.utc).date()
    if not isinstance(today, date):
        raise TypeError("today must be a date")
    alerts = []
    if metrics["committed_batches"] == 0:
        alerts.append({"code": "NO_BATCHES", "severity": "critical"})
    if metrics["accepted_orders"] == 0:
        alerts.append({"code": "NO_ACCEPTED_ORDERS", "severity": "critical"})
    ratio = metrics["rejection_ratio"]
    if isinstance(ratio, bool) or not isinstance(ratio, (float, int)) or not math.isfinite(ratio) or not 0 <= ratio <= 1:
        raise ValueError("Invalid rejection_ratio metric")
    if ratio > max_rejection_ratio:
        alerts.append({"code": "HIGH_REJECTION_RATIO", "severity": "warning"})
    watermark = metrics["event_date_watermark"]
    if watermark is None:
        alerts.append({"code": "MISSING_WATERMARK", "severity": "warning"})
    elif (today - date.fromisoformat(watermark)).days > max_watermark_age_days:
        alerts.append({"code": "STALE_WATERMARK", "severity": "warning"})
    return alerts


def alert_report(database, *, max_rejection_ratio=0.25, max_watermark_age_days=2, today=None):
    metrics = metrics_snapshot(database)
    alerts = evaluate_alerts(metrics, max_rejection_ratio=max_rejection_ratio,
                             max_watermark_age_days=max_watermark_age_days, today=today)
    return {"status": "alert" if alerts else "healthy", "alert_count": len(alerts),
            "alerts": alerts, "metrics": metrics}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate retail pipeline alert rules")
    parser.add_argument("database")
    parser.add_argument("--max-rejection-ratio", type=float, default=0.25)
    parser.add_argument("--max-watermark-age-days", type=int, default=2)
    args = parser.parse_args(argv)
    report = alert_report(args.database, max_rejection_ratio=args.max_rejection_ratio,
                          max_watermark_age_days=args.max_watermark_age_days)
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 2 if report["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
