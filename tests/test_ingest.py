import csv
import json
import tempfile
import unittest
from pathlib import Path
from retail_pipeline.ingest import ingest, validate

class IngestTests(unittest.TestCase):
    def row(self, **overrides):
        return {**dict(order_id="A", customer_id="C", order_date="2026-11-01", product_id="P", quantity="2", unit_price="4.50"), **overrides}

    def test_valid_row(self):
        self.assertIsNone(validate(self.row(), set()))

    def test_duplicate(self):
        self.assertEqual(validate(self.row(), {"A"}), "duplicate order_id")

    def test_bad_quantity(self):
        self.assertIn("positive", validate(self.row(quantity="0"), set()))

    def test_missing_required(self):
        self.assertIn("missing", validate({}, set()))

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "orders.csv"
            with source.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(self.row()))
                writer.writeheader()
                writer.writerow(self.row())
                writer.writerow(self.row())
            result = ingest(source, Path(directory) / "out")
            self.assertEqual(result, {"accepted": 1, "rejected": 1})
            self.assertEqual(json.loads((Path(directory) / "out" / "summary.json").read_text()), result)

if __name__ == "__main__":
    unittest.main()
