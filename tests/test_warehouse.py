"""Integration tests for incremental ingestion and SQL warehouse reporting."""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from retail_pipeline.incremental import ingest_batch
from retail_pipeline.warehouse import warehouse_report

FIELDS = ["order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price"]

class WarehouseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "state.sqlite"

    def batch(self, name, rows):
        source = self.root / f"{name}.csv"
        with source.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return ingest_batch(source, self.db, name)

    def test_revenue_uses_exact_decimal_and_groups_by_date_product(self):
        self.batch("first", [
            dict(zip(FIELDS, ["o1", "c1", "2026-11-01", "p1", "3", "0.10"])),
            dict(zip(FIELDS, ["o2", "c2", "2026-11-01", "p1", "1", "0.20"])),
            dict(zip(FIELDS, ["o3", "c1", "2026-11-02", "p2", "2", "12.25"])),
        ])
        report = warehouse_report(self.db)
        self.assertEqual((report["orders"], report["customers"], report["products"]), (3, 2, 2))
        self.assertEqual(report["daily_product_revenue"], [
            {"order_date": "2026-11-01", "product_id": "p1", "revenue": "0.50"},
            {"order_date": "2026-11-02", "product_id": "p2", "revenue": "24.50"},
        ])

    def test_rejected_duplicates_excluded_and_replays_do_not_change_totals(self):
        rows = [
            dict(zip(FIELDS, ["o1", "c1", "2026-11-01", "p1", "1", "5.00"])),
            dict(zip(FIELDS, ["o1", "c2", "2026-11-01", "p1", "1", "999.00"])),
        ]
        self.batch("first", rows)
        first = warehouse_report(self.db)
        self.assertEqual((first["orders"], first["rejected_rows"]), (1, 1))
        self.assertEqual(first["daily_product_revenue"][0]["revenue"], "5.00")
        self.batch("first", rows)
        self.assertEqual(warehouse_report(self.db), first)

    def test_late_arrival_updates_earlier_day_without_losing_history(self):
        self.batch("newer", [dict(zip(FIELDS, ["o2", "c1", "2026-11-05", "p1", "1", "10.00"]))])
        self.batch("older", [dict(zip(FIELDS, ["o1", "c1", "2026-11-01", "p1", "1", "2.00"]))])
        self.assertEqual([x["revenue"] for x in warehouse_report(self.db)["daily_product_revenue"]],
                         ["2.00", "10.00"])

    def test_views_are_idempotent_and_queryable(self):
        self.batch("one", [dict(zip(FIELDS, ["o1", "c1", "2026-11-01", "p1", "2", "5.00"]))])
        warehouse_report(self.db)
        warehouse_report(self.db)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT units_sold FROM mart_daily_product_activity").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT order_count FROM dim_customers").fetchone()[0], 1)

    def test_missing_database_does_not_create_empty_file(self):
        with self.assertRaises(FileNotFoundError):
            warehouse_report(self.db)
        self.assertFalse(self.db.exists())

if __name__ == "__main__":
    unittest.main()
