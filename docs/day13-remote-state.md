# Milestone 13 — Terraform remote-state readiness

Terraform state can contain secrets. This milestone adds an offline static safety check, **not** an AWS deployment.

## Manual bootstrap
1. Create a dedicated private S3 state bucket with versioning, encryption, public-access blocking and TLS enforcement using a separately managed bootstrap process.
2. Restrict the deployment role to the relevant state object and lockfile permissions.
3. Create an untracked `infra/terraform/backend.hcl` with `bucket`, `key`, `region`, `encrypt = true`, and `use_lockfile = true`. Use a distinct key per environment.
4. Run `python scripts/check_tf_backend.py infra/terraform/backend.hcl` and `python -m unittest discover -s tests -p 'test_tf_backend.py' -v`.
5. After independently confirming bucket/IAM controls, configure the Terraform root `backend "s3" {}` and migrate using `terraform -chdir=infra/terraform init -backend-config=backend.hcl -migrate-state` with a secure state backup.
6. Test locking, restoration, and access denial in a sandbox before any production usage.

## Limitations
The validator handles only simple literal HCL assignments. It does not verify AWS bucket existence, bucket policy, permissions, actual encryption, locking, or Terraform version. Native S3 lockfiles require a compatible Terraform version. Passing static checks is not deployment approval. Never commit state, credentials, or backend.hcl.
