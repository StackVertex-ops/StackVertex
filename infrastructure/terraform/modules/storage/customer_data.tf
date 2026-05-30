# Customer Data Storage - S3 Buckets für Customer Application Data

# S3 Bucket für Customer Data (Shared mit Prefixes)
resource "aws_s3_bucket" "customer_data" {
  bucket = "${var.project_name}-${var.environment}-customer-data-${var.aws_account_id}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-customer-data"
    Description = "Customer application data storage"
    Purpose     = "customer-data"
  }
}

# Versioning für Customer Data (optional, aber empfohlen)
resource "aws_s3_bucket_versioning" "customer_data" {
  bucket = aws_s3_bucket.customer_data.id

  versioning_configuration {
    status = var.enable_customer_data_versioning ? "Enabled" : "Disabled"
  }
}

# Encryption at rest (PFLICHT für Customer Data!)
resource "aws_s3_bucket_server_side_encryption_configuration" "customer_data" {
  bucket = aws_s3_bucket.customer_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.customer_data_encryption_type
      kms_master_key_id = var.customer_data_encryption_type == "aws:kms" ? var.customer_data_kms_key_id : null
    }
    bucket_key_enabled = var.customer_data_encryption_type == "aws:kms" ? true : false
  }
}

# Block public access (KRITISCH!)
resource "aws_s3_bucket_public_access_block" "customer_data" {
  bucket = aws_s3_bucket.customer_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle Rules für Customer Data
resource "aws_s3_bucket_lifecycle_configuration" "customer_data" {
  bucket = aws_s3_bucket.customer_data.id

  # Rule 1: Transition alte Daten zu günstigeren Storage Classes
  rule {
    id     = "transition-old-data"
    status = var.enable_customer_data_lifecycle ? "Enabled" : "Disabled"

    filter {
      prefix = "" # Alle Objekte
    }

    # Nach 30 Tagen → Infrequent Access (50% günstiger)
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Nach 90 Tagen → Intelligent-Tiering (Auto-Optimization)
    transition {
      days          = 90
      storage_class = "INTELLIGENT_TIERING"
    }

    # Optional: Nach 180 Tagen → Glacier (nur für Backups)
    dynamic "transition" {
      for_each = var.enable_customer_data_archival ? [1] : []
      content {
        days          = 180
        storage_class = "GLACIER_IR" # Instant Retrieval
      }
    }
  }

  # Rule 2: Delete old versions (nur wenn Versioning aktiv)
  dynamic "rule" {
    for_each = var.enable_customer_data_versioning ? [1] : []
    content {
      id     = "delete-old-versions"
      status = "Enabled"

      filter {}

      noncurrent_version_transition {
        noncurrent_days = 30
        storage_class   = "STANDARD_IA"
      }

      noncurrent_version_expiration {
        noncurrent_days = var.customer_data_version_retention_days
      }
    }
  }

  # Rule 3: Delete incomplete multipart uploads (Cleanup)
  rule {
    id     = "cleanup-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# CORS Configuration für Customer Data (wenn Frontend direkt auf S3 zugreift)
resource "aws_s3_bucket_cors_configuration" "customer_data" {
  count  = var.enable_customer_data_cors ? 1 : 0
  bucket = aws_s3_bucket.customer_data.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.customer_data_cors_origins
    expose_headers  = ["ETag", "x-amz-request-id"]
    max_age_seconds = 3600
  }
}

# Note: Bucket Policy wird im Environment erstellt (nach Lambda Role Creation)
# Siehe environments/*/bucket_policies.tf

# CloudWatch Metrics für Customer Data Bucket
resource "aws_s3_bucket_metric" "customer_data" {
  bucket = aws_s3_bucket.customer_data.id
  name   = "EntireBucket"
}

# Optional: S3 Event Notifications (z.B. für Lambda Triggers)
resource "aws_s3_bucket_notification" "customer_data" {
  count  = var.enable_customer_data_notifications ? 1 : 0
  bucket = aws_s3_bucket.customer_data.id

  # Lambda Trigger bei Object Creation
  dynamic "lambda_function" {
    for_each = var.customer_data_notification_lambda_arn != null ? [1] : []
    content {
      lambda_function_arn = var.customer_data_notification_lambda_arn
      events              = ["s3:ObjectCreated:*"]
      filter_prefix       = "uploads/"
    }
  }
}

# Optional: KMS Key für Customer Data Encryption
resource "aws_kms_key" "customer_data" {
  count                   = var.create_customer_data_kms_key ? 1 : 0
  description             = "KMS key for ${var.project_name} customer data encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-${var.environment}-customer-data-kms"
  }
}

resource "aws_kms_alias" "customer_data" {
  count         = var.create_customer_data_kms_key ? 1 : 0
  name          = "alias/${var.project_name}-${var.environment}-customer-data"
  target_key_id = aws_kms_key.customer_data[0].key_id
}

# KMS Key Policy
resource "aws_kms_key_policy" "customer_data" {
  count  = var.create_customer_data_kms_key ? 1 : 0
  key_id = aws_kms_key.customer_data[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Sid    = "Enable IAM User Permissions"
          Effect = "Allow"
          Principal = {
            AWS = "arn:aws:iam::${var.aws_account_id}:root"
          }
          Action   = "kms:*"
          Resource = "*"
        }
      ],
      var.lambda_execution_role_arn != "" ? [
        {
          Sid    = "Allow Lambda to use the key"
          Effect = "Allow"
          Principal = {
            AWS = var.lambda_execution_role_arn
          }
          Action = [
            "kms:Decrypt",
            "kms:Encrypt",
            "kms:GenerateDataKey",
            "kms:DescribeKey"
          ]
          Resource = "*"
        }
      ] : [],
      [
        {
          Sid    = "Allow S3 to use the key for server-side encryption"
          Effect = "Allow"
          Principal = {
            Service = "s3.amazonaws.com"
          }
          Action = [
            "kms:Decrypt",
            "kms:GenerateDataKey"
          ]
          Resource = "*"
        }
      ]
    )
  })
}
