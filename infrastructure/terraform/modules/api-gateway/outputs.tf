/**
 * API Gateway Module - Outputs
 */

# ==========================================
# HTTP API
# ==========================================

output "http_api_id" {
  description = "HTTP API ID"
  value       = aws_apigatewayv2_api.http.id
}

output "http_api_endpoint" {
  description = "HTTP API default endpoint"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "http_api_invoke_url" {
  description = "HTTP API invoke URL (with stage)"
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/${var.stage_name}"
}

output "http_api_custom_domain_url" {
  description = "HTTP API custom domain URL (if configured)"
  value       = var.custom_domain_name != "" ? "https://${var.custom_domain_name}" : ""
}

output "http_api_execution_arn" {
  description = "HTTP API execution ARN"
  value       = aws_apigatewayv2_api.http.execution_arn
}

# ==========================================
# WebSocket API
# ==========================================

output "websocket_api_id" {
  description = "WebSocket API ID"
  value       = aws_apigatewayv2_api.websocket.id
}

output "websocket_api_endpoint" {
  description = "WebSocket API default endpoint"
  value       = aws_apigatewayv2_api.websocket.api_endpoint
}

output "websocket_api_invoke_url" {
  description = "WebSocket API invoke URL (with stage)"
  value       = "${replace(aws_apigatewayv2_api.websocket.api_endpoint, "wss://", "")}/${var.stage_name}"
}

output "websocket_api_connection_url" {
  description = "WebSocket API connection URL (wss://)"
  value       = "wss://${replace(aws_apigatewayv2_api.websocket.api_endpoint, "wss://", "")}/${var.stage_name}"
}

output "websocket_api_custom_domain_url" {
  description = "WebSocket API custom domain URL (if configured)"
  value       = var.websocket_custom_domain_name != "" ? "wss://${var.websocket_custom_domain_name}" : ""
}

output "websocket_api_execution_arn" {
  description = "WebSocket API execution ARN"
  value       = aws_apigatewayv2_api.websocket.execution_arn
}

# ==========================================
# Stages
# ==========================================

output "http_stage_id" {
  description = "HTTP API stage ID"
  value       = aws_apigatewayv2_stage.http.id
}

output "http_stage_invoke_url" {
  description = "HTTP API stage invoke URL"
  value       = aws_apigatewayv2_stage.http.invoke_url
}

output "websocket_stage_id" {
  description = "WebSocket API stage ID"
  value       = aws_apigatewayv2_stage.websocket.id
}

output "websocket_stage_invoke_url" {
  description = "WebSocket API stage invoke URL"
  value       = aws_apigatewayv2_stage.websocket.invoke_url
}

# ==========================================
# CloudWatch Log Groups
# ==========================================

output "http_log_group_name" {
  description = "HTTP API CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.http_api.name
}

output "websocket_log_group_name" {
  description = "WebSocket API CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.websocket_api.name
}

# ==========================================
# Custom Domains
# ==========================================

output "http_custom_domain_target" {
  description = "HTTP API custom domain target (for Route53)"
  value       = var.custom_domain_name != "" ? aws_apigatewayv2_domain_name.http[0].domain_name_configuration[0].target_domain_name : ""
}

output "websocket_custom_domain_target" {
  description = "WebSocket API custom domain target (for Route53)"
  value       = var.websocket_custom_domain_name != "" ? aws_apigatewayv2_domain_name.websocket[0].domain_name_configuration[0].target_domain_name : ""
}
