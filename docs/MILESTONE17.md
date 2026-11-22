# Milestone 17 — CSV data quality promotion gate

Validates required columns, unique business keys, empty batches, and null fractions before promoting staging data. Emits JSON and exits nonzero on invalid data.

Run `python -m unittest discover -s tests -v` and `python -m src.pipeline_guard.quality examples/orders.csv --required id amount --unique-key id --report artifacts/quality.json`.

This is a single-file, in-memory gate; large data requires distributed uniqueness checks. No AWS deployment is performed.
