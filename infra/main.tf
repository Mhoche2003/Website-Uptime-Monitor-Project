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

module "monitored_site" {
  source = "./modules/monitored_site"

  project_name     = var.project_name
  aws_region       = var.aws_region
  site_marker_text = var.site_marker_text

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

module "lambda_checks" {
  source = "./modules/lambda_checks"

  project_name              = var.project_name
  dynamodb_table_name       = module.dynamodb_history.table_name
  dynamodb_table_arn        = module.dynamodb_history.table_arn
  sns_topic_arn             = module.sns_alerts.topic_arn
  site_url                  = module.monitored_site.website_endpoint
  expected_content          = var.site_marker_text
  latency_threshold_seconds = var.latency_threshold_seconds

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

module "s3_dashboard" {
  source = "./modules/s3_dashboard"

  project_name = var.project_name
  aws_region   = var.aws_region

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

module "aggregate_metrics" {
  source = "./modules/aggregate_metrics"

  project_name          = var.project_name
  dynamodb_table_name   = module.dynamodb_history.table_name
  dynamodb_table_arn    = module.dynamodb_history.table_arn
  dashboard_bucket_name = module.s3_dashboard.bucket_name
  dashboard_bucket_arn  = module.s3_dashboard.bucket_arn

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}
