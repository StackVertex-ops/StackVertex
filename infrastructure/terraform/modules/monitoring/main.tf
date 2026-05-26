# Monitoring & Observability Module
# Zentrales Monitoring für komplette StackVertex Infrastruktur

terraform {
  required_version = ">= 1.5.0"
}

# SNS Topic für Alerts (Critical)
resource "aws_sns_topic" "critical_alerts" {
  name              = "${var.project_name}-${var.environment}-critical-alerts"
  display_name      = "StackVertex Critical Alerts"
  kms_master_key_id = var.enable_sns_encryption ? aws_kms_key.sns[0].id : null

  tags = {
    Name     = "${var.project_name}-${var.environment}-critical-alerts"
    Severity = "critical"
  }
}

# SNS Topic für Warnings
resource "aws_sns_topic" "warning_alerts" {
  name              = "${var.project_name}-${var.environment}-warning-alerts"
  display_name      = "StackVertex Warning Alerts"
  kms_master_key_id = var.enable_sns_encryption ? aws_kms_key.sns[0].id : null

  tags = {
    Name     = "${var.project_name}-${var.environment}-warning-alerts"
    Severity = "warning"
  }
}

# SNS Topic für Info
resource "aws_sns_topic" "info_alerts" {
  name         = "${var.project_name}-${var.environment}-info-alerts"
  display_name = "StackVertex Info Alerts"

  tags = {
    Name     = "${var.project_name}-${var.environment}-info-alerts"
    Severity = "info"
  }
}

# Email Subscription für Critical Alerts
resource "aws_sns_topic_subscription" "critical_email" {
  count     = length(var.critical_alert_emails)
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "email"
  endpoint  = var.critical_alert_emails[count.index]
}

# Email Subscription für Warnings
resource "aws_sns_topic_subscription" "warning_email" {
  count     = length(var.warning_alert_emails)
  topic_arn = aws_sns_topic.warning_alerts.arn
  protocol  = "email"
  endpoint  = var.warning_alert_emails[count.index]
}

# Slack Webhook (Optional)
resource "aws_sns_topic_subscription" "critical_slack" {
  count     = var.slack_webhook_url != null ? 1 : 0
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

# KMS Key für SNS Encryption
resource "aws_kms_key" "sns" {
  count                   = var.enable_sns_encryption ? 1 : 0
  description             = "KMS key for SNS topic encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch to use the key"
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Dashboard - Gesamtübersicht
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-overview"

  dashboard_body = jsonencode({
    widgets = [
      # Lambda Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { stat = "Sum", label = "Total Invocations" }],
            [".", "Errors", { stat = "Sum", label = "Errors" }],
            [".", "Throttles", { stat = "Sum", label = "Throttles" }],
            [".", "Duration", { stat = "Average", label = "Avg Duration" }],
            [".", "ConcurrentExecutions", { stat = "Maximum", label = "Max Concurrent" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Performance"
          yAxis = {
            left = {
              label = "Count"
            }
          }
        }
      },
      # API Gateway Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", { stat = "Sum", label = "Requests" }],
            [".", "4XXError", { stat = "Sum", label = "4XX Errors" }],
            [".", "5XXError", { stat = "Sum", label = "5XX Errors" }],
            [".", "Latency", { stat = "Average", label = "Latency" }]
          ]
          period = 300
          region = var.aws_region
          title  = "API Gateway Performance"
        }
      },
      # Aurora Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average", label = "CPU %" }],
            [".", "DatabaseConnections", { stat = "Average", label = "Connections" }],
            [".", "ServerlessDatabaseCapacity", { stat = "Average", label = "ACUs" }],
            [".", "ReadLatency", { stat = "Average", label = "Read Latency" }],
            [".", "WriteLatency", { stat = "Average", label = "Write Latency" }]
          ]
          period = 300
          region = var.aws_region
          title  = "Aurora Database Performance"
        }
      },
      # S3 Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/S3", "BucketSizeBytes", { stat = "Average", label = "Bucket Size" }],
            [".", "NumberOfObjects", { stat = "Average", label = "Object Count" }]
          ]
          period = 86400
          region = var.aws_region
          title  = "S3 Storage"
        }
      },
      # Error Rate (Calculated)
      {
        type = "metric"
        properties = {
          metrics = [
            [
              { expression = "m2/m1*100", label = "Error Rate %", id = "e1" }
            ],
            ["AWS/Lambda", "Invocations", { id = "m1", visible = false }],
            [".", "Errors", { id = "m2", visible = false }]
          ]
          period = 300
          region = var.aws_region
          title  = "Error Rate"
          yAxis = {
            left = {
              label = "Percentage"
              max   = 100
            }
          }
        }
      },
      # Logs Insights Query Widget
      {
        type = "log"
        properties = {
          query   = "SOURCE '/aws/lambda/${var.lambda_function_name}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20"
          region  = var.aws_region
          title   = "Recent Errors (Last 20)"
          stacked = false
        }
      }
    ]
  })
}

