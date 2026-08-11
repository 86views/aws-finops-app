variable "project" {
  type = string
}

variable "monthly_limit" {
  type        = number
  description = "Monthly cost budget in USD"
  default     = 1000
}

variable "alert_threshold_pct" {
  type        = number
  default     = 80
  description = "Percentage of budget at which to alert"
}

variable "existing_anomaly_monitor_arn" {
  description = "ARN of an existing anomaly monitor to use instead of creating a new one"
  type        = string
  default     = null
}

variable "anomaly_impact_threshold" {
  type        = number
  default     = 50
  description = "Minimum absolute impact (USD) to trigger anomaly alert"
}

variable "subscriber_emails" {
  type        = list(string)
  description = "Email addresses for budget & anomaly notifications"
}

variable "tags" {
  type    = map(string)
  default = {}
}
