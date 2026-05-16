# WAF Module - Web Application Firewall & DDoS Protection
# Focus: Maximum protection with minimal cost

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# WAF Web ACL for CloudFront (Global)
# Note: CloudFront WAF must be created in us-east-1
resource "aws_wafv2_web_acl" "cloudfront" {
  count = var.enable_cloudfront_waf ? 1 : 0

  name  = "${var.project_name}-${var.environment}-cloudfront-waf"
  scope = "CLOUDFRONT" # CloudFront requires CLOUDFRONT scope

  default_action {
    allow {}
  }

  # Rule 1: AWS Managed Rules - Core Rule Set (FREE)
  # Protects against OWASP Top 10 vulnerabilities
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"

        # Exclude rules that might cause false positives
        # Adjust based on your application needs
        dynamic "rule_action_override" {
          for_each = var.waf_rule_exclusions

          content {
            name = rule_action_override.value
            action_to_use {
              count {}
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rule 2: AWS Managed Rules - Known Bad Inputs (FREE)
  # Blocks requests with malicious patterns
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rule 3: AWS Managed Rules - SQL Injection (FREE)
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rule 4: Rate Limiting - Protect against DDoS
  # Cost: $1/month per rule + $0.60 per 1M requests
  rule {
    name     = "RateLimitRule"
    priority = 4

    action {
      block {
        custom_response {
          response_code = 429
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit_requests # Default: 2000 requests per 5 min
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRuleMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rule 5: Geo-Blocking (Optional, cost-effective way to reduce attack surface)
  dynamic "rule" {
    for_each = var.enable_geo_blocking ? [1] : []

    content {
      name     = "GeoBlockingRule"
      priority = 5

      action {
        block {}
      }

      statement {
        not_statement {
          statement {
            geo_match_statement {
              country_codes = var.allowed_countries # e.g., ["DE", "AT", "CH", "US", "GB"]
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "GeoBlockingRuleMetric"
        sampled_requests_enabled   = true
      }
    }
  }

  # Rule 6: AWS Managed Rules - Bot Control (PAID: ~$10/month)
  # Only enable for production if budget allows
  dynamic "rule" {
    for_each = var.enable_bot_control ? [1] : []

    content {
      name     = "AWSManagedRulesBotControlRuleSet"
      priority = 6

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesBotControlRuleSet"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesBotControlRuleSetMetric"
        sampled_requests_enabled   = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-cloudfront-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cloudfront-waf"
    Environment = var.environment
  }
}

# WAF Web ACL for ALB (Regional)
resource "aws_wafv2_web_acl" "regional" {
  count = var.enable_regional_waf ? 1 : 0

  name  = "${var.project_name}-${var.environment}-regional-waf"
  scope = "REGIONAL" # For ALB, API Gateway

  default_action {
    allow {}
  }

  # Same rules as CloudFront WAF (reusable pattern)
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 3

    action {
      block {
        custom_response {
          response_code = 429
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit_requests
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRuleMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-regional-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-regional-waf"
    Environment = var.environment
  }
}

# WAF Association with ALB
resource "aws_wafv2_web_acl_association" "alb" {
  count = var.enable_regional_waf && var.alb_arn != null ? 1 : 0

  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.regional[0].arn
}

# CloudWatch Log Group for WAF Logs (for forensics)
resource "aws_cloudwatch_log_group" "waf_logs" {
  count = var.enable_waf_logging ? 1 : 0

  name              = "/aws/wafv2/${var.project_name}-${var.environment}"
  retention_in_days = var.waf_log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-waf-logs"
    Environment = var.environment
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "cloudfront" {
  count = var.enable_cloudfront_waf && var.enable_waf_logging ? 1 : 0

  resource_arn = aws_wafv2_web_acl.cloudfront[0].arn

  log_destination_configs = [
    aws_cloudwatch_log_group.waf_logs[0].arn
  ]

  # Redact sensitive fields (GDPR compliance)
  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }
}

# CloudWatch Alarm - High Blocked Requests (possible attack)
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  count = var.enable_waf_alarms && var.enable_cloudfront_waf ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-waf-high-blocked-requests"
  alarm_description   = "High number of blocked requests (possible attack)"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300 # 5 minutes
  statistic           = "Sum"
  threshold           = var.blocked_requests_threshold # Default: 1000
  treat_missing_data  = "notBreaching"

  dimensions = {
    WebACL = aws_wafv2_web_acl.cloudfront[0].name
    Region = "us-east-1" # CloudFront is always us-east-1
    Rule   = "ALL"
  }

  alarm_actions = var.alarm_sns_topic_arns

  tags = {
    Name        = "${var.project_name}-${var.environment}-waf-blocked-alarm"
    Environment = var.environment
  }
}

# AWS Shield Standard (FREE) - Automatically enabled
# No Terraform resource needed, AWS Shield Standard is automatically active
# for CloudFront and ALB

# Output for Shield Advanced (PAID: $3000/month - only if absolutely necessary)
# Not created by default due to high cost
