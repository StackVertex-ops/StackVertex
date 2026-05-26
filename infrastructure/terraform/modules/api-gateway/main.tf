/**
 * API Gateway Module
 *
 * Erstellt:
 * - HTTP API (API Gateway v2) für REST Endpoints
 * - WebSocket API für Real-time Deployment Updates
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ==========================================
# HTTP API (REST)
# ==========================================

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project_name}-${var.environment}-http-api"
  protocol_type = "HTTP"
  description   = "StackVertex HTTP API"

  cors_configuration {
    allow_origins     = var.cors_allow_origins
    allow_methods     = var.cors_allow_methods
    allow_headers     = var.cors_allow_headers
    expose_headers    = var.cors_expose_headers
    allow_credentials = var.cors_allow_credentials
    max_age           = var.cors_max_age
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-http-api"
    Environment = var.environment
  })
}

# HTTP API Integration (Lambda)
resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.http.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.lambda_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds = var.integration_timeout_ms
}

# HTTP API Default Route (catch-all)
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# HTTP API Stage
resource "aws_apigatewayv2_stage" "http" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = var.stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.throttle_burst_limit
    throttling_rate_limit  = var.throttle_rate_limit
  }

  # Access Logs
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.http_api.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-http-stage"
    Environment = var.environment
  })
}

# Lambda Permission für API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# CloudWatch Log Group für HTTP API
resource "aws_cloudwatch_log_group" "http_api" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}-http"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-http-api-logs"
    Environment = var.environment
  })
}

# ==========================================
# WebSocket API
# ==========================================

resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${var.project_name}-${var.environment}-websocket-api"
  protocol_type              = "WEBSOCKET"
  description                = "StackVertex WebSocket API for Real-time Updates"
  route_selection_expression = "$request.body.action"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-websocket-api"
    Environment = var.environment
  })
}

# WebSocket Integration: $connect
resource "aws_apigatewayv2_integration" "connect" {
  api_id             = aws_apigatewayv2_api.websocket.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.websocket_lambda_arns["connect"]
  integration_method = "POST"
  content_handling_strategy = "CONVERT_TO_TEXT"
}

# WebSocket Integration: $disconnect
resource "aws_apigatewayv2_integration" "disconnect" {
  api_id             = aws_apigatewayv2_api.websocket.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.websocket_lambda_arns["disconnect"]
  integration_method = "POST"
  content_handling_strategy = "CONVERT_TO_TEXT"
}

# WebSocket Integration: $default
resource "aws_apigatewayv2_integration" "default_ws" {
  api_id             = aws_apigatewayv2_api.websocket.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.websocket_lambda_arns["message"]
  integration_method = "POST"
  content_handling_strategy = "CONVERT_TO_TEXT"
}

# WebSocket Route: $connect
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.connect.id}"
}

# WebSocket Route: $disconnect
resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.disconnect.id}"
}

# WebSocket Route: $default
resource "aws_apigatewayv2_route" "default_ws" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.default_ws.id}"
}

# WebSocket Stage
resource "aws_apigatewayv2_stage" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = var.stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.throttle_burst_limit
    throttling_rate_limit  = var.throttle_rate_limit
  }

  # Access Logs
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.websocket_api.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      connectionId     = "$context.connectionId"
      eventType        = "$context.eventType"
      routeKey         = "$context.routeKey"
      status           = "$context.status"
      requestTime      = "$context.requestTime"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-websocket-stage"
    Environment = var.environment
  })
}

# Lambda Permissions für WebSocket API
resource "aws_lambda_permission" "websocket_connect" {
  statement_id  = "AllowWebSocketConnectInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.websocket_lambda_function_names["connect"]
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/$connect"
}

resource "aws_lambda_permission" "websocket_disconnect" {
  statement_id  = "AllowWebSocketDisconnectInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.websocket_lambda_function_names["disconnect"]
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/$disconnect"
}

resource "aws_lambda_permission" "websocket_message" {
  statement_id  = "AllowWebSocketMessageInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.websocket_lambda_function_names["message"]
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/$default"
}

# CloudWatch Log Group für WebSocket API
resource "aws_cloudwatch_log_group" "websocket_api" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}-websocket"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-websocket-api-logs"
    Environment = var.environment
  })
}

# ==========================================
# Custom Domain (optional)
# ==========================================

resource "aws_apigatewayv2_domain_name" "http" {
  count       = var.custom_domain_name != "" ? 1 : 0
  domain_name = var.custom_domain_name

  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-http-domain"
    Environment = var.environment
  })
}

resource "aws_apigatewayv2_api_mapping" "http" {
  count       = var.custom_domain_name != "" ? 1 : 0
  api_id      = aws_apigatewayv2_api.http.id
  domain_name = aws_apigatewayv2_domain_name.http[0].id
  stage       = aws_apigatewayv2_stage.http.id
}

resource "aws_apigatewayv2_domain_name" "websocket" {
  count       = var.websocket_custom_domain_name != "" ? 1 : 0
  domain_name = var.websocket_custom_domain_name

  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-websocket-domain"
    Environment = var.environment
  })
}

resource "aws_apigatewayv2_api_mapping" "websocket" {
  count       = var.websocket_custom_domain_name != "" ? 1 : 0
  api_id      = aws_apigatewayv2_api.websocket.id
  domain_name = aws_apigatewayv2_domain_name.websocket[0].id
  stage       = aws_apigatewayv2_stage.websocket.id
}

# ==========================================
# WAF (optional)
# ==========================================

resource "aws_wafv2_web_acl_association" "http" {
  count        = var.waf_acl_arn != "" ? 1 : 0
  resource_arn = aws_apigatewayv2_stage.http.arn
  web_acl_arn  = var.waf_acl_arn
}
