variable "monitor_name" {
  type    = string
  default = "finops-anomaly-monitor"
}

variable "monitor_type" {
  description = "DIMENSIONAL or CUSTOM"
  type        = string
  default     = "DIMENSIONAL"
}

variable "monitor_dimension" {
  description = "Only used when monitor_type = DIMENSIONAL. e.g. SERVICE, LINKED_ACCOUNT"
  type        = string
  default     = "SERVICE"
}

variable "subscription_name" {
  type    = string
  default = "finops-anomaly-alerts"
}

variable "frequency" {
  description = "DAILY, IMMEDIATE, or WEEKLY"
  type        = string
  default     = "DAILY"
}

variable "threshold_amount" {
  description = "USD — only alert on anomalies above this impact"
  type        = number
  default     = 10
}

variable "sns_topic_arn" {
  description = "SNS topic to publish anomaly alerts to (from the sns module)"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
