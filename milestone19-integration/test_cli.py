"""Exercise the actual ETL gate process contract used by CI."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().with_name('gate.py')

class CLITests(unittest.TestCase):
    def invoke(self, csv_text, contract='{"columns":["id","amount"]}'):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / 'batch.csv'
            config = Path(directory) / 'contract.json'
            if csv_text is not None:
                batch.write_text(csv_text, encoding='utf-8')
            config.write_text(contract, encoding='utf-8')
            result = subprocess.run([sys.executable, str(GATE), str(batch),
                str(config), '--required', 'amount', '--key', 'id'],
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.stderr, '')
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0 if report['passed'] else 1)
            return report

    def test_valid(self):
        self.assertTrue(self.invoke('id,amount\n1,10\n')['passed'])

    def test_schema_drift(self):
        report = self.invoke('id,total\n1,10\n')
        self.assertFalse(report['passed'])
        self.assertIsNone(report['quality'])

    def test_duplicate(self):
        report = self.invoke('id,amount\n1,10\n1,20\n')
        self.assertFalse(report['passed'])
        self.assertTrue(report['schema']['passed'])
        self.assertFalse(report['quality']['passed'])

    def test_invalid_contract(self):
        self.assertIn('error', self.invoke('id,amount\n1,10\n', '{'))

    def test_missing_input(self):
        self.assertIn('error', self.invoke(None))

if __name__ == '__main__':
    unittest.main()
