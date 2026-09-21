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

output "monitored_site_url" {
  description = "URL of the monitored test site."
  value       = module.monitored_site.website_endpoint
}

output "checks_schedule_rule_name" {
  description = "Name of the EventBridge rule scheduling the checks."
  value       = module.lambda_checks.checks_schedule_rule_name
}

output "dashboard_url" {
  description = "URL of the dashboard site."
  value       = module.s3_dashboard.website_endpoint
}

output "aggregation_schedule_rule_name" {
  description = "Name of the EventBridge rule scheduling the metrics aggregation."
  value       = module.aggregate_metrics.aggregation_schedule_rule_name
}
