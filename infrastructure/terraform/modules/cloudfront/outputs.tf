# CloudFront Module Outputs

output "frontend_distribution_id" {
  description = "CloudFront distribution ID for frontend"
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_distribution_arn" {
  description = "CloudFront distribution ARN for frontend"
  value       = aws_cloudfront_distribution.frontend.arn
}

output "frontend_domain_name" {
  description = "CloudFront domain name for frontend"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_url" {
  description = "Frontend URL (custom domain or CloudFront)"
  value       = var.frontend_domain != null ? "https://${var.frontend_domain}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_distribution_id" {
  description = "CloudFront distribution ID for API"
  value       = var.enable_api_cloudfront ? aws_cloudfront_distribution.api[0].id : null
}

output "api_distribution_arn" {
  description = "CloudFront distribution ARN for API"
  value       = var.enable_api_cloudfront ? aws_cloudfront_distribution.api[0].arn : null
}

output "api_domain_name" {
  description = "CloudFront domain name for API"
  value       = var.enable_api_cloudfront ? aws_cloudfront_distribution.api[0].domain_name : null
}

output "api_url" {
  description = "API URL (custom domain or CloudFront)"
  value       = var.enable_api_cloudfront ? (var.api_domain != null ? "https://${var.api_domain}" : "https://${aws_cloudfront_distribution.api[0].domain_name}") : null
}
