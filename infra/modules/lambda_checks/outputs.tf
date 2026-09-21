output "check_availability_function_name" {
  value = aws_lambda_function.check_availability.function_name
}

output "check_latency_function_name" {
  value = aws_lambda_function.check_latency.function_name
}

output "check_content_function_name" {
  value = aws_lambda_function.check_content.function_name
}

output "checks_schedule_rule_name" {
  value = aws_cloudwatch_event_rule.checks_schedule.name
}
