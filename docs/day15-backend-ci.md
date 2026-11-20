# Milestone 15 — Terraform backend security in CI

This incremental milestone adds a **read-only, offline** GitHub Actions check for the S3 backend validator introduced in Milestone 13. It runs when the validator, its tests, or this workflow changes. It tests both valid/invalid backend syntax and a deliberately insecure temporary configuration that must fail validation.

## Local verification

```bash
python -m unittest discover -s tests -p 'test_tf_backend.py' -v
python -m unittest discover -s tests -p 'test_backend_ci.py' -v
```

## Security and deployment limits

The workflow requests only `contents: read`. It does not request OIDC tokens, AWS credentials, or execute Terraform `apply`. The temporary unsafe fixture is generated during CI and deleted at the end of the step. No real `backend.hcl`, Terraform state, or secrets are uploaded. Static checks do **not** prove AWS bucket security, state locking, or IAM permissions. Review GitHub Actions results before merging stacked pull requests.

## Next

Run the workflow on GitHub, fix any failures, then review and merge stacked PRs in dependency order. Separately evaluate a secure sandbox for remote state integration tests.
