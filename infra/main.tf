module "dynamodb_history" {
  source = "./modules/dynamodb_history"

  project_name = var.project_name

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

module "sns_alerts" {
  source = "./modules/sns_alerts"

  project_name = var.project_name
  alert_email  = var.alert_email

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}
