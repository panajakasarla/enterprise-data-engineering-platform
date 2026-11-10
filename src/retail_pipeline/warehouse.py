"""SQLite analytics mart built on committed incremental retail orders.

Views are read-only and derive metrics from accepted orders. Revenue is computed
using decimal arithmetic in Python to avoid binary floating-point rounding.
"""
import argparse
import json
import sqlite3
from decimal import Decimal
from pathlib import Path

SCHEMA = """
CREATE VIEW IF NOT EXISTS dim_customers AS
SELECT customer_id, MIN(order_date) AS first_order_date,
       MAX(order_date) AS last_order_date, COUNT(*) AS order_count
FROM orders GROUP BY customer_id;

CREATE VIEW IF NOT EXISTS dim_products AS
SELECT product_id, COUNT(*) AS order_count,
       SUM(quantity) AS units_sold
FROM orders GROUP BY product_id;

CREATE VIEW IF NOT EXISTS fact_order_lines AS
SELECT order_id, customer_id, product_id, order_date,
       quantity, unit_price, source_batch
FROM orders;

CREATE VIEW IF NOT EXISTS mart_daily_product_activity AS
SELECT order_date, product_id, COUNT(*) AS order_count,
       SUM(quantity) AS units_sold
FROM orders GROUP BY order_date, product_id;
"""

def create_views(db):
    """Install idempotent warehouse views; the ingest schema must already exist."""
    present = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
    ).fetchone()
    if not present:
        raise ValueError("Missing orders table: ingest a batch before building the warehouse")
    db.executescript(SCHEMA)

def daily_revenue(db):
    """Return reproducible daily product revenue, exact to cents."""
    rows = db.execute("""
        SELECT order_date, product_id, quantity, unit_price
        FROM fact_order_lines
        ORDER BY order_date, product_id, order_id
    """)
    totals = {}
    for day, product, quantity, unit_price in rows:
        key = (day, product)
        totals[key] = totals.get(key, Decimal("0")) + Decimal(unit_price) * quantity
    return [
        {"order_date": day, "product_id": product,
         "revenue": str(amount.quantize(Decimal("0.01")))}
        for (day, product), amount in sorted(totals.items())
    ]

def warehouse_report(database):
    """Build views and return analytics plus data-quality observability."""
    path = Path(database)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint database not found: {path}")
    with sqlite3.connect(path) as db:
        create_views(db)
        metrics = db.execute("""
            SELECT (SELECT COUNT(*) FROM orders),
                   (SELECT COUNT(*) FROM batches),
                   (SELECT COUNT(*) FROM rejections)
        """).fetchone()
        customers = db.execute(
            "SELECT COUNT(*) FROM dim_customers"
        ).fetchone()[0]
        products = db.execute(
            "SELECT COUNT(*) FROM dim_products"
        ).fetchone()[0]
        revenue = daily_revenue(db)
    return {"orders": metrics[0], "batches": metrics[1],
            "rejected_rows": metrics[2], "customers": customers,
            "products": products, "daily_product_revenue": revenue}

def main():
    parser = argparse.ArgumentParser(description="Build retail SQL warehouse views")
    parser.add_argument("database", help="Existing incremental SQLite database")
    args = parser.parse_args()
    print(json.dumps(warehouse_report(args.database), indent=2))

if __name__ == "__main__":
    main()
