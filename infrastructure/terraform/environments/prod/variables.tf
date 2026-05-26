# Production Environment Variables

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "stackvertex"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "dr_region" {
  description = "Disaster Recovery (secondary) AWS region for cross-region backups"
  type        = string
  default     = "eu-west-1" # Ireland as DR region
}

# Networking
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.2.0.0/16" # Prod: 10.2.x.x (unterscheidet sich von dev 10.0.x.x und staging 10.1.x.x)
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
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for critical alerts"
  type        = string
  default     = null
  sensitive   = true
}

variable "pagerduty_endpoint" {
  description = "PagerDuty integration endpoint for 24/7 on-call alerts"
  type        = string
  default     = null
  sensitive   = true
}

# CORS
variable "cors_origins" {
  description = "Allowed CORS origins for API"
  type        = string
  default     = "https://app.stackvertex.io" # Prod Frontend URL
}

# Domain & DNS
variable "domain_name" {
  description = "Primary domain name (e.g., stackvertex.io)"
  type        = string
  default     = "stackvertex.io"
}

variable "create_acm_certificate" {
  description = "Create ACM certificate for domain (requires Route53 hosted zone)"
  type        = bool
  default     = true
}

variable "create_route53_zone" {
  description = "Create Route53 hosted zone for domain"
  type        = bool
  default     = true
}

variable "enable_cloudfront" {
  description = "Enable CloudFront CDN for frontend"
  type        = bool
  default     = true
}

variable "cloudfront_price_class" {
  description = "CloudFront price class (PriceClass_All, PriceClass_200, PriceClass_100)"
  type        = string
  default     = "PriceClass_100" # US, Canada, Europe (günstiger als worldwide)
}
