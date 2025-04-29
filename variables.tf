variable "api_url" {
  type        = string
  default     = "https://web-api.tp.entsoe.eu/api"
  description = "Base URL for the ENTSO-E API."
}

variable "document_type" {
  type        = string
  default     = "A71"
  description = "Type of document to request from the ENTSO-E API."
}

variable "extra_params" {
  type        = string
  default     = ""
  description = "Optional extra query parameters to include in the API request."
}

variable "in_domain" {
  type        = string
  default     = "10YSK-SEPS-----K"
  description = "EIC code representing the country."
}

variable "lambda_schedule_expression" {
  type        = string
  default     = "cron(0 0 * * ? *)"
  description = "EventBridge schedule expression to trigger the Lambda function."
}

variable "process_type" {
  type        = string
  default     = "A01"
  description = "Process type for the API request."
}

variable "s3_bucket_name" {
  type        = string
  default     = "entsoe-parsed-data"
  description = "Name of the S3 bucket to store parsed ENTSO-E data."
}

variable "security_token" {
  type        = string
  description = "Security token (API key) for authenticating with the ENTSO-E API."
}
