data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "parse_entsoe_data" {
  function_name = "parseEntsoeData"
  role          = aws_iam_role.parse_entsoe_data_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout = 120

  environment {
    variables = {
      API_URL        = var.api_url,
      DOCUMENT_TYPE  = var.document_type,
      EXTRA_PARAMS   = var.extra_params,
      IN_DOMAIN      = var.in_domain,
      PROCESS_TYPE   = var.process_type,
      S3_BUCKET_NAME = var.s3_bucket_name,
      SECURITY_TOKEN = var.security_token
    }
  }

  layers = [
    "arn:aws:lambda:eu-north-1:765089596571:layer:parseEntsoeData:1"
  ]
}

resource "aws_cloudwatch_event_rule" "parse_entsoe_data_schedule" {
  name                = "parse-entsoe-data-schedule"
  description         = "Trigger Lambda on a schedule"
  schedule_expression = var.lambda_schedule_expression
}

resource "aws_cloudwatch_event_target" "parse_entsoe_data_target" {
  rule      = aws_cloudwatch_event_rule.parse_entsoe_data_schedule.name
  target_id = "parseEntsoeDataLambda"
  arn       = aws_lambda_function.parse_entsoe_data.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.parse_entsoe_data.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.parse_entsoe_data_schedule.arn
}
