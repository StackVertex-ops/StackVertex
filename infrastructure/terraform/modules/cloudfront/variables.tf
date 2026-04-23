# CloudFront Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# Frontend CloudFront
variable "frontend_bucket_id" {
  description = "S3 bucket ID for frontend"
  type        = string
}

variable "frontend_bucket_arn" {
  description = "S3 bucket ARN for frontend"
  type        = string
}

variable "frontend_bucket_domain_name" {
  description = "S3 bucket domain name for frontend"
  type        = string
}

variable "frontend_domain" {
  description = "Custom domain for frontend (e.g., app.yourcompany.com)"
  type        = string
  default     = null
}

variable "frontend_certificate_arn" {
  description = "ACM certificate ARN for frontend domain (must be in us-east-1!)"
  type        = string
}

# API CloudFront
variable "enable_api_cloudfront" {
  description = "Enable CloudFront for API Gateway"
  type        = bool
  default     = true
}

variable "api_gateway_domain_name" {
  description = "API Gateway domain name"
  type        = string
  default     = ""
}

variable "api_domain" {
  description = "Custom domain for API (e.g., api.yourcompany.com)"
  type        = string
  default     = null
}

variable "api_certificate_arn" {
  description = "ACM certificate ARN for API domain (must be in us-east-1!)"
  type        = string
  default     = ""
}

variable "api_cache_policy_id" {
  description = "CloudFront cache policy ID for API (optional, creates default if null)"
  type        = string
  default     = null
}

# General
variable "price_class" {
  description = "CloudFront price class (PriceClass_All, PriceClass_200, PriceClass_100)"
  type        = string
  default     = "PriceClass_100" # Nur US/EU (günstiger)

  validation {
    condition     = contains(["PriceClass_All", "PriceClass_200", "PriceClass_100"], var.price_class)
    error_message = "Price class must be PriceClass_All, PriceClass_200, or PriceClass_100"
  }
}
