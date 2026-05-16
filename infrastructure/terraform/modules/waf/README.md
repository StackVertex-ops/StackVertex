# WAF Module - Web Application Firewall & DDoS Protection

## Übersicht

Dieses Modul implementiert AWS WAF (Web Application Firewall) für maximalen Schutz bei minimalen Kosten.

**Design-Prinzip:** "Schutz ist wichtiger als Kosten" - kostenlose AWS Managed Rules kombiniert mit optionalen Premium-Features.

## Features

### ✅ Kostenlose Features (Immer aktiviert)

1. **AWS Managed Rules - Core Rule Set**
   - Schutz gegen OWASP Top 10 Schwachstellen
   - SQL Injection, XSS, Path Traversal, etc.
   - **Kosten:** $0 (FREE)

2. **AWS Managed Rules - Known Bad Inputs**
   - Blockiert Requests mit bekannten Malware-Patterns
   - **Kosten:** $0 (FREE)

3. **AWS Managed Rules - SQL Injection**
   - Spezialisierter Schutz gegen SQLi-Angriffe
   - **Kosten:** $0 (FREE)

4. **Rate Limiting**
   - Default: 2000 Requests pro 5 Minuten pro IP
   - Blockiert DDoS-Angriffe automatisch
   - **Kosten:** $1/Monat + $0.60 pro 1M Requests

5. **AWS Shield Standard**
   - Automatischer DDoS-Schutz (Layer 3/4)
   - **Kosten:** $0 (FREE, automatisch aktiv)

### 🔒 Optionale Premium-Features

1. **Geo-Blocking** (`enable_geo_blocking = true`)
   - Blockiert Requests aus nicht-erlaubten Ländern
   - Reduziert Angriffsfläche deutlich
   - **Kosten:** $0 (im Web ACL enthalten)

2. **Bot Control** (`enable_bot_control = true`)
   - Erkennt und blockiert schädliche Bots
   - Machine Learning basiert
   - **Kosten:** ~$10/Monat (nur für Prod empfohlen)

## Architektur

### CloudFront WAF (CLOUDFRONT Scope)
- **Region:** us-east-1 (erforderlich für CloudFront)
- **Scope:** Global (alle CloudFront Edge Locations)
- **Use Case:** Frontend (Static Website, SPA) + Backend (API Gateway als Origin)

### Regional WAF (REGIONAL Scope)
- **Region:** eu-central-1 (oder konfigurierbare Region)
- **Scope:** ALB, API Gateway REST API (v1)
- **Use Case:** Backend API (nur wenn ALB oder REST API verwendet wird)

**⚠️ Wichtig:** API Gateway HTTP API (v2) wird von WAF NICHT unterstützt! Nur REST API (v1), ALB, und CloudFront.

**OverCloud-Architektur:** Da OverCloud API Gateway HTTP API (v2) verwendet, schützen wir sowohl Frontend als auch Backend über CloudFront WAF:

```
┌───────────────────────────────────────────────────────┐
│              CloudFront (Global)                      │
│    WAF: OWASP + SQLi + Rate Limit + Bot Control      │
│                                                        │
│  Origins:                                             │
│  - /static/* → S3 Bucket (Frontend)                   │
│  - /api/*    → API Gateway HTTP API (Backend)         │
└───────────────────┬────────────────┬──────────────────┘
                    │                │
           ┌────────▼─────┐   ┌──────▼────────┐
           │  S3 (Static) │   │  API Gateway  │
           │   Frontend   │   │  HTTP API v2  │
           └──────────────┘   └───────┬───────┘
                                      │
                              ┌───────▼────────┐
                              │ Lambda Function│
                              └────────────────┘

✅ Vorteil: Single WAF schützt ALLES (Frontend + Backend)
✅ Kosten: Nur 1x CloudFront WAF (~$15-20/month statt $30-40)
✅ Performance: CloudFront Edge Caching + WAF in einem
```

**Alternative (wenn ALB verwendet würde):**
```
┌─────────────────────────────────────────────────┐
│           ALB (eu-central-1)                    │
│     WAF: OWASP + SQLi + Rate Limit              │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  ECS / Lambda   │
         └─────────────────┘

❌ Problem: Höhere Kosten (ALB $16/month + Regional WAF $15/month)
❌ Problem: HTTP API v2 nicht kompatibel mit WAF
```

## Kosten-Übersicht

