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
data "archive_file" "llm_analysis_zip" {
  type        = "zip"
  source_file = "${var.lambda_src_path}/llm_analysis_lambda.py"
  output_path = "${path.module}/../build/llm_analysis_lambda.zip"
}

resource "aws_lambda_function" "llm_analysis" {
  function_name    = "nepse_llm_analysis_lambda"
  role             = aws_iam_role.llm_lambda_role.arn
  handler          = "llm_analysis_lambda.lambda_handler"
  runtime          = "python3.10"
  timeout          = 60
  memory_size      = 512
  filename         = data.archive_file.llm_analysis_zip.output_path
  source_code_hash = data.archive_file.llm_analysis_zip.output_base64sha256

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