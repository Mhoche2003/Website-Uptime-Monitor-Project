variable "project_name" {
  description = "Short name used to prefix the topic name."
  type        = string
}

variable "alert_email" {
  description = "Email address subscribed to alert notifications."
  type        = string
}

variable "tags" {
  description = "Tags applied to the topic."
  type        = map(string)
  default     = {}
}
