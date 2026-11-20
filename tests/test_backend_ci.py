"""Offline CI contract checks; no AWS credentials or Terraform installation needed."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/backend-security.yml'

class BackendCIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding='utf-8')

    def test_workflow_triggers_for_parser_and_tests(self):
        for path in ('scripts/check_tf_backend.py', 'tests/test_tf_backend.py', 'tests/test_backend_ci.py'):
            self.assertIn(path, self.workflow)
        self.assertIn('pull_request:', self.workflow)

    def test_permissions_are_read_only(self):
        self.assertIn('contents: read', self.workflow)
        self.assertNotIn('id-token: write', self.workflow)

    def test_negative_fixture_is_fail_closed(self):
        self.assertIn('if python scripts/check_tf_backend.py "$fixture"; then', self.workflow)
        self.assertIn('exit 1', self.workflow)
        self.assertIn('encrypt = false', self.workflow)

    def test_no_cloud_deployment(self):
        for unsafe in ('terraform apply', 'aws configure', 'AWS_ACCESS_KEY_ID', 'terraform destroy'):
            self.assertNotIn(unsafe, self.workflow)

if __name__ == '__main__':
    unittest.main()
