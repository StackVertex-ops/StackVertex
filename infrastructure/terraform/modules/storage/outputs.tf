# Storage Module Outputs

output "deployment_states_bucket_id" {
  description = "S3 bucket name for deployment states"
  value       = aws_s3_bucket.deployment_states.id
}

output "deployment_states_bucket_arn" {
  description = "S3 bucket ARN for deployment states"
  value       = aws_s3_bucket.deployment_states.arn
}

output "terraform_workspaces_bucket_id" {
  description = "S3 bucket name for Terraform workspaces (if created)"
  value       = var.create_workspace_bucket ? aws_s3_bucket.terraform_workspaces[0].id : null
}

output "terraform_workspaces_bucket_arn" {
  description = "S3 bucket ARN for Terraform workspaces (if created)"
  value       = var.create_workspace_bucket ? aws_s3_bucket.terraform_workspaces[0].arn : null
}

# Customer Data Outputs
output "customer_data_bucket_id" {
  description = "S3 bucket name for customer application data"
  value       = aws_s3_bucket.customer_data.id
}

output "customer_data_bucket_arn" {
  description = "S3 bucket ARN for customer application data"
  value       = aws_s3_bucket.customer_data.arn
}

output "customer_data_bucket_domain_name" {
  description = "S3 bucket domain name for customer data"
  value       = aws_s3_bucket.customer_data.bucket_domain_name
}

output "customer_data_kms_key_id" {
  description = "KMS key ID for customer data encryption (if created)"
  value       = var.create_customer_data_kms_key ? aws_kms_key.customer_data[0].id : null
}

output "customer_data_kms_key_arn" {
  description = "KMS key ARN for customer data encryption (if created)"
  value       = var.create_customer_data_kms_key ? aws_kms_key.customer_data[0].arn : null
}

# Large Items Outputs (DynamoDB offload)
output "large_items_bucket_id" {
  description = "S3 bucket name for large items (DynamoDB offload > 300KB)"
  value       = aws_s3_bucket.large_items.id
}

output "large_items_bucket_arn" {
  description = "S3 bucket ARN for large items"
  value       = aws_s3_bucket.large_items.arn
}

# Frontend Outputs
output "frontend_bucket_id" {
  description = "S3 bucket name for frontend static website hosting"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "S3 bucket ARN for frontend"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_domain_name" {
  description = "S3 bucket domain name for frontend"
  value       = aws_s3_bucket.frontend.bucket_domain_name
}

output "frontend_bucket_website_endpoint" {
  description = "S3 bucket website endpoint for frontend"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}
