# StackVertex Staging Environment
# Pre-Production environment for testing before prod deployment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend config wird von bootstrap script generiert
  # backend.tf ist separate Datei
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "StackVertex"
      ManagedBy   = "Terraform"
      Environment = "staging"
    }
  }
}

# Data Sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Locals
locals {
  aws_account_id     = data.aws_caller_identity.current.account_id
  aws_region         = data.aws_region.current.name
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2) # 2 AZs für staging

  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = local.aws_region
  vpc_cidr           = var.vpc_cidr
  availability_zones = local.availability_zones

  enable_nat_gateway   = true  # Staging: NAT Gateway für realistische Tests
  enable_vpc_endpoints = true
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_name              = var.project_name
  environment               = var.environment
  aws_account_id            = local.aws_account_id
  deployment_retention_days = 180 # Staging: 180 Tage Retention

  create_workspace_bucket = true # Staging: Workspace Bucket

  # Customer Data Storage
  enable_customer_data_versioning      = true
  customer_data_encryption_type        = "aws:kms" # Staging: KMS encryption
  create_customer_data_kms_key         = true      # Staging: eigener KMS Key
  enable_customer_data_lifecycle       = true
  enable_customer_data_archival        = true  # Staging: Glacier nach 90 Tagen
  customer_data_version_retention_days = 60    # Staging: 60 Tage Versionen
}

# Database Module
module "database" {
  source = "../../modules/database"

  project_name       = var.project_name
  environment        = var.environment
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.networking.aurora_security_group_id

  postgres_version = "15.4"
  database_name    = var.database_name
  master_username  = var.db_master_username
  master_password  = var.db_master_password

  # Staging: Mittlere Kapazität
  min_capacity = 1
  max_capacity = 4

  # Staging: 7 Tage Backup Retention
  backup_retention_days = 7
  skip_final_snapshot   = false # Staging: Final Snapshot erstellen

  enable_performance_insights = true  # Staging: Performance Insights
  enable_cloudwatch_alarms    = true  # Staging: CloudWatch Alarms
}

# Compute Module
module "compute" {
  source = "../../modules/compute"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = local.aws_account_id

  # Lambda Config
  lambda_image_uri   = var.lambda_image_uri
  lambda_timeout     = 60  # Staging: längere Timeouts
  lambda_memory_size = 1024 # Staging: mehr Memory
  log_level          = "INFO" # Staging: INFO logging

  # VPC
  enable_vpc               = true
  private_subnet_ids       = module.networking.private_subnet_ids
  lambda_security_group_id = module.networking.lambda_security_group_id

  # Database
  db_secret_arn = module.database.secret_arn

  # S3
  deployment_bucket_name    = module.storage.deployment_states_bucket_id
  deployment_bucket_arn     = module.storage.deployment_states_bucket_arn
  customer_data_bucket_name = module.storage.customer_data_bucket_id
  customer_data_bucket_arn  = module.storage.customer_data_bucket_arn
  terraform_state_bucket    = var.terraform_state_bucket

  # API Gateway
  enable_api_gateway         = true
  enable_lambda_function_url = false
  enable_websocket           = true
  cors_origins               = var.cors_origins # Staging: Configured CORS

  # Monitoring
  enable_cloudwatch_alarms = true # Staging: Alarms aktiv
  log_retention_days       = 14   # Staging: 14 Tage Log Retention
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = local.aws_region
  aws_account_id = local.aws_account_id

  # Alert Contacts
  critical_alert_emails = var.alert_emails
  warning_alert_emails  = var.alert_emails
  slack_webhook_url     = var.slack_webhook_url

  # Resource IDs
  lambda_function_name  = module.compute.lambda_function_name
  lambda_log_group_name = module.compute.lambda_log_group_name
  api_gateway_id        = module.compute.http_api_id
  db_cluster_id         = module.database.cluster_id

