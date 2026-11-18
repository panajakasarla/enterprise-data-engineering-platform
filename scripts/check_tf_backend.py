"""Offline, fail-closed check for a simple Terraform S3 backend config."""
import argparse
import re
import sys
from pathlib import Path

REQUIRED = ("bucket", "key", "region", "encrypt", "use_lockfile")

def validate(text: str) -> list[str]:
    errors, fields = [], {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r'([a-z_]+)\s*=\s*("[^"]*"|true|false)', line)
        if not match:
            errors.append(f"line {n}: unsupported backend syntax")
            continue
        key, value = match.groups()
        if key in fields:
            errors.append(f"duplicate field: {key}")
        fields[key] = value
    errors += [f"missing field: {key}" for key in REQUIRED if key not in fields]
    for key in ("bucket", "key", "region"):
        if key in fields and (not fields[key].startswith('"') or not fields[key][1:-1].strip()):
            errors.append(f"{key} must be a nonempty quoted string")
    for key in ("encrypt", "use_lockfile"):
        if fields.get(key) != "true":
            errors.append(f"{key} must be true")
    if fields.get("key", "").startswith('"'):
        path = fields["key"][1:-1]
        if path.startswith("/") or ".." in path.split("/") or not path.endswith(".tfstate"):
            errors.append("key must be a relative .tfstate path without traversal")
    forbidden = {"access_key", "secret_key", "token", "profile", "skip_credentials_validation"}
    errors += [f"forbidden field: {key}" for key in sorted(forbidden & fields.keys())]
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.config.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"cannot read config: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Static checks passed; AWS resources and permissions remain unverified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