# Lambda Alarms - Critical
resource "aws_cloudwatch_metric_alarm" "lambda_errors_critical" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-errors-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold_critical
  alarm_description   = "CRITICAL: Lambda error count exceeded ${var.lambda_error_threshold_critical}"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  ok_actions          = [aws_sns_topic.info_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = {
    Severity = "critical"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "CRITICAL: Lambda is being throttled"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = {
    Severity = "critical"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-duration-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = var.lambda_timeout_ms * 0.8 # 80% of timeout
  alarm_description   = "WARNING: Lambda duration approaching timeout"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = {
    Severity = "warning"
  }
}

# API Gateway Alarms
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-api-5xx-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = var.api_5xx_threshold_critical
  alarm_description   = "CRITICAL: API Gateway 5XX errors exceeded ${var.api_5xx_threshold_critical}"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_gateway_id
  }

  tags = {
    Severity = "critical"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-api-4xx-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = var.api_4xx_threshold_warning
  alarm_description   = "WARNING: API Gateway 4XX errors exceeded ${var.api_4xx_threshold_warning}"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_gateway_id
  }

  tags = {
    Severity = "warning"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "${var.project_name}-${var.environment}-api-latency-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Average"
  threshold           = var.api_latency_threshold_ms
  alarm_description   = "WARNING: API Gateway latency exceeded ${var.api_latency_threshold_ms}ms"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_gateway_id
  }

  tags = {
    Severity = "warning"
  }
}

# Aurora Database Alarms
resource "aws_cloudwatch_metric_alarm" "aurora_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-aurora-cpu-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CRITICAL: Aurora CPU utilization > 80%"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBClusterIdentifier = var.db_cluster_id
  }

  tags = {
    Severity = "critical"
  }
}

resource "aws_cloudwatch_metric_alarm" "aurora_connections" {
  alarm_name          = "${var.project_name}-${var.environment}-aurora-connections-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.aurora_max_connections * 0.8
  alarm_description   = "WARNING: Aurora connections > 80% of max"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBClusterIdentifier = var.db_cluster_id
  }

  tags = {
    Severity = "warning"
  }
}

resource "aws_cloudwatch_metric_alarm" "aurora_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-aurora-storage-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "VolumeBytesUsed"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.aurora_storage_threshold_bytes
  alarm_description   = "WARNING: Aurora storage usage high"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBClusterIdentifier = var.db_cluster_id
  }

  tags = {
    Severity = "warning"
  }
}

# Composite Alarm - Gesamtsystem Health
resource "aws_cloudwatch_composite_alarm" "system_health" {
  alarm_name          = "${var.project_name}-${var.environment}-system-health"
  alarm_description   = "Overall system health - triggers if multiple critical alarms fire"
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  ok_actions          = [aws_sns_topic.info_alerts.arn]

  alarm_rule = join(" OR ", [
    "ALARM(${aws_cloudwatch_metric_alarm.lambda_errors_critical.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.api_5xx_errors.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.aurora_cpu.alarm_name})"
  ])

  tags = {
    Severity = "critical"
  }
}

# Log Metric Filters - Custom Metrics aus Logs
resource "aws_cloudwatch_log_metric_filter" "deployment_failures" {
  name           = "${var.project_name}-${var.environment}-deployment-failures"
  log_group_name = var.lambda_log_group_name
  pattern        = "[timestamp, request_id, level = ERROR, msg = *deployment*failed*]"

  metric_transformation {
    name      = "DeploymentFailures"
    namespace = "StackVertex/${var.environment}"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "deployment_failures" {
  alarm_name          = "${var.project_name}-${var.environment}-deployment-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DeploymentFailures"
  namespace           = "StackVertex/${var.environment}"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "CRITICAL: Multiple deployment failures detected"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Severity = "critical"
  }
}

# Security: Unauthorized Access Attempts
resource "aws_cloudwatch_log_metric_filter" "unauthorized_access" {
  name           = "${var.project_name}-${var.environment}-unauthorized-access"
  log_group_name = var.lambda_log_group_name
  pattern        = "[timestamp, request_id, level, msg = *Unauthorized* || msg = *403* || msg = *401*]"

  metric_transformation {
    name      = "UnauthorizedAccessAttempts"
    namespace = "StackVertex/${var.environment}"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "unauthorized_access" {
  alarm_name          = "${var.project_name}-${var.environment}-unauthorized-access"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnauthorizedAccessAttempts"
  namespace           = "StackVertex/${var.environment}"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "WARNING: Multiple unauthorized access attempts detected"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Severity = "warning"
  }
}

# CloudWatch Insights Saved Queries
resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${var.project_name}-${var.environment}-error-analysis"

  log_group_names = [
    var.lambda_log_group_name
  ]

  query_string = <<-EOQ
    fields @timestamp, @message, level, request_id
    | filter level = "ERROR"
    | stats count() by bin(5m)
    | sort @timestamp desc
  EOQ
}

resource "aws_cloudwatch_query_definition" "slow_requests" {
  name = "${var.project_name}-${var.environment}-slow-requests"

  log_group_names = [
    var.lambda_log_group_name
  ]

  query_string = <<-EOQ
    fields @timestamp, @message, duration_ms, request_path
    | filter duration_ms > 1000
    | sort duration_ms desc
    | limit 50
  EOQ
}

resource "aws_cloudwatch_query_definition" "deployment_history" {
  name = "${var.project_name}-${var.environment}-deployment-history"

  log_group_names = [
    var.lambda_log_group_name
  ]

  query_string = <<-EOQ
    fields @timestamp, deployment_id, status, customer_id
    | filter @message like /deployment/
    | sort @timestamp desc
  EOQ
}
