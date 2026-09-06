output "history_table_name" {
  description = "Name of the DynamoDB table storing check history."
  value       = module.dynamodb_history.table_name
}

output "history_table_arn" {
  description = "ARN of the DynamoDB table storing check history."
  value       = module.dynamodb_history.table_arn
}
