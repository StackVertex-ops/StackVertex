# Security Module Variables

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

# SNS Topic ARNs (from Monitoring Module)
variable "critical_alerts_topic_arn" {
  description = "SNS topic ARN for critical alerts"
  type        = string
}

variable "warning_alerts_topic_arn" {
  description = "SNS topic ARN for warning alerts"
  type        = string
}

variable "info_alerts_topic_arn" {
  description = "SNS topic ARN for info alerts"
  type        = string
}

# CloudTrail Settings
variable "cloudtrail_retention_days" {
  description = "Number of days to retain CloudTrail logs in S3"
  type        = number
  default     = 365
}

variable "cloudtrail_log_retention_days" {
  description = "Number of days to retain CloudTrail logs in CloudWatch"
  type        = number
  default     = 90
}

variable "enable_multi_region_trail" {
  description = "Enable multi-region CloudTrail"
  type        = bool
  default     = false # True für prod
}

variable "enable_advanced_event_selectors" {
  description = "Enable advanced event selectors for CloudTrail"
  type        = bool
  default     = false
}

# GuardDuty Settings
variable "enable_guardduty" {
  description = "Enable AWS GuardDuty threat detection"
  type        = bool
  default     = true
}

variable "guardduty_finding_frequency" {
  description = "GuardDuty finding publishing frequency"
  type        = string
  default     = "FIFTEEN_MINUTES"

  validation {
    condition     = contains(["FIFTEEN_MINUTES", "ONE_HOUR", "SIX_HOURS"], var.guardduty_finding_frequency)
    error_message = "Must be FIFTEEN_MINUTES, ONE_HOUR, or SIX_HOURS"
  }
}

# Security Hub Settings
variable "enable_security_hub" {
  description = "Enable AWS Security Hub"
  type        = bool
  default     = true
}
