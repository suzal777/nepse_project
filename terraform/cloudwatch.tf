# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "nepse-lambda-error-alerts"
}

# Subscribe your email
resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "sujalphaiju777@gmail.com"
}

resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  for_each = toset(var.lambda_names)

  alarm_name          = "nepse-${each.key}-error-alarm"
  alarm_description   = "Alarm when ${each.key} Lambda has errors > 0"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60   # 1 minute interval
  statistic           = "Sum"
  threshold           = 0    # trigger if >0 errors
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = each.key
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}