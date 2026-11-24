"""Dependency-free CSV schema contract gate."""
import argparse
import csv
import json
from pathlib import Path

def validate(path: Path, contract: dict) -> dict:
    expected = contract["columns"]
    if not isinstance(expected, list) or not expected or len(expected) != len(set(expected)) or not all(isinstance(c, str) and c for c in expected):
        raise ValueError("contract columns must be unique nonempty strings")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        actual = next(reader, [])
        missing = [c for c in expected if c not in actual]
        unexpected = [c for c in actual if c not in expected]
        duplicates = sorted({c for c in actual if actual.count(c) > 1})
        order_changed = not missing and not unexpected and actual != expected
        invalid_width = sum(len(row) != len(actual) for row in reader)
    violations = {"missing_columns": missing, "unexpected_columns": unexpected, "duplicate_columns": duplicates, "column_order_changed": order_changed if contract.get("strict_order", False) else False, "malformed_rows": invalid_width}
    return {"passed": not any(violations.values()), "violations": violations, "expected_columns": expected, "actual_columns": actual}

def main(argv=None):
    parser = argparse.ArgumentParser(description="Fail CI on CSV schema drift")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("contract_file", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.csv_file, json.loads(args.contract_file.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result = {"passed": False, "error": str(exc)}
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    return 0 if result["passed"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
