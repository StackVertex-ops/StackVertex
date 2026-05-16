# Backup Module - AWS Backup for Automated Backups & DR
# Handles DynamoDB, Aurora, and S3 Cross-Region Replication

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Backup Vault - Primary Region
resource "aws_backup_vault" "main" {
  name        = "${var.project_name}-${var.environment}-vault"
  kms_key_arn = var.kms_key_arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-backup-vault"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# AWS Backup Vault - Secondary Region (DR)
resource "aws_backup_vault" "dr" {
  count = var.enable_cross_region_backup ? 1 : 0

  provider = aws.secondary

  name        = "${var.project_name}-${var.environment}-vault-dr"
  kms_key_arn = var.dr_kms_key_arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-backup-vault-dr"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "DisasterRecovery"
  }
}

# IAM Role for AWS Backup
resource "aws_iam_role" "backup" {
  name = "${var.project_name}-${var.environment}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-backup-role"
    Environment = var.environment
  }
}

# Attach AWS Managed Backup Policy
resource "aws_iam_role_policy_attachment" "backup_policy" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore_policy" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# Backup Plan - Daily
resource "aws_backup_plan" "daily" {
  name = "${var.project_name}-${var.environment}-daily"

  rule {
    rule_name         = "daily-backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 * * ? *)" # 2 AM UTC every day

    lifecycle {
      delete_after = var.daily_backup_retention_days
    }

    # Cross-Region Copy (optional)
    dynamic "copy_action" {
      for_each = var.enable_cross_region_backup ? [1] : []

      content {
        destination_vault_arn = aws_backup_vault.dr[0].arn

        lifecycle {
          delete_after = var.daily_backup_retention_days
        }
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-daily-backup-plan"
    Environment = var.environment
  }
}

# Backup Plan - Weekly
resource "aws_backup_plan" "weekly" {
  count = var.enable_weekly_backups ? 1 : 0

  name = "${var.project_name}-${var.environment}-weekly"

  rule {
    rule_name         = "weekly-backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 3 ? * SUN *)" # 3 AM UTC every Sunday

    lifecycle {
      delete_after = var.weekly_backup_retention_days
    }

    # Cross-Region Copy
    dynamic "copy_action" {
      for_each = var.enable_cross_region_backup ? [1] : []

      content {
        destination_vault_arn = aws_backup_vault.dr[0].arn

        lifecycle {
          delete_after = var.weekly_backup_retention_days
        }
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-weekly-backup-plan"
    Environment = var.environment
  }
}

# Backup Plan - Monthly
resource "aws_backup_plan" "monthly" {
  count = var.enable_monthly_backups ? 1 : 0

  name = "${var.project_name}-${var.environment}-monthly"

  rule {
    rule_name         = "monthly-backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 4 1 * ? *)" # 4 AM UTC on 1st of each month

    lifecycle {
      delete_after = var.monthly_backup_retention_days
    }

    # Cross-Region Copy
    dynamic "copy_action" {
      for_each = var.enable_cross_region_backup ? [1] : []

      content {
        destination_vault_arn = aws_backup_vault.dr[0].arn

        lifecycle {
          delete_after = var.monthly_backup_retention_days
        }
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-monthly-backup-plan"
    Environment = var.environment
  }
}

# Backup Selection - DynamoDB Tables
resource "aws_backup_selection" "dynamodb" {
  count = length(var.dynamodb_table_arns) > 0 ? 1 : 0

  name          = "${var.project_name}-${var.environment}-dynamodb"
  iam_role_arn  = aws_iam_role.backup.arn
  plan_id       = aws_backup_plan.daily.id

  resources = var.dynamodb_table_arns
}

# Backup Selection - Aurora Database
resource "aws_backup_selection" "aurora" {
  count = var.aurora_cluster_arn != null ? 1 : 0

  name          = "${var.project_name}-${var.environment}-aurora"
  iam_role_arn  = aws_iam_role.backup.arn
  plan_id       = aws_backup_plan.daily.id

  resources = [var.aurora_cluster_arn]
}

# Backup Selection - Weekly (if enabled)
resource "aws_backup_selection" "weekly_dynamodb" {
  count = var.enable_weekly_backups && length(var.dynamodb_table_arns) > 0 ? 1 : 0

  name          = "${var.project_name}-${var.environment}-dynamodb-weekly"
  iam_role_arn  = aws_iam_role.backup.arn
  plan_id       = aws_backup_plan.weekly[0].id

  resources = var.dynamodb_table_arns
}

# Backup Selection - Monthly (if enabled)
resource "aws_backup_selection" "monthly_dynamodb" {
  count = var.enable_monthly_backups && length(var.dynamodb_table_arns) > 0 ? 1 : 0

  name          = "${var.project_name}-${var.environment}-dynamodb-monthly"
  iam_role_arn  = aws_iam_role.backup.arn
  plan_id       = aws_backup_plan.monthly[0].id

  resources = var.dynamodb_table_arns
}

# CloudWatch Alarms for Backup Failures
resource "aws_cloudwatch_metric_alarm" "backup_failed" {
  count = var.enable_backup_alarms ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-backup-failed"
  alarm_description   = "Backup job failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "NumberOfBackupJobsFailed"
  namespace           = "AWS/Backup"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    BackupVaultName = aws_backup_vault.main.name
  }

  alarm_actions = var.alarm_sns_topic_arns

  tags = {
    Name        = "${var.project_name}-${var.environment}-backup-failed-alarm"
    Environment = var.environment
  }
}

# S3 Cross-Region Replication (for S3 buckets backup)
# Note: This requires S3 buckets to be created first
# Configuration is done in storage module, but we provide IAM role

resource "aws_iam_role" "s3_replication" {
  count = var.enable_s3_cross_region_replication ? 1 : 0

  name = "${var.project_name}-${var.environment}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-s3-replication-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "s3_replication" {
  count = var.enable_s3_cross_region_replication ? 1 : 0

  name = "${var.project_name}-${var.environment}-s3-replication-policy"
  role = aws_iam_role.s3_replication[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = var.s3_source_bucket_arns
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = [for arn in var.s3_source_bucket_arns : "${arn}/*"]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = [for arn in var.s3_destination_bucket_arns : "${arn}/*"]
      }
    ]
  })
}
