# OverCloud Dev Environment

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
      Project     = "OverCloud"
      ManagedBy   = "Terraform"
      Environment = "dev"
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
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2) # Nur 2 AZs für dev

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

  enable_nat_gateway   = false # Dev ohne NAT Gateway (cost saving)
  enable_vpc_endpoints = true
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_name              = var.project_name
  environment               = var.environment
  aws_account_id            = local.aws_account_id
  deployment_retention_days = 90 # Dev: 90 Tage Retention

  create_workspace_bucket = false # Dev braucht kein separates Workspace Bucket

  # Customer Data Storage
  enable_customer_data_versioning      = true
  customer_data_encryption_type        = "AES256" # Dev: Standard encryption
  create_customer_data_kms_key         = false    # Dev: kein KMS
  enable_customer_data_lifecycle       = true
  enable_customer_data_archival        = false # Dev: kein Glacier
  customer_data_version_retention_days = 30    # Dev: 30 Tage Versionen
}

# Database Module
module "database" {
  source = "../../modules/database"

  project_name       = var.project_name
  environment        = var.environment
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.networking.aurora_security_group_id

  postgres_version   = "15.4"
  database_name      = var.database_name
  master_username    = var.db_master_username
  master_password    = var.db_master_password

  # Dev: Kleine Kapazität
  min_capacity = 0.5
  max_capacity = 1

  # Dev: Kürzere Retention
  backup_retention_days = 3
  skip_final_snapshot   = true

  enable_performance_insights = false
  enable_cloudwatch_alarms    = false
}

# Compute Module
module "compute" {
  source = "../../modules/compute"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = local.aws_account_id

  # Lambda Config
  lambda_image_uri   = var.lambda_image_uri
  lambda_timeout     = 30
  lambda_memory_size = 512
  log_level          = "DEBUG" # Dev: Debug logging

  # VPC
  enable_vpc                = true
  private_subnet_ids        = module.networking.private_subnet_ids
  lambda_security_group_id  = module.networking.lambda_security_group_id

  # Database
  db_secret_arn = module.database.secret_arn

  # S3
  deployment_bucket_name   = module.storage.deployment_states_bucket_id
  deployment_bucket_arn    = module.storage.deployment_states_bucket_arn
  customer_data_bucket_name = module.storage.customer_data_bucket_id
  customer_data_bucket_arn = module.storage.customer_data_bucket_arn
  terraform_state_bucket   = var.terraform_state_bucket

  # API Gateway
  enable_api_gateway        = true
  enable_lambda_function_url = false
  enable_websocket          = true
  cors_origins              = "*" # Dev: Allow all origins

  # Monitoring
  enable_cloudwatch_alarms = false
  log_retention_days       = 7 # Dev: 7 Tage Log Retention
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

  # Thresholds (dev: toleranter)
  lambda_error_threshold_critical = 20  # Dev: 20 Fehler
  api_5xx_threshold_critical      = 10  # Dev: 10 Fehler
  api_4xx_threshold_warning       = 100 # Dev: 100 Fehler
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
  cloudtrail_retention_days     = 90 # Dev: 90 Tage
  cloudtrail_log_retention_days = 30
  enable_multi_region_trail     = false

  # GuardDuty
  enable_guardduty            = true
  guardduty_finding_frequency = "ONE_HOUR" # Dev: 1x pro Stunde

  # Security Hub
  enable_security_hub = var.enable_security_hub # Optional für dev
}
