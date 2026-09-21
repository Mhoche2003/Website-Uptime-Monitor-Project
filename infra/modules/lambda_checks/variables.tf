variable "project_name" {
  type = string
}

variable "dynamodb_table_name" {
  type = string
}

variable "dynamodb_table_arn" {
  type = string
}

variable "sns_topic_arn" {
  type = string
}

variable "site_url" {
  type = string
}

variable "expected_content" {
  type = string
}

variable "latency_threshold_seconds" {
  type    = number
  default = 30
}

variable "tags" {
  type    = map(string)
  default = {}
}
