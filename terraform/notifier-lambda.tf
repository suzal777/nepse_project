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
data "archive_file" "notifier_zip" {
  type        = "zip"
  source_file = "${var.lambda_src_path}/notifier_lambda.py"
  output_path = "${path.module}/../build/notifier_lambda.zip"
}

resource "aws_lambda_function" "notifier_lambda" {
  function_name    = "nepse_notifier_lambda"
  role             = aws_iam_role.notifier_lambda_role.arn
  handler          = "notifier_lambda.lambda_handler"
  runtime          = "python3.11"
  timeout          = 20
  memory_size      = 256
  filename         = data.archive_file.notifier_zip.output_path
  source_code_hash = data.archive_file.notifier_zip.output_base64sha256

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



