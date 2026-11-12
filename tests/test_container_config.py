"""Fast configuration regression checks; no Docker daemon required."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContainerConfigTests(unittest.TestCase):
    def test_dockerfile_uses_pinned_airflow_and_local_package(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("apache/airflow:2.10.5-python3.11", dockerfile)
        self.assertIn("pip install --no-cache-dir --no-deps .", dockerfile)
        self.assertIn("COPY --chown=airflow:root dags/", dockerfile)

    def test_compose_has_dag_configuration_and_persistent_storage(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        for value in ("command: standalone", "RETAIL_SOURCE:", "RETAIL_DB:",
                      "RETAIL_REPORT:", "RETAIL_MAX_REJECTION_RATIO:",
                      "retail-outputs:", "airflow-metadata:", "airflow-logs:"):
            with self.subTest(value=value):
                self.assertIn(value, compose)

    def test_port_is_bound_to_loopback_only(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8080:8080"', compose)

    def test_smoke_script_checks_dag_imports_and_registration(self):
        script = (ROOT / "scripts/check_airflow_dag.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", script)
        self.assertIn("airflow dags list-import-errors", script)
        self.assertIn("retail_daily_warehouse", script)


if __name__ == "__main__":
    unittest.main()
