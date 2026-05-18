output "bucket_name" {
  description = "Name of the S3 bucket for user data"
  value       = aws_s3_bucket.user_data.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.user_data.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.user_data.bucket_domain_name
}

output "kms_key_id" {
  description = "ID of the KMS key used for encryption"
  value       = aws_kms_key.user_data.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = aws_kms_key.user_data.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role with S3 access"
  value       = aws_iam_role.data_upload_lambda.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.data_upload_lambda.name
}

output "s3_access_policy_arn" {
  description = "ARN of the IAM policy for S3 access"
  value       = aws_iam_policy.user_data_access.arn
}
