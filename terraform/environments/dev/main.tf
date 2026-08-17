

locals {
  # Strip any trailing "-${var.environment}" if present in var.project, 
  # or simply use var.project if it already reflects the full project-env naming:
  name_prefix = endswith(var.project, "-${var.environment}") ? var.project : "${var.project}-${var.environment}"

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

module "s3_reports" {
  source         = "../../modules/s3"
  bucket_name    = "${local.name_prefix}-reports-${data.aws_caller_identity.current.account_id}"
  retention_days = 90
  tags           = local.tags
}

module "iam" {
  source                     = "../../modules/iam"
  project                    = local.name_prefix
  github_org                 = var.github_org
  github_repo                = var.github_repo
  github_owner_id            = var.github_owner_id
  github_repo_id             = var.github_repo_id
  state_bucket               = var.state_bucket
  reports_bucket             = module.s3_reports.bucket_name
  create_oidc_provider       = var.create_oidc_provider
  slack_webhook_url          = var.slack_webhook_url
  existing_oidc_provider_arn = var.existing_oidc_provider_arn
  tags                       = local.tags
}

module "budgets" {
  source                       = "../../modules/budgets"
  project                      = local.name_prefix
  monthly_limit                = var.monthly_budget_limit
  alert_threshold_pct          = var.budget_alert_threshold
  anomaly_impact_threshold     = var.anomaly_impact_threshold
  existing_anomaly_monitor_arn = var.existing_anomaly_monitor_arn
  subscriber_emails            = var.alert_emails
  tags                         = local.tags
}

# Note: the "budgets" module above already provisions AWS Cost Anomaly Detection
# (aws_ce_anomaly_monitor + subscription, email-based). The separate SNS-based
# "cost-anomaly" module in terraform/modules/ is NOT wired here on purpose — using
# both would create two competing anomaly monitors on the same account.

data "aws_caller_identity" "current" {}

# ── Networking ────────────────────────────────────────────────────────────
module "vpc" {
  source              = "../../modules/vpc"
  project_name        = local.name_prefix
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  azs                 = var.azs
  tags                = local.tags
}

module "security_groups" {
  source         = "../../modules/security-groups"
  project_name   = local.name_prefix
  environment    = var.environment
  vpc_id         = module.vpc.vpc_id
  container_port = var.container_port
  enable_https   = var.enable_https
  tags           = local.tags
}

# ── Container registry ──────────────────────────────────────────────────
module "ecr" {
  source          = "../../modules/ecr"
  repository_name = "${local.name_prefix}-app"
  tags            = local.tags
}

# ── Load balancer ────────────────────────────────────────────────────────
module "alb" {
  source                = "../../modules/alb"
  project_name          = local.name_prefix
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id
  container_port        = var.container_port
  health_check_path     = "/health"
  tags                  = local.tags
}

# ── Logs + billing alarm (created up front, BEFORE ecs — the task definition
#    references this log group by name and ECS won't auto-create it) ────────
module "cloudwatch_logs" {
  source                      = "../../modules/cloudwatch"
  project_name                = local.name_prefix
  environment                 = var.environment
  log_group_names             = ["/ecs/${local.name_prefix}-app"]
  log_retention_days          = var.log_retention_days
  enable_billing_alarm        = true
  billing_alarm_threshold_usd = var.billing_alarm_threshold_usd
  alarm_sns_topic_arn         = module.sns_alerts.topic_arn
  tags                        = local.tags
}

# ── SNS topic for CloudWatch alarm notifications (billing, ECS CPU) ───────
# Separate from the budgets module's own email subscriptions — this one backs
# the cloudwatch module's metric alarms specifically.
module "sns_alerts" {
  source              = "../../modules/sns"
  topic_name          = "${local.name_prefix}-alarms"
  email_subscriptions = var.alert_emails
  tags                = local.tags
}

# ── ECS (Fargate, desired_count = 1, no NAT — public subnets) ─────────────
# ── ECS (Fargate, desired_count = 1, no NAT — public subnets) ─────────────
module "ecs" {
  source             = "../../modules/ecs"
  project_name       = local.name_prefix
  environment        = var.environment
  container_image    = "${module.ecr.repository_url}:${var.container_image_tag}"
  container_port     = var.container_port
  cpu                = var.ecs_cpu
  memory             = var.ecs_memory
  desired_count      = var.ecs_desired_count
  execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn      = module.iam.finops_app_role_arn
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.ecs_security_group_id]
  target_group_arn   = module.alb.target_group_arn
  log_group_name     = "/ecs/${local.name_prefix}-app"
  aws_region         = var.aws_region

  environment_variables = {
    APP_ENV                  = var.environment
    AWS_REGION               = var.aws_region
    DATABASE_URL             = "sqlite+aiosqlite:///./data/finops.db"
    REPORT_OUTPUT_DIR        = "/app/data/reports"
    # Scheduling is handled by EventBridge/Lambda
    SCHEDULER_ENABLED        = "false"
    SLACK_CHANNEL            = "#all-oluleye"
    SES_FROM_EMAIL           = var.ses_verified_email
    SES_TO_EMAILS            = jsonencode(var.alert_emails)
    BUDGET_ALERT_THRESHOLD   = tostring(var.budget_alert_threshold)
    ANOMALY_IMPACT_THRESHOLD = tostring(var.anomaly_impact_threshold)
    DASHBOARD_TITLE          = "AWS FinOps Dashboard"
    API_KEY                  = var.api_key
}

  secrets = merge(
    module.iam.slack_webhook_parameter_arn != null ? { SLACK_WEBHOOK_URL = module.iam.slack_webhook_parameter_arn } : {}
  )

  tags = local.tags

  depends_on = [

    module.cloudwatch_logs,

  ]
}

