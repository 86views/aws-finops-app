variable "project" {
  type        = string
  description = "Project name prefix"
}

variable "github_org" {
  type        = string
  description = "GitHub organisation or user"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
}

variable "state_bucket" {
  type        = string
  description = "S3 bucket used for Terraform state"
}

variable "reports_bucket" {
  type        = string
  description = "S3 bucket for generated cost reports"
}

variable "create_oidc_provider" {
  type        = bool
  default     = true
  description = "Create the GitHub OIDC provider (set false if already exists)"
}

variable "existing_oidc_provider_arn" {
  type        = string
  default     = ""
  description = "ARN of existing GitHub OIDC provider"
}

variable "tags" {
  type    = map(string)
  default = {}
}


variable "slack_webhook_url" {
  type        = string
  default     = null
  sensitive   = true
  description = "Slack incoming webhook URL for cost alerts, stored as SSM SecureString. Leave null to skip Slack provisioning entirely."
}