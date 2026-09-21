variable "project_name" {
  type = string
}

variable "dynamodb_table_name" {
  type = string
}

variable "dynamodb_table_arn" {
  type = string
}

variable "dashboard_bucket_name" {
  type = string
}

variable "dashboard_bucket_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
