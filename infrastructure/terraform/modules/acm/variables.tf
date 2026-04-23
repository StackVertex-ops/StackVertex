# ACM Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for DNS validation"
  type        = string
}

# Frontend Certificate
variable "create_frontend_certificate" {
  description = "Create SSL certificate for frontend"
  type        = bool
  default     = true
}

variable "frontend_domain" {
  description = "Frontend domain name (e.g., app.yourcompany.com or yourcompany.com)"
  type        = string
}

variable "frontend_additional_domains" {
  description = "Additional domains for frontend certificate (e.g., www.yourcompany.com)"
  type        = list(string)
  default     = []
}

# API Certificate
variable "create_api_certificate" {
  description = "Create SSL certificate for API"
  type        = bool
  default     = true
}

variable "api_domain" {
  description = "API domain name (e.g., api.yourcompany.com)"
  type        = string
  default     = ""
}

variable "api_additional_domains" {
  description = "Additional domains for API certificate"
  type        = list(string)
  default     = []
}
