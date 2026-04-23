# Networking Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets (costs ~$32/month)"
  type        = bool
  default     = false # False für dev, true für prod wenn Lambda in VPC
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services (cost optimization)"
  type        = bool
  default     = true
}
