# StackVertex Production Environment
# High-availability, secure, production-ready deployment

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
      Environment = "production"
      CostCenter  = "Platform"
    }
  }
}

# Secondary Provider for Disaster Recovery (Cross-Region Backup)
provider "aws" {
  alias  = "secondary"
  region = var.dr_region

  default_tags {
    tags = {
      Project     = "StackVertex"
      ManagedBy   = "Terraform"
      Environment = "production-dr"
      CostCenter  = "Platform"
      Purpose     = "DisasterRecovery"
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
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3) # Prod: 3 AZs für HA

  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    CostCenter  = "Platform"
    Criticality = "High"
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

  enable_nat_gateway   = true # Prod: NAT Gateway required
  enable_vpc_endpoints = true # Prod: VPC Endpoints für bessere Performance & Security
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_name              = var.project_name
  environment               = var.environment
  aws_account_id            = local.aws_account_id
  deployment_retention_days = 365 # Prod: 1 Jahr Retention

  create_workspace_bucket = true # Prod: Workspace Bucket

  # Customer Data Storage
  enable_customer_data_versioning      = true
  customer_data_encryption_type        = "aws:kms" # Prod: KMS encryption mandatory
  create_customer_data_kms_key         = true      # Prod: eigener KMS Key mit Rotation
  enable_customer_data_lifecycle       = true
  enable_customer_data_archival        = true # Prod: Glacier nach 90 Tagen
  customer_data_version_retention_days = 90   # Prod: 90 Tage Versionen (muss > 30 sein wegen Transition)

  # Frontend Storage
  enable_public_website_access = false # Prod: CloudFront only (kein direkter S3 Zugriff)
}

# Database Module (LEGACY - PostgreSQL)
# ❌ DISABLED: Ersetzt durch DynamoDB (siehe database-dynamodb module)
# Uncomment nur für Migration von alten Daten
# module "database" {
#   source = "../../modules/database"
#
#   project_name       = var.project_name
#   environment        = var.environment
#   private_subnet_ids = module.networking.private_subnet_ids
#   security_group_id  = module.networking.aurora_security_group_id
#
#   postgres_version = "15.4"
#   database_name    = var.database_name
#   master_username  = var.db_master_username
#   master_password  = var.db_master_password
#
#   # Prod: High Capacity mit Auto-Scaling
#   min_capacity = 2
#   max_capacity = 16
#
#   # Prod: 30 Tage Backup Retention + Deletion Protection
#   backup_retention_days = 30
#   skip_final_snapshot   = false           # Prod: Final Snapshot mandatory
#   deletion_protection   = true            # Prod: Deletion Protection enabled
#
#   enable_performance_insights = true # Prod: Performance Insights mandatory
#   enable_cloudwatch_alarms    = true # Prod: CloudWatch Alarms mandatory
#
#   # Prod: Multi-AZ for High Availability
#   # Note: Aurora Serverless v2 supports Multi-AZ durch Replicas
# }

# DynamoDB Module (Primary Database)
module "database_dynamodb" {
  source = "../../modules/database-dynamodb"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = local.aws_region
  aws_account_id = local.aws_account_id

  # Prod: Provisioned Capacity with Auto-Scaling (vorhersagbare Performance)
  billing_mode = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  enable_autoscaling = true
  autoscaling_read_target  = 70  # Target 70% utilization
  autoscaling_write_target = 70
  autoscaling_read_min     = 5
  autoscaling_read_max     = 100
  autoscaling_write_min    = 5
  autoscaling_write_max    = 100

  # Prod: Point-in-Time Recovery enabled (35 days)
  enable_point_in_time_recovery = true

  # Prod: Automated backups
  enable_automated_backups = true
  backup_retention_days    = 30

  # TTL enabled für auto-cleanup
  enable_ttl = true
  ttl_attribute_name = "ttl"
}

# Compute Module
module "compute" {
  source = "../../modules/compute"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = local.aws_account_id

  # Lambda Config
  lambda_image_uri   = var.lambda_image_uri
  lambda_timeout     = 120  # Prod: längere Timeouts für komplexe Operationen
  lambda_memory_size = 2048 # Prod: 2GB Memory
  log_level          = "WARNING" # Prod: WARNING (nur wichtige Logs)

  # VPC
  enable_vpc               = true
  private_subnet_ids       = module.networking.private_subnet_ids
  lambda_security_group_id = module.networking.lambda_security_group_id

  # DynamoDB (ersetzt PostgreSQL)
  dynamodb_table_name = module.database_dynamodb.table_name
  dynamodb_table_arn  = module.database_dynamodb.table_arn

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
  cors_origins               = var.cors_origins # Prod: Strict CORS

  # Monitoring
  enable_cloudwatch_alarms = true # Prod: Alarms mandatory
  log_retention_days       = 30   # Prod: 30 Tage Log Retention

  # Reserved Concurrency (optional, für vorhersagbare Performance)
  # reserved_concurrent_executions = 100
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
  pagerduty_endpoint    = var.pagerduty_endpoint # Prod: PagerDuty für 24/7 On-Call

  # Resource IDs
  lambda_function_name  = module.compute.lambda_function_name
  lambda_log_group_name = module.compute.lambda_log_group_name
  api_gateway_id        = module.compute.http_api_id
  dynamodb_table_name   = module.database_dynamodb.table_name

  # Thresholds (prod: sehr streng)
  lambda_error_threshold_critical = 5  # Prod: 5 Fehler triggern Alert
  api_5xx_threshold_critical      = 3  # Prod: 3 Fehler triggern Alert
  api_4xx_threshold_warning       = 20 # Prod: 20 4XX Fehler

  # SLA Monitoring
  enable_sla_monitoring = true # Prod: 99.9% Uptime SLA
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
  cloudtrail_retention_days     = 365 # Prod: 1 Jahr (Compliance)
  cloudtrail_log_retention_days = 90
  enable_multi_region_trail     = true # Prod: Multi-Region für Compliance

  # GuardDuty
  enable_guardduty            = true
  guardduty_finding_frequency = "FIFTEEN_MINUTES" # Prod: 15 min

  # Security Hub
  enable_security_hub = true # Prod: Security Hub mandatory

  # Config
  enable_config = true # Prod: AWS Config für Compliance Tracking
}

# Backup Module - Automated Backups & Disaster Recovery
module "backup" {
  source = "../../modules/backup"

  providers = {
    aws.secondary = aws.secondary # DR region provider
  }

  project_name = var.project_name
  environment  = var.environment
  aws_region   = local.aws_region
  dr_region    = var.dr_region

  # KMS Encryption (use storage module KMS key if available)
  kms_key_arn    = module.storage.customer_data_kms_key_arn
  dr_kms_key_arn = null # MVP: DR region KMS wird in Phase 2 konfiguriert

  # Backup Retention (Production: Long retention)
  daily_backup_retention_days   = 30   # 30 days
  weekly_backup_retention_days  = 90   # 90 days (quarterly)
  monthly_backup_retention_days = 365  # 1 year (annual compliance)

  # Backup Plans (Production: All enabled)
  enable_weekly_backups  = true
  enable_monthly_backups = true

  # Cross-Region Backup for Disaster Recovery
  enable_cross_region_backup = false # MVP: DR wird in Phase 2 aktiviert

  # Resources to Backup
  # DynamoDB Point-in-Time Recovery is enabled in the database_dynamodb module
  dynamodb_table_arns = [module.database_dynamodb.table_arn]

  # S3 Cross-Region Replication
  enable_s3_cross_region_replication = false # MVP: DR wird in Phase 2 aktiviert
  s3_source_bucket_arns = [
    module.storage.customer_data_bucket_arn,
    module.storage.deployment_states_bucket_arn
  ]
  s3_destination_bucket_arns = [] # MVP: DR region S3 wird in Phase 2 erstellt

  # Monitoring
  enable_backup_alarms = true
  alarm_sns_topic_arns = [
    module.monitoring.critical_alerts_topic_arn
  ]
}

# WAF Module - Web Application Firewall & DDoS Protection
# Prod: Maximum protection - All features enabled
# Note: StackVertex uses API Gateway HTTP API (v2) which is NOT compatible with WAF.
#       Instead, we protect both frontend AND backend via CloudFront WAF by routing
#       API traffic through CloudFront (e.g., /api/* origin to API Gateway).
module "waf" {
  source = "../../modules/waf"

  project_name = var.project_name
  environment  = var.environment

  # Prod: Enable CloudFront WAF (protects frontend AND backend via CloudFront)
  enable_cloudfront_waf = true

  # Prod: Regional WAF disabled (HTTP API v2 not compatible with WAF)
  # To protect backend: Route API Gateway through CloudFront as origin
  enable_regional_waf = false

  # Rate Limiting (Prod: Strict - 2000 requests per 5 min per IP)
  rate_limit_requests = 2000

  # Geo-Blocking (Prod: Enabled - Only EU + US)
  enable_geo_blocking = true
  allowed_countries   = ["DE", "AT", "CH", "FR", "NL", "BE", "IT", "ES", "GB", "US", "CA"]

  # Bot Control (Prod: Enabled for maximum protection)
  # Cost: ~$10/month but protection is more important
  enable_bot_control = true

  # Logging (Prod: Enabled for forensics)
  enable_waf_logging      = true
  waf_log_retention_days  = 90 # Prod: 90 days retention

  # Alarms (Prod: Enabled for attack detection)
  enable_waf_alarms           = true
  blocked_requests_threshold  = 1000 # Alert when >1000 requests blocked in 5 min
  alarm_sns_topic_arns        = [module.monitoring.critical_alerts_topic_arn]
}

# Route53 Module - DNS Management
module "route53" {
  source = "../../modules/route53"
  count  = var.create_route53_zone ? 1 : 0

  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.domain_name

  # DNSSEC (optional, für höhere Sicherheit)
  enable_dnssec = false # MVP: Erst in Phase 2

  # Monitoring
  enable_health_checks = true
  alarm_sns_topic_arns = [module.monitoring.warning_alerts_topic_arn]
}

# ACM Module - SSL/TLS Certificates
module "acm" {
  source = "../../modules/acm"
  count  = var.create_acm_certificate ? 1 : 0

  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.domain_name

  # Subject Alternative Names (SANs)
  subject_alternative_names = [
    "*.${var.domain_name}", # Wildcard für Subdomains (app.stackvertex.io, api.stackvertex.io)
  ]

  # Route53 Zone ID for DNS validation
  route53_zone_id = var.create_route53_zone ? module.route53[0].zone_id : null

  # Certificate Transparency Logging (best practice)
  enable_certificate_transparency_logging = true
}

# CloudFront Module - CDN & HTTPS Distribution
module "cloudfront" {
  source = "../../modules/cloudfront"
  count  = var.enable_cloudfront ? 1 : 0

  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.domain_name

  # SSL Certificate (ACM)
  acm_certificate_arn = var.create_acm_certificate ? module.acm[0].certificate_arn : null

  # Origins
  # 1. Frontend Origin (S3 bucket for static site)
  s3_bucket_regional_domain_name = module.storage.frontend_bucket_regional_domain_name
  s3_origin_id                   = "S3-Frontend"

  # 2. Backend Origin (API Gateway for API routes)
  # CloudFront kann /api/* requests an API Gateway routen
  api_gateway_domain_name = module.compute.http_api_domain_name
  api_origin_id           = "APIGateway-Backend"

  # Price Class (Prod: PriceClass_100 = US, Canada, Europe)
  price_class = var.cloudfront_price_class

  # WAF (from waf module)
  web_acl_id = module.waf.cloudfront_web_acl_id

  # Logging (S3 bucket for CloudFront access logs)
  enable_logging       = true
  logging_bucket       = module.storage.logs_bucket_id
  logging_prefix       = "cloudfront/"
  log_retention_days   = 90

  # Performance & Security
  http_version                 = "http2and3" # HTTP/2 + HTTP/3 (QUIC)
  minimum_protocol_version     = "TLSv1.2_2021"
  enable_ipv6                  = true
  default_root_object          = "index.html"
  custom_error_responses       = [
    {
      error_code         = 404
      response_code      = 200
      response_page_path = "/index.html" # SPA routing
    },
    {
      error_code         = 403
      response_code      = 200
      response_page_path = "/index.html" # SPA routing
    }
  ]

  # Cache Behavior
  # Frontend: Cache everything (HTML, CSS, JS, images)
  # Backend: No cache (API responses)
  default_cache_behavior = {
    target_origin_id       = "S3-Frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    default_ttl            = 3600      # 1 hour
    max_ttl                = 86400     # 1 day
    min_ttl                = 0
  }

  ordered_cache_behaviors = [
    {
      path_pattern           = "/api/*"
      target_origin_id       = "APIGateway-Backend"
      viewer_protocol_policy = "https-only"
      allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
      cached_methods         = ["GET", "HEAD"]
      compress               = true
      default_ttl            = 0  # No cache for API
      max_ttl                = 0
      min_ttl                = 0
    },
    {
      path_pattern           = "/ws"
      target_origin_id       = "APIGateway-Backend"
      viewer_protocol_policy = "https-only"
      allowed_methods        = ["GET", "HEAD", "OPTIONS"]
      cached_methods         = []
      compress               = false
      default_ttl            = 0  # No cache for WebSocket upgrade
      max_ttl                = 0
      min_ttl                = 0
    }
  ]

  # Geo Restrictions (optional, WAF already handles this)
  geo_restriction_type = "none"

  # Monitoring
  enable_cloudfront_alarms = true
  alarm_sns_topic_arns     = [module.monitoring.warning_alerts_topic_arn]
}
