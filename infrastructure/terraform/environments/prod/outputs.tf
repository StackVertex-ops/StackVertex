# Production Environment Outputs

# Networking
output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.networking.private_subnet_ids
}

# Database (DynamoDB)
output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.database_dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = module.database_dynamodb.table_arn
}

# Compute
output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.compute.lambda_function_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for Lambda images"
  value       = module.compute.ecr_repository_url
}

output "api_endpoint" {
  description = "API Gateway HTTP endpoint URL"
  value       = module.compute.http_api_invoke_url
}

output "websocket_endpoint" {
  description = "WebSocket API endpoint URL"
  value       = module.compute.websocket_api_invoke_url
}

# Storage
output "deployment_bucket" {
  description = "S3 bucket for deployment states"
  value       = module.storage.deployment_states_bucket_id
}

output "customer_data_bucket" {
  description = "S3 bucket for customer application data"
  value       = module.storage.customer_data_bucket_id
}

output "workspace_bucket" {
  description = "S3 bucket for Terraform workspace files"
  value       = module.storage.workspace_bucket_id
}

# Monitoring
output "cloudwatch_dashboard_url" {
  description = "CloudWatch Dashboard URL"
  value       = module.monitoring.dashboard_url
}

output "critical_alerts_topic" {
  description = "SNS Topic ARN for critical alerts"
  value       = module.monitoring.critical_alerts_topic_arn
}

# Security
output "cloudtrail_name" {
  description = "CloudTrail name"
  value       = module.security.cloudtrail_name
}

output "security_monitoring_urls" {
  description = "Security monitoring console URLs"
  value       = module.security.security_monitoring_urls
}

output "kms_key_id" {
  description = "KMS key ID for customer data encryption"
  value       = module.storage.customer_data_kms_key_id
}

# Domain & CDN
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.create_route53_zone ? module.route53[0].zone_id : null
}

output "route53_name_servers" {
  description = "Route53 nameservers for domain configuration"
  value       = var.create_route53_zone ? module.route53[0].name_servers : []
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  value       = var.create_acm_certificate ? module.acm[0].certificate_arn : null
}

output "acm_certificate_status" {
  description = "ACM certificate validation status"
  value       = var.create_acm_certificate ? module.acm[0].certificate_status : null
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = var.enable_cloudfront ? module.cloudfront[0].distribution_id : null
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = var.enable_cloudfront ? module.cloudfront[0].distribution_domain_name : null
}

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = var.enable_cloudfront ? module.cloudfront[0].distribution_arn : null
}

# Summary
output "deployment_summary" {
  description = "Deployment summary with all important URLs and resources"
  value = <<-EOT

    ✅ StackVertex PRODUCTION Environment Deployed!

    🌐 Domain:             ${var.domain_name}
    ${var.enable_cloudfront ? "🚀 CloudFront URL:     https://${module.cloudfront[0].distribution_domain_name}" : ""}
    ${var.create_route53_zone ? "📡 Name Servers:       ${join(", ", module.route53[0].name_servers)}" : ""}
    ${var.create_acm_certificate ? "🔐 SSL Certificate:    ${module.acm[0].certificate_status}" : ""}

    🌐 API Endpoint:       ${module.compute.http_api_invoke_url}
    🔌 WebSocket Endpoint: ${module.compute.websocket_api_invoke_url}

    📦 ECR Repository:     ${module.compute.ecr_repository_url}
    🗄️  Deployment Bucket:  ${module.storage.deployment_states_bucket_id}
    💾 Customer Data:      ${module.storage.customer_data_bucket_id}
    📁 Workspace Bucket:   ${module.storage.workspace_bucket_id}

    💾 DynamoDB Table:     ${module.database_dynamodb.table_name}
    🔑 KMS Key:            ${module.storage.customer_data_kms_key_id}

    📊 Monitoring:
    - CloudWatch Dashboard: ${module.monitoring.dashboard_url}
    - CloudTrail: ${module.security.security_monitoring_urls.cloudtrail}
    - GuardDuty: ${module.security.security_monitoring_urls.guardduty}
    - Security Hub: ${module.security.security_monitoring_urls.security_hub}
    - Config: ${module.security.security_monitoring_urls.config}

    🔔 Alerts configured for (STRICT THRESHOLDS):
    - Lambda Errors (threshold: 5), Throttles, Timeouts
    - API Gateway 4XX (threshold: 20) / 5XX (threshold: 3) Errors
    - DynamoDB Throttles, User Errors, System Errors
    - Deployment Failures
    - Security Events (GuardDuty Findings, Config Non-Compliance)
    - IAM/S3 Policy Changes
    - Root Account Usage
    - 99.9% Uptime SLA Monitoring

    🔐 Security Features ACTIVE:
    - ✅ Multi-Region CloudTrail
    - ✅ GuardDuty Threat Detection
    - ✅ Security Hub Compliance Scanning
    - ✅ AWS Config Rule Evaluation
    - ✅ KMS Encryption (Customer Data)
    - ✅ VPC Endpoints (Private AWS API Access)
    - ✅ NAT Gateway (Controlled Egress)
    - ✅ DynamoDB Point-in-Time Recovery (35 days)
    - ✅ DynamoDB Automated Backups (30 days retention)
    ${var.enable_cloudfront ? "- ✅ CloudFront WAF (Rate Limiting, Geo-Blocking, Bot Control)" : ""}
    ${var.create_acm_certificate ? "- ✅ TLS 1.2+ Encryption (ACM Certificate)" : ""}

    ⚠️  PRODUCTION CHECKLIST:
    1. ✅ Verify all alert emails are configured
    2. ✅ Test PagerDuty integration for 24/7 on-call
    3. ✅ Review CloudWatch Alarms (all should be green)
    4. ✅ Check Security Hub Compliance Score
    5. ✅ Verify GuardDuty is enabled and monitoring
    6. ✅ Test DynamoDB backup restoration procedure
    7. ✅ Validate CORS origins match production frontend
    ${var.create_route53_zone ? "8. ✅ Configure domain nameservers with your registrar" : "8. ⏭️  Skipped (Route53 disabled)"}
    ${var.create_acm_certificate ? "9. ✅ Verify ACM certificate is ISSUED (DNS validation)" : "9. ⏭️  Skipped (ACM disabled)"}
    ${var.enable_cloudfront ? "10. ✅ Test CloudFront distribution and cache behavior" : "10. ⏭️  Skipped (CloudFront disabled)"}
    11. ✅ Run load tests and performance validation
    12. ✅ Execute disaster recovery drill
    13. ✅ Document incident response procedures

    📋 Next Steps:
    ${var.create_route53_zone ? "1. ✅ Update domain registrar with Route53 nameservers" : "1. ⏭️  Configure DNS manually (no Route53)"}
    ${var.create_acm_certificate ? "2. ✅ Wait for ACM certificate validation (~5-10 min)" : "2. ⏭️  Setup SSL certificate manually"}
    ${var.enable_cloudfront ? "3. ✅ CloudFront deployment (~15-20 min)" : "3. ⏭️  No CloudFront"}
    4. Run security scan (OWASP ZAP, Trivy)
    5. Load testing (Artillery, k6, or Gatling)
    6. DynamoDB backup restoration test
    7. Document runbook for common issues
    8. Schedule regular security audits

  EOT
}
