module "dynamodb_history" {
  source = "./modules/dynamodb_history"

  project_name = var.project_name

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}
