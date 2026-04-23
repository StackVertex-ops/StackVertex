# Monitoring Module Outputs

output "critical_alerts_topic_arn" {
  description = "SNS topic ARN for critical alerts"
  value       = aws_sns_topic.critical_alerts.arn
}

output "warning_alerts_topic_arn" {
  description = "SNS topic ARN for warning alerts"
  value       = aws_sns_topic.warning_alerts.arn
}

output "info_alerts_topic_arn" {
  description = "SNS topic ARN for info alerts"
  value       = aws_sns_topic.info_alerts.arn
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "all_alarm_names" {
  description = "List of all CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.lambda_errors_critical.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_throttles.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_duration.alarm_name,
    aws_cloudwatch_metric_alarm.api_5xx_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_4xx_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_latency.alarm_name,
    aws_cloudwatch_metric_alarm.aurora_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.aurora_connections.alarm_name,
    aws_cloudwatch_metric_alarm.aurora_storage.alarm_name,
    aws_cloudwatch_metric_alarm.deployment_failures.alarm_name,
    aws_cloudwatch_metric_alarm.unauthorized_access.alarm_name
  ]
}
