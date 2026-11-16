"""Offline regression checks for the scoped GitHub OIDC IAM module."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "infra" / "terraform"


class IamSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iam = (ROOT / "iam.tf").read_text(encoding="utf-8")
        cls.variables = (ROOT / "iam_variables.tf").read_text(encoding="utf-8")
        cls.outputs = (ROOT / "iam_outputs.tf").read_text(encoding="utf-8")

    def test_oidc_only_and_audience(self):
        self.assertIn('"sts:AssumeRoleWithWebIdentity"', self.iam)
        self.assertIn('"token.actions.githubusercontent.com:aud"', self.iam)
        self.assertIn('["sts.amazonaws.com"]', self.iam)
        self.assertNotIn('"sts:AssumeRole"', self.iam)

    def test_exact_repo_and_branch_subject(self):
        self.assertIn('"token.actions.githubusercontent.com:sub"', self.iam)
        self.assertIn('repo:${var.github_repository}:ref:refs/heads/${var.github_deploy_branch}', self.iam)
        self.assertIn('default     = "main"', self.variables)

    def test_scoped_s3_actions(self):
        self.assertIn('"s3:ListBucket"', self.iam)
        self.assertIn('"s3:GetObject", "s3:PutObject"', self.iam)
        self.assertIn('"${aws_s3_bucket.artifacts.arn}/${var.artifact_prefix}/*"', self.iam)
        self.assertIn('variable = "s3:prefix"', self.iam)
        self.assertNotIn('"s3:*"', self.iam)

    def test_no_access_keys_or_inline_credentials(self):
        for forbidden in ('aws_access_key_id', 'aws_secret_access_key', 'AWS_SECRET_ACCESS_KEY'):
            self.assertNotIn(forbidden, self.iam + self.variables)
        self.assertIn('artifact_writer_role_arn', self.outputs)

    def test_explicit_existing_provider(self):
        self.assertIn('var.github_oidc_provider_arn', self.iam)
        self.assertIn('oidc-provider/token', self.variables)
        self.assertNotIn('resource "aws_iam_openid_connect_provider"', self.iam)


if __name__ == "__main__":
    unittest.main()
