output "artifact_bucket_name" {
  description = "Private bucket for future pipeline artifacts"
  value       = aws_s3_bucket.artifacts.id
}

output "artifact_bucket_arn" {
  description = "Bucket ARN for future least-privilege IAM policies"
  value       = aws_s3_bucket.artifacts.arn
}
