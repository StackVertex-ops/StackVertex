# Bootstrap Variables

variable "project_name" {
  description = "Project name (used for resource naming)"
  type        = string
  default     = "overcloud"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1" # Frankfurt
}

variable "aws_account_id" {
  description = "AWS Account ID (for unique bucket naming)"
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "AWS Account ID must be 12 digits"
  }
}
