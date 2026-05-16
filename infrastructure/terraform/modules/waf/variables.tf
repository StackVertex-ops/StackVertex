# WAF Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

# WAF Configuration
variable "enable_cloudfront_waf" {
  description = "Enable WAF for CloudFront distribution (global)"
  type        = bool
  default     = false
}

variable "enable_regional_waf" {
  description = "Enable WAF for ALB (regional)"
  type        = bool
  default     = false
}

variable "rate_limit_requests" {
  description = "Maximum requests per IP per 5 minutes (rate limiting)"
  type        = number
  default     = 2000 # 2000 requests / 5 min = safe default
}

# Geo-Blocking (Optional)
variable "enable_geo_blocking" {
  description = "Enable geo-blocking to only allow specific countries"
  type        = bool
  default     = false # Cost-effective way to reduce attack surface
}

variable "allowed_countries" {
  description = "List of allowed country codes (ISO 3166-1 alpha-2) when geo-blocking is enabled"
  type        = list(string)
  default     = ["DE", "AT", "CH", "US", "GB", "FR", "NL", "BE"] # EU + US by default
}

# Bot Control (PAID: ~$10/month)
variable "enable_bot_control" {
  description = "Enable AWS Managed Bot Control rules (PAID: ~$10/month). Only enable for production if budget allows"
  type        = bool
  default     = false # Default: disabled for cost savings
}

# Rule Exclusions (for false positives)
variable "waf_rule_exclusions" {
  description = "List of AWS Managed Rules to exclude if they cause false positives"
  type        = list(string)
  default     = [] # Add rule names here if needed, e.g., ["SizeRestrictions_BODY"]
}

# WAF Logging
variable "enable_waf_logging" {
  description = "Enable WAF logging to CloudWatch (for forensics and debugging)"
  type        = bool
  default     = true
}

variable "waf_log_retention_days" {
  description = "Number of days to retain WAF logs in CloudWatch"
  type        = number
  default     = 30 # Prod: 30, Staging: 14, Dev: 7
}

# CloudWatch Alarms
variable "enable_waf_alarms" {
  description = "Enable CloudWatch alarms for WAF (high blocked requests = possible attack)"
  type        = bool
  default     = true
}

variable "blocked_requests_threshold" {
  description = "Threshold for blocked requests alarm (triggers when exceeded)"
  type        = number
  default     = 1000 # 1000 blocked requests in 5 min = likely attack
}

variable "alarm_sns_topic_arns" {
  description = "List of SNS topic ARNs to send alarm notifications to"
  type        = list(string)
  default     = []
}

# ALB Association
variable "alb_arn" {
  description = "ARN of the Application Load Balancer to associate with regional WAF (optional)"
  type        = string
  default     = null
}
