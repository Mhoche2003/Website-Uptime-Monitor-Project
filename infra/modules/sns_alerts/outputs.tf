output "topic_arn" {
  description = "ARN of the SNS topic, used by lambda_checks to publish alerts."
  value       = aws_sns_topic.alerts.arn
}
