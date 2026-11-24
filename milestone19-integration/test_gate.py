import tempfile
import unittest
from pathlib import Path
from gate import run


class GateTests(unittest.TestCase):
    def check(self, content):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'batch.csv'
            path.write_text(content)
            return run(path, {'columns': ['id', 'amount']}, ['amount'], 'id')

    def test_valid(self):
        self.assertTrue(self.check('id,amount\n1,10\n2,20\n')['passed'])

    def test_schema_failure_skips_quality(self):
        result = self.check('id,total\n1,10\n')
        self.assertFalse(result['passed'])
        self.assertIsNone(result['quality'])

    def test_duplicate(self):
        self.assertFalse(self.check('id,amount\n1,10\n1,20\n')['passed'])

    def test_null(self):
        self.assertFalse(self.check('id,amount\n1,\n')['passed'])

    def test_empty(self):
        self.assertFalse(self.check('id,amount\n')['passed'])

    def test_malformed(self):
        self.assertIsNone(self.check('id,amount\n1,10,20\n')['quality'])
