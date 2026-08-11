output "budget_name" {
  value = aws_budgets_budget.monthly.name
}

output "anomaly_monitor_arn" {
  value = var.existing_anomaly_monitor_arn != null ? var.existing_anomaly_monitor_arn : aws_ce_anomaly_monitor.account[0].arn
}
