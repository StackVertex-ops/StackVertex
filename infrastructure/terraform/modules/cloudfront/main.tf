# CloudFront Module - CDN + HTTPS für Frontend & API

terraform {
  required_version = ">= 1.5.0"
}

# CloudFront Origin Access Identity für S3
resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "${var.project_name}-${var.environment}-frontend-oai"
}

# CloudFront Distribution für Frontend (Static Website)
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name}-${var.environment}-frontend"
  default_root_object = "index.html"
  price_class         = var.price_class
  aliases             = var.frontend_domain != null ? [var.frontend_domain] : []

  origin {
    domain_name = var.frontend_bucket_domain_name
    origin_id   = "S3-Frontend"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    target_origin_id       = "S3-Frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600   # 1 Stunde
    max_ttl     = 86400  # 24 Stunden
  }

  # Custom Error Response für SPA (React Router, etc.)
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL Certificate
  viewer_certificate {
    acm_certificate_arn      = var.frontend_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-cdn"
  }
}

# CloudFront Distribution für API
resource "aws_cloudfront_distribution" "api" {
  count = var.enable_api_cloudfront ? 1 : 0

  enabled         = true
  is_ipv6_enabled = true
  comment         = "${var.project_name}-${var.environment}-api"
  price_class     = var.price_class
  aliases         = var.api_domain != null ? [var.api_domain] : []

  origin {
    domain_name = var.api_gateway_domain_name
    origin_id   = "API-Gateway"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "API-Gateway"
    viewer_protocol_policy = "https-only"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # Caching Strategy für API
    cache_policy_id          = var.api_cache_policy_id != null ? var.api_cache_policy_id : aws_cloudfront_cache_policy.api[0].id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api[0].id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.api_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-cdn"
  }
}

# Cache Policy für API
resource "aws_cloudfront_cache_policy" "api" {
  count = var.enable_api_cloudfront && var.api_cache_policy_id == null ? 1 : 0

  name        = "${var.project_name}-${var.environment}-api-cache-policy"
  comment     = "Cache policy for API with short TTL"
  default_ttl = 0      # Kein Default Caching
  max_ttl     = 300    # Max 5 Minuten
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Authorization", "Accept", "Content-Type"]
      }
    }

    query_strings_config {
      query_string_behavior = "all"
    }

    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

# Origin Request Policy für API
resource "aws_cloudfront_origin_request_policy" "api" {
  count = var.enable_api_cloudfront ? 1 : 0

  name    = "${var.project_name}-${var.environment}-api-origin-request-policy"
  comment = "Forward all headers, query strings, and cookies to API"

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "allViewer"
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

# S3 Bucket Policy für CloudFront Access
resource "aws_s3_bucket_policy" "frontend_cloudfront" {
  bucket = var.frontend_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAI"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${var.frontend_bucket_arn}/*"
      }
    ]
  })
}
