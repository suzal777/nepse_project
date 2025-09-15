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

resource "aws_s3_bucket_lifecycle_configuration" "market" {
  bucket = aws_s3_bucket.market.id

  # --- Delete 'raw/' folder quickly ---
  rule {
    id     = "delete-raw"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    expiration {
      days = 30
    }
  }

  # --- Delete 'rejects/' folder quickly ---
  rule {
    id     = "delete-rejects"
    status = "Enabled"

    filter {
      prefix = "rejects/"
    }

    expiration {
      days = 30
    }
  }

  # --- Move 'processed/' to Glacier and delete later ---
  rule {
    id     = "processed-to-glacier"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 365 
    }
  }

  # --- Move 'metadata/' to Glacier and delete later ---
  rule {
    id     = "metadata-to-glacier"
    status = "Enabled"

    filter {
      prefix = "metadata/"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
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

# --- Lambda Invoke Permissions ---
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