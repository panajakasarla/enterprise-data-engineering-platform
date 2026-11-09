"""Regression tests for transactional checkpoints and replay behavior."""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from retail_pipeline.incremental import ingest_batch, status

FIELDS = ("order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price")

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def order(order_id, date="2026-11-08", quantity="2"):
    return dict(order_id=order_id, customer_id="C1", order_date=date,
                product_id="P1", quantity=quantity, unit_price="10.00")

class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "state.sqlite"
        self.source = self.root / "batch.csv"

    def test_replay_is_noop(self):
        write_csv(self.source, [order("A")])
        self.assertEqual(ingest_batch(self.source, self.db, "b1")["accepted"], 1)
        self.assertEqual(ingest_batch(self.source, self.db, "b1")["status"], "skipped")
        self.assertEqual(status(self.db)["orders"], 1)

    def test_changed_content_with_same_id_is_rejected(self):
        write_csv(self.source, [order("A")])
        ingest_batch(self.source, self.db, "b1")
        write_csv(self.source, [order("B")])
        with self.assertRaisesRegex(ValueError, "different content"):
            ingest_batch(self.source, self.db, "b1")
        self.assertEqual(status(self.db)["orders"], 1)

    def test_late_arrival_and_cross_batch_duplicate(self):
        write_csv(self.source, [order("A", "2026-11-08")])
        ingest_batch(self.source, self.db, "b1")
        write_csv(self.source, [order("B", "2026-11-01"), order("A")])
        result = ingest_batch(self.source, self.db, "b2")
        self.assertEqual((result["accepted"], result["rejected"]), (1, 1))
        self.assertEqual(status(self.db), {"batches": 2, "orders": 2, "event_date_watermark": "2026-11-08"})
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT reason FROM rejections").fetchone()[0], "duplicate_order_id")

    def test_failed_batch_rolls_back(self):
        write_csv(self.source, [order("A")])
        ingest_batch(self.source, self.db, "b1")
        write_csv(self.source, [order("B")])
        with self.assertRaises(ValueError):
            ingest_batch(self.source, self.db, "b1")
        self.assertEqual(status(self.db)["batches"], 1)

    def test_invalid_row_is_audited(self):
        write_csv(self.source, [order("A", quantity="-1"), order("B")])
        result = ingest_batch(self.source, self.db, "b1")
        self.assertEqual((result["accepted"], result["rejected"]), (1, 1))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT reason FROM rejections").fetchone()[0], "invalid_quantity_or_price")

if __name__ == "__main__":
    unittest.main()
