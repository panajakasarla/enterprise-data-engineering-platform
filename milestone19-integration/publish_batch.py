"""Validate a private snapshot and atomically publish accepted CSV batches."""
import os
import shutil
import tempfile
from pathlib import Path
from gate import run


def publish(source, destination, contract, required, key):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('source and destination must differ')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as out:
            temporary = Path(out.name)
            with source.open('rb') as incoming:
                shutil.copyfileobj(incoming, out)
            out.flush()
            os.fsync(out.fileno())
        report = run(temporary, contract, required, key)
        if report['passed']:
            os.replace(temporary, destination)
        return report
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
