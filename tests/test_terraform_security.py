"""Offline guardrails for the Terraform S3 reference module."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "infra" / "terraform"


class TerraformSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "main.tf").read_text(encoding="utf-8")
        cls.versions = (ROOT / "versions.tf").read_text(encoding="utf-8")
        cls.variables = (ROOT / "variables.tf").read_text(encoding="utf-8")

    def test_provider_version_pinned_to_major(self):
        self.assertIn('version = "~> 5.0"', self.versions)

    def test_public_access_blocked(self):
        for field in ("block_public_acls", "block_public_policy",
                      "ignore_public_acls", "restrict_public_buckets"):
            self.assertRegex(self.main, rf"{field}\\s*=\\s*true")

    def test_encryption_and_versioning(self):
        self.assertIn('sse_algorithm = "AES256"', self.main)
        self.assertIn('status = "Enabled"', self.main)
        self.assertIn("aws_s3_bucket_versioning", self.main)

    def test_tls_only_and_no_force_destroy(self):
        self.assertIn('"aws:SecureTransport" = "false"', self.main)
        self.assertIn("force_destroy = false", self.main)

    def test_bucket_name_is_required(self):
        self.assertIn('variable "bucket_name"', self.variables)
        self.assertNotIn('default     =', self.variables.split('variable "bucket_name"')[1].split("variable ")[0])


if __name__ == "__main__":
    unittest.main()