  # Thresholds (staging: strenger als dev)
  lambda_error_threshold_critical = 10 # Staging: 10 Fehler
  api_5xx_threshold_critical      = 5  # Staging: 5 Fehler
  api_4xx_threshold_warning       = 50 # Staging: 50 Fehler
}

# Security Module
module "security" {
  source = "../../modules/security"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = local.aws_region
  aws_account_id = local.aws_account_id

  # SNS Topics from Monitoring
  critical_alerts_topic_arn = module.monitoring.critical_alerts_topic_arn
  warning_alerts_topic_arn  = module.monitoring.warning_alerts_topic_arn
  info_alerts_topic_arn     = module.monitoring.info_alerts_topic_arn

  # CloudTrail
  cloudtrail_retention_days     = 180 # Staging: 180 Tage
  cloudtrail_log_retention_days = 60
  enable_multi_region_trail     = false # Staging: Single-Region

  # GuardDuty
  enable_guardduty            = true
  guardduty_finding_frequency = "FIFTEEN_MINUTES" # Staging: 15 min

  # Security Hub
  enable_security_hub = true # Staging: Security Hub aktiv
}

# Backup Module - Automated Backups (Staging: Basic Setup)
module "backup" {
  source = "../../modules/backup"

  # Note: Staging doesn't need DR provider since cross-region is disabled
  providers = {
    aws.secondary = aws # Use primary region as dummy (not used)
  }

  project_name = var.project_name
  environment  = var.environment
  aws_region   = local.aws_region
  dr_region    = "eu-west-1" # Not used since cross_region is false

  # KMS Encryption (use storage module KMS key)
  kms_key_arn = module.storage.customer_data_kms_key_arn

  # Backup Retention (Staging: Medium retention)
  daily_backup_retention_days   = 7   # 7 days
  weekly_backup_retention_days  = 30  # 30 days
  monthly_backup_retention_days = 90  # 90 days

  # Backup Plans (Staging: Daily + Weekly)
  enable_weekly_backups  = true
  enable_monthly_backups = false # Staging: No monthly backups

  # Cross-Region Backup (Staging: Disabled for cost savings)
  enable_cross_region_backup = false

  # Resources to Backup
  aurora_cluster_arn = module.database.cluster_arn

  # S3 Cross-Region Replication (Staging: Disabled)
  enable_s3_cross_region_replication = false

  # Monitoring
  enable_backup_alarms = true
  alarm_sns_topic_arns = [
    module.monitoring.critical_alerts_topic_arn
  ]
}

# WAF Module - Web Application Firewall & DDoS Protection
# Staging: Cost-optimized protection (no Bot Control, shorter retention)
# Note: StackVertex uses API Gateway HTTP API (v2) which is NOT compatible with WAF.
#       Instead, we protect both frontend AND backend via CloudFront WAF by routing
#       API traffic through CloudFront (e.g., /api/* origin to API Gateway).
module "waf" {
  source = "../../modules/waf"

  project_name = var.project_name
  environment  = var.environment

  # Staging: Enable CloudFront WAF for realistic testing
  enable_cloudfront_waf = true

  # Staging: Regional WAF disabled (HTTP API v2 not compatible with WAF)
  enable_regional_waf = false

  # Rate Limiting (Staging: Same as prod for realistic tests)
  rate_limit_requests = 2000

  # Geo-Blocking (Staging: Disabled for easier testing from anywhere)
  enable_geo_blocking = false

  # Bot Control (Staging: Disabled for cost savings - ~$10/month saved)
  enable_bot_control = false

  # Logging (Staging: Enabled but shorter retention)
  enable_waf_logging      = true
  waf_log_retention_days  = 14 # Staging: 14 days retention

  # Alarms (Staging: Enabled for testing alarm setup)
  enable_waf_alarms           = true
  blocked_requests_threshold  = 500 # Lower threshold for testing
  alarm_sns_topic_arns        = [module.monitoring.critical_alerts_topic_arn]
}
