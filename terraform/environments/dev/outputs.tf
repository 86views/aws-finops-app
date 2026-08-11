output "reports_bucket" {
  value = module.s3_reports.bucket_name
}

output "github_actions_role_arn" {
  value = module.iam.github_actions_role_arn
}

output "finops_app_role_arn" {
  value = module.iam.finops_app_role_arn
}

output "ecs_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = module.iam.ecs_execution_role_arn
}

output "budget_name" {
  value = module.budgets.budget_name
}

output "anomaly_monitor_arn" {
  value = module.budgets.anomaly_monitor_arn
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "alb_dns_name" {
  description = "Dashboard URL — visit http://<this> once the ECS service is healthy"
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "ecs_service_name" {
  value = module.ecs.service_name
}

output "cloudwatch_dashboard_name" {
  value = module.monitoring.dashboard_name
}

output "sns_alerts_topic_arn" {
  value = module.sns_alerts.topic_arn
}
