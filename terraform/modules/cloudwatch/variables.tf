variable "project_name" {
  type = string
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "log_group_names" {
  description = "Log groups to create (e.g. ECS app log group). Lambda/module-owned log groups shouldn't be duplicated here."
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "Keep short — CloudWatch Logs free tier is 5GB ingestion + storage/month"
  type        = number
  default     = 7
}

variable "enable_billing_alarm" {
  description = "Billing metric data only exists in us-east-1 — alarm must be created there"
  type        = bool
  default     = true
}

variable "billing_alarm_threshold_usd" {
  type    = number
  default = 5
}

variable "alarm_sns_topic_arn" {
  description = "Where billing/ECS alarms notify (from the sns module)"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Optional — enables CPU/Memory utilization alarms on the ECS service"
  type        = string
  default     = null
}

variable "ecs_service_name" {
  type    = string
  default = null
}

variable "ecs_cpu_alarm_threshold" {
  type    = number
  default = 80
}

variable "tags" {
  type    = map(string)
  default = {}
}
