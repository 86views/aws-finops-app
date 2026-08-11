variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "aws-finops"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "github_org" {
  type        = string
  description = "GitHub organisation or username"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
  default     = "aws-finops"
}

variable "state_bucket" {
  type        = string
  description = "Existing S3 bucket for Terraform state"
  default     = "placeholder-tfstate"
}

variable "create_oidc_provider" {
  type    = bool
  default = true
}

variable "existing_oidc_provider_arn" {
  type    = string
  default = ""
}

variable "monthly_budget_limit" {
  type    = number
  default = 500
}

variable "budget_alert_threshold" {
  type    = number
  default = 80
}

variable "existing_anomaly_monitor_arn" {
  description = "ARN of an existing Cost Anomaly Detection monitor (optional)"
  type        = string
  default     = null
}

variable "anomaly_impact_threshold" {
  type    = number
  default = 50
}

variable "alert_emails" {
  type = list(string)
}


variable "slack_webhook_url" {
  type        = string
  default     = null
  sensitive   = true
  description = "Slack incoming webhook URL for cost alerts, stored as SSM SecureString. Leave null to skip Slack provisioning entirely."
}

# ── Networking ────────────────────────────────────────────────────────────
variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

# ── Container / ECS ───────────────────────────────────────────────────────
variable "container_port" {
  type    = number
  default = 8000
}

variable "container_image_tag" {
  description = "Tag to deploy. CI pushes new tags; bump this (or wire to CI output) to roll out"
  type        = string
  default     = "latest"
}

variable "ecs_cpu" {
  type    = number
  default = 256
}

variable "ecs_memory" {
  type    = number
  default = 512
}

variable "ecs_desired_count" {
  description = "Kept at 1 for free-tier usage"
  type        = number
  default     = 1
}

variable "enable_https" {
  type    = bool
  default = false
}

# ── SES ───────────────────────────────────────────────────────────────────
variable "api_key" {
  description = "Shared secret for the app's /api/* routes. Change from the default before deploying."
  type        = string
  default     = "change-me-in-production"
  sensitive   = true
}

variable "ses_verified_email" {
  description = "Single verified sender email for SES (sandbox-friendly, no DNS needed)"
  type        = string
}

# ── CloudWatch / monitoring ─────────────────────────────────────────────
variable "log_retention_days" {
  type    = number
  default = 7
}

variable "billing_alarm_threshold_usd" {
  type    = number
  default = 5
}

# ── Scheduler (Lambda + EventBridge) ────────────────────────────────────
# The app already runs its own internal APScheduler (see app/main.py) whenever the ECS
# task is up. This external scheduler is OFF by default — it's an optional decoupled path
# that calls the app's HTTP API instead of relying on the container's in-process scheduler
# (useful if you ever move off a single always-on task). Flip it on if you want it.
variable "enable_external_scheduler" {
  type    = bool
  default = false
}

variable "daily_report_schedule" {
  type    = string
  default = "cron(0 8 * * ? *)"
}

variable "weekly_report_schedule" {
  type    = string
  default = "cron(0 9 ? * MON *)"
}