# ── ECS CPU alarm — separate call, AFTER ecs exists, to avoid a cycle with
#    cloudwatch_logs (which ecs depends on for its log group) ────────────
module "cloudwatch_ecs_alarm" {
  source               = "../../modules/cloudwatch"
  project_name         = local.name_prefix
  environment          = var.environment
  log_group_names      = []    # already created by cloudwatch_logs above
  enable_billing_alarm = false # already created by cloudwatch_logs above
  alarm_sns_topic_arn  = module.sns_alerts.topic_arn
  ecs_cluster_name     = module.ecs.cluster_name
  ecs_service_name     = module.ecs.service_name
  tags                 = local.tags
}

# ── SES (single verified sender — no DNS required) ─────────────────────────
module "ses" {
  source         = "../../modules/ses"
  email_identity = var.ses_verified_email
  tags           = local.tags
}

# ── Dashboard combining ECS, ALB, and billing metrics ──────────────────────
module "monitoring" {
  source                  = "../../modules/monitoring"
  dashboard_name          = "${local.name_prefix}-dashboard"
  aws_region              = var.aws_region
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_service_name        = module.ecs.service_name
  alb_arn_suffix          = module.alb.alb_arn_suffix
  target_group_arn_suffix = module.alb.target_group_arn_suffix
  lambda_function_name    = var.enable_external_scheduler ? module.lambda_report_trigger[0].function_name : null
}

# ── Optional: decoupled scheduler (off by default — see enable_external_scheduler) ─
module "lambda_report_trigger" {
  count              = var.enable_external_scheduler ? 1 : 0
  source             = "../../modules/lambda"
  function_name      = "${local.name_prefix}-report-trigger"
  role_arn           = module.iam.finops_app_role_arn
  source_dir         = "${path.module}/lambda_src/report_trigger"
  timeout            = 30
  memory_size        = 128
  log_retention_days = var.log_retention_days

  environment_variables = {
    DASHBOARD_URL = "http://${module.alb.alb_dns_name}"
    API_KEY       = var.api_key
  }

  tags = local.tags
}

module "eventbridge_daily" {
  count                = var.enable_external_scheduler ? 1 : 0
  source               = "../../modules/eventbridge"
  rule_name            = "${local.name_prefix}-daily-report"
  description          = "Triggers daily FinOps report generation"
  schedule_expression  = var.daily_report_schedule
  lambda_function_arn  = module.lambda_report_trigger[0].function_arn
  lambda_function_name = module.lambda_report_trigger[0].function_name
  input_json           = jsonencode({ period = "daily" })
  tags                 = local.tags
}

module "eventbridge_weekly" {
  count                = var.enable_external_scheduler ? 1 : 0
  source               = "../../modules/eventbridge"
  rule_name            = "${local.name_prefix}-weekly-report"
  description          = "Triggers weekly FinOps report generation"
  schedule_expression  = var.weekly_report_schedule
  lambda_function_arn  = module.lambda_report_trigger[0].function_arn
  lambda_function_name = module.lambda_report_trigger[0].function_name
  input_json           = jsonencode({ period = "weekly" })
  tags                 = local.tags
}


