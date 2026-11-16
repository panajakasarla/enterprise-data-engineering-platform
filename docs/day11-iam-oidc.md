# Milestone 11 — Least-privilege GitHub OIDC access and Terraform CI

A pre-existing AWS GitHub OIDC provider is trusted by an IAM role with exact repository and branch subject matching and the `sts.amazonaws.com` audience. The role can list only the configured artifact prefix and read/write objects only beneath that prefix in the existing S3 bucket. No static access keys are provisioned.

## Offline validation

```bash
python -m unittest discover -s tests -p 'test_terraform_iam.py' -v
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform init -backend=false
terraform -chdir=infra/terraform validate
```

The GitHub Actions workflow runs these checks without AWS credentials and never executes `terraform apply`. Terraform provider downloads require network access.

## Manual deployment (opt-in)

Create or identify an AWS OIDC provider for `token.actions.githubusercontent.com` with audience `sts.amazonaws.com`. Set `bucket_name` and `github_oidc_provider_arn` via ignored tfvars or environment variables. Review the exact trusted repository/branch and the IAM policy before running `terraform plan`. Use approved credentials and a secure state backend for any manual apply. Store the output role ARN as an Actions variable only when needed by a future protected deployment workflow.

This module does not deploy infrastructure, create an OIDC provider, protect GitHub branches, or prove AWS authorization. Storage and request charges may apply after manual deployment. Do not expose cloud credentials to untrusted pull-request workflows.

Next: protected GitHub environments and an opt-in, manually approved deployment workflow.
