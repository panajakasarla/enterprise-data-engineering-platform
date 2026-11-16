variable "github_oidc_provider_arn" {
  description = "ARN of an existing AWS IAM OIDC provider for token.actions.githubusercontent.com"
  type        = string
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:oidc-provider/token\\.actions\\.githubusercontent\\.com$", var.github_oidc_provider_arn))
    error_message = "Provide the ARN of the existing GitHub Actions OIDC provider."
  }
}

variable "github_repository" {
  description = "Exact GitHub owner/repository allowed to assume the role"
  type        = string
  default     = "panajakasarla/enterprise-data-engineering-platform"
  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "Expected owner/repository."
  }
}

variable "github_deploy_branch" {
  description = "Only this GitHub branch may assume the role (normally main)"
  type        = string
  default     = "main"
  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9_./-]*$", var.github_deploy_branch)) && !can(regex("\\.\\.|//", var.github_deploy_branch))
    error_message = "Provide a valid explicit branch name."
  }
}

variable "artifact_prefix" {
  description = "Single S3 object-key prefix the role can read/write"
  type        = string
  default     = "pipeline-artifacts"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9/_-]*[a-z0-9]$", var.artifact_prefix)) && !can(regex("//|\\.\\.", var.artifact_prefix))
    error_message = "Use a nonempty, safe lowercase artifact prefix."
  }
}
