"""Validate retail orders from CSV and separate accepted/rejected rows."""
import argparse
import csv
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = ("order_id", "customer_id", "order_date", "product_id", "quantity", "unit_price")

def validate(row, seen):
    missing = [name for name in REQUIRED if not (row.get(name) or "").strip()]
    if missing:
        return "missing: " + ", ".join(missing)
    if row["order_id"].strip() in seen:
        return "duplicate order_id"
    try:
        date.fromisoformat(row["order_date"].strip())
    except ValueError:
        return "invalid order_date"
    try:
        quantity = int(row["quantity"])
        price = Decimal(row["unit_price"])
    except (ValueError, InvalidOperation):
        return "invalid quantity or unit_price"
    if quantity <= 0 or not price.is_finite() or price < 0:
        return "quantity must be positive and price nonnegative"
    seen.add(row["order_id"].strip())
    return None

def ingest(source, output_dir):
    source, output_dir = Path(source), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    accepted = rejected = 0
    seen = set()
    with source.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(name not in reader.fieldnames for name in REQUIRED):
            raise ValueError("CSV is missing required columns")
        fields = list(reader.fieldnames)
        with (output_dir / "valid_orders.csv").open("w", newline="", encoding="utf-8") as good, (output_dir / "rejected_orders.csv").open("w", newline="", encoding="utf-8") as bad:
            good_writer = csv.DictWriter(good, fieldnames=fields)
            bad_writer = csv.DictWriter(bad, fieldnames=fields + ["rejection_reason"])
            good_writer.writeheader()
            bad_writer.writeheader()
            for row in reader:
                reason = validate(row, seen)
                if reason:
                    bad_writer.writerow({**row, "rejection_reason": reason})
                    rejected += 1
                else:
                    good_writer.writerow(row)
                    accepted += 1
    summary = {"accepted": accepted, "rejected": rejected}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    print(json.dumps(ingest(args.source, args.output_dir), indent=2))

if __name__ == "__main__":
    main()
