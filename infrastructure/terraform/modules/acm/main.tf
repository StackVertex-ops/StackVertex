# ACM Module - SSL/TLS Certificates

terraform {
  required_version = ">= 1.5.0"
}

# ACM Certificate für Frontend (muss in us-east-1 sein für CloudFront!)
resource "aws_acm_certificate" "frontend" {
  count = var.create_frontend_certificate ? 1 : 0

  domain_name               = var.frontend_domain
  subject_alternative_names = var.frontend_additional_domains
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-cert"
  }
}

# DNS Validation Records für Frontend Certificate
resource "aws_route53_record" "frontend_validation" {
  for_each = var.create_frontend_certificate ? {
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# Certificate Validation für Frontend
resource "aws_acm_certificate_validation" "frontend" {
  count = var.create_frontend_certificate ? 1 : 0

  certificate_arn         = aws_acm_certificate.frontend[0].arn
  validation_record_fqdns = [for record in aws_route53_record.frontend_validation : record.fqdn]

  timeouts {
    create = "10m"
  }
}

# ACM Certificate für API (muss in us-east-1 sein für CloudFront!)
resource "aws_acm_certificate" "api" {
  count = var.create_api_certificate ? 1 : 0

  domain_name               = var.api_domain
  subject_alternative_names = var.api_additional_domains
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-cert"
  }
}

# DNS Validation Records für API Certificate
resource "aws_route53_record" "api_validation" {
  for_each = var.create_api_certificate ? {
    for dvo in aws_acm_certificate.api[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# Certificate Validation für API
resource "aws_acm_certificate_validation" "api" {
  count = var.create_api_certificate ? 1 : 0

  certificate_arn         = aws_acm_certificate.api[0].arn
  validation_record_fqdns = [for record in aws_route53_record.api_validation : record.fqdn]

  timeouts {
    create = "10m"
  }
}
