output "monitor_arn" {
  value = aws_ce_anomaly_monitor.this.arn
}

output "subscription_arn" {
  value = aws_ce_anomaly_subscription.this.arn
}
