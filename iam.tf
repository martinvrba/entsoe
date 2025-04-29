resource "aws_iam_role" "parse_entsoe_data_role" {
  name = "parse_entsoe_data_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "parse_entsoe_data_policy" {
  name = "parse_entsoe_data_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject"
        ],
        Resource = "${aws_s3_bucket.data_bucket.arn}/*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "parse_entsoe_data_policy_attach" {
  role       = aws_iam_role.parse_entsoe_data_role.name
  policy_arn = aws_iam_policy.parse_entsoe_data_policy.arn
}
