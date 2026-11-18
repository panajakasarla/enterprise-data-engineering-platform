"""Offline tests for Terraform backend config safety."""
import unittest
from scripts.check_tf_backend import validate

VALID = 'bucket = "portfolio-state-example"\nkey = "dev/platform.tfstate"\nregion = "us-east-1"\nencrypt = true\nuse_lockfile = true\n'

class BackendValidationTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(VALID), [])
    def test_missing_lock(self):
        self.assertIn("missing field: use_lockfile", validate(VALID.replace("use_lockfile = true", "")))
    def test_disabled_encryption(self):
        self.assertIn("encrypt must be true", validate(VALID.replace("encrypt = true", "encrypt = false")))
    def test_embedded_credentials(self):
        self.assertIn("forbidden field: access_key", validate(VALID + 'access_key = "bad"\n'))
    def test_traversal(self):
        self.assertTrue(any("traversal" in x for x in validate(VALID.replace("dev/platform.tfstate", "../platform.tfstate"))))
    def test_duplicate(self):
        self.assertIn("duplicate field: region", validate(VALID + 'region = "us-west-2"\n'))
    def test_unparsed(self):
        self.assertTrue(any("unsupported" in x for x in validate(VALID + 'foo = ${bar}\n')))

if __name__ == "__main__":
    unittest.main()
