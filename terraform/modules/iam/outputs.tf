output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}

output "finops_app_role_arn" {
  value = aws_iam_role.finops_app.arn
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_execution.arn
}


output "finops_app_role_name" {
  value = aws_iam_role.finops_app.name
}

output "instance_profile_name" {
  value = aws_iam_instance_profile.finops_app.name
}


output "slack_webhook_parameter_arn" {
  description = "null if slack_webhook_url wasn't provided"
  value       = var.slack_webhook_url != null ? aws_ssm_parameter.slack_webhook_url[0].arn : null
}