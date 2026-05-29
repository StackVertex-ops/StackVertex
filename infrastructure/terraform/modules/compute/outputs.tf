# Compute Module Outputs

# Lambda
output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "lambda_role_arn" {
  description = "Lambda IAM role ARN"
  value       = aws_iam_role.lambda.arn
}

output "lambda_function_url" {
  description = "Lambda function URL (if enabled)"
  value       = var.enable_lambda_function_url ? aws_lambda_function_url.api[0].function_url : null
}

# ECR
output "ecr_repository_url" {
  description = "ECR repository URL for Lambda Docker images"
  value       = data.aws_ecr_repository.lambda.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name"
  value       = data.aws_ecr_repository.lambda.name
}

# S3
output "lambda_code_bucket" {
  description = "S3 bucket name for Lambda code"
  value       = aws_s3_bucket.lambda_code.id
}

# API Gateway HTTP
output "http_api_id" {
  description = "API Gateway HTTP API ID"
  value       = var.enable_api_gateway ? aws_apigatewayv2_api.http[0].id : null
}

output "http_api_endpoint" {
  description = "API Gateway HTTP API endpoint URL"
  value       = var.enable_api_gateway ? aws_apigatewayv2_api.http[0].api_endpoint : null
}

output "http_api_invoke_url" {
  description = "API Gateway HTTP API invoke URL"
  value       = var.enable_api_gateway ? "${aws_apigatewayv2_api.http[0].api_endpoint}/" : null
}

# WebSocket API
output "websocket_api_id" {
  description = "API Gateway WebSocket API ID"
  value       = var.enable_websocket ? aws_apigatewayv2_api.websocket[0].id : null
}

output "websocket_api_endpoint" {
  description = "API Gateway WebSocket API endpoint URL"
  value       = var.enable_websocket ? aws_apigatewayv2_api.websocket[0].api_endpoint : null
}

output "websocket_api_invoke_url" {
  description = "WebSocket API invoke URL"
  value       = var.enable_websocket ? "${replace(aws_apigatewayv2_api.websocket[0].api_endpoint, "wss://", "")}/${var.environment}" : null
}

# CloudWatch
output "lambda_log_group_name" {
  description = "Lambda CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda.name
}
