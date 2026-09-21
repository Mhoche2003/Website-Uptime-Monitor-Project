data "archive_file" "check_availability" {
  type        = "zip"
  source_file = "${path.module}/src/check_availability/lambda_function.py"
  output_path = "${path.module}/builds/check_availability.zip"
}

data "archive_file" "check_latency" {
  type        = "zip"
  source_file = "${path.module}/src/check_latency/lambda_function.py"
  output_path = "${path.module}/builds/check_latency.zip"
}

data "archive_file" "check_content" {
  type        = "zip"
  source_file = "${path.module}/src/check_content/lambda_function.py"
  output_path = "${path.module}/builds/check_content.zip"
}

resource "aws_iam_role" "lambda_checks" {
  name = "${var.project_name}-lambda-checks-role"

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

resource "aws_iam_role_policy" "lambda_checks" {
  name = "${var.project_name}-lambda-checks-policy"
  role = aws_iam_role.lambda_checks.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = var.dynamodb_table_arn
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = var.sns_topic_arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "check_availability" {
  function_name    = "${var.project_name}-check-availability"
  role             = aws_iam_role.lambda_checks.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 40
  memory_size      = 128
  filename         = data.archive_file.check_availability.output_path
  source_code_hash = data.archive_file.check_availability.output_base64sha256

  environment {
    variables = {
      SITE_URL       = var.site_url
      DYNAMODB_TABLE = var.dynamodb_table_name
      SNS_TOPIC_ARN  = var.sns_topic_arn
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "check_latency" {
  function_name    = "${var.project_name}-check-latency"
  role             = aws_iam_role.lambda_checks.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 40
  memory_size      = 128
  filename         = data.archive_file.check_latency.output_path
  source_code_hash = data.archive_file.check_latency.output_base64sha256

  environment {
    variables = {
      SITE_URL          = var.site_url
      DYNAMODB_TABLE    = var.dynamodb_table_name
      SNS_TOPIC_ARN     = var.sns_topic_arn
      LATENCY_THRESHOLD = tostring(var.latency_threshold_seconds)
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "check_content" {
  function_name    = "${var.project_name}-check-content"
  role             = aws_iam_role.lambda_checks.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 40
  memory_size      = 128
  filename         = data.archive_file.check_content.output_path
  source_code_hash = data.archive_file.check_content.output_base64sha256

  environment {
    variables = {
      SITE_URL         = var.site_url
      DYNAMODB_TABLE   = var.dynamodb_table_name
      SNS_TOPIC_ARN    = var.sns_topic_arn
      EXPECTED_CONTENT = var.expected_content
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_event_rule" "checks_schedule" {
  name                = "${var.project_name}-checks-schedule"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "check_availability" {
  rule      = aws_cloudwatch_event_rule.checks_schedule.name
  target_id = "check_availability"
  arn       = aws_lambda_function.check_availability.arn
}

resource "aws_cloudwatch_event_target" "check_latency" {
  rule      = aws_cloudwatch_event_rule.checks_schedule.name
  target_id = "check_latency"
  arn       = aws_lambda_function.check_latency.arn
}

resource "aws_cloudwatch_event_target" "check_content" {
  rule      = aws_cloudwatch_event_rule.checks_schedule.name
  target_id = "check_content"
  arn       = aws_lambda_function.check_content.arn
}

resource "aws_lambda_permission" "check_availability" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_availability.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.checks_schedule.arn
}

resource "aws_lambda_permission" "check_latency" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_latency.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.checks_schedule.arn
}

resource "aws_lambda_permission" "check_content" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_content.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.checks_schedule.arn
}
