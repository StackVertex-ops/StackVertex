# API Gateway Module

Erstellt AWS API Gateway v2 (HTTP API + WebSocket API) für StackVertex:
- **HTTP API** - REST Endpoints (Lambda Integration)
- **WebSocket API** - Real-time Deployment Updates (Lambda Integration)

## Features

- **HTTP API** (API Gateway v2) - schneller & günstiger als REST API v1
- **WebSocket API** - $connect, $disconnect, $default Routes
- **CORS Configuration** - vollständig konfigurierbar
- **Throttling & Rate Limiting** - DDoS Protection
- **CloudWatch Logs** - Access Logs für alle Requests
- **Custom Domains** (optional) - eigene Domain mit ACM Certificate
- **WAF Integration** (optional) - Web Application Firewall
- **Lambda Permissions** - automatisch erstellt

## Architektur

```
┌──────────────────────────────────────────────────────┐
│                   Internet Users                     │
└────────────────┬─────────────────┬───────────────────┘
                 │                 │
                 ▼                 ▼
        ┌─────────────┐   ┌─────────────────┐
        │  HTTP API   │   │  WebSocket API  │
        │  (REST)     │   │  (Real-time)    │
        └──────┬──────┘   └────────┬────────┘
               │                   │
               │                   ├─ $connect
               │                   ├─ $disconnect
               │                   └─ $default
               │                   │
               ▼                   ▼
        ┌──────────────────────────────┐
        │    Lambda Functions          │
        │  - api-handler               │
        │  - ws-connect                │
        │  - ws-disconnect             │
        │  - ws-message                │
        └──────────────────────────────┘
```

## Usage

```hcl
module "api_gateway" {
  source = "../../modules/api-gateway"

  # Project Configuration
  project_name = "stackvertex"
  environment  = "prod"

  # HTTP API
  lambda_invoke_arn    = module.lambda_api.api_handler_invoke_arn
  lambda_function_name = module.lambda_api.api_handler_function_name
  stage_name           = "prod"
  integration_timeout_ms = 30000

  # CORS
  cors_allow_origins     = ["https://app.stackvertex.io", "https://www.stackvertex.io"]
  cors_allow_methods     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
  cors_allow_headers     = ["*"]
  cors_allow_credentials = true
  cors_max_age           = 86400

  # Throttling
  throttle_burst_limit = 5000
  throttle_rate_limit  = 2000

  # WebSocket API
  websocket_lambda_arns = module.lambda_api.websocket_lambda_arns
  websocket_lambda_function_names = {
    connect    = module.lambda_api.websocket_connect_function_name
    disconnect = module.lambda_api.websocket_disconnect_function_name
    message    = module.lambda_api.websocket_message_function_name
  }

  # Custom Domain (optional)
  custom_domain_name           = "api.stackvertex.io"
  websocket_custom_domain_name = "ws.stackvertex.io"
  certificate_arn              = module.acm.certificate_arn

  # WAF (optional)
  waf_acl_arn = module.waf.web_acl_arn

  # Logs
  log_retention_days = 30

  tags = {
    Project     = "StackVertex"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
```

## HTTP API vs REST API (v1)

**Warum HTTP API (v2)?**

| Feature | HTTP API (v2) | REST API (v1) |
|---------|---------------|---------------|
| **Preis** | 50% günstiger | Teurer |
| **Performance** | Schneller | Langsamer |
| **WebSocket** | Native Support | Separate API |
| **Lambda Proxy** | Payload v2.0 | Payload v1.0 |
| **CORS** | Built-in | Manuell |
| **Authorizer** | JWT, Lambda | Lambda Custom |

**Fazit:** HTTP API ist für StackVertex perfekt!

## WebSocket API

### Routes

- **$connect** - Client verbindet sich
- **$disconnect** - Client trennt Verbindung
- **$default** - Default Message Handler

### Connection Management

WebSocket Connections werden in **DynamoDB** gespeichert:

```python
# Connection in DynamoDB speichern
{
  "pk": "WSCONN#<connection_id>",
  "sk": "METADATA",
  "deployment_id": "...",
  "connected_at": "2026-05-25T10:00:00Z",
  "user_id": "..."
}
```

### Message Pushing

Backend pushed Messages via **API Gateway Management API**:

