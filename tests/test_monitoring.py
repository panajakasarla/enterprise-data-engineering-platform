"""Standard-library regression tests for operational observability."""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from retail_pipeline.monitoring import emit_event, metrics_snapshot, monitored_run


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "orders.csv"
        self.database = self.root / "checkpoints.sqlite"
        self.report = self.root / "report.json"

    def write_orders(self, rows):
        with self.source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=(
                "order_id", "customer_id", "order_date", "product_id",
                "quantity", "unit_price"))
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def order(order_id, quantity="2"):
        return dict(order_id=order_id, customer_id="PRIVATE-CUSTOMER",
                    order_date="2026-11-13", product_id="P1",
                    quantity=quantity, unit_price="2.50")

    def test_missing_database_is_not_created(self):
        with self.assertRaises(FileNotFoundError):
            metrics_snapshot(self.database)
        self.assertFalse(self.database.exists())

    def test_success_event_and_snapshot(self):
        self.write_orders([self.order("A"), self.order("B", "-1")])
        stream = io.StringIO()
        result = monitored_run(self.source, self.database, self.report, 0.5, stream=stream)
        event = json.loads(stream.getvalue())
        self.assertEqual(event["status"], "success")
        self.assertEqual(event["metrics"]["accepted_orders"], 1)
        self.assertEqual(event["metrics"]["rejected_orders"], 1)
        self.assertEqual(event["metrics"]["committed_batches"], 1)
        self.assertEqual(event["metrics"]["rejection_ratio"], 0.5)
        self.assertEqual(event["metrics"]["event_date_watermark"], "2026-11-13")
        self.assertTrue(self.report.exists())
        self.assertEqual(result["ingestion"]["status"], "committed")
        self.assertNotIn("PRIVATE-CUSTOMER", stream.getvalue())

    def test_replay_does_not_inflate_counts(self):
        self.write_orders([self.order("A")])
        monitored_run(self.source, self.database, self.report, stream=io.StringIO())
        replay = monitored_run(self.source, self.database, self.report, stream=io.StringIO())
        self.assertEqual(replay["ingestion"]["status"], "skipped")
        self.assertEqual(metrics_snapshot(self.database)["committed_batches"], 1)
        self.assertEqual(metrics_snapshot(self.database)["accepted_orders"], 1)

    def test_failure_is_logged_and_reraised_without_sensitive_data(self):
        self.write_orders([self.order("A"), self.order("B", "-1")])
        stream = io.StringIO()
        with self.assertRaisesRegex(ValueError, "rejection ratio"):
            monitored_run(self.source, self.database, self.report, stream=stream)
        event = json.loads(stream.getvalue())
        self.assertEqual(event["status"], "failure")
        self.assertEqual(event["error_type"], "ValueError")
        self.assertNotIn("PRIVATE-CUSTOMER", stream.getvalue())
        self.assertNotIn(str(self.source), stream.getvalue())
        self.assertFalse(self.report.exists())

    def test_emit_event_validation(self):
        with self.assertRaises(ValueError):
            emit_event("run", status="unknown", duration_ms=0, stream=io.StringIO())
        with self.assertRaises(ValueError):
            emit_event("run", status="success", duration_ms=-1, stream=io.StringIO())

    def test_metrics_for_empty_committed_batch(self):
        self.write_orders([])
        from retail_pipeline.incremental import ingest_batch
        ingest_batch(self.source, self.database, "empty")
        metrics = metrics_snapshot(self.database)
        self.assertEqual(metrics["rejection_ratio"], 0.0)
        self.assertIsNone(metrics["event_date_watermark"])


if __name__ == "__main__":
    unittest.main()
