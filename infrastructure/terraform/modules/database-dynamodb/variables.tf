# DynamoDB Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS Region (übernommen vom Provider, hier nur für Konsistenz)"
  type        = string
  default     = ""
}

variable "aws_account_id" {
  description = "AWS Account ID (übernommen vom Provider, hier nur für Konsistenz)"
  type        = string
  default     = ""
}

variable "billing_mode" {
  description = "DynamoDB billing mode (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "enable_point_in_time_recovery" {
  description = "Enable Point-in-Time Recovery (Backup)"
  type        = bool
  default     = false
}

variable "enable_automated_backups" {
  description = "Enable AWS Backup für DynamoDB (zusätzlich zu PITR)"
  type        = bool
  default     = false
}

variable "enable_ttl" {
  description = "Enable Time-To-Live für automatische Löschung"
  type        = bool
  default     = true
}

variable "ttl_attribute_name" {
  description = "TTL attribute name"
  type        = string
  default     = "ttl"
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
