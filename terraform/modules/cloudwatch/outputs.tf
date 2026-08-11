output "log_group_names" {
  value = [for lg in aws_cloudwatch_log_group.this : lg.name]
}

output "log_group_arns" {
  value = { for k, lg in aws_cloudwatch_log_group.this : k => lg.arn }
}

output "billing_alarm_arn" {
  value = var.enable_billing_alarm ? aws_cloudwatch_metric_alarm.billing[0].arn : null
}
