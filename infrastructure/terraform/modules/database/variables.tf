# Database Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for Aurora"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for Aurora"
  type        = string
}

variable "postgres_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "overcloud"
}

variable "master_username" {
  description = "Master username for Aurora"
  type        = string
  default     = "overcloud_admin"
  sensitive   = true
}

variable "master_password" {
  description = "Master password for Aurora"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.master_password) >= 16
    error_message = "Master password must be at least 16 characters"
  }
}

variable "min_capacity" {
  description = "Minimum Aurora Serverless v2 capacity (ACUs)"
  type        = number
  default     = 0.5 # 0.5 ACU = ~1 GB RAM
}

variable "max_capacity" {
  description = "Maximum Aurora Serverless v2 capacity (ACUs)"
  type        = number
  default     = 2 # 2 ACU = ~4 GB RAM
}

variable "instance_count" {
  description = "Number of Aurora instances (min 1 for serverless v2)"
  type        = number
  default     = 1
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on destroy (set false for prod!)"
  type        = bool
  default     = true
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights"
  type        = bool
  default     = false # True für prod
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = false
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  type        = string
  default     = null
}

variable "max_connections_threshold" {
  description = "Threshold for max database connections alarm"
  type        = number
  default     = 100
}
