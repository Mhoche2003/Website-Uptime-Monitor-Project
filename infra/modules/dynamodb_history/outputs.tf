output "table_name" {
  description = "Name of the DynamoDB table storing check history."
  value       = aws_dynamodb_table.history.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table, used to scope Lambda IAM permissions."
  value       = aws_dynamodb_table.history.arn
}
