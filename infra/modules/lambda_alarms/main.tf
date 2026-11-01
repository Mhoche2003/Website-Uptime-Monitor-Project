# Crash alarm: the Lambda runs but ends with an error
resource "aws_cloudwatch_metric_alarm" "errors" {
  for_each = var.lambdas

  alarm_name        = "${var.project_name}-${each.key}-errors"
  alarm_description = "${each.value.function_name} ended with an error"

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  dimensions = {
    FunctionName = each.value.function_name
  }

  statistic           = "Sum"
  period              = each.value.schedule_seconds
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"

  # No data means no run so there is no error to report
  treat_missing_data = "notBreaching"

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = var.tags
}

# Silent alarm: the Lambda does not run at all (for example EventBridge is broken)
resource "aws_cloudwatch_metric_alarm" "silent" {
  for_each = var.lambdas

  alarm_name        = "${var.project_name}-${each.key}-silent"
  alarm_description = "${each.value.function_name} did not run for ${var.silent_after_periods} periods in a row"

  namespace   = "AWS/Lambda"
  metric_name = "Invocations"
  dimensions = {
    FunctionName = each.value.function_name
  }

  statistic          = "Sum"
  period             = each.value.schedule_seconds
  evaluation_periods = var.silent_after_periods
  # Every period must be empty. One empty period alone can just be a timing jitter
  datapoints_to_alarm = var.silent_after_periods
  threshold           = 1
  comparison_operator = "LessThanThreshold"

  # No data at all is what we are looking for
  treat_missing_data = "breaching"

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = var.tags
}
