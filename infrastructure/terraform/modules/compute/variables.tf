# Compute Module Variables

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

# Lambda Configuration
variable "lambda_image_uri" {
  description = "Docker image URI for Lambda (ECR)"
  type        = string
  default     = null # Wird per CI/CD deployed
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

# VPC Configuration
variable "enable_vpc" {
  description = "Deploy Lambda in VPC (needed for Aurora access)"
  type        = bool
  default     = true
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for Lambda"
  type        = list(string)
  default     = []
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda"
  type        = string
  default     = ""
}

# Database Configuration (DynamoDB)
variable "dynamodb_table_name" {
  description = "DynamoDB table name for application data"
  type        = string
  default     = ""
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN for IAM permissions"
  type        = string
  default     = ""
}

# S3 Configuration
variable "deployment_bucket_name" {
  description = "S3 bucket name for customer deployments"
  type        = string
}

variable "deployment_bucket_arn" {
  description = "S3 bucket ARN for customer deployments"
  type        = string
}

variable "customer_data_bucket_name" {
  description = "S3 bucket name for customer application data"
  type        = string
  default     = null
}

variable "customer_data_bucket_arn" {
  description = "S3 bucket ARN for customer application data"
  type        = string
  default     = null
}

variable "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state"
  type        = string
}

# API Gateway Configuration
variable "enable_api_gateway" {
  description = "Enable API Gateway HTTP API"
  type        = bool
  default     = true
}

variable "enable_lambda_function_url" {
  description = "Enable Lambda Function URL (alternative to API Gateway)"
  type        = bool
  default     = false
}

variable "enable_websocket" {
  description = "Enable WebSocket API for real-time updates"
  type        = bool
  default     = true
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = "*"
}

# Environment Variables
variable "additional_environment_variables" {
  description = "Additional environment variables for Lambda"
  type        = map(string)
  default     = {}
}

# CloudWatch Alarms
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
