/**
 * Lambda API Module - Variables
 */

# ==========================================
# Project Configuration
# ==========================================

variable "project_name" {
  description = "Project name (e.g., stackvertex)"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

# ==========================================
# Lambda Configuration
# ==========================================

variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds (max 900)"
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout <= 900
    error_message = "Lambda timeout cannot exceed 900 seconds (15 minutes)."
  }
}

variable "lambda_memory" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory >= 128 && var.lambda_memory <= 10240
    error_message = "Lambda memory must be between 128 MB and 10240 MB."
  }
}

variable "lambda_code_zip_path" {
  description = "Path to Lambda code ZIP file"
  type        = string
}

variable "lambda_layer_zip_path" {
  description = "Path to Lambda layer ZIP file (dependencies)"
  type        = string
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

# ==========================================
# Networking (optional)
# ==========================================

variable "vpc_id" {
  description = "VPC ID for Lambda (optional, leave empty for no VPC)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for Lambda (private subnets recommended)"
  type        = list(string)
  default     = []
}

# ==========================================
# DynamoDB Configuration
# ==========================================

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "dynamodb_endpoint_url" {
  description = "DynamoDB endpoint URL (for local testing)"
  type        = string
  default     = ""
}

# ==========================================
# S3 Configuration
# ==========================================

variable "s3_bucket_name" {
  description = "S3 bucket for large items"
  type        = string
}

variable "user_data_bucket_name" {
  description = "S3 bucket for user data uploads"
  type        = string
}

variable "large_item_threshold" {
  description = "Threshold for storing items in S3 (bytes)"
  type        = number
  default     = 300000
}

# ==========================================
# ECS Configuration (für Deployment Orchestrator)
# ==========================================

variable "ecs_cluster_name" {
  description = "ECS Cluster name for deployment workers"
  type        = string
}

variable "ecs_task_definition_arn" {
  description = "ECS Task Definition ARN for deployment workers"
  type        = string
}

variable "ecs_subnets" {
  description = "ECS Subnets for deployment workers"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "ECS Security Group ID for deployment workers"
  type        = string
}

# ==========================================
# Security (Secrets Manager)
# ==========================================

variable "jwt_secret_arn" {
  description = "Secrets Manager ARN for JWT Secret"
  type        = string
  default     = ""
}

variable "jwt_algorithm" {
  description = "JWT Algorithm"
  type        = string
  default     = "HS256"
}

variable "access_token_expire_minutes" {
  description = "Access Token expiration in minutes"
  type        = number
  default     = 15
}

variable "refresh_token_expire_days" {
  description = "Refresh Token expiration in days"
  type        = number
  default     = 7
}

# ==========================================
# Stripe (optional)
# ==========================================

variable "stripe_enabled" {
  description = "Enable Stripe integration"
  type        = bool
  default     = false
}

variable "stripe_secret_key_arn" {
  description = "Secrets Manager ARN for Stripe Secret Key"
  type        = string
  default     = ""
}

variable "stripe_webhook_secret_arn" {
  description = "Secrets Manager ARN for Stripe Webhook Secret"
  type        = string
  default     = ""
}

# ==========================================
# WebSocket Configuration
# ==========================================

variable "websocket_api_id" {
  description = "API Gateway WebSocket API ID"
  type        = string
  default     = ""
}

variable "websocket_api_endpoint" {
  description = "API Gateway WebSocket API Endpoint"
  type        = string
  default     = ""
}

# ==========================================
# Extra Environment Variables
# ==========================================

variable "extra_environment_variables" {
  description = "Additional environment variables for Lambda"
  type        = map(string)
  default     = {}
}
