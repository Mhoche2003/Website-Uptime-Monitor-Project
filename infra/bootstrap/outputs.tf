output "state_bucket_name" {
  description = "Name of the S3 bucket holding the Terraform state. Used in the backend config of infra/."
  value       = aws_s3_bucket.terraform_state.bucket
}

output "lock_table_name" {
  description = "Name of the DynamoDB table used for state locking. Used in the backend config of infra/."
  value       = aws_dynamodb_table.terraform_locks.name
}
