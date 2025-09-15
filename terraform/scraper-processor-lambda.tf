# --- IAM Role for Scraper and Processor Lambdas ---
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
data "archive_file" "scraper_zip" {
  type        = "zip"
  source_file = "${var.lambda_src_path}/scraper_lambda.py"
  output_path = "${path.module}/../build/scraper_lambda.zip"
}

resource "aws_lambda_function" "scraper" {
  function_name    = "nepse_scraper_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "scraper_lambda.lambda_handler"
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.scraper_zip.output_path
  source_code_hash = data.archive_file.scraper_zip.output_base64sha256
  layers           = [aws_lambda_layer_version.scraper_layer.arn]


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

# --- Lambda Layer (Scraper deps) ---
data "archive_file" "scraper_layer_zip" {
  type        = "zip"
  source_dir  = "${var.lambda_src_path}/layer"
  output_path = "${path.module}/../build/scraper_layer.zip"
}

resource "aws_lambda_layer_version" "scraper_layer" {
  layer_name          = "scraper_layer"
  filename            = data.archive_file.scraper_layer_zip.output_path
  source_code_hash    = data.archive_file.scraper_layer_zip.output_base64sha256
  compatible_runtimes = ["python3.10"]
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

# --- Processor Lambda ---
data "archive_file" "processor_zip" {
  type        = "zip"
  source_file = "${var.lambda_src_path}/processor_lambda.py"
  output_path = "${path.module}/../build/processor_lambda.zip"
}

resource "aws_lambda_function" "processor" {
  function_name    = "nepse_processor_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "processor_lambda.lambda_handler"
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.processor_zip.output_path
  source_code_hash = data.archive_file.processor_zip.output_base64sha256

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