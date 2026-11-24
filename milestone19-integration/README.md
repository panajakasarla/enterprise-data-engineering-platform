# Integrated CSV quality gate (Milestone 19)

Run `python -m unittest -v` from this directory. Run `python gate.py batch.csv contract.json --required amount --key id` with a CSV containing `id,amount` and a JSON contract such as `{"columns":["id","amount"]}`. Exit 0 permits downstream processing; exit 1 blocks it. Redirect stdout to a JSON report if needed.

The schema stage runs before the row quality stage. A schema failure skips row checks. This standalone integration includes snapshots of the Milestone 17 and 18 validators for reproducibility; replace these copies with imports from the canonical modules once both PRs are merged. Use immutable staged input because the two validators read the file separately. This is a local CSV gate, not a distributed Spark implementation or cloud deployment.
