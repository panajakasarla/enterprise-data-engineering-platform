"""Transactional, replay-safe incremental order ingestion using SQLite.

This local reference implementation models batch checkpoints and late-arriving data.
The checkpoint and data changes commit together, so a failed batch can be retried.
"""
import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = ("order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price")

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS batches (
        batch_id TEXT PRIMARY KEY, content_sha256 TEXT NOT NULL,
        accepted INTEGER NOT NULL, rejected INTEGER NOT NULL,
        committed_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL,
        order_date TEXT NOT NULL, product_id TEXT NOT NULL,
        quantity INTEGER NOT NULL, unit_price TEXT NOT NULL,
        source_batch TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS rejections (
        batch_id TEXT NOT NULL, row_number INTEGER NOT NULL,
        order_id TEXT, reason TEXT NOT NULL,
        PRIMARY KEY (batch_id, row_number))""")

def validate(row):
    for column in REQUIRED:
        if not (row.get(column) or "").strip():
            return None, "missing_" + column
    try:
        parsed_date = date.fromisoformat(row["order_date"].strip())
    except ValueError:
        return None, "invalid_order_date"
    try:
        qty = int(row["quantity"].strip())
        price = Decimal(row["unit_price"].strip())
    except (ValueError, InvalidOperation):
        return None, "invalid_quantity_or_price"
    if qty <= 0 or not price.is_finite() or price < 0:
        return None, "invalid_quantity_or_price"
    return (row["order_id"].strip(), row["customer_id"].strip(),
            parsed_date.isoformat(), row["product_id"].strip(),
            qty, str(price)), None

def ingest_batch(source, database, batch_id):
    """Apply one immutable batch; replays are no-ops, changed IDs are rejected."""
    if not batch_id or not batch_id.strip():
        raise ValueError("batch_id must not be empty")
    source = Path(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with sqlite3.connect(database) as db:
        db.execute("BEGIN IMMEDIATE")
        initialize(db)
        previous = db.execute("SELECT content_sha256 FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()
        if previous:
            if previous[0] != digest:
                raise ValueError("batch_id already used for different content")
            return {"batch_id": batch_id, "status": "skipped", "accepted": 0, "rejected": 0}
        accepted = rejected = 0
        with source.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or any(c not in reader.fieldnames for c in REQUIRED):
                raise ValueError("CSV is missing required columns")
            for row_number, row in enumerate(reader, start=2):
                values, reason = validate(row)
                if not reason:
                    try:
                        db.execute("""INSERT INTO orders
                            (order_id, customer_id, order_date, product_id, quantity, unit_price, source_batch)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""", (*values, batch_id))
                        accepted += 1
                    except sqlite3.IntegrityError:
                        reason = "duplicate_order_id"
                if reason:
                    db.execute("INSERT INTO rejections VALUES (?, ?, ?, ?)",
                               (batch_id, row_number, row.get("order_id"), reason))
                    rejected += 1
        db.execute("INSERT INTO batches VALUES (?, ?, ?, ?, ?)",
                   (batch_id, digest, accepted, rejected, datetime.now(timezone.utc).isoformat()))
    return {"batch_id": batch_id, "status": "committed", "accepted": accepted, "rejected": rejected}

def status(database):
    with sqlite3.connect(database) as db:
        initialize(db)
        batch_count = db.execute("SELECT COUNT(*) FROM batches").fetchone()[0]
        order_count = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        watermark = db.execute("SELECT MAX(order_date) FROM orders").fetchone()[0]
    return {"batches": batch_count, "orders": order_count, "event_date_watermark": watermark}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="CSV input file")
    parser.add_argument("database", help="SQLite checkpoint and order database")
    parser.add_argument("--batch-id", required=True, help="Stable unique ID for the source batch")
    args = parser.parse_args()
    print(json.dumps(ingest_batch(args.source, args.database, args.batch_id), indent=2))
    print(json.dumps(status(args.database), indent=2))

if __name__ == "__main__":
    main()
