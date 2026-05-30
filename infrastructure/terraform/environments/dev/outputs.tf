# Dev Environment Outputs

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
  description = "DynamoDB main table name"
  value       = module.database_dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "DynamoDB main table ARN"
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

# Summary
output "deployment_summary" {
  description = "Deployment summary with all important URLs and resources"
  value       = <<-EOT

    ✅ StackVertex Dev Environment Deployed!

    🌐 API Endpoint:       ${module.compute.http_api_invoke_url}
    🔌 WebSocket Endpoint: wss://${module.compute.websocket_api_invoke_url}

    📦 ECR Repository:     ${module.compute.ecr_repository_url}
    🗄️  Deployment Bucket:  ${module.storage.deployment_states_bucket_id}
    💾 Customer Data:      ${module.storage.customer_data_bucket_id}

    📊 DynamoDB Tables:
    - Main Table:         ${module.database_dynamodb.table_name}
    - WebSocket Table:    ${module.database_dynamodb.websocket_table_name}

    📊 Monitoring:
    - CloudWatch Dashboard: ${module.monitoring.dashboard_url}
    - CloudTrail: ${module.security.security_monitoring_urls.cloudtrail}
    - GuardDuty: ${coalesce(module.security.security_monitoring_urls.guardduty, "disabled")}

    🔔 Alerts configured for:
    - Lambda Errors, Throttles, Timeouts
    - API Gateway 4XX/5XX Errors
    - DynamoDB Throttles
    - Deployment Failures
    - Unauthorized Access
    - IAM/S3 Policy Changes
    - Root Account Usage

    📋 Next Steps:
    1. Build & push Docker image to ECR
    2. Update Lambda function with new image
    3. Test API endpoint
    4. Configure alert emails (terraform.tfvars: alert_emails)

  EOT
}
