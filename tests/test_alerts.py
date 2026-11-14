"""Alert-rule unit tests and checkpoint integration."""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from retail_pipeline.alerts import alert_report, evaluate_alerts, main
from retail_pipeline.orchestration import ingest


class AlertTests(unittest.TestCase):
    def setUp(self):
        self.metrics = {"committed_batches": 1, "accepted_orders": 10,
                        "rejected_orders": 0, "rejection_ratio": 0.0,
                        "event_date_watermark": "2026-11-13"}

    def test_healthy(self):
        self.assertEqual([], evaluate_alerts(self.metrics, today=date(2026, 11, 14)))

    def test_stale_watermark(self):
        codes = [a["code"] for a in evaluate_alerts(self.metrics, today=date(2026, 11, 17))]
        self.assertEqual(["STALE_WATERMARK"], codes)

    def test_multiple_alerts(self):
        metrics = dict(self.metrics, committed_batches=0, accepted_orders=0,
                       rejection_ratio=0.5, event_date_watermark=None)
        codes = [a["code"] for a in evaluate_alerts(metrics, today=date(2026, 11, 14))]
        self.assertEqual(["NO_BATCHES", "NO_ACCEPTED_ORDERS", "HIGH_REJECTION_RATIO", "MISSING_WATERMARK"], codes)

    def test_ratio_boundary(self):
        metrics = dict(self.metrics, rejection_ratio=0.25)
        self.assertEqual([], evaluate_alerts(metrics, today=date(2026, 11, 14)))

    def test_invalid_thresholds(self):
        for ratio in (-0.1, 1.1, float("nan"), float("inf"), True):
            with self.subTest(ratio=ratio), self.assertRaises(ValueError):
                evaluate_alerts(self.metrics, max_rejection_ratio=ratio)
        for days in (-1, 1.5, True):
            with self.subTest(days=days), self.assertRaises(ValueError):
                evaluate_alerts(self.metrics, max_watermark_age_days=days)

    def test_integration_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "orders.csv"
            source.write_text("order_id,customer_id,product_id,order_date,quantity,unit_price\n"
                              "A1,C1,P1,2026-11-13,2,10.00\n", encoding="utf-8")
            db = Path(tmp) / "checkpoint.sqlite"
            ingest(source, db)
            self.assertEqual("healthy", alert_report(db, today=date(2026, 11, 14))["status"])
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = main([str(db), "--max-watermark-age-days", "0"])
            self.assertEqual(2, code)
            self.assertEqual("alert", json.loads(output.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
