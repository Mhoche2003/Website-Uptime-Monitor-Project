variable "project_name" {
  description = "Short name used to prefix the alarm names."
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic that gets the alarm and the back to normal notifications."
  type        = string
}

variable "lambdas" {
  description = "Lambdas to watch. The key is a short name for the alarms. schedule_seconds is how often EventBridge runs the Lambda."
  type = map(object({
    function_name    = string
    schedule_seconds = number
  }))
}

variable "silent_after_periods" {
  description = "Number of schedule periods in a row without any run before the silent alarm goes off."
  type        = number
  default     = 3
}

variable "tags" {
  description = "Tags applied to the alarms."
  type        = map(string)
  default     = {}
}
