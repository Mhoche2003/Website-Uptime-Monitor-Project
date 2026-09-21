data "archive_file" "aggregate_metrics" {
  type        = "zip"
  source_file = "${path.module}/src/aggregate_metrics/lambda_function.py"
  output_path = "${path.module}/builds/aggregate_metrics.zip"
}

resource "aws_iam_role" "aggregate_metrics" {
  name = "${var.project_name}-aggregate-metrics-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "aggregate_metrics" {
  name = "${var.project_name}-aggregate-metrics-policy"
  role = aws_iam_role.aggregate_metrics.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Query"]
        Resource = var.dynamodb_table_arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${var.dashboard_bucket_arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "aggregate_metrics" {
  function_name    = "${var.project_name}-aggregate-metrics"
  role             = aws_iam_role.aggregate_metrics.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 128
  filename         = data.archive_file.aggregate_metrics.output_path
  source_code_hash = data.archive_file.aggregate_metrics.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE   = var.dynamodb_table_name
      DASHBOARD_BUCKET = var.dashboard_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_event_rule" "aggregation_schedule" {
  name                = "${var.project_name}-aggregation-schedule"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "aggregate_metrics" {
  rule      = aws_cloudwatch_event_rule.aggregation_schedule.name
  target_id = "aggregate_metrics"
  arn       = aws_lambda_function.aggregate_metrics.arn
}

resource "aws_lambda_permission" "aggregate_metrics" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.aggregate_metrics.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.aggregation_schedule.arn
}
