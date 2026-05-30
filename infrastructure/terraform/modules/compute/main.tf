# Compute Module - Lambda + API Gateway

terraform {
  required_version = ">= 1.5.0"
}

# IAM Role für Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-role"
  }
}

# Lambda Basic Execution Policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda VPC Execution Policy (für ENI Management)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count      = var.enable_vpc ? 1 : 0
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Custom IAM Policy für Lambda (Secrets Manager, S3, etc.)
resource "aws_iam_policy" "lambda_custom" {
  name        = "${var.project_name}-${var.environment}-lambda-custom-policy"
  description = "Custom policy for StackVertex Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${var.deployment_bucket_arn}/*",
          var.customer_data_bucket_arn != null ? "${var.customer_data_bucket_arn}/*" : ""
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = compact([
          var.deployment_bucket_arn,
          var.customer_data_bucket_arn
        ])
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_custom" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda_custom.arn
}

# S3 Bucket für Lambda Code
resource "aws_s3_bucket" "lambda_code" {
  bucket = "${var.project_name}-${var.environment}-lambda-code-${var.aws_account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-code"
  }
}

resource "aws_s3_bucket_versioning" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ECR Repository für Lambda Docker Images
# NOTE: Wird vom Bootstrap Workflow erstellt, hier nur als data source
data "aws_ecr_repository" "lambda" {
  name = "${var.project_name}-${var.environment}-lambda"
}

# ECR Lifecycle Policy wird vom Bootstrap Workflow erstellt

# Lambda Function (Container Image)
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-${var.environment}-api"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.lambda_image_uri != null ? var.lambda_image_uri : "${data.aws_ecr_repository.lambda.repository_url}:latest"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment {
    variables = merge(
      {
        ENVIRONMENT             = var.environment
        DYNAMODB_TABLE_NAME     = var.dynamodb_table_name
        DEPLOYMENT_BUCKET       = var.deployment_bucket_name
        CUSTOMER_DATA_BUCKET    = var.customer_data_bucket_name != null ? var.customer_data_bucket_name : ""
        TERRAFORM_STATE_BUCKET  = var.terraform_state_bucket
        CORS_ORIGINS            = var.cors_origins
        LOG_LEVEL               = var.log_level
      },
      var.additional_environment_variables
    )
  }

  dynamic "vpc_config" {
    for_each = var.enable_vpc ? [1] : []
    content {
      subnet_ids         = var.private_subnet_ids
      security_group_ids = [var.lambda_security_group_id]
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-lambda"
  }

  # Lifecycle: ignoriere image_uri changes (wird via CI/CD deployed)
  lifecycle {
    ignore_changes = [image_uri]
  }
}

# Lambda Function URL (Alternative zu API Gateway für einfachere Setups)
resource "aws_lambda_function_url" "api" {
  count              = var.enable_lambda_function_url ? 1 : 0
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE" # Öffentlich, FastAPI macht Auth

  cors {
    allow_credentials = var.cors_origins == "*" ? false : true
    allow_origins     = split(",", var.cors_origins)
    allow_methods     = ["*"]
    allow_headers     = ["*"]
    max_age           = 3600
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-logs"
  }
}

# Lambda Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-lambda-high-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Lambda function error rate is too high"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-lambda-high-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = var.lambda_timeout * 1000 * 0.8 # 80% of timeout
  alarm_description   = "Lambda function duration is approaching timeout"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
}

# API Gateway HTTP API (für REST API)
resource "aws_apigatewayv2_api" "http" {
  count         = var.enable_api_gateway ? 1 : 0
  name          = "${var.project_name}-${var.environment}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_credentials = var.cors_origins == "*" ? false : true
    allow_origins     = split(",", var.cors_origins)
    allow_methods     = ["*"]
    allow_headers     = ["*"]
    max_age           = 3600
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-http-api"
  }
}

# API Gateway Integration (Lambda)
resource "aws_apigatewayv2_integration" "lambda" {
  count              = var.enable_api_gateway ? 1 : 0
  api_id             = aws_apigatewayv2_api.http[0].id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# API Gateway Route (Catch-All)
resource "aws_apigatewayv2_route" "default" {
  count     = var.enable_api_gateway ? 1 : 0
  api_id    = aws_apigatewayv2_api.http[0].id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "default" {
  count       = var.enable_api_gateway ? 1 : 0
  api_id      = aws_apigatewayv2_api.http[0].id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-http-api-stage"
  }
}

# CloudWatch Log Group für API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  count             = var.enable_api_gateway ? 1 : 0
  name              = "/aws/apigateway/${var.project_name}-${var.environment}-http-api"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-${var.environment}-api-gateway-logs"
  }
}

# Lambda Permission für API Gateway
resource "aws_lambda_permission" "api_gateway" {
  count         = var.enable_api_gateway ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http[0].execution_arn}/*/*"
}

# WebSocket API (für real-time updates)
resource "aws_apigatewayv2_api" "websocket" {
  count         = var.enable_websocket ? 1 : 0
  name          = "${var.project_name}-${var.environment}-websocket-api"
  protocol_type = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  tags = {
    Name = "${var.project_name}-${var.environment}-websocket-api"
  }
}

# WebSocket Integration
resource "aws_apigatewayv2_integration" "websocket" {
  count              = var.enable_websocket ? 1 : 0
  api_id             = aws_apigatewayv2_api.websocket[0].id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  integration_method = "POST"
}

# WebSocket Routes
resource "aws_apigatewayv2_route" "websocket_connect" {
  count     = var.enable_websocket ? 1 : 0
  api_id    = aws_apigatewayv2_api.websocket[0].id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket[0].id}"
}

resource "aws_apigatewayv2_route" "websocket_disconnect" {
  count     = var.enable_websocket ? 1 : 0
  api_id    = aws_apigatewayv2_api.websocket[0].id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket[0].id}"
}

resource "aws_apigatewayv2_route" "websocket_default" {
  count     = var.enable_websocket ? 1 : 0
  api_id    = aws_apigatewayv2_api.websocket[0].id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.websocket[0].id}"
}

# WebSocket Stage
resource "aws_apigatewayv2_stage" "websocket" {
  count       = var.enable_websocket ? 1 : 0
  api_id      = aws_apigatewayv2_api.websocket[0].id
  name        = var.environment
  auto_deploy = true

  tags = {
    Name = "${var.project_name}-${var.environment}-websocket-stage"
  }
}

# Lambda Permission für WebSocket API
resource "aws_lambda_permission" "websocket" {
  count         = var.enable_websocket ? 1 : 0
  statement_id  = "AllowWebSocketAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket[0].execution_arn}/*/*"
}
