# enterprise-data-engineering-platform

## Milestone 17 — Data quality gate

Dependency-free CSV batch checks for required columns, unique keys, empty batches and null thresholds. Runs in GitHub Actions.

```bash
python -m unittest discover -s tests -v
python -m src.pipeline_guard.quality examples/orders.csv --required id amount --unique-key id --report artifacts/quality.json
```

See [documentation](docs/MILESTONE17.md). Earlier milestone branches remain separate pending integration.
