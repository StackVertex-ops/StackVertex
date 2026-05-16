# Backup Module Outputs

output "backup_vault_arn" {
  description = "ARN of the primary backup vault"
  value       = aws_backup_vault.main.arn
}

output "backup_vault_name" {
  description = "Name of the primary backup vault"
  value       = aws_backup_vault.main.name
}

output "dr_backup_vault_arn" {
  description = "ARN of the DR backup vault (if enabled)"
  value       = var.enable_cross_region_backup ? aws_backup_vault.dr[0].arn : null
}

output "backup_role_arn" {
  description = "IAM role ARN for AWS Backup service"
  value       = aws_iam_role.backup.arn
}

output "daily_backup_plan_id" {
  description = "ID of the daily backup plan"
  value       = aws_backup_plan.daily.id
}

output "weekly_backup_plan_id" {
  description = "ID of the weekly backup plan (if enabled)"
  value       = var.enable_weekly_backups ? aws_backup_plan.weekly[0].id : null
}

output "monthly_backup_plan_id" {
  description = "ID of the monthly backup plan (if enabled)"
  value       = var.enable_monthly_backups ? aws_backup_plan.monthly[0].id : null
}

output "s3_replication_role_arn" {
  description = "IAM role ARN for S3 cross-region replication (if enabled)"
  value       = var.enable_s3_cross_region_replication ? aws_iam_role.s3_replication[0].arn : null
}

output "backup_summary" {
  description = "Summary of backup configuration"
  value = {
    primary_vault        = aws_backup_vault.main.name
    dr_vault             = var.enable_cross_region_backup ? aws_backup_vault.dr[0].name : "disabled"
    daily_retention      = "${var.daily_backup_retention_days} days"
    weekly_retention     = var.enable_weekly_backups ? "${var.weekly_backup_retention_days} days" : "disabled"
    monthly_retention    = var.enable_monthly_backups ? "${var.monthly_backup_retention_days} days" : "disabled"
    cross_region_enabled = var.enable_cross_region_backup
    dr_region            = var.enable_cross_region_backup ? var.dr_region : null
  }
}
