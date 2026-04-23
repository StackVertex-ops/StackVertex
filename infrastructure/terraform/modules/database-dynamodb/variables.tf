# DynamoDB Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "enable_pitr" {
  description = "Enable Point-in-Time Recovery (Backup)"
  type        = bool
  default     = false # True für prod
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption (optional)"
  type        = string
  default     = null
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = false
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  type        = string
  default     = null
}