### Staging (Cost-Optimized)
```
Web ACL (CloudFront only):        ~$5/month
Rate Limiting Rules:              $1/month
Request Charges:                  $0.60 per 1M requests
Logging (14 days retention):      ~$1/month
───────────────────────────────────────────────
Total (Staging):                  ~$7-8/month
```

### Production (Maximum Protection)
```
Web ACL (CloudFront only):        ~$5/month
Rate Limiting Rules:              $1/month
Bot Control (Premium):            ~$10/month
Request Charges:                  $0.60 per 1M requests
Logging (90 days retention):      ~$3-5/month
───────────────────────────────────────────────
Total (Production):               ~$19-22/month
```

**Note:** Request Charges hängen vom Traffic ab. Bei 10M Requests/Monat = $6 zusätzlich.

**Kostenersparnis:** Durch Verwendung von CloudFront WAF für Frontend + Backend (statt separater Regional WAF) sparen wir ~$10-15/Monat.

## Environment-Strategie

### Dev
- ❌ WAF disabled (Kosten sparen)
- Testing ohne WAF-Blockierung

### Staging
- ✅ CloudFront WAF enabled (schützt Frontend + Backend)
- ❌ Regional WAF disabled (HTTP API v2 nicht kompatibel)
- ✅ Rate Limiting enabled
- ❌ Geo-Blocking disabled (leichteres Testing)
- ❌ Bot Control disabled (Kosten sparen: ~$10/month)
- 14 Tage Log Retention

### Production
- ✅ CloudFront WAF enabled (schützt Frontend + Backend)
- ❌ Regional WAF disabled (HTTP API v2 nicht kompatibel)
- ✅ Rate Limiting enabled
- ✅ Geo-Blocking enabled (nur EU + US)
- ✅ Bot Control enabled (maximaler Schutz)
- 90 Tage Log Retention

**Hinweis:** Backend wird über CloudFront geschützt indem API Gateway als CloudFront Origin konfiguriert wird (z.B. `/api/*` → API Gateway). Dadurch profitiert auch das Backend von CloudFront WAF, Caching und Edge Locations.

## Usage

### Production (Maximum Protection)
```hcl
module "waf" {
  source = "../../modules/waf"

  project_name = "overcloud"
  environment  = "prod"

  # Enable both CloudFront + Regional WAF
  enable_cloudfront_waf = true
  enable_regional_waf   = true
  alb_arn               = module.compute.alb_arn

  # Rate Limiting
  rate_limit_requests = 2000 # 2000 requests per 5 min per IP

  # Geo-Blocking (only EU + US)
  enable_geo_blocking = true
  allowed_countries   = ["DE", "AT", "CH", "FR", "NL", "BE", "IT", "ES", "GB", "US", "CA"]

  # Bot Control (Premium - $10/month)
  enable_bot_control = true

  # Logging
  enable_waf_logging      = true
  waf_log_retention_days  = 90

  # Alarms
  enable_waf_alarms          = true
  blocked_requests_threshold = 1000
  alarm_sns_topic_arns       = [module.monitoring.critical_alerts_topic_arn]
}
```

### Staging (Cost-Optimized)
```hcl
module "waf" {
  source = "../../modules/waf"

  project_name = "overcloud"
  environment  = "staging"

  enable_cloudfront_waf = true
  enable_regional_waf   = true
  alb_arn               = module.compute.alb_arn

  rate_limit_requests = 2000

  # Geo-Blocking disabled for easier testing
  enable_geo_blocking = false

  # Bot Control disabled (save ~$10/month)
  enable_bot_control = false

  enable_waf_logging      = true
  waf_log_retention_days  = 14

  enable_waf_alarms          = true
  blocked_requests_threshold = 500 # Lower threshold for testing
  alarm_sns_topic_arns       = [module.monitoring.critical_alerts_topic_arn]
}
```

## Outputs

```hcl
# CloudFront WAF
cloudfront_web_acl_id   # Web ACL ID (for CloudFront association)
cloudfront_web_acl_arn  # Web ACL ARN

# Regional WAF
regional_web_acl_id     # Web ACL ID (for ALB association)
regional_web_acl_arn    # Web ACL ARN

# Logging
waf_log_group_name      # CloudWatch Log Group name
waf_log_group_arn       # CloudWatch Log Group ARN

# Cost & Security Summary
waf_cost_summary        # Monthly cost breakdown
waf_security_summary    # Enabled features overview
```

## Monitoring & Alarms

### CloudWatch Metrics
- `BlockedRequests` - Anzahl blockierter Requests
- `AllowedRequests` - Anzahl erlaubter Requests
- `CountedRequests` - Anzahl gezählter Requests (Count-Modus)

