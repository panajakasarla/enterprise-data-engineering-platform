"""Airflow-free integration tests for orchestrated batch processing."""
import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from retail_pipeline.orchestration import run_pipeline, stable_batch_id, quality_gate

FIELDS = ("order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price")

class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.source = root / "orders.csv"
        self.db = root / "checkpoint.sqlite"
        self.report = root / "reports" / "warehouse.json"

    def write(self, rows):
        with self.source.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def order(self, order_id, qty="2"):
        return dict(order_id=order_id, customer_id="C1", order_date="2026-11-11",
                    product_id="P1", quantity=qty, unit_price="2.50")

    def test_revenue_and_report(self):
        self.write([self.order("A"), self.order("B")])
        result = run_pipeline(self.source, self.db, self.report)
        self.assertEqual(result["quality"]["accepted"], 2)
        self.assertEqual(json.loads(self.report.read_text())["daily_product_revenue"][0]["revenue"], "10.00")

    def test_replay_is_noop(self):
        self.write([self.order("A")])
        run_pipeline(self.source, self.db, self.report)
        second = run_pipeline(self.source, self.db, self.report)
        self.assertEqual(second["ingestion"]["status"], "skipped")
        self.assertEqual(second["report"]["orders"], 1)

    def test_gate_blocks_publication(self):
        self.write([self.order("A"), self.order("B", "-1")])
        with self.assertRaisesRegex(ValueError, "rejection ratio"):
            run_pipeline(self.source, self.db, self.report)
        self.assertFalse(self.report.exists())
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM batches").fetchone()[0], 1)

    def test_empty_input_rejected(self):
        self.write([])
        with self.assertRaisesRegex(ValueError, "no accepted orders"):
            run_pipeline(self.source, self.db, self.report)
        self.assertFalse(self.report.exists())

    def test_content_based_batch_id(self):
        self.write([self.order("A")])
        first = stable_batch_id(self.source)
        self.assertEqual(first, stable_batch_id(self.source))
        self.write([self.order("B")])
        self.assertNotEqual(first, stable_batch_id(self.source))

    def test_invalid_threshold(self):
        self.write([self.order("A")])
        run_pipeline(self.source, self.db, self.report)
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            quality_gate(self.db, 1.2)

    def test_missing_database(self):
        with self.assertRaises(FileNotFoundError):
            quality_gate(self.db)

if __name__ == "__main__":
    unittest.main()
