# Milestone 23: ETL run observability

From `milestone19-integration`, using Python 3.11+:

```sh
printf 'id,amount\n1,10\n' > input.csv
printf '{"columns":["id","amount"]}\n' > contract.json
python run_observed.py input.csv curated.csv contract.json --required amount --key id
python -m unittest discover -v
```

Each invocation emits one JSON event with a unique run ID, elapsed milliseconds, status, exit code and nested validation report. Exit 0 publishes, 1 rejects, 2 indicates an error. The wrapper preserves the existing CLI's outcome classification; validation read errors may be classified as rejection. Invalid CLI arguments produce a generic error event. The nested report may contain sensitive values or paths; review/redact before shipping to centralized logging. No external monitoring, timeout, retries or cloud deployment is included.
