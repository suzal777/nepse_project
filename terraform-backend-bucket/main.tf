provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "tf_bucket" {
  bucket        = "sujal-terraform-state"
  force_destroy = false

  tags = {
    Owner     = "Sujal Phaiju"
    ManagedBy = "terraform"
  }
}

# --- SSE Configuration ---
resource "aws_s3_bucket_server_side_encryption_configuration" "tf_bucket_sse" {
  bucket = aws_s3_bucket.tf_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- Versioning ---
resource "aws_s3_bucket_versioning" "tf_bucket_versioning" {
  bucket = aws_s3_bucket.tf_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}