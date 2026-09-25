variable "project_name" {
  description = "Short name used to prefix and tag resources."
  type        = string
}

variable "aws_region" {
  description = "AWS region where the project's resources are created."
  type        = string
}

variable "deployer_iam_user_name" {
  description = "Name of the existing IAM user that runs Terraform for this project. Set in terraform.tfvars (gitignored)."
  type        = string
}

variable "tags" {
  description = "Common tags applied to resources."
  type        = map(string)
  default     = {}
}
