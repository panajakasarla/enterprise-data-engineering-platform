# Milestone 20: Integrated gate CI

From the repository root, run:

```sh
python -m unittest discover -s milestone19-integration -v
```

The six existing unit tests and five new subprocess tests verify the actual CLI exit status and JSON output, including schema drift, duplicate IDs, malformed contract JSON and missing input. Exit 0 permits processing; exit 1 blocks it. The workflow runs on relevant pull requests with Python 3.11 and 3.12 and read-only repository permissions. No external dependencies or cloud credentials are required. The manual dispatch trigger becomes available when the workflow is on the default branch.

This is an incremental patch on the Milestone 19 branch. The ZIP includes the existing validator snapshots for local reproduction. Canonical imports remain a follow-up after earlier PRs are integrated. Use immutable staged inputs. Local testing does not establish remote CI success or production readiness.
