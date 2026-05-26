variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "version_retention_days" {
  description = "Number of days to retain old object versions"
  type        = number
  default     = 90
}

variable "enable_glacier_transition" {
  description = "Enable automatic transition to Glacier storage class"
  type        = bool
  default     = false
}

variable "glacier_transition_days" {
  description = "Days after which to transition objects to Glacier"
  type        = number
  default     = 365
}

variable "allowed_cors_origins" {
  description = "Allowed CORS origins for direct browser uploads"
  type        = list(string)
  default = [
    "https://app.stackvertex.io",
    "https://staging.stackvertex.io"
  ]
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
