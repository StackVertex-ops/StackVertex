# Staging Environment Outputs

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

# Database
output "database_endpoint" {
  description = "Aurora database endpoint"
  value       = module.database.cluster_endpoint
  sensitive   = true
}

output "database_secret_arn" {
  description = "ARN of database credentials secret"
  value       = module.database.secret_arn
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

# Summary
output "deployment_summary" {
  description = "Deployment summary with all important URLs and resources"
  value = <<-EOT

    ✅ StackVertex Staging Environment Deployed!

    🌐 API Endpoint:       ${module.compute.http_api_invoke_url}
    🔌 WebSocket Endpoint: ${module.compute.websocket_api_invoke_url}

    📦 ECR Repository:     ${module.compute.ecr_repository_url}
    🗄️  Deployment Bucket:  ${module.storage.deployment_states_bucket_id}
    💾 Customer Data:      ${module.storage.customer_data_bucket_id}
    📁 Workspace Bucket:   ${module.storage.workspace_bucket_id}

    💾 Database Endpoint:  ${module.database.cluster_endpoint}
    🔐 Database Secret:    ${module.database.secret_arn}
    🔑 KMS Key:            ${module.storage.customer_data_kms_key_id}

    📊 Monitoring:
    - CloudWatch Dashboard: ${module.monitoring.dashboard_url}
    - CloudTrail: ${module.security.security_monitoring_urls.cloudtrail}
    - GuardDuty: ${module.security.security_monitoring_urls.guardduty}
    - Security Hub: ${module.security.security_monitoring_urls.security_hub}

    🔔 Alerts configured for:
    - Lambda Errors (threshold: 10), Throttles, Timeouts
    - API Gateway 4XX (threshold: 50) / 5XX (threshold: 5) Errors
    - Aurora CPU, Connections, Storage
    - Deployment Failures
    - Security Events (GuardDuty Findings)
    - IAM/S3 Policy Changes
    - Root Account Usage

    📋 Next Steps:
    1. Build & push Docker image to ECR
    2. Update Lambda function with new image
    3. Run database migrations (alembic upgrade head)
    4. Configure alert emails (terraform.tfvars: alert_emails)
    5. Test API endpoint against prod-like scenarios
    6. Load testing and performance validation
    7. Security scan with OWASP ZAP

  EOT
}
