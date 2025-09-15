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




