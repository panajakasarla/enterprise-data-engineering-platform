import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ObservedTests(unittest.TestCase):
    def test_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest, contract = [root / x for x in ('input.csv', 'output.csv', 'contract.json')]
            contract.write_text('{"columns":["id","amount"]}')
            ids = set()
            for data, expected, status in [('id,amount\n1,10\n', 0, 'published'), ('id,amount\n1,10\n1,20\n', 1, 'rejected'), (None, 2, 'error')]:
                with self.subTest(status=status):
                    if data is None:
                        source.unlink()
                    else:
                        source.write_text(data)
                    result = subprocess.run([sys.executable, str(Path(__file__).with_name('run_observed.py')), str(source), str(dest), str(contract), '--required', 'amount', '--key', 'id'], capture_output=True, text=True)
                    event = json.loads(result.stdout)
                    self.assertEqual(result.returncode, expected)
                    self.assertEqual(event['exit_code'], expected)
                    self.assertEqual(event['status'], status)
                    self.assertGreaterEqual(event['duration_ms'], 0)
                    self.assertNotIn(event['run_id'], ids)
                    ids.add(event['run_id'])
                    self.assertEqual(dest.read_text(), 'id,amount\n1,10\n')

    def test_invalid_arguments(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('run_observed.py'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'error')
