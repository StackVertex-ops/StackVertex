# Dev Environment Variables

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "stackvertex"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

# Networking
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

# Database (LEGACY - PostgreSQL variables, not used anymore)
# DynamoDB hat keine Credentials - serverless!
# Diese Variables nur für Migration behalten:
# variable "database_name" {
#   description = "Database name"
#   type        = string
#   default     = "stackvertex"
# }
#
# variable "db_master_username" {
#   description = "Database master username"
#   type        = string
#   default     = "stackvertex_admin"
#   sensitive   = true
# }
#
# variable "db_master_password" {
#   description = "Database master password (min 16 chars)"
#   type        = string
#   sensitive   = true
#
#   validation {
#     condition     = length(var.db_master_password) >= 16
#     error_message = "Database password must be at least 16 characters"
#   }
# }

# Lambda
variable "lambda_image_uri" {
  description = "Lambda Docker image URI (ECR)"
  type        = string
  default     = null # Wird von CI/CD deployed
}

# Terraform State
variable "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state (from bootstrap)"
  type        = string
}

# Monitoring & Alerts
variable "alert_emails" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for critical alerts"
  type        = string
  default     = null
  sensitive   = true
}

# Security
variable "enable_security_hub" {
  description = "Enable AWS Security Hub (optional for dev)"
  type        = bool
  default     = false
}
