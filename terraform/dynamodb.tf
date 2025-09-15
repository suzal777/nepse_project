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
