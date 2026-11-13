"""Structured JSON events and read-only operational metrics for the retail pipeline.

No customer IDs, order IDs, source paths, or raw exception text are logged.
"""
import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from retail_pipeline.orchestration import run_pipeline


def metrics_snapshot(database):
    """Read committed checkpoint counts; do not create an absent database."""
    path = Path(database)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint database not found: {path}")
    with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as db:
        accepted, rejected, batches = (
            db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            db.execute("SELECT COUNT(*) FROM rejections").fetchone()[0],
            db.execute("SELECT COUNT(*) FROM batches").fetchone()[0],
        )
        watermark = db.execute("SELECT MAX(order_date) FROM orders").fetchone()[0]
    total = accepted + rejected
    return {
        "accepted_orders": accepted,
        "rejected_orders": rejected,
        "committed_batches": batches,
        "rejection_ratio": round(rejected / total, 6) if total else 0.0,
        "event_date_watermark": watermark,
    }


def emit_event(event, *, status, duration_ms, metrics=None, error_type=None, stream=None):
    """Write a single machine-readable, non-sensitive log line."""
    if status not in ("success", "failure"):
        raise ValueError("Invalid status")
    if duration_ms < 0:
        raise ValueError("Duration must not be negative")
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "status": status,
        "duration_ms": duration_ms,
    }
    if metrics is not None:
        payload["metrics"] = metrics
    if error_type is not None:
        payload["error_type"] = error_type
    print(json.dumps(payload, sort_keys=True, allow_nan=False), file=stream or sys.stdout)
    return payload


def monitored_run(source, database, destination, max_rejection_ratio=0.25, stream=None):
    """Run existing pipeline, recording success/failure without masking errors."""
    started = time.monotonic()
    try:
        result = run_pipeline(source, database, destination, max_rejection_ratio)
    except Exception as exc:
        emit_event(
            "retail_pipeline_run",
            status="failure",
            duration_ms=round((time.monotonic() - started) * 1000, 2),
            error_type=type(exc).__name__,
            stream=stream,
        )
        raise
    emit_event(
        "retail_pipeline_run",
        status="success",
        duration_ms=round((time.monotonic() - started) * 1000, 2),
        metrics=metrics_snapshot(database),
        stream=stream,
    )
    return result


def main():
    parser = argparse.ArgumentParser(description="Run retail pipeline with JSON monitoring")
    parser.add_argument("source")
    parser.add_argument("database")
    parser.add_argument("report")
    parser.add_argument("--max-rejection-ratio", type=float, default=0.25)
    args = parser.parse_args()
    monitored_run(args.source, args.database, args.report, args.max_rejection_ratio)


if __name__ == "__main__":
    main()
