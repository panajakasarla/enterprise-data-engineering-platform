import argparse
import csv
import json
from pathlib import Path

def validate_csv(path, required_columns, unique_key, max_null_fraction=0.0):
    if not 0 <= max_null_fraction <= 1:
        raise ValueError("max_null_fraction must be between 0 and 1")
    required = list(dict.fromkeys([*required_columns, unique_key]))
    issues = []
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = [col for col in required if col not in (reader.fieldnames or [])]
        if missing:
            return {"passed": False, "rows": 0, "issues": ["missing columns: " + ", ".join(missing)]}
        seen, nulls, count = set(), dict.fromkeys(required, 0), 0
        for row in reader:
            count += 1
            for col in required:
                if row[col] is None or not row[col].strip():
                    nulls[col] += 1
            key = row[unique_key]
            if key and key.strip():
                if key in seen:
                    issues.append(f"duplicate {unique_key} at row {count + 1}")
                seen.add(key)
    if not count:
        issues.append("empty batch")
    for col, n in nulls.items():
        if count and n / count > max_null_fraction:
            issues.append(f"null threshold exceeded for {col}: {n}/{count}")
    return {"passed": not issues, "rows": count, "issues": issues}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_path", type=Path)
    p.add_argument("--required", nargs="+", required=True)
    p.add_argument("--unique-key", required=True)
    p.add_argument("--max-null-fraction", type=float, default=0.0)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    result = validate_csv(a.csv_path, a.required, a.unique_key, a.max_null_fraction)
    output = json.dumps(result, indent=2)
    print(output)
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(output + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
