import tempfile
import unittest
from pathlib import Path
from publish_batch import publish


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'input.csv'
        self.dest = Path(self.tmp.name) / 'curated.csv'
        self.dest.write_text('previous')

    def invoke(self, content):
        self.source.write_text(content)
        return publish(self.source, self.dest, {'columns': ['id', 'amount']}, ['amount'], 'id')

    def test_valid_replaces(self):
        self.assertTrue(self.invoke('id,amount\n1,10\n')['passed'])
        self.assertEqual(self.dest.read_text(), self.source.read_text())

    def test_invalid_preserves(self):
        self.assertFalse(self.invoke('id,amount\n1,10\n1,20\n')['passed'])
        self.assertEqual(self.dest.read_text(), 'previous')
        self.assertEqual(len(list(self.dest.parent.iterdir())), 2)

    def test_missing_preserves(self):
        with self.assertRaises(FileNotFoundError):
            publish(self.source, self.dest, {}, [], 'id')
        self.assertEqual(list(self.dest.parent.iterdir()), [self.dest])

    def test_same_path_rejected(self):
        with self.assertRaises(ValueError):
            publish(self.dest, self.dest, {}, [], 'id')
        self.assertEqual(self.dest.read_text(), 'previous')
