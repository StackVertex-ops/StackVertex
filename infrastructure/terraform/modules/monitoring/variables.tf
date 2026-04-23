# Monitoring Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

# Alert Contacts
variable "critical_alert_emails" {
  description = "Email addresses for critical alerts"
  type        = list(string)
  default     = []
}

variable "warning_alert_emails" {
  description = "Email addresses for warning alerts"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for critical alerts"
  type        = string
  default     = null
  sensitive   = true
}

variable "enable_sns_encryption" {
  description = "Enable KMS encryption for SNS topics"
  type        = bool
  default     = true
}

# Resource IDs
variable "lambda_function_name" {
  description = "Lambda function name to monitor"
  type        = string
}

variable "lambda_log_group_name" {
  description = "Lambda CloudWatch log group name"
  type        = string
}

variable "api_gateway_id" {
  description = "API Gateway ID to monitor"
  type        = string
}

variable "db_cluster_id" {
  description = "Aurora cluster ID to monitor"
  type        = string
}

# Alarm Thresholds - Lambda
variable "lambda_error_threshold_critical" {
  description = "Number of Lambda errors before critical alarm"
  type        = number
  default     = 10
}

variable "lambda_timeout_ms" {
  description = "Lambda timeout in milliseconds"
  type        = number
  default     = 30000
}

# Alarm Thresholds - API Gateway
variable "api_5xx_threshold_critical" {
  description = "Number of 5XX errors before critical alarm"
  type        = number
  default     = 5
}

variable "api_4xx_threshold_warning" {
  description = "Number of 4XX errors before warning alarm"
  type        = number
  default     = 50
}

variable "api_latency_threshold_ms" {
  description = "API latency threshold in milliseconds"
  type        = number
  default     = 2000
}

# Alarm Thresholds - Aurora
variable "aurora_max_connections" {
  description = "Max Aurora connections (for threshold calculation)"
  type        = number
  default     = 100
}

variable "aurora_storage_threshold_bytes" {
  description = "Aurora storage threshold in bytes"
  type        = number
  default     = 10737418240 # 10 GB
}
