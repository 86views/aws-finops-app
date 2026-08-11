data "aws_caller_identity" "current" {}

resource "aws_budgets_budget" "monthly" {
  name         = "${var.project}-monthly-cost"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_limit)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_types {
    include_credit             = false
    include_discount           = true
    include_other_subscription = true
    include_recurring          = true
    include_refund             = false
    include_subscription       = true
    include_support            = true
    include_tax                = true
    include_upfront            = true
    use_amortized              = false
    use_blended                = false
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = var.alert_threshold_pct
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.subscriber_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = var.alert_threshold_pct
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.subscriber_emails
  }

  tags = var.tags
}

# Cost Anomaly Detection monitor (account-level)
resource "aws_ce_anomaly_monitor" "account" {
  count             = var.existing_anomaly_monitor_arn == null ? 1 : 0
  name              = "${var.project}-account-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  tags = var.tags
}

resource "aws_ce_anomaly_subscription" "default" {
  name      = "${var.project}-anomaly-sub"
  frequency = "DAILY"

  monitor_arn_list = [
    var.existing_anomaly_monitor_arn != null
    ? var.existing_anomaly_monitor_arn
    : aws_ce_anomaly_monitor.account[0].arn
  ]

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = [tostring(var.anomaly_impact_threshold)]
    }
  }

  subscriber {
    type    = "EMAIL"
    address = var.subscriber_emails[0]
  }

  tags = var.tags
}