# Single CloudWatch dashboard pulling together ECS, ALB, and Lambda metrics.
# Purely observability — the free tier includes 3 dashboards/month at no cost.

locals {
  ecs_widget = var.ecs_cluster_name != null ? [{
    type   = "metric"
    x      = 0
    y      = 0
    width  = 12
    height = 6
    properties = {
      title  = "ECS Service — CPU & Memory"
      view   = "timeSeries"
      region = var.aws_region
      metrics = [
        ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", var.ecs_service_name],
        ["AWS/ECS", "MemoryUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", var.ecs_service_name]
      ]
      period = 300
      stat   = "Average"
    }
  }] : []

  alb_widget = var.alb_arn_suffix != null ? [{
    type   = "metric"
    x      = 12
    y      = 0
    width  = 12
    height = 6
    properties = {
      title  = "ALB — Requests & Target Health"
      view   = "timeSeries"
      region = var.aws_region
      metrics = [
        ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix],
        ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", var.target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix],
        ["AWS/ApplicationELB", "UnHealthyHostCount", "TargetGroup", var.target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix]
      ]
      period = 300
      stat   = "Sum"
    }
  }] : []

  lambda_widget = var.lambda_function_name != null ? [{
    type   = "metric"
    x      = 0
    y      = 6
    width  = 12
    height = 6
    properties = {
      title  = "Lambda — Invocations & Errors"
      view   = "timeSeries"
      region = var.aws_region
      metrics = [
        ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_name],
        ["AWS/Lambda", "Errors", "FunctionName", var.lambda_function_name],
        ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name]
      ]
      period = 300
      stat   = "Sum"
    }
  }] : []

  billing_widget = [{
    type   = "metric"
    x      = 12
    y      = 6
    width  = 12
    height = 6
    properties = {
      title  = "Estimated Charges (USD)"
      view   = "timeSeries"
      region = "us-east-1"
      metrics = [
        ["AWS/Billing", "EstimatedCharges", "Currency", "USD"]
      ]
      period = 21600
      stat   = "Maximum"
    }
  }]

  all_widgets = concat(local.ecs_widget, local.alb_widget, local.lambda_widget, local.billing_widget)
}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.dashboard_name
  dashboard_body = jsonencode({
    widgets = local.all_widgets
  })
}
