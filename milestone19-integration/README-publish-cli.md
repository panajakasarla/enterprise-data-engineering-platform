# Milestone 22: Scheduler-ready publication CLI

Run from `milestone19-integration` with Python 3.11+ (standard library only).

```sh
printf 'id,amount\n1,10\n' > input.csv
printf '{"columns":["id","amount"]}\n' > contract.json
python publish_cli.py input.csv curated.csv contract.json --required amount --key id
python -m unittest discover -v
```

The command prints a JSON report to stdout. Exit 0 means published, 1 means the quality gate rejected the batch, and 2 means an input/configuration or publication exception was caught. The existing gate can also report read/validation errors as exit 1. Argument parsing errors use argparse's exit 2 and stderr. A rejected batch preserves the previous destination. The destination directory must exist. This wraps the local atomic publisher; it does not implement S3, scheduler retries, concurrent-writer locking, or durable audit storage. Use exit codes in a scheduler to prevent downstream processing on failure.
