"""Emit a scheduler-friendly JSON event around the publication CLI."""
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    start = time.monotonic()
    event = {'run_id': str(uuid.uuid4()), 'event': 'csv_publication'}
    try:
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('publish_cli.py')), *args], capture_output=True, text=True)
        code = result.returncode
        event['report'] = json.loads(result.stdout)
        if not isinstance(event['report'], dict):
            raise ValueError('expected JSON object')
    except (OSError, ValueError):
        code = 2
        event['report'] = {'error': 'publication command did not return a JSON object'}
    event['exit_code'] = code
    event['status'] = {0: 'published', 1: 'rejected'}.get(code, 'error')
    event['duration_ms'] = round((time.monotonic() - start) * 1000)
    print(json.dumps(event))
    return code if code in (0, 1, 2) else 2


if __name__ == '__main__':
    raise SystemExit(main())
