"""Run schema checks before row quality checks on a staged CSV batch."""
import argparse
import csv
import json
from pathlib import Path
from schema_contract import validate
from quality import validate_csv


def run(path, contract, required, key):
    try:
        schema = validate(path, contract)
        if not schema['passed']:
            return {'passed': False, 'schema': schema, 'quality': None}
        quality = validate_csv(path, required, key)
        return {'passed': quality['passed'], 'schema': schema, 'quality': quality}
    except (OSError, ValueError, TypeError, KeyError, csv.Error) as exc:
        return {'passed': False, 'error': str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('contract', type=Path)
    parser.add_argument('--required', nargs='+', required=True)
    parser.add_argument('--key', required=True)
    args = parser.parse_args()
    try:
        result = run(args.batch, json.loads(args.contract.read_text()), args.required, args.key)
    except (OSError, ValueError) as exc:
        result = {'passed': False, 'error': str(exc)}
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
