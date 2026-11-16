output "artifact_writer_role_arn" {
  description = "GitHub OIDC role ARN; configure as an Actions variable after applying"
  value       = aws_iam_role.artifact_writer.arn
}
