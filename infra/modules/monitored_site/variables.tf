variable "project_name" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "site_marker_text" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
