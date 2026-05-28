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

    S3 Bucket: ${aws_s3_bucket.terraform_state.id}
    DynamoDB Table: ${aws_dynamodb_table.terraform_locks.name}
    Region: ${var.aws_region}

    Next Steps:
    1. Backend config files will be auto-generated
    2. Run: cd ../environments/dev && terraform init
    3. Verify state is in S3
    4. Start deployment

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
