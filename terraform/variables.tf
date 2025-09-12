variable "region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_prefix" {
  type    = string
  default = "nepse-market-data"
}

variable "scraper_schedule" {
  type    = string
  # 10:15 UTC = 4:00 PM NPT
  default = "cron(15 10 * * ? *)"
}

variable "target_url" {
  type = string
  default = "https://www.sharesansar.com/today-share-price"
}

variable "ses_email_from" {
  type = string
  default = "sujalphaiju777@gmail.com"
}

variable "ses_email_to" {
  type = string
  default = "sujalphaiju777@gmail.com"
}

variable "lambda_names" {
  type    = list(string)
  default = ["scraper_lambda", "processor_lambda", "llm_analysis_lambda", "notifier-lambda"]
}