### CloudWatch Alarms
- **High Blocked Requests** - Triggert bei >1000 (Prod) oder >500 (Staging) blockierten Requests in 5 Minuten
- **Action:** SNS Notification an Critical Alerts Topic

### CloudWatch Logs
- **Location:** `/aws/wafv2/overcloud-{environment}`
- **Retention:** 90 Tage (Prod), 14 Tage (Staging)
- **Redacted Fields:**
  - `authorization` Header (GDPR-konform)
  - `cookie` Header (GDPR-konform)

## Troubleshooting

### False Positives
Wenn legitime Requests blockiert werden:

1. **CloudWatch Logs prüfen:**
   ```bash
   aws logs tail /aws/wafv2/overcloud-prod --follow
   ```

2. **Blockierte Rule identifizieren:**
   - Log enthält `terminatingRuleId` und `ruleGroupList`

3. **Rule in Count-Modus setzen:**
   ```hcl
   waf_rule_exclusions = ["SizeRestrictions_BODY"]
   ```

4. **Terraform Apply:**
   ```bash
   terraform apply -target=module.waf
   ```

### Rate Limiting zu streng?
Wenn legitime User geblockt werden:

```hcl
rate_limit_requests = 5000 # Erhöhen (von 2000 auf 5000)
```

### Geo-Blocking blockiert legitime User?
Land hinzufügen:

```hcl
allowed_countries = ["DE", "AT", "CH", "FR", "NL", "BE", "IT", "ES", "GB", "US", "CA", "IN"] # India hinzugefügt
```

## Testing

### 1. Rate Limiting Test
```bash
# 100 Requests in kurzer Zeit senden (sollte geblockt werden)
for i in {1..100}; do
  curl -i https://staging.overcloud.io/api/health
  sleep 0.1
done
```

**Erwartetes Ergebnis:** HTTP 429 (Too Many Requests) nach ~20 Requests

### 2. Geo-Blocking Test (wenn enabled)
```bash
# Request von blockiertem Land simulieren (mit Proxy/VPN)
curl -i https://prod.overcloud.io -x socks5://russia-proxy:1080
```

**Erwartetes Ergebnis:** HTTP 403 (Forbidden)

### 3. SQLi-Test (sollte geblockt werden)
```bash
curl -i "https://staging.overcloud.io/api/users?id=1' OR '1'='1"
```

**Erwartetes Ergebnis:** HTTP 403 (Forbidden) durch AWS Managed Rules

## Compliance

### DSGVO
- ✅ **Logging Redaction:** Authorization + Cookie Header werden redacted
- ✅ **Data Retention:** Logs werden nach 90 Tagen (Prod) automatisch gelöscht
- ✅ **Geo-Blocking:** Kann verwendet werden um Requests außerhalb EU zu blockieren

### ISO 27001
- ✅ **Access Control:** WAF verhindert unbefugten Zugriff
- ✅ **Monitoring:** CloudWatch Alarms bei Angriffen
- ✅ **Audit Logs:** Vollständige Request-Logs in CloudWatch

### SOC 2
- ✅ **Availability:** DDoS-Schutz durch Rate Limiting + Shield Standard
- ✅ **Security:** Multi-Layer Defense (OWASP + SQLi + Rate Limiting + Bot Control)
- ✅ **Monitoring:** Real-time Alerts bei Angriffen

## Weitere Optimierungen (Optional)

### AWS Shield Advanced (Nicht implementiert)
- **Kosten:** $3.000/Monat (!!)
- **Nutzen:** Erweiterte DDoS-Protection + Cost Protection
- **Empfehlung:** Nur bei sehr großem Traffic (>1M$/Jahr Umsatz)

### Custom Rules (Nicht implementiert)
- IP-Blacklisting (wenn bekannte Angreifer identifiziert)
- Custom Regex Patterns (für spezifische Threats)
- **Implementierung:** Kann bei Bedarf hinzugefügt werden

## Support

Bei Fragen oder Problemen:
1. CloudWatch Logs prüfen
2. WAF Dashboard in AWS Console öffnen
3. Bei False Positives: Rule exclusions hinzufügen
4. Bei Unsicherheit: Andy kontaktieren

## Changelog

### v1.0.0 (2026-05-15)
- Initial Release
- CloudFront + Regional WAF
- AWS Managed Rules (Core, Known Bad Inputs, SQLi)
- Rate Limiting
- Optional Geo-Blocking
- Optional Bot Control
- CloudWatch Logging + Alarms
