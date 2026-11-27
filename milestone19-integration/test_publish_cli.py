import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PublishCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source = root / 'input.csv'
        self.dest = root / 'output.csv'
        self.contract = root / 'contract.json'
        self.source.write_text('id,amount\n1,10\n')
        self.dest.write_text('previous')
        self.contract.write_text('{"columns": ["id", "amount"]}')

    def invoke(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('publish_cli.py')), str(self.source), str(self.dest), str(self.contract), '--required', 'amount', '--key', 'id'], capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def test_success(self):
        code, report = self.invoke()
        self.assertEqual(code, 0)
        self.assertTrue(report['published'])
        self.assertEqual(self.dest.read_bytes(), self.source.read_bytes())

    def test_rejected(self):
        self.source.write_text('id,amount\n1,10\n1,20\n')
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertFalse(report['published'])
        self.assertEqual(self.dest.read_text(), 'previous')

    def test_bad_contract(self):
        self.contract.write_text('[]')
        code, report = self.invoke()
        self.assertEqual(code, 2)
        self.assertFalse(report['published'])
        self.assertEqual(self.dest.read_text(), 'previous')

    def test_missing_input(self):
        self.source.unlink()
        code, report = self.invoke()
        self.assertEqual(code, 2)
        self.assertFalse(report['published'])
        self.assertEqual(self.dest.read_text(), 'previous')
