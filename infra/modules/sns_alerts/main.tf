resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
  tags = var.tags
}

# AWS emails a confirmation link to this address; alerts only start flowing
# once it's clicked. This is standard SNS behavior, not something Terraform
# can bypass.
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
