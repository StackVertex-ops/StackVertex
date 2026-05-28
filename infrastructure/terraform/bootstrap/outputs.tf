# Bootstrap Outputs

output "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "terraform_state_bucket_arn" {
  description = "S3 bucket ARN for Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

output "terraform_locks_table" {
  description = "DynamoDB table name for Terraform state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "deployment_states_bucket" {
  description = "S3 bucket for customer deployment states"
  value       = aws_s3_bucket.deployment_states.id
}

output "ecr_repository_dev" {
  description = "ECR repository URL for dev environment"
  value       = aws_ecr_repository.lambda_dev.repository_url
}

output "ecr_repository_staging" {
  description = "ECR repository URL for staging environment"
  value       = aws_ecr_repository.lambda_staging.repository_url
}

output "ecr_repository_prod" {
  description = "ECR repository URL for prod environment"
  value       = aws_ecr_repository.lambda_prod.repository_url
}

output "backend_config" {
  description = "Backend configuration for other Terraform projects"
  value = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.id}"
        key            = "environments/ENV_NAME/terraform.tfstate"
        region         = "${var.aws_region}"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
      }
    }
  EOT
}

output "next_steps" {
  description = "Instructions for next steps"
  value = <<-EOT

    ✅ Bootstrap Complete!

    📦 S3 Buckets:
      - Terraform State: ${aws_s3_bucket.terraform_state.id}
      - Deployment States: ${aws_s3_bucket.deployment_states.id}

    🔒 DynamoDB Lock Table: ${aws_dynamodb_table.terraform_locks.name}

    🐳 ECR Repositories:
      - Dev: ${aws_ecr_repository.lambda_dev.repository_url}
      - Staging: ${aws_ecr_repository.lambda_staging.repository_url}
      - Prod: ${aws_ecr_repository.lambda_prod.repository_url}

    🌍 Region: ${var.aws_region}

    Next Steps:
    1. Backend config files auto-generated ✅
    2. ECR repositories ready for Docker images ✅
    3. Run: cd ../environments/dev && terraform init
    4. Start deployment with GitHub Actions workflow

    Backend Config Example:
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.id}"
        key            = "dev/terraform.tfstate"
        region         = "${var.aws_region}"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
      }
    }
  EOT
}
