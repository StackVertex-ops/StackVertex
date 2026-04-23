# Route53 Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "domain_name" {
  description = "Main domain name (e.g., yourcompany.com)"
  type        = string
}

variable "create_hosted_zone" {
  description = "Create new hosted zone (false if zone already exists)"
  type        = bool
  default     = false
}

# Frontend
variable "frontend_subdomain" {
  description = "Subdomain for frontend (empty string for root domain, null to skip)"
  type        = string
  default     = null
}

variable "cloudfront_frontend_domain_name" {
  description = "CloudFront domain name for frontend"
  type        = string
  default     = ""
}

# API
variable "api_subdomain" {
  description = "Subdomain for API (e.g., 'api' for api.yourcompany.com)"
  type        = string
  default     = null
}

variable "cloudfront_api_domain_name" {
  description = "CloudFront domain name for API (null if direct to API Gateway)"
  type        = string
  default     = null
}

variable "api_gateway_domain_name" {
  description = "API Gateway domain name (if not using CloudFront)"
  type        = string
  default     = ""
}

# Hosted Zone IDs
variable "cloudfront_hosted_zone_id" {
  description = "CloudFront hosted zone ID (global: Z2FDTNDATAQYW2)"
  type        = string
  default     = "Z2FDTNDATAQYW2" # CloudFront Global Hosted Zone
}

variable "api_gateway_hosted_zone_id" {
  description = "API Gateway regional hosted zone ID"
  type        = string
  default     = ""
}

# General
variable "enable_ipv6" {
  description = "Create AAAA records for IPv6"
  type        = bool
  default     = true
}

variable "verification_txt" {
  description = "TXT record for domain verification (optional)"
  type        = string
  default     = null
}

variable "mx_records" {
  description = "MX records for email (optional)"
  type        = list(string)
  default     = []
}
