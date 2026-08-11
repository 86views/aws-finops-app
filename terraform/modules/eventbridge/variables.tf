variable "rule_name" {
  type = string
}

variable "description" {
  type    = string
  default = "Scheduled trigger for FinOps report generation"
}

variable "schedule_expression" {
  description = "e.g. rate(1 day) or cron(0 7 * * ? *)"
  type        = string
  default     = "rate(1 day)"
}

variable "lambda_function_arn" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "input_json" {
  description = "Optional static JSON payload passed to the Lambda target"
  type        = string
  default     = null
}

variable "enabled" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
