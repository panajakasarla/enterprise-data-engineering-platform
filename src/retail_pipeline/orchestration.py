"""Airflow-independent, replay-safe retail pipeline orchestration."""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile
from retail_pipeline.incremental import ingest_batch
from retail_pipeline.warehouse import warehouse_report

def stable_batch_id(source):
    """Identical input bytes produce the same immutable batch ID."""
    return "retail-" + hashlib.sha256(Path(source).read_bytes()).hexdigest()[:24]

def ingest(source, database):
    return ingest_batch(source, database, stable_batch_id(source))

def quality_gate(database, max_rejection_ratio=0.25):
    """Fail on empty accepted data or excessive cumulative rejected rows."""
    if not 0 <= max_rejection_ratio <= 1:
        raise ValueError("max_rejection_ratio must be between 0 and 1")
    if not Path(database).is_file():
        raise FileNotFoundError(f"Checkpoint database not found: {database}")
    with sqlite3.connect(database) as db:
        accepted = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        rejected = db.execute("SELECT COUNT(*) FROM rejections").fetchone()[0]
        batches = db.execute("SELECT COUNT(*) FROM batches").fetchone()[0]
    if batches == 0 or accepted == 0:
        raise ValueError("Data quality gate failed: no accepted orders")
    ratio = rejected / (accepted + rejected)
    if ratio > max_rejection_ratio:
        raise ValueError(f"Data quality gate failed: rejection ratio {ratio:.3f} exceeds {max_rejection_ratio:.3f}")
    return {"accepted": accepted, "rejected": rejected, "rejection_ratio": round(ratio, 6), "batches": batches}

def publish_report(database, destination):
    """Atomically replace the published JSON warehouse snapshot."""
    report = warehouse_report(database)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent,
                                prefix=".retail-", suffix=".json", delete=False) as f:
            temp = Path(f.name)
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, destination)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    return report

def run_pipeline(source, database, destination, max_rejection_ratio=0.25):
    result = ingest(source, database)
    gate = quality_gate(database, max_rejection_ratio)
    report = publish_report(database, destination)
    return {"ingestion": result, "quality": gate, "report": report}

def main():
    parser = argparse.ArgumentParser(description="Run local retail ingestion, quality gate and SQL report")
    parser.add_argument("source")
    parser.add_argument("database")
    parser.add_argument("report")
    parser.add_argument("--max-rejection-ratio", type=float, default=0.25)
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.source, args.database, args.report, args.max_rejection_ratio), indent=2))

if __name__ == "__main__":
    main()
