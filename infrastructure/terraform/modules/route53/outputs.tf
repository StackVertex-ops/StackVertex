# Route53 Module Outputs

output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = local.hosted_zone_id
}

output "hosted_zone_name_servers" {
  description = "Name servers for hosted zone (set these at domain registrar)"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : null
}

output "frontend_fqdn" {
  description = "Fully qualified domain name for frontend"
  value       = var.frontend_subdomain != null ? (var.frontend_subdomain == "" ? var.domain_name : "${var.frontend_subdomain}.${var.domain_name}") : null
}

output "api_fqdn" {
  description = "Fully qualified domain name for API"
  value       = var.api_subdomain != null ? "${var.api_subdomain}.${var.domain_name}" : null
}
