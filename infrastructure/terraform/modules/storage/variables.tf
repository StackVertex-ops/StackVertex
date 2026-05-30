# Storage Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "deployment_retention_days" {
  description = "Number of days to retain deployment states before deletion"
  type        = number
  default     = 730 # 2 years
}

variable "create_workspace_bucket" {
  description = "Create separate bucket for Terraform workspaces (temporary files)"
  type        = bool
  default     = false
}

# Customer Data Storage Variables
variable "enable_customer_data_versioning" {
  description = "Enable versioning for customer data bucket"
  type        = bool
  default     = true
}

variable "customer_data_encryption_type" {
  description = "Encryption type for customer data (AES256 or aws:kms)"
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.customer_data_encryption_type)
    error_message = "Encryption type must be AES256 or aws:kms"
  }
}

variable "create_customer_data_kms_key" {
  description = "Create dedicated KMS key for customer data encryption"
  type        = bool
  default     = false # True für prod empfohlen
}

variable "customer_data_kms_key_id" {
  description = "Existing KMS key ID for customer data (if not creating new one)"
  type        = string
  default     = null
}

variable "enable_customer_data_lifecycle" {
  description = "Enable lifecycle rules for customer data (transitions to cheaper storage)"
  type        = bool
  default     = true
}

variable "enable_customer_data_archival" {
  description = "Enable archival to Glacier for customer data"
  type        = bool
  default     = false # Nur für Backups/Archive sinnvoll
}

variable "customer_data_version_retention_days" {
  description = "Days to retain old versions of customer data"
  type        = number
  default     = 90
}

variable "enable_customer_data_cors" {
  description = "Enable CORS for customer data bucket (direct frontend access)"
  type        = bool
  default     = false
}

variable "customer_data_cors_origins" {
  description = "Allowed CORS origins for customer data bucket"
  type        = list(string)
  default     = []
}

variable "enable_customer_data_notifications" {
  description = "Enable S3 event notifications for customer data"
  type        = bool
  default     = false
}

variable "customer_data_notification_lambda_arn" {
  description = "Lambda ARN for S3 event notifications"
  type        = string
  default     = null
}

variable "lambda_execution_role_arn" {
  description = "Lambda execution role ARN for KMS key policy"
  type        = string
  default     = ""
}

# Frontend Storage Variables
variable "enable_frontend_versioning" {
  description = "Enable versioning for frontend bucket (for rollbacks)"
  type        = bool
  default     = false
}

variable "enable_public_website_access" {
  description = "Enable public read access for S3 website (dev: true, prod: false with CloudFront)"
  type        = bool
  default     = false
}

variable "enable_frontend_cors" {
  description = "Enable CORS for frontend bucket"
  type        = bool
  default     = false
}

variable "frontend_cors_origins" {
  description = "Allowed CORS origins for frontend bucket"
  type        = list(string)
  default     = ["*"]
}