```python
import boto3

client = boto3.client('apigatewaymanagementapi',
    endpoint_url='https://<api-id>.execute-api.<region>.amazonaws.com/<stage>')

client.post_to_connection(
    ConnectionId='<connection_id>',
    Data=json.dumps({"type": "status_update", ...})
)
```

## CORS Configuration

**Production Best Practice:**

```hcl
cors_allow_origins     = ["https://app.stackvertex.io"]
cors_allow_methods     = ["GET", "POST", "PUT", "PATCH", "DELETE"]
cors_allow_headers     = ["Content-Type", "Authorization", "X-CSRF-Token"]
cors_allow_credentials = true
```

**Development:**

```hcl
cors_allow_origins = ["http://localhost:5173", "http://localhost:3000"]
cors_allow_headers = ["*"]
```

**⚠️ NIEMALS in Production:**

```hcl
cors_allow_origins = ["*"]
cors_allow_credentials = true
```

Reason: `*` + credentials ist ein **Security Risk**!

## Throttling & Rate Limiting

### Default Limits

- **Burst Limit**: 5000 requests
- **Rate Limit**: 2000 requests/second

### Per-User Rate Limiting

API Gateway Throttling ist **global**. Für Per-User Limits:

1. **Backend Implementation** (slowapi)
2. **WAF Rate-based Rules**
3. **CloudFront Rate Limiting**

### Production Tuning

**High Traffic (10k req/s):**

```hcl
throttle_burst_limit = 10000
throttle_rate_limit  = 10000
```

**Cost Optimization (low traffic):**

```hcl
throttle_burst_limit = 1000
throttle_rate_limit  = 500
```

## Custom Domain Setup

### 1. ACM Certificate erstellen

```hcl
module "acm" {
  source = "../../modules/acm"
  
  domain_name = "api.stackvertex.io"
  subject_alternative_names = [
    "ws.stackvertex.io"
  ]
}
```

### 2. API Gateway mit Custom Domain

```hcl
custom_domain_name           = "api.stackvertex.io"
websocket_custom_domain_name = "ws.stackvertex.io"
certificate_arn              = module.acm.certificate_arn
```

### 3. Route53 DNS Records

```hcl
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "api.stackvertex.io"
  type    = "A"

  alias {
    name                   = module.api_gateway.http_custom_domain_target
    zone_id                = "Z2FDTNDATAQYW2"  # CloudFront Zone ID
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "websocket" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "ws.stackvertex.io"
  type    = "A"

  alias {
    name                   = module.api_gateway.websocket_custom_domain_target
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}
```

## WAF Integration

**Warum WAF?**

- **DDoS Protection** - Rate-based Rules
- **SQL Injection Prevention** - Managed Rule Groups
- **XSS Protection** - Managed Rule Groups
- **IP Whitelisting/Blacklisting**
- **Geo-blocking**

**Example:**

```hcl
module "waf" {
  source = "../../modules/waf"
  
  name = "stackvertex-prod-waf"
  
  # AWS Managed Rules
  managed_rule_groups = [
    "AWSManagedRulesCommonRuleSet",
    "AWSManagedRulesKnownBadInputsRuleSet",
    "AWSManagedRulesSQLiRuleSet"
  ]
  
  # Rate Limiting
  rate_limit = 2000  # requests per 5 minutes from single IP
}

module "api_gateway" {
  source = "../../modules/api-gateway"
  
  waf_acl_arn = module.waf.web_acl_arn
  ...
}
```

## CloudWatch Logs

### Access Logs Format

HTTP API Logs:

```json
{
  "requestId": "abc123",
  "ip": "1.2.3.4",
  "requestTime": "25/May/2026:10:00:00 +0000",
  "httpMethod": "POST",
  "routeKey": "$default",
  "status": 200,
  "protocol": "HTTP/1.1",
  "responseLength": 1234,
  "integrationError": ""
}
```

WebSocket Logs:

```json
{
  "requestId": "xyz789",
  "connectionId": "abc123==",
  "eventType": "MESSAGE",
  "routeKey": "$default",
  "status": 200,
  "requestTime": "25/May/2026:10:00:00 +0000",
  "integrationError": ""
}
```

### Log Insights Queries

**Top API Endpoints:**

```sql
fields @timestamp, httpMethod, routeKey, status
| stats count() by routeKey
| sort count desc
```

