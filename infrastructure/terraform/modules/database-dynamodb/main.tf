# DynamoDB Module - Ultra-Low-Cost Alternative zu Aurora
# Single-Table-Design für alle Daten

terraform {
  required_version = ">= 1.5.0"
}

# Single DynamoDB Table für alle Entities
resource "aws_dynamodb_table" "main" {
  name           = "${var.project_name}-${var.environment}-main"
  billing_mode   = var.billing_mode
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # GSI für Queries nach Type
  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  # Time-To-Live für automatische Cleanup
  ttl {
    attribute_name = var.ttl_attribute_name
    enabled        = var.enable_ttl
  }

  # Point-in-Time Recovery (Backup)
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Server-Side Encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-main-table"
  }
}

# DynamoDB für WebSocket Connections
resource "aws_dynamodb_table" "websocket_connections" {
  name           = "${var.project_name}-${var.environment}-websocket-connections"
  billing_mode   = var.billing_mode
  hash_key       = "connectionId"

  attribute {
    name = "connectionId"
    type = "S"
  }

  # TTL: Connections älter als 2 Stunden werden automatisch gelöscht
  ttl {
    attribute_name = var.ttl_attribute_name
    enabled        = var.enable_ttl
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-websocket-connections"
  }
}

# CloudWatch Alarms (nur Critical)
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-dynamodb-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "DynamoDB is throttling requests"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    TableName = aws_dynamodb_table.main.name
  }
}
