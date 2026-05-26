/**
 * Lambda API Module - Outputs
 */

# ==========================================
# Lambda Functions
# ==========================================

output "api_handler_function_arn" {
  description = "ARN of the API Handler Lambda Function"
  value       = aws_lambda_function.api_handler.arn
}

output "api_handler_function_name" {
  description = "Name of the API Handler Lambda Function"
  value       = aws_lambda_function.api_handler.function_name
}

output "api_handler_invoke_arn" {
  description = "Invoke ARN for API Handler (for API Gateway integration)"
  value       = aws_lambda_function.api_handler.invoke_arn
}

output "api_handler_qualified_arn" {
  description = "Qualified ARN of the API Handler Lambda Function"
  value       = aws_lambda_function.api_handler.qualified_arn
}

# ==========================================
# WebSocket Lambda Functions
# ==========================================

output "websocket_connect_function_arn" {
  description = "ARN of the WebSocket Connect Lambda Function"
  value       = aws_lambda_function.websocket_connect.arn
}

output "websocket_connect_invoke_arn" {
  description = "Invoke ARN for WebSocket Connect (for API Gateway integration)"
  value       = aws_lambda_function.websocket_connect.invoke_arn
}

output "websocket_disconnect_function_arn" {
  description = "ARN of the WebSocket Disconnect Lambda Function"
  value       = aws_lambda_function.websocket_disconnect.arn
}

output "websocket_disconnect_invoke_arn" {
  description = "Invoke ARN for WebSocket Disconnect (for API Gateway integration)"
  value       = aws_lambda_function.websocket_disconnect.invoke_arn
}

output "websocket_message_function_arn" {
  description = "ARN of the WebSocket Message Lambda Function"
  value       = aws_lambda_function.websocket_message.arn
}

output "websocket_message_invoke_arn" {
  description = "Invoke ARN for WebSocket Message (for API Gateway integration)"
  value       = aws_lambda_function.websocket_message.invoke_arn
}

output "websocket_lambda_arns" {
  description = "Map of WebSocket Lambda ARNs"
  value = {
    connect    = aws_lambda_function.websocket_connect.invoke_arn
    disconnect = aws_lambda_function.websocket_disconnect.invoke_arn
    message    = aws_lambda_function.websocket_message.invoke_arn
  }
}

# ==========================================
# IAM Role
# ==========================================

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda Execution Role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda Execution Role"
  value       = aws_iam_role.lambda_execution.name
}

# ==========================================
# Lambda Layer
# ==========================================

output "dependencies_layer_arn" {
  description = "ARN of the Dependencies Lambda Layer"
  value       = aws_lambda_layer_version.dependencies.arn
}

output "dependencies_layer_version" {
  description = "Version of the Dependencies Lambda Layer"
  value       = aws_lambda_layer_version.dependencies.version
}

# ==========================================
# CloudWatch Log Groups
# ==========================================

output "api_handler_log_group_name" {
  description = "Name of the API Handler CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.api_handler.name
}

output "websocket_log_group_names" {
  description = "Map of WebSocket Lambda CloudWatch Log Group names"
  value = {
    connect    = aws_cloudwatch_log_group.websocket_connect.name
    disconnect = aws_cloudwatch_log_group.websocket_disconnect.name
    message    = aws_cloudwatch_log_group.websocket_message.name
  }
}

# ==========================================
# Security Group (if VPC is used)
# ==========================================

output "lambda_security_group_id" {
  description = "Security Group ID for Lambda Functions (empty if no VPC)"
  value       = var.vpc_id != "" ? aws_security_group.lambda[0].id : ""
}
