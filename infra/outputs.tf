output "history_table_name" {
  description = "Name of the DynamoDB table storing check history."
  value       = module.dynamodb_history.table_name
}

output "history_table_arn" {
  description = "ARN of the DynamoDB table storing check history."
  value       = module.dynamodb_history.table_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic used for alerts."
  value       = module.sns_alerts.topic_arn
}
