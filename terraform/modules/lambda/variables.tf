variable "function_name" {
  type = string
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "handler" {
  type    = string
  default = "handler.lambda_handler"
}

variable "role_arn" {
  description = "IAM role ARN for the Lambda (from existing iam module)"
  type        = string
}

variable "source_dir" {
  description = "Local directory containing the Lambda source code to zip"
  type        = string
}

variable "timeout" {
  description = "Seconds — keep modest, free tier gives 400,000 GB-seconds/month"
  type        = number
  default     = 30
}

variable "memory_size" {
  type    = number
  default = 128
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "log_retention_days" {
  type    = number
  default = 7
}

variable "tags" {
  type    = map(string)
  default = {}
}
