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
