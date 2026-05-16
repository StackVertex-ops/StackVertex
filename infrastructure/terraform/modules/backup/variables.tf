# Backup Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "Primary AWS region"
  type        = string
}

variable "dr_region" {
  description = "Disaster Recovery (secondary) AWS region"
  type        = string
  default     = "eu-west-1"
}

# KMS Encryption
variable "kms_key_arn" {
  description = "KMS key ARN for backup vault encryption (primary region)"
  type        = string
  default     = null # Uses AWS managed key if not provided
}

variable "dr_kms_key_arn" {
  description = "KMS key ARN for DR backup vault encryption (secondary region)"
  type        = string
  default     = null
}

# Backup Retention
variable "daily_backup_retention_days" {
  description = "Retention period for daily backups (days)"
  type        = number
  default     = 7
}

variable "weekly_backup_retention_days" {
  description = "Retention period for weekly backups (days)"
  type        = number
  default     = 30
}

variable "monthly_backup_retention_days" {
  description = "Retention period for monthly backups (days)"
  type        = number
  default     = 365
}

# Backup Plans
variable "enable_weekly_backups" {
  description = "Enable weekly backup plan (in addition to daily)"
  type        = bool
  default     = true
}

variable "enable_monthly_backups" {
  description = "Enable monthly backup plan (in addition to daily and weekly)"
  type        = bool
  default     = true
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup copy for disaster recovery"
  type        = bool
  default     = false
}

# Resources to Backup
variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs to backup"
  type        = list(string)
  default     = []
}

variable "aurora_cluster_arn" {
  description = "Aurora cluster ARN to backup (optional)"
  type        = string
  default     = null
}

# S3 Cross-Region Replication
variable "enable_s3_cross_region_replication" {
  description = "Enable S3 cross-region replication (separate from AWS Backup)"
  type        = bool
  default     = false
}

variable "s3_source_bucket_arns" {
  description = "List of source S3 bucket ARNs for replication"
  type        = list(string)
  default     = []
}

variable "s3_destination_bucket_arns" {
  description = "List of destination S3 bucket ARNs for replication"
  type        = list(string)
  default     = []
}

# Monitoring
variable "enable_backup_alarms" {
  description = "Enable CloudWatch alarms for backup failures"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arns" {
  description = "SNS topic ARNs for backup failure alerts"
  type        = list(string)
  default     = []
}
