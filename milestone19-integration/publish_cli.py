"""Publish a validated CSV batch from a command-line job."""
import argparse
import json
from pathlib import Path
from publish_batch import publish


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('contract', type=Path)
    parser.add_argument('--required', nargs='+', required=True)
    parser.add_argument('--key', required=True)
    args = parser.parse_args(argv)
    try:
        contract = json.loads(args.contract.read_text(encoding='utf-8'))
        if not isinstance(contract, dict) or not isinstance(contract.get('columns'), list):
            raise ValueError('contract must contain a columns list')
        report = publish(args.source, args.destination, contract, args.required, args.key)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'published': False, 'error': str(exc)}))
        return 2
    print(json.dumps({'published': report['passed'], 'validation': report}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
