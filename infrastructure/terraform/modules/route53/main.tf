# Route53 Module - DNS Management

terraform {
  required_version = ">= 1.5.0"
}

# Hosted Zone (falls neu erstellt werden soll)
resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0
  name  = var.domain_name

  tags = {
    Name = "${var.project_name}-${var.environment}-hosted-zone"
  }
}

# Data Source für existierende Hosted Zone
data "aws_route53_zone" "existing" {
  count = var.create_hosted_zone ? 0 : 1
  name  = var.domain_name
}

locals {
  hosted_zone_id = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
}

# A Record für Frontend (Alias zu CloudFront)
resource "aws_route53_record" "frontend" {
  count   = var.frontend_subdomain != null ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.frontend_subdomain == "" ? var.domain_name : "${var.frontend_subdomain}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.cloudfront_frontend_domain_name
    zone_id                = var.cloudfront_hosted_zone_id # CloudFront Hosted Zone ID (global)
    evaluate_target_health = false
  }
}

# AAAA Record (IPv6) für Frontend
resource "aws_route53_record" "frontend_ipv6" {
  count   = var.frontend_subdomain != null && var.enable_ipv6 ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.frontend_subdomain == "" ? var.domain_name : "${var.frontend_subdomain}.${var.domain_name}"
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_frontend_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# A Record für API (Alias zu CloudFront oder API Gateway)
resource "aws_route53_record" "api" {
  count   = var.api_subdomain != null ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = "${var.api_subdomain}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.cloudfront_api_domain_name != null ? var.cloudfront_api_domain_name : var.api_gateway_domain_name
    zone_id                = var.cloudfront_api_domain_name != null ? var.cloudfront_hosted_zone_id : var.api_gateway_hosted_zone_id
    evaluate_target_health = false
  }
}

# AAAA Record (IPv6) für API
resource "aws_route53_record" "api_ipv6" {
  count   = var.api_subdomain != null && var.enable_ipv6 ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = "${var.api_subdomain}.${var.domain_name}"
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_api_domain_name != null ? var.cloudfront_api_domain_name : var.api_gateway_domain_name
    zone_id                = var.cloudfront_api_domain_name != null ? var.cloudfront_hosted_zone_id : var.api_gateway_hosted_zone_id
    evaluate_target_health = false
  }
}

# TXT Record für Domain Verification (optional)
resource "aws_route53_record" "verification" {
  count   = var.verification_txt != null ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = 300
  records = [var.verification_txt]
}

# MX Records für Email (optional)
resource "aws_route53_record" "mx" {
  count   = length(var.mx_records) > 0 ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = 300
  records = var.mx_records
}
