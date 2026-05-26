/**
 * API Gateway Module - Variables
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

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

# ==========================================
# HTTP API Configuration
# ==========================================

variable "lambda_invoke_arn" {
  description = "Lambda invoke ARN for HTTP API integration"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name for HTTP API"
  type        = string
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"
}

variable "integration_timeout_ms" {
  description = "Integration timeout in milliseconds (max 30000)"
  type        = number
  default     = 30000

  validation {
    condition     = var.integration_timeout_ms >= 50 && var.integration_timeout_ms <= 30000
    error_message = "Integration timeout must be between 50ms and 30000ms."
  }
}

# ==========================================
# CORS Configuration
# ==========================================

variable "cors_allow_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allow_methods" {
  description = "CORS allowed methods"
  type        = list(string)
  default     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
}

variable "cors_allow_headers" {
  description = "CORS allowed headers"
  type        = list(string)
  default     = ["*"]
}

variable "cors_expose_headers" {
  description = "CORS exposed headers"
  type        = list(string)
  default     = []
}

variable "cors_allow_credentials" {
  description = "CORS allow credentials"
  type        = bool
  default     = true
}

variable "cors_max_age" {
  description = "CORS max age in seconds"
  type        = number
  default     = 86400
}

# ==========================================
# Throttling Configuration
# ==========================================

variable "throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
}

variable "throttle_rate_limit" {
  description = "API Gateway throttle rate limit (requests per second)"
  type        = number
  default     = 2000
}

# ==========================================
# WebSocket API Configuration
# ==========================================

variable "websocket_lambda_arns" {
  description = "Map of WebSocket Lambda invoke ARNs (connect, disconnect, message)"
  type = map(string)
}

variable "websocket_lambda_function_names" {
  description = "Map of WebSocket Lambda function names (connect, disconnect, message)"
  type = map(string)
}

# ==========================================
# Custom Domain (optional)
# ==========================================

variable "custom_domain_name" {
  description = "Custom domain name for HTTP API (optional)"
  type        = string
  default     = ""
}

variable "websocket_custom_domain_name" {
  description = "Custom domain name for WebSocket API (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (required if custom domain is used)"
  type        = string
  default     = ""
}

# ==========================================
# WAF Configuration (optional)
# ==========================================

variable "waf_acl_arn" {
  description = "WAF Web ACL ARN (optional)"
  type        = string
  default     = ""
}

# ==========================================
# CloudWatch Logs
# ==========================================

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}
