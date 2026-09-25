variable "aws_region" {
  description = "AWS region where the project's resources are created."
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Short name used to prefix and tag resources."
  type        = string
  default     = "website-uptime-monitor"
}

variable "alert_email" {
  description = "Email address subscribed to alert notifications. Set in terraform.tfvars (gitignored), never with a default here."
  type        = string
}

variable "site_marker_text" {
  description = "Text the content check looks for on the monitored site's page."
  type        = string
  default     = "Website Uptime Monitor - test page"
}

variable "latency_threshold_seconds" {
  description = "Latency threshold in seconds above which the latency check fails."
  type        = number
  default     = 30
}

variable "deployer_iam_user_name" {
  description = "Name of the existing IAM user that runs Terraform for this project. Set in terraform.tfvars (gitignored), never with a default here."
  type        = string
}
