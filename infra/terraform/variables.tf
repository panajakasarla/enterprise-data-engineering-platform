variable "aws_region" {
  description = "AWS region for the private artifact bucket"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name; choose a non-sensitive value"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name)) && !can(regex("\\.\\.", var.bucket_name))
    error_message = "Use a valid lowercase S3 bucket name (3-63 characters)."
  }
}

variable "environment" {
  description = "Environment label for cost attribution"
  type        = string
  default     = "dev"
}
