# Frontend Static Website Hosting - S3 Bucket + CloudFront

# S3 Bucket für Frontend (Static Website Hosting)
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-${var.environment}-frontend"

  tags = {
    Name        = "${var.project_name}-${var.environment}-frontend"
    Description = "Static website hosting for frontend"
    Purpose     = "frontend"
  }
}

# Public Access Block (für dev: public website, prod: CloudFront only)
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = !var.enable_public_website_access
  block_public_policy     = false # Bucket Policy muss allowed sein
  ignore_public_acls      = !var.enable_public_website_access
  restrict_public_buckets = !var.enable_public_website_access
}

# Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Versioning (optional, für Rollbacks)
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = var.enable_frontend_versioning ? "Enabled" : "Disabled"
  }
}

# Website Configuration
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html" # SPA Routing - alle 404s gehen zu index.html
  }
}

# Bucket Policy - Public Read (dev) oder CloudFront only (prod)
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      var.enable_public_website_access ? [
        {
          Sid       = "PublicReadGetObject"
          Effect    = "Allow"
          Principal = "*"
          Action    = "s3:GetObject"
          Resource  = "${aws_s3_bucket.frontend.arn}/*"
        }
      ] : [],
      !var.enable_public_website_access ? [
        {
          Sid    = "AllowCloudFrontOAI"
          Effect = "Allow"
          Principal = {
            Service = "cloudfront.amazonaws.com"
          }
          Action   = "s3:GetObject"
          Resource = "${aws_s3_bucket.frontend.arn}/*"
        }
      ] : []
    )
  })
}

# CORS Configuration (falls direkt von anderem Origin zugegriffen wird)
resource "aws_s3_bucket_cors_configuration" "frontend" {
  count  = var.enable_frontend_cors ? 1 : 0
  bucket = aws_s3_bucket.frontend.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = var.frontend_cors_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}
