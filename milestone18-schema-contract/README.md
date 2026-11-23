# Milestone 18 — CSV schema contract gate

Dependency-free, fail-closed schema drift gate for batch ingestion. Complements Milestone 17 row-level quality checks.

## Run

```bash
python milestone18-schema-contract/src/schema_contract.py milestone18-schema-contract/sample.csv milestone18-schema-contract/contract.json --report schema-report.json
python -m unittest discover -s milestone18-schema-contract/tests -v
```

Exit code 0 indicates pass; 2 indicates schema drift or invalid configuration. JSON output reports missing, unexpected, duplicate, reordered (if strict_order), and malformed-width rows. UTF-8 BOM is accepted.

## Integration and limitations

Run this check before row-level validation; reject nonzero results and retain reports as pipeline artifacts. Contract updates require review. This validates headers and row widths, not column types, semantic quality, schema evolution, or nested formats. No cloud resources deployed.
