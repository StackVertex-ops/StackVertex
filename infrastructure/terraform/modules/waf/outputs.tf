# WAF Module Outputs

# CloudFront WAF
output "cloudfront_web_acl_id" {
  description = "ID of the CloudFront WAF Web ACL"
  value       = var.enable_cloudfront_waf ? aws_wafv2_web_acl.cloudfront[0].id : null
}

output "cloudfront_web_acl_arn" {
  description = "ARN of the CloudFront WAF Web ACL"
  value       = var.enable_cloudfront_waf ? aws_wafv2_web_acl.cloudfront[0].arn : null
}

output "cloudfront_web_acl_name" {
  description = "Name of the CloudFront WAF Web ACL"
  value       = var.enable_cloudfront_waf ? aws_wafv2_web_acl.cloudfront[0].name : null
}

# Regional WAF (ALB)
output "regional_web_acl_id" {
  description = "ID of the regional WAF Web ACL"
  value       = var.enable_regional_waf ? aws_wafv2_web_acl.regional[0].id : null
}

output "regional_web_acl_arn" {
  description = "ARN of the regional WAF Web ACL"
  value       = var.enable_regional_waf ? aws_wafv2_web_acl.regional[0].arn : null
}

output "regional_web_acl_name" {
  description = "Name of the regional WAF Web ACL"
  value       = var.enable_regional_waf ? aws_wafv2_web_acl.regional[0].name : null
}

# Logging
output "waf_log_group_name" {
  description = "Name of the CloudWatch Log Group for WAF logs"
  value       = var.enable_waf_logging ? aws_cloudwatch_log_group.waf_logs[0].name : null
}

output "waf_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for WAF logs"
  value       = var.enable_waf_logging ? aws_cloudwatch_log_group.waf_logs[0].arn : null
}

# Cost Summary
output "waf_cost_summary" {
  description = "Summary of WAF costs (monthly estimates)"
  value = {
    base_cost = var.enable_cloudfront_waf || var.enable_regional_waf ? "~$5/month (Web ACL + Rules)" : "$0"
    rate_limiting_cost = var.enable_cloudfront_waf || var.enable_regional_waf ? "$1/month per rule + $0.60 per 1M requests" : "$0"
    bot_control_cost = var.enable_bot_control ? "~$10/month" : "$0 (disabled)"
    total_estimated = var.enable_bot_control ? "~$16-20/month" : "~$6-10/month"
    free_features = [
      "AWS Managed Rules (Core, Known Bad Inputs, SQLi)",
      "Shield Standard (DDoS protection)",
      "CloudWatch Metrics"
    ]
    note = "Actual costs depend on traffic volume. Rate limiting charges $0.60 per 1M requests."
  }
}

# Security Summary
output "waf_security_summary" {
  description = "Summary of enabled security features"
  value = {
    cloudfront_waf_enabled = var.enable_cloudfront_waf
    regional_waf_enabled   = var.enable_regional_waf
    rate_limiting_enabled  = var.enable_cloudfront_waf || var.enable_regional_waf
    rate_limit_threshold   = "${var.rate_limit_requests} requests per 5 minutes"
    geo_blocking_enabled   = var.enable_geo_blocking
    allowed_countries      = var.enable_geo_blocking ? var.allowed_countries : []
    bot_control_enabled    = var.enable_bot_control
    waf_logging_enabled    = var.enable_waf_logging
    waf_alarms_enabled     = var.enable_waf_alarms

    protection_level = var.enable_bot_control && var.enable_geo_blocking ? "Maximum (All features)" : var.enable_geo_blocking ? "High (Geo-blocking enabled)" : "Standard (AWS Managed Rules + Rate Limiting)"

    managed_rules = [
      "AWSManagedRulesCommonRuleSet (OWASP Top 10)",
      "AWSManagedRulesKnownBadInputsRuleSet",
      "AWSManagedRulesSQLiRuleSet",
      var.enable_bot_control ? "AWSManagedRulesBotControlRuleSet (PAID)" : "Bot Control: Disabled (cost saving)"
    ]
  }
}

# Alarm ARN
output "waf_blocked_requests_alarm_arn" {
  description = "ARN of the WAF blocked requests CloudWatch alarm"
  value       = var.enable_waf_alarms && var.enable_cloudfront_waf ? aws_cloudwatch_metric_alarm.waf_blocked_requests[0].arn : null
}
