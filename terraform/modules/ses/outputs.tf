output "email_identity_arn" {
  value = var.email_identity != null ? aws_ses_email_identity.this[0].arn : null
}

output "domain_identity_arn" {
  value = var.domain_name != null ? aws_ses_domain_identity.this[0].arn : null
}

output "domain_verification_token" {
  description = "Add as a TXT record at _amazonses.<domain> to verify"
  value       = var.domain_name != null ? aws_ses_domain_identity.this[0].verification_token : null
}

output "dkim_tokens" {
  description = "Add as CNAME records: <token>._domainkey.<domain>"
  value       = var.domain_name != null && var.enable_dkim ? aws_ses_domain_dkim.this[0].dkim_tokens : null
}
