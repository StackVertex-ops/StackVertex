# Security Module Outputs

output "cloudtrail_name" {
  description = "CloudTrail trail name"
  value       = aws_cloudtrail.main.name
}

output "cloudtrail_arn" {
  description = "CloudTrail trail ARN"
  value       = aws_cloudtrail.main.arn
}

output "cloudtrail_bucket_name" {
  description = "S3 bucket name for CloudTrail logs"
  value       = aws_s3_bucket.cloudtrail.id
}

output "cloudtrail_log_group_name" {
  description = "CloudWatch log group name for CloudTrail"
  value       = aws_cloudwatch_log_group.cloudtrail.name
}

output "guardduty_detector_id" {
  description = "GuardDuty detector ID"
  value       = var.enable_guardduty ? aws_guardduty_detector.main.id : null
}

output "security_hub_arn" {
  description = "Security Hub account ARN"
  value       = var.enable_security_hub ? aws_securityhub_account.main[0].arn : null
}

output "security_monitoring_urls" {
  description = "URLs for security monitoring consoles"
  value = {
    cloudtrail   = "https://console.aws.amazon.com/cloudtrail/home?region=${var.aws_region}#/trails/${aws_cloudtrail.main.name}"
    guardduty    = var.enable_guardduty ? "https://console.aws.amazon.com/guardduty/home?region=${var.aws_region}#/findings" : null
    security_hub = var.enable_security_hub ? "https://console.aws.amazon.com/securityhub/home?region=${var.aws_region}#/summary" : null
  }
}
