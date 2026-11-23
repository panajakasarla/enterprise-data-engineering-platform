# enterprise-data-engineering-platform

## Milestone 18 — CSV schema contract gate

The standalone `milestone18-schema-contract/` module detects CSV schema drift before batch ingestion. Run:

```bash
python -m unittest discover -s milestone18-schema-contract/tests -v
python milestone18-schema-contract/src/schema_contract.py milestone18-schema-contract/sample.csv milestone18-schema-contract/contract.json
```

See [Milestone 18 README](milestone18-schema-contract/README.md) for contract rules, JSON reports, integration, and limitations. Earlier milestones are pending review in separate pull requests.
