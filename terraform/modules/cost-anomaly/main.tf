# Cost Anomaly Detection can't publish to an SNS topic unless the topic policy explicitly
# allows costalerts.amazonaws.com — without this, alerts fail silently.
resource "aws_sns_topic_policy" "allow_cost_anomaly" {
  arn = var.sns_topic_arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCostAnomalyDetectionPublish"
        Effect    = "Allow"
        Principal = { Service = "costalerts.amazonaws.com" }
        Action    = "SNS:Publish"
        Resource  = var.sns_topic_arn
      }
    ]
  })
}

resource "aws_ce_anomaly_monitor" "this" {
  name              = var.monitor_name
  monitor_type      = var.monitor_type
  monitor_dimension = var.monitor_type == "DIMENSIONAL" ? var.monitor_dimension : null

  tags = var.tags
}

resource "aws_ce_anomaly_subscription" "this" {
  name      = var.subscription_name
  frequency = var.frequency

  monitor_arn_list = [aws_ce_anomaly_monitor.this.arn]

  subscriber {
    type    = "SNS"
    address = var.sns_topic_arn
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      values        = [tostring(var.threshold_amount)]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  tags = var.tags
}
