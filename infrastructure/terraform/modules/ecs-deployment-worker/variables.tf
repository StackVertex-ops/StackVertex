/**
 * ECS Deployment Worker Module - Variables
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
# ECS Configuration
# ==========================================

variable "task_cpu" {
  description = "ECS Task CPU units (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.task_cpu)
    error_message = "Task CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "task_memory" {
  description = "ECS Task memory in MB (depends on CPU)"
  type        = number
  default     = 1024

  validation {
    condition     = var.task_memory >= 512 && var.task_memory <= 30720
    error_message = "Task memory must be between 512 MB and 30720 MB."
  }
}

variable "container_image" {
  description = "Container image URL (ECR)"
  type        = string
}

variable "enable_container_insights" {
  description = "Enable ECS Container Insights (costs extra)"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

# ==========================================
# Networking
# ==========================================

variable "vpc_id" {
  description = "VPC ID for ECS Tasks"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS Tasks (private subnets recommended)"
  type        = list(string)
}

# ==========================================
# DynamoDB Configuration
# ==========================================

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
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

# ==========================================
# Security (Secrets Manager)
# ==========================================

variable "jwt_secret_arn" {
  description = "Secrets Manager ARN for JWT Secret"
  type        = string
  default     = ""
}

# ==========================================
# Extra Environment Variables
# ==========================================

variable "extra_environment_variables" {
  description = "Additional environment variables for ECS Task"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}
