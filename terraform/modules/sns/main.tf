resource "aws_sns_topic" "this" {
  name = var.topic_name
  tags = var.tags
}

resource "aws_sns_topic_subscription" "email" {
  for_each  = toset(var.email_subscriptions)
  topic_arn = aws_sns_topic.this.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_sns_topic_subscription" "lambda" {
  count     = var.lambda_subscription_arn != null ? 1 : 0
  topic_arn = aws_sns_topic.this.arn
  protocol  = "lambda"
  endpoint  = var.lambda_subscription_arn
}

resource "aws_lambda_permission" "allow_sns" {
  count         = var.lambda_subscription_arn != null ? 1 : 0
  statement_id  = "AllowExecutionFromSNS-${var.topic_name}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_subscription_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.this.arn
}
