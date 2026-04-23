# DynamoDB Module Outputs

output "table_name" {
  description = "Main DynamoDB table name"
  value       = aws_dynamodb_table.main.name
}

output "table_arn" {
  description = "Main DynamoDB table ARN"
  value       = aws_dynamodb_table.main.arn
}

output "websocket_table_name" {
  description = "WebSocket connections table name"
  value       = aws_dynamodb_table.websocket_connections.name
}

output "websocket_table_arn" {
  description = "WebSocket connections table ARN"
  value       = aws_dynamodb_table.websocket_connections.arn
}
