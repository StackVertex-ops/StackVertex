/**
 * Lambda API Module
 *
 * Erstellt Lambda Functions für FastAPI (via Mangum) und WebSocket Handler.
 * Handelt 99% des API Traffics für schnelle Requests (<15 Min).
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

# ==========================================
# Lambda Functions
# ==========================================

# Lambda Layer für Dependencies (Python packages)
resource "aws_lambda_layer_version" "dependencies" {
  filename            = var.lambda_layer_zip_path
  layer_name          = "${var.project_name}-${var.environment}-dependencies"
  compatible_runtimes = [var.lambda_runtime]
  description         = "Python dependencies (FastAPI, boto3, etc.)"

  lifecycle {
    create_before_destroy = true
  }
}

# Main API Handler (FastAPI via Mangum)
resource "aws_lambda_function" "api_handler" {
  function_name = "${var.project_name}-${var.environment}-api-handler"
  description   = "FastAPI Main Handler (via Mangum)"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "lambda_handler.handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory

  filename         = var.lambda_code_zip_path
  source_code_hash = filebase64sha256(var.lambda_code_zip_path)

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = merge({
      # DynamoDB
      DYNAMODB_TABLE_NAME           = var.dynamodb_table_name
      DYNAMODB_ENDPOINT_URL         = var.dynamodb_endpoint_url

      # S3
      S3_LARGE_ITEMS_BUCKET         = var.s3_bucket_name
      USER_DATA_BUCKET              = var.user_data_bucket_name
      LARGE_ITEM_THRESHOLD          = var.large_item_threshold

      # AWS
      AWS_REGION                    = var.aws_region

      # Security
      SECRET_KEY                    = var.jwt_secret_key != "" ? var.jwt_secret_key : (var.jwt_secret_arn != "" ? data.aws_secretsmanager_secret_version.jwt_secret[0].secret_string : "")
      ALGORITHM                     = var.jwt_algorithm
      ACCESS_TOKEN_EXPIRE_MINUTES   = var.access_token_expire_minutes
      REFRESH_TOKEN_EXPIRE_DAYS     = var.refresh_token_expire_days
      ENV                           = var.environment

      # ECS (für Deployment Orchestrator)
      ECS_CLUSTER_NAME              = var.ecs_cluster_name
      ECS_TASK_DEFINITION           = var.ecs_task_definition_arn
      ECS_SUBNETS                   = join(",", var.ecs_subnets)
      ECS_SECURITY_GROUP            = var.ecs_security_group_id

      # Stripe (optional)
      STRIPE_SECRET_KEY             = var.stripe_secret_key_arn != "" ? data.aws_secretsmanager_secret_version.stripe_secret[0].secret_string : ""
      STRIPE_WEBHOOK_SECRET         = var.stripe_webhook_secret_arn != "" ? data.aws_secretsmanager_secret_version.stripe_webhook[0].secret_string : ""
      STRIPE_ENABLED                = var.stripe_enabled

      # API Gateway (für WebSocket Management API)
      WEBSOCKET_API_ENDPOINT        = var.websocket_api_endpoint
    }, var.extra_environment_variables)
  }

  # VPC Configuration (optional)
  dynamic "vpc_config" {
    for_each = var.vpc_id != "" ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = [aws_security_group.lambda[0].id]
    }
  }

  # Tracing
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  # CloudWatch Logs
  depends_on = [
    aws_cloudwatch_log_group.api_handler,
    aws_iam_role_policy_attachment.lambda_logs,
  ]

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-api-handler"
    Environment = var.environment
    Function    = "api-handler"
  })
}

# WebSocket $connect Handler
resource "aws_lambda_function" "websocket_connect" {
  function_name = "${var.project_name}-${var.environment}-ws-connect"
  description   = "WebSocket $connect Handler"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "websocket_connect.handler"
  runtime       = var.lambda_runtime
  timeout       = 30
  memory_size   = 256

  filename         = var.lambda_code_zip_path
  source_code_hash = filebase64sha256(var.lambda_code_zip_path)

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      AWS_REGION          = var.aws_region
      ENV                 = var.environment
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.websocket_connect,
    aws_iam_role_policy_attachment.lambda_logs,
  ]

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ws-connect"
    Environment = var.environment
    Function    = "websocket-connect"
  })
}

# WebSocket $disconnect Handler
resource "aws_lambda_function" "websocket_disconnect" {
  function_name = "${var.project_name}-${var.environment}-ws-disconnect"
  description   = "WebSocket $disconnect Handler"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "websocket_disconnect.handler"
  runtime       = var.lambda_runtime
  timeout       = 30
  memory_size   = 256

  filename         = var.lambda_code_zip_path
  source_code_hash = filebase64sha256(var.lambda_code_zip_path)

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      AWS_REGION          = var.aws_region
      ENV                 = var.environment
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.websocket_disconnect,
    aws_iam_role_policy_attachment.lambda_logs,
  ]

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ws-disconnect"
    Environment = var.environment
    Function    = "websocket-disconnect"
  })
}

# WebSocket $default Handler (message routing)
resource "aws_lambda_function" "websocket_message" {
  function_name = "${var.project_name}-${var.environment}-ws-message"
  description   = "WebSocket $default Message Handler"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "websocket_message.handler"
  runtime       = var.lambda_runtime
  timeout       = 30
  memory_size   = 256

  filename         = var.lambda_code_zip_path
  source_code_hash = filebase64sha256(var.lambda_code_zip_path)

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      DYNAMODB_TABLE_NAME    = var.dynamodb_table_name
      AWS_REGION             = var.aws_region
      ENV                    = var.environment
      WEBSOCKET_API_ENDPOINT = var.websocket_api_endpoint
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.websocket_message,
    aws_iam_role_policy_attachment.lambda_logs,
  ]

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ws-message"
    Environment = var.environment
    Function    = "websocket-message"
  })
}

# ==========================================
# CloudWatch Log Groups
# ==========================================

resource "aws_cloudwatch_log_group" "api_handler" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-api-handler"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-api-handler-logs"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "websocket_connect" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-ws-connect"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ws-connect-logs"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "websocket_disconnect" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-ws-disconnect"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ws-disconnect-logs"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "websocket_message" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-ws-message"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-ws-message-logs"
    Environment = var.environment
  })
}

# ==========================================
# IAM Role & Policies
# ==========================================

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.project_name}-${var.environment}-lambda-execution"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-lambda-execution"
    Environment = var.environment
  })
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# CloudWatch Logs Policy
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC Execution Policy (if VPC is used)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count      = var.vpc_id != "" ? 1 : 0
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# X-Ray Tracing Policy
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count      = var.enable_xray ? 1 : 0
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Custom Lambda Policies
resource "aws_iam_role_policy" "lambda_permissions" {
  name   = "${var.project_name}-${var.environment}-lambda-permissions"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

data "aws_iam_policy_document" "lambda_permissions" {
  # DynamoDB Access
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
    ]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_table_name}",
      "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_table_name}/index/*",
    ]
  }

  # S3 Access
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.s3_bucket_name}",
      "arn:aws:s3:::${var.s3_bucket_name}/*",
      "arn:aws:s3:::${var.user_data_bucket_name}",
      "arn:aws:s3:::${var.user_data_bucket_name}/*",
    ]
  }

  # ECS RunTask (für Deployment Orchestrator)
  statement {
    effect = "Allow"
    actions = [
      "ecs:RunTask",
      "ecs:DescribeTasks",
      "ecs:StopTask",
    ]
    resources = [
      var.ecs_task_definition_arn,
      "arn:aws:ecs:${var.aws_region}:*:task/${var.ecs_cluster_name}/*",
    ]
  }

  # IAM PassRole für ECS Task Execution
  statement {
    effect = "Allow"
    actions = [
      "iam:PassRole",
    ]
    resources = [
      "arn:aws:iam::*:role/${var.project_name}-${var.environment}-ecs-task-execution",
      "arn:aws:iam::*:role/${var.project_name}-${var.environment}-ecs-task-role",
    ]
  }

  # Secrets Manager (für JWT Secret, Stripe, etc.)
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = compact([
      var.jwt_secret_arn,
      var.stripe_secret_key_arn,
      var.stripe_webhook_secret_arn,
    ])
  }

  # API Gateway Management API (für WebSocket postToConnection)
  statement {
    effect = "Allow"
    actions = [
      "execute-api:ManageConnections",
    ]
    resources = [
      "arn:aws:execute-api:${var.aws_region}:*:${var.websocket_api_id}/*",
    ]
  }

  # CloudWatch Logs (zusätzlich zu BasicExecutionRole)
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project_name}-${var.environment}-*",
    ]
  }
}

# ==========================================
# Security Group (if VPC is used)
# ==========================================

resource "aws_security_group" "lambda" {
  count       = var.vpc_id != "" ? 1 : 0
  name        = "${var.project_name}-${var.environment}-lambda-sg"
  description = "Security Group for Lambda Functions"
  vpc_id      = var.vpc_id

  # Outbound: Allow all (Lambda needs to access AWS services)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-lambda-sg"
    Environment = var.environment
  })
}

# ==========================================
# Secrets Manager (fetch values)
# ==========================================

data "aws_secretsmanager_secret_version" "jwt_secret" {
  count     = var.jwt_secret_arn != "" ? 1 : 0
  secret_id = var.jwt_secret_arn
}

data "aws_secretsmanager_secret_version" "stripe_secret" {
  count     = var.stripe_secret_key_arn != "" ? 1 : 0
  secret_id = var.stripe_secret_key_arn
}

data "aws_secretsmanager_secret_version" "stripe_webhook" {
  count     = var.stripe_webhook_secret_arn != "" ? 1 : 0
  secret_id = var.stripe_webhook_secret_arn
}
