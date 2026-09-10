resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
  tags = var.tags
}

#AWS envoie un lien de confirmation à l'email fourni.
#Les alertes arrivent seulement après avoir cliqué sur le lien.
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
