output "dashboard_arn" {
  value = aws_cloudwatch_dashboard.this.dashboard_arn
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.this.dashboard_name
}
