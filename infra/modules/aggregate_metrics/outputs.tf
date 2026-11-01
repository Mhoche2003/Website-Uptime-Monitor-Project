output "aggregation_schedule_rule_name" {
  value = aws_cloudwatch_event_rule.aggregation_schedule.name
}

output "aggregate_metrics_function_name" {
  value = aws_lambda_function.aggregate_metrics.function_name
}
