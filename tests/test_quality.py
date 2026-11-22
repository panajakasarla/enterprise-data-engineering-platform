import tempfile
import unittest
from pathlib import Path
from src.pipeline_guard.quality import validate_csv

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "batch.csv"

    def check(self, data, **kwargs):
        self.path.write_text(data, encoding="utf-8")
        return validate_csv(self.path, ["id", "amount"], "id", **kwargs)

    def test_valid(self):
        self.assertTrue(self.check("id,amount\n1,10\n2,20\n")["passed"])
    def test_duplicate_key(self):
        self.assertFalse(self.check("id,amount\n1,10\n1,20\n")["passed"])
    def test_missing_column(self):
        self.assertFalse(self.check("id\n1\n")["passed"])
    def test_null_threshold(self):
        self.assertFalse(self.check("id,amount\n1,\n2,20\n")["passed"])
        self.assertTrue(self.check("id,amount\n1,\n2,20\n", max_null_fraction=0.5)["passed"])
    def test_empty_batch(self):
        self.assertFalse(self.check("id,amount\n")["passed"])
    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            self.check("id,amount\n1,10\n", max_null_fraction=1.5)
