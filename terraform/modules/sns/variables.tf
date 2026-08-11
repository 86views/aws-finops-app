variable "topic_name" {
  type = string
}

variable "email_subscriptions" {
  description = "List of email addresses to subscribe to the topic"
  type        = list(string)
  default     = []
}

variable "lambda_subscription_arn" {
  description = "Optional Lambda ARN to subscribe (e.g. a Slack-forwarder function)"
  type        = string
  default     = null
}

variable "lambda_subscription_function_name" {
  description = "Required alongside lambda_subscription_arn to grant SNS invoke permission"
  type        = string
  default     = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
