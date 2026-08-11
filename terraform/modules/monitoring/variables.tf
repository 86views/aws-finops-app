variable "dashboard_name" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "ecs_cluster_name" {
  type    = string
  default = null
}

variable "ecs_service_name" {
  type    = string
  default = null
}

variable "alb_arn_suffix" {
  description = "From the alb module's alb_arn_suffix output"
  type        = string
  default     = null
}

variable "target_group_arn_suffix" {
  description = "From the alb module's target_group_arn_suffix output"
  type        = string
  default     = null
}

variable "lambda_function_name" {
  type    = string
  default = null
}
