# Milestone 10 — Terraform-managed private artifact bucket

This module provisions **one private, versioned AWS S3 bucket** for future pipeline reports and artifacts. It is a deployment-ready reference, not a claim that any cloud resource was created.

## Security decisions

- All four S3 public-access-block settings are enabled.
- Bucket owner enforced ownership disables ACL-based access.
- AES-256 server-side encryption is the default; TLS-only bucket policy denies insecure requests.
- Versioning is enabled and `force_destroy = false` protects against accidental destruction of a nonempty bucket.
- Incomplete multipart uploads are aborted after seven days.
- No IAM credentials, access keys, or broad upload permissions are provisioned.

## Validate without deploying

```bash
python -m unittest discover -s tests -p 'test_terraform_security.py' -v
cd infra/terraform
terraform init -backend=false
terraform fmt -check
terraform validate
terraform plan -var='bucket_name=replace-with-globally-unique-name'
```

The final `plan` requires AWS credentials and may contact AWS. Do not run `apply` without reviewing cost, IAM permissions, organization policy, and resource naming. Configure a secure remote Terraform backend before team use; local state can contain sensitive metadata. No Terraform state or credentials should be committed.

## Limits and next step

This is a foundational S3 storage module, **not** an Airflow deployment, alert notification service, or automated cloud pipeline. AWS storage and request charges may apply after deployment. Next add scoped IAM roles and an optional alert delivery adapter with idempotency and secret management.
