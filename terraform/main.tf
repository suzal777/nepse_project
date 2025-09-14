provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

terraform {
  backend "s3" {
    bucket         = "nepse-terraform-state"
    key            = "nepse_project/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    use_lockfile   = true
  }
}


resource "random_id" "suffix" {
  byte_length = 4
}

# --- S3 Bucket with prefixes ---
resource "aws_s3_bucket" "market" {
  bucket        = "${var.bucket_prefix}-${random_id.suffix.hex}"
  force_destroy = true

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "market" {
  bucket = aws_s3_bucket.market.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- IAM Role for Lambdas ---
resource "aws_iam_role" "lambda_role" {
  name = "nepse-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach policies
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# --- Scraper Lambda ---
resource "aws_lambda_function" "scraper" {
  function_name    = "nepse_scraper_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "scraper_lambda.lambda_handler"
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 256
  filename         = "${path.module}/../build/scraper_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/scraper_lambda.zip")

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.market.bucket
      TARGET_URL  = var.target_url
    }
  }

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

# --- Processor Lambda ---
resource "aws_lambda_function" "processor" {
  function_name    = "nepse_processor_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "processor_lambda.lambda_handler"
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 256
  filename         = "${path.module}/../build/processor_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/processor_lambda.zip")

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.market.bucket
    }
  }

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

# --- EventBridge Rule (daily scrape trigger) ---
resource "aws_cloudwatch_event_rule" "daily_scraper" {
  name                = "daily-nepse-scraper-rule"
  schedule_expression = var.scraper_schedule
}

resource "aws_cloudwatch_event_target" "scraper_target" {
  rule      = aws_cloudwatch_event_rule.daily_scraper.name
  target_id = "nepse_scraper_lambda"
  arn       = aws_lambda_function.scraper.arn
}

resource "aws_lambda_permission" "allow_eventbridge_scraper" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scraper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_scraper.arn
}

# --- DynamoDB Table ---
resource "aws_dynamodb_table" "llm_analysis" {
  name         = "Nepse-LLM-Analysis"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_key"

  attribute {
    name = "file_key"
    type = "S"
  }

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

# --- IAM Role for LLM Lambda ---
resource "aws_iam_role" "llm_lambda_role" {
  name = "nepse_llm_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Attach policies to LLM Lambda
resource "aws_iam_role_policy_attachment" "llm_lambda_basic" {
  role       = aws_iam_role.llm_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "llm_lambda_s3" {
  role       = aws_iam_role.llm_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "llm_lambda_dynamo" {
  role       = aws_iam_role.llm_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "llm_lambda_bedrock" {
  role       = aws_iam_role.llm_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# --- EventBridge PutEvents Policy for LLM Lambda ---
resource "aws_iam_policy" "llm_eventbridge_putevents" {
  name        = "Nepse_LLM_EventBridge_PutEvents"
  description = "Allows LLM Lambda to put events to EventBridge"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["events:PutEvents"]
        Resource = "arn:aws:events:${var.region}:${data.aws_caller_identity.current.account_id}:event-bus/default"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "llm_lambda_eventbridge" {
  role       = aws_iam_role.llm_lambda_role.name
  policy_arn = aws_iam_policy.llm_eventbridge_putevents.arn
}

# --- LLM Lambda Function ---
resource "aws_lambda_function" "llm_analysis" {
  function_name    = "nepse_llm_analysis_lambda"
  role             = aws_iam_role.llm_lambda_role.arn
  handler          = "llm_analysis_lambda.lambda_handler"
  runtime          = "python3.10"
  timeout          = 60
  memory_size      = 512
  filename         = "${path.module}/../build/llm_analysis_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/llm_analysis_lambda.zip")

  environment {
    variables = {
      BUCKET_NAME     = aws_s3_bucket.market.bucket
      DYNAMO_TABLE    = aws_dynamodb_table.llm_analysis.name
      LLM_MODEL       = "amazon.nova-lite-v1:0"
      ALERT_EVENT_BUS = "default"
    }
  }

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

# --- Lambda Permissions ---
resource "aws_lambda_permission" "allow_s3_processor" {
  statement_id  = "AllowExecutionFromS3Processor"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.market.arn
}

resource "aws_lambda_permission" "allow_s3_llm" {
  statement_id  = "AllowExecutionFromS3LLM"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.llm_analysis.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.market.arn
}

# --- Unified S3 Bucket Notification ---
resource "aws_s3_bucket_notification" "bucket_notifications" {
  bucket = aws_s3_bucket.market.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.llm_analysis.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "processed/"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_processor,
    aws_lambda_permission.allow_s3_llm
  ]
}

# ---------- EventBridge Rule ----------
resource "aws_cloudwatch_event_rule" "anomaly_detected_rule" {
  name           = "nepse-anomaly-detected-rule"
  description    = "Triggers notifier Lambda when anomaly is detected"
  event_bus_name = "default"

  event_pattern = jsonencode({
    "detail-type" = ["AnomalyDetected"],
    "source"      = ["llm_analysis"]
  })
}

# ---------- Notifier Lambda Role ----------
resource "aws_iam_role" "notifier_lambda_role" {
  name = "nepse_notifier_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Attach SES + Basic Lambda Execution Policies to Notifier
resource "aws_iam_role_policy_attachment" "notifier_ses" {
  role       = aws_iam_role.notifier_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}

resource "aws_iam_role_policy_attachment" "notifier_lambda_basic" {
  role       = aws_iam_role.notifier_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---------- Notifier Lambda ----------
resource "aws_lambda_function" "notifier_lambda" {
  function_name    = "nepse_notifier_lambda"
  role             = aws_iam_role.notifier_lambda_role.arn
  handler          = "notifier_lambda.lambda_handler"
  runtime          = "python3.11"
  timeout          = 20
  memory_size      = 256
  filename         = "${path.module}/../build/notifier_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/notifier_lambda.zip")

  environment {
    variables = {
      SES_EMAIL_FROM = var.ses_email_from
      SES_EMAIL_TO   = var.ses_email_to
    }
  }

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

# ---------- EventBridge Target ----------
resource "aws_cloudwatch_event_target" "notifier_target" {
  rule           = aws_cloudwatch_event_rule.anomaly_detected_rule.name
  target_id      = "nepse_notifier_lambda"
  arn            = aws_lambda_function.notifier_lambda.arn
  event_bus_name = "default"
}

# ---------- Allow EventBridge to invoke Notifier Lambda ----------
resource "aws_lambda_permission" "allow_eventbridge_notifier" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifier_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.anomaly_detected_rule.arn
}

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
