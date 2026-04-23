# ACM Module Outputs

output "frontend_certificate_arn" {
  description = "ARN of frontend SSL certificate"
  value       = var.create_frontend_certificate ? aws_acm_certificate_validation.frontend[0].certificate_arn : null
}

output "frontend_certificate_domain" {
  description = "Domain name of frontend certificate"
  value       = var.create_frontend_certificate ? aws_acm_certificate.frontend[0].domain_name : null
}

output "api_certificate_arn" {
  description = "ARN of API SSL certificate"
  value       = var.create_api_certificate ? aws_acm_certificate_validation.api[0].certificate_arn : null
}

output "api_certificate_domain" {
  description = "Domain name of API certificate"
  value       = var.create_api_certificate ? aws_acm_certificate.api[0].domain_name : null
}
