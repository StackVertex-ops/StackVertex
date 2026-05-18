/**
 * User Data Storage Module
 *
 * S3 Bucket für Upload von User-Daten (Docker Images, Static Files)
 * - Encrypted at Rest (KMS)
 * - Versioning enabled (für Rollbacks)
 * - Lifecycle Rules (Auto-Cleanup)
 * - IAM Policies für Lambda/ECS Access
 */

# S3 Bucket für User-Daten
resource "aws_s3_bucket" "user_data" {
  bucket = "overcloud-user-data-${var.environment}"

  tags = {
    Name        = "OverCloud User Data Storage"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "OverCloud"
  }
}

# Encryption at Rest (KMS)
resource "aws_s3_bucket_server_side_encryption_configuration" "user_data" {
  bucket = aws_s3_bucket.user_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.user_data.arn
    }
    bucket_key_enabled = true
  }
}

# Versioning (für Rollbacks)
resource "aws_s3_bucket_versioning" "user_data" {
  bucket = aws_s3_bucket.user_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block Public Access (Security)
resource "aws_s3_bucket_public_access_block" "user_data" {
  bucket = aws_s3_bucket.user_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle Rules (Auto-Cleanup)
resource "aws_s3_bucket_lifecycle_configuration" "user_data" {
  bucket = aws_s3_bucket.user_data.id

  # Cleanup alte Versionen nach 90 Tagen
  rule {
    id     = "cleanup-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.version_retention_days
    }
  }

  # Cleanup unvollständige Multipart Uploads nach 7 Tagen
  rule {
    id     = "cleanup-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Optional: Transition alte Daten zu Glacier
  dynamic "rule" {
    for_each = var.enable_glacier_transition ? [1] : []

    content {
      id     = "transition-to-glacier"
      status = "Enabled"

      transition {
        days          = var.glacier_transition_days
        storage_class = "GLACIER"
      }

      noncurrent_version_transition {
        noncurrent_days = var.glacier_transition_days
        storage_class   = "GLACIER"
      }
    }
  }
}

# CORS Configuration (für direkte Browser Uploads)
resource "aws_s3_bucket_cors_configuration" "user_data" {
  bucket = aws_s3_bucket.user_data.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = var.allowed_cors_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# KMS Key für Encryption
resource "aws_kms_key" "user_data" {
  description             = "KMS key for OverCloud user data encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "overcloud-user-data-key-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_kms_alias" "user_data" {
  name          = "alias/overcloud-user-data-${var.environment}"
  target_key_id = aws_kms_key.user_data.key_id
}

# IAM Policy für Lambda/ECS (Data Upload/Copy)
resource "aws_iam_policy" "user_data_access" {
  name        = "overcloud-user-data-access-${var.environment}"
  description = "Allow Lambda/ECS to read/write user data in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetObjectVersion",
          "s3:ListBucketVersions"
        ]
        Resource = [
          aws_s3_bucket.user_data.arn,
          "${aws_s3_bucket.user_data.arn}/*"
        ]
      },
      {
        Sid    = "KMSAccess"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.user_data.arn
      }
    ]
  })

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# IAM Role für Lambda (Data Upload Service)
resource "aws_iam_role" "data_upload_lambda" {
  name = "overcloud-data-upload-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Attach S3 Access Policy to Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.data_upload_lambda.name
  policy_arn = aws_iam_policy.user_data_access.arn
}

# Attach Basic Lambda Execution Policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.data_upload_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Group für Audit Logs
resource "aws_cloudwatch_log_group" "user_data_access_logs" {
  name              = "/aws/s3/overcloud-user-data-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
