import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from schema_contract import main, validate

class SchemaContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv = self.root / "batch.csv"
        self.contract = {"columns": ["order_id", "amount"]}

    def check(self, content, **overrides):
        self.csv.write_text(content, encoding="utf-8")
        return validate(self.csv, {**self.contract, **overrides})

    def test_valid(self):
        self.assertTrue(self.check("order_id,amount\n1,9\n")["passed"])
    def test_missing(self):
        self.assertEqual(self.check("order_id\n1\n")["violations"]["missing_columns"], ["amount"])
    def test_extra(self):
        self.assertEqual(self.check("order_id,amount,secret\n1,9,x\n")["violations"]["unexpected_columns"], ["secret"])
    def test_duplicate_header(self):
        self.assertEqual(self.check("order_id,amount,amount\n1,9,10\n")["violations"]["duplicate_columns"], ["amount"])
    def test_order_optional(self):
        self.assertTrue(self.check("amount,order_id\n9,1\n")["passed"])
        self.assertFalse(self.check("amount,order_id\n9,1\n", strict_order=True)["passed"])
    def test_bad_width(self):
        self.assertEqual(self.check("order_id,amount\n1\n")["violations"]["malformed_rows"], 1)
    def test_empty_file(self):
        self.assertFalse(self.check("")["passed"])
    def test_invalid_contract(self):
        with self.assertRaises(ValueError):
            self.check("a\n", columns=["a", "a"])
    def test_cli_report_and_exit(self):
        self.csv.write_text("order_id\n1\n", encoding="utf-8")
        spec = self.root / "contract.json"
        spec.write_text(json.dumps(self.contract))
        report = self.root / "report.json"
        self.assertEqual(main([str(self.csv), str(spec), "--report", str(report)]), 2)
        self.assertFalse(json.loads(report.read_text())["passed"])

if __name__ == "__main__":
    unittest.main()
