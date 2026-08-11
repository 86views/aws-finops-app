resource "aws_cloudwatch_log_group" "this" {
  for_each          = toset(var.log_group_names)
  name              = each.value
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# Billing metrics only publish to CloudWatch in us-east-1 — make sure the provider/alias
# used for this resource targets us-east-1 regardless of your app's home region.
resource "aws_cloudwatch_metric_alarm" "billing" {
  count               = var.enable_billing_alarm ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-estimated-charges"
  alarm_description   = "Fires when estimated AWS charges exceed the free-tier safety threshold"
  namespace           = "AWS/Billing"
  metric_name         = "EstimatedCharges"
  dimensions          = { Currency = "USD" }
  statistic           = "Maximum"
  period              = 21600 # 6 hours — billing metric only updates a few times/day
  evaluation_periods  = 1
  threshold           = var.billing_alarm_threshold_usd
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alarm_sns_topic_arn]
  ok_actions          = [var.alarm_sns_topic_arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  count             = var.ecs_cluster_name != null ? 1 : 0
  alarm_name        = "${var.project_name}-${var.environment}-ecs-cpu-high"
  alarm_description = "ECS service CPU utilization is high"
  namespace         = "AWS/ECS"
  metric_name       = "CPUUtilization"
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = var.ecs_cpu_alarm_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alarm_sns_topic_arn]

  tags = var.tags
}
