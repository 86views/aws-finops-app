# Pick ONE path: a single verified email (fastest, no DNS) or a full domain (needs DNS records added manually
# or via your DNS provider's Terraform provider).

resource "aws_ses_email_identity" "this" {
  count = var.email_identity != null ? 1 : 0
  email = var.email_identity
}

resource "aws_ses_domain_identity" "this" {
  count  = var.domain_name != null ? 1 : 0
  domain = var.domain_name
}

resource "aws_ses_domain_dkim" "this" {
  count  = var.domain_name != null && var.enable_dkim ? 1 : 0
  domain = aws_ses_domain_identity.this[0].domain
}
