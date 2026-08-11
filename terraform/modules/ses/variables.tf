variable "email_identity" {
  description = "Single verified sender email (simplest path — no DNS needed). Leave null if using domain_name instead."
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Domain to verify for SES (requires DNS access to add TXT/CNAME records). Leave null if using email_identity instead."
  type        = string
  default     = null
}

variable "enable_dkim" {
  description = "Only applies when domain_name is set"
  type        = bool
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
