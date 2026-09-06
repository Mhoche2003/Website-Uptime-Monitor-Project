variable "project_name" {
  description = "Short name used to prefix the table name."
  type        = string
}

variable "tags" {
  description = "Tags applied to the table."
  type        = map(string)
  default     = {}
}