**Error Rate:**

```sql
fields @timestamp, status, integrationError
| filter status >= 400
| stats count() by status
```

**WebSocket Connections:**

```sql
fields @timestamp, eventType, connectionId
| filter eventType = "CONNECT"
| stats count() by bin(5m)
```

## Cost Optimization

### API Gateway Pricing (us-east-1)

**HTTP API:**
- $1.00 per million requests
- $0.09 per GB data transfer out

**WebSocket API:**
- $1.00 per million messages
- $0.25 per million connection minutes

**Example (1M HTTP requests + 100k WS connections @ 10 min average):**

```
HTTP: 1M × $1.00 = $1.00
WS Messages: 200k × $1.00 = $0.20
WS Connections: 100k × 10 min = 1M min × $0.25/M = $0.25
Total: $1.45/month
```

### Optimization Tips

1. **Caching** - CloudFront vor API Gateway
2. **Batching** - Multiple operations in one request
3. **Compression** - gzip/br für Responses
4. **WebSocket** - nur für real-time, nicht für Polling

## Security Best Practices

### ✅ Implemented

- **HTTPS only** - TLS 1.2+
- **CORS** - Whitelist Origins
- **Throttling** - DDoS Protection
- **CloudWatch Logs** - Audit Trail
- **Lambda Authorizer** - JWT Validation

### ⚠️ TODO (für Production)

- **WAF** - Managed Rule Groups
- **API Keys** - für externe APIs (optional)
- **Usage Plans** - Quotas & Throttling per Customer
- **CloudFront** - Caching + DDoS Protection
- **Resource Policies** - IP Whitelisting (optional)

## Troubleshooting

### 502 Bad Gateway

**Ursachen:**
- Lambda Timeout (>30s)
- Lambda Error (unhandled exception)
- Integration Timeout

**Lösung:**
1. Check Lambda CloudWatch Logs
2. Erhöhe Lambda Timeout
3. Fix Lambda Code

### 429 Too Many Requests

**Ursachen:**
- Throttling Limit erreicht
- Burst Limit überschritten

**Lösung:**
1. Erhöhe `throttle_rate_limit`
2. Implementiere Client-side Retry (exponential backoff)
3. Cache Responses

### WebSocket Connection Timeout

**Problem:** WebSocket disconnect nach 2 Stunden (idle)

**Grund:** API Gateway Limit (max idle time)

**Lösung:** Client implementiert ping/pong (keep-alive)

```javascript
// Client-side Keep-Alive
setInterval(() => {
  ws.send(JSON.stringify({ action: 'ping' }));
}, 60000);  // Every 60 seconds
```

### CORS Errors

**Problem:** Browser blocks API calls

**Ursachen:**
- `cors_allow_origins` falsch konfiguriert
- `cors_allow_credentials = true` + `origins = ["*"]`
- `cors_allow_headers` fehlt

**Lösung:**
1. Explizite Origin Whitelist
2. Include alle verwendeten Headers
3. Test mit `curl -H "Origin: ..."` 

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Project name | string | - | yes |
| environment | Environment | string | - | yes |
| lambda_invoke_arn | Lambda invoke ARN | string | - | yes |
| lambda_function_name | Lambda function name | string | - | yes |
| stage_name | Stage name | string | prod | no |
| cors_allow_origins | CORS origins | list(string) | ["*"] | no |
| throttle_burst_limit | Burst limit | number | 5000 | no |
| throttle_rate_limit | Rate limit | number | 2000 | no |
| websocket_lambda_arns | WebSocket Lambda ARNs | map(string) | - | yes |
| custom_domain_name | Custom domain | string | "" | no |
| certificate_arn | ACM certificate ARN | string | "" | no |
| waf_acl_arn | WAF ACL ARN | string | "" | no |

## Outputs

| Name | Description |
|------|-------------|
| http_api_endpoint | HTTP API endpoint URL |
| websocket_api_connection_url | WebSocket connection URL |
| http_api_id | HTTP API ID |
| websocket_api_id | WebSocket API ID |

## Related Modules

- **lambda-api** - Lambda Functions für API Handlers
- **acm** - SSL/TLS Certificates
- **waf** - Web Application Firewall
- **route53** - DNS Records

## License

Proprietary - StackVertex Platform
