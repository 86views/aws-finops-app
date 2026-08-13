aws_region  = "us-east-1"
project     = "aws-finops-app"
environment = "dev"

github_org  = "86views"
github_repo = "aws-finops-app"
github_owner_id = "21120209"
github_repo_id  = "1327623911"

create_oidc_provider = false
existing_oidc_provider_arn = "arn:aws:iam::173331852212:oidc-provider/token.actions.githubusercontent.com"

monthly_budget_limit     = 500
budget_alert_threshold   = 80
anomaly_impact_threshold = 50
existing_anomaly_monitor_arn = "arn:aws:ce::173331852212:anomalymonitor/ef02443a-c76e-4f42-83c5-c85ab06e35dc"



ses_verified_email = "oluleye.oluseun@gmail.com"
alert_emails = ["oluleye.oluseun@gmail.com"]