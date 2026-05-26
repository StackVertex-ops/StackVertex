# StackVertex Deployment Guide

> Complete guide for deploying StackVertex in Dev and Production environments

**Last Updated:** 2026-05-26

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Comparison](#environment-comparison)
3. [Dev Deployment (Pluralsight Sandbox)](#dev-deployment-pluralsight-sandbox)
4. [Production Deployment (stackvertex.io)](#production-deployment-stackvertexio)
5. [Domain Configuration](#domain-configuration)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Destroy & Cleanup](#destroy--cleanup)
8. [Troubleshooting](#troubleshooting)

---

## Overview

StackVertex hat zwei Deployment-Environments:

- **Dev** - Schnelles Testing in Pluralsight Sandbox (4h Zeit-Limit)
- **Production** - Full-Featured Deployment mit Custom Domain (stackvertex.io)

Beide Environments nutzen:
- **DynamoDB** (NoSQL, Serverless) - Single Table Design
- **Hybrid Serverless** - Lambda (<15min) + ECS Fargate (>15min deployments)
- **Region:** Frankfurt (eu-central-1) - DSGVO-compliant

---

## Environment Comparison

| Feature | Dev (Pluralsight) | Production (Own AWS) |
|---------|------------------|----------------------|
| **Region** | eu-central-1 (Frankfurt) | eu-central-1 (Frankfurt) |
| **Database** | DynamoDB (On-Demand) | DynamoDB (Provisioned + Auto-Scaling) |
| **Backups** | Disabled | 30 days, Point-in-Time Recovery |
| **Domain** | ❌ No custom domain | ✅ stackvertex.io |
| **HTTPS** | ❌ HTTP only | ✅ ACM Certificate |
| **CDN** | ❌ No CloudFront | ✅ CloudFront (HTTP/2+3) |
| **DNS** | ❌ No Route53 | ✅ Route53 Hosted Zone |
| **WAF** | ❌ No WAF | ✅ CloudFront WAF (Rate Limiting, Geo-Blocking, Bot Control) |
| **NAT Gateway** | ❌ Disabled (cost-saving) | ✅ Enabled (security) |
| **Monitoring** | Basic CloudWatch | Full CloudWatch + PagerDuty |
| **Security Hub** | ❌ Disabled | ✅ Enabled |
| **Deploy Time** | 15-20 min | 30-45 min (incl. CloudFront) |
| **Destroy Time** | 10-15 min | 20-30 min (incl. CloudFront) |
| **Cost** | ~$5-10/day | ~$50-100/month |

---

## Dev Deployment (Pluralsight Sandbox)

### Time Budget (4 hours total)

```
Deploy:  30-45 min
Testing:  2-3 hours
Destroy: 15-20 min (start at 3:40h max!)
```

⚠️ **WICHTIG:** Destroy spätestens nach 3:40h starten, sonst Timeout!

### Prerequisites

1. **Pluralsight Sandbox** aktiv
2. **AWS CLI** installiert & konfiguriert
3. **Terraform 1.5+** installiert
4. **GitHub Secrets** konfiguriert (siehe `.github/workflows/`)

### Manual Deployment

```bash
# 1. Bootstrap (nur beim ersten Mal)
cd infrastructure/scripts
./bootstrap.sh dev

# 2. Terraform Init & Plan
cd ../terraform/environments/dev
terraform init
terraform plan -out=tfplan

# 3. Deploy
terraform apply tfplan

# 4. Verify
terraform output deployment_summary
```

**Deploy-Zeit:** ~15-20 Minuten

### GitHub Actions Deployment

```bash
# Trigger via GitHub Actions (empfohlen)
git push origin main

# Workflow: .github/workflows/deploy.yml
# Wird automatisch bei Push auf main ausgeführt
```

### Testing Phase (2-3h)

Nach dem Deployment:

1. **API testen**
   ```bash
   export API_URL=$(terraform output -raw api_endpoint)
   curl $API_URL/health
   ```

2. **Frontend testen** (optional)
   - S3 Static Website URL aus output
   - Oder lokal: `cd frontend && npm run dev`

3. **Features testen**
   - Authentication (JWT)
   - Architecture Designer
   - Terraform Generation
   - Deployment Engine
   - Cost Calculation

### Destroy (nach max 3:40h!)

**Option 1: Terraform Destroy** (empfohlen)
```bash
cd infrastructure/terraform/environments/dev
terraform destroy -auto-approve
```

**Option 2: Quick Destroy Script** (schneller)
```bash
cd infrastructure/scripts
./quick-destroy.sh dev
```

**Option 3: GitHub Actions Workflow**
```bash
# Via GitHub UI:
# Actions → Manual Destroy → Run workflow
# Environment: dev
# Type "DESTROY" to confirm
```

**Option 4: Manual Cleanup** (wenn alles andere fehlschlägt)
- Siehe [DESTROY.md](./DESTROY.md) für detaillierte Anleitung

---

## Production Deployment (stackvertex.io)

### Prerequisites

1. **Domain:** stackvertex.io (bereits gekauft)
2. **AWS Account** (eigener Account, kein Sandbox)
3. **GitHub Secrets** konfiguriert
4. **Email für Alerts:** andy@stackvertex.io

### 1. Bootstrap

```bash
cd infrastructure/scripts
./bootstrap.sh prod
```

Erstellt:
- S3 Bucket für Terraform State
- DynamoDB Table für State Locking
- KMS Key für Encryption

### 2. Domain Pre-Configuration

**WICHTIG:** Route53 Nameserver VOR Terraform Apply konfigurieren!

```bash
# Nach bootstrap.sh:
cd ../terraform/environments/prod
terraform init
terraform plan -target=module.route53

# Nameserver aus output kopieren
terraform apply -target=module.route53
terraform output route53_name_servers

# Beispiel Output:
# [
#   "ns-123.awsdns-12.com",
#   "ns-456.awsdns-45.net",
#   "ns-789.awsdns-78.org",
#   "ns-012.awsdns-01.co.uk"
# ]
```

**Bei Domain-Registrar (z.B. Google Domains):**
1. Gehe zu DNS Settings für `stackvertex.io`
2. Ändere Nameservers zu Route53 Nameservern (siehe output)
3. Warte 5-10 Minuten auf DNS Propagation

Verify:
```bash
dig NS stackvertex.io +short
# Sollte Route53 Nameserver zeigen
```

### 3. ACM Certificate Validation

Nach Route53 ist konfiguriert:

```bash
# ACM Zertifikat erstellen
terraform apply -target=module.acm

# DNS Validation Record wird automatisch in Route53 erstellt
# Warte ~5-10 Minuten

# Status prüfen
terraform output acm_certificate_status
# Sollte: "ISSUED" zeigen
```

### 4. Full Deployment

```bash
# Komplettes Environment deployen
terraform plan -out=tfplan
terraform apply tfplan

# Deploy-Zeit: ~30-45 Minuten
# - DynamoDB: ~2 min
# - VPC/Networking: ~3 min
# - Lambda/API Gateway: ~5 min
# - CloudFront: ~15-20 min (longest!)
# - Monitoring/Security: ~5 min
```

### 5. Post-Deployment Configuration

#### A. Frontend Deployment

```bash
# Build frontend
cd frontend
npm run build

# Upload to S3 (via CloudFront)
aws s3 sync dist/ s3://stackvertex-prod-frontend --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

#### B. Backend Deployment

```bash
# Build & Push Docker Image
cd backend
docker build -t stackvertex-backend:latest .

# Tag & Push to ECR
ECR_URL=$(terraform output -raw ecr_repository_url)
docker tag stackvertex-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Update Lambda
aws lambda update-function-code \
  --function-name stackvertex-prod-api \
  --image-uri $ECR_URL:latest
```

#### C. DNS Records

CloudFront Distribution Domain aus output:
```bash
terraform output cloudfront_domain_name
# z.B.: d123abc456def.cloudfront.net
```

**Option 1: CNAME (empfohlen für MVP)**
```bash
# In Route53 (oder via Terraform):
# app.stackvertex.io → CNAME → d123abc456def.cloudfront.net
```

**Option 2: Alias (später, für root domain)**
```bash
# stackvertex.io → ALIAS → CloudFront Distribution
# Requires: CloudFront Alternate Domain Names configured
```

### 6. Monitoring Setup

#### Alert Emails konfigurieren

In `prod/terraform.tfvars`:
```hcl
alert_emails = ["andy@stackvertex.io", "alerts@stackvertex.io"]
```

#### PagerDuty (optional, für 24/7 On-Call)

```hcl
pagerduty_endpoint = "https://events.pagerduty.com/integration/..."
```

#### Slack Webhook (optional)

```hcl
slack_webhook_url = "https://hooks.slack.com/services/..."
```

### 7. Security Checklist

Nach Deployment:

- [ ] **Security Hub:** Compliance Score > 90%
- [ ] **GuardDuty:** Enabled, keine Critical Findings
- [ ] **CloudTrail:** Multi-Region Trail aktiv
- [ ] **KMS:** Customer Data Encryption enabled
- [ ] **WAF:** Rate Limiting, Geo-Blocking, Bot Control aktiv
- [ ] **IAM:** Least Privilege Policies
- [ ] **Secrets:** Keine Secrets in Code/Logs
- [ ] **HTTPS:** ACM Certificate ISSUED, TLS 1.2+
- [ ] **DynamoDB:** Point-in-Time Recovery enabled, Backups konfiguriert

### 8. Performance Testing

```bash
# Load Test (Artillery)
cd tests/load
artillery run load-test.yml

# Target: 1000 req/s
# Expected: p95 < 200ms, p99 < 500ms
```

---

## Domain Configuration

### stackvertex.io - DNS Records

| Record | Type | Value | Purpose |
|--------|------|-------|---------|
| `stackvertex.io` | A | ALIAS → CloudFront | Root domain → Frontend |
| `app.stackvertex.io` | CNAME | CloudFront Distribution | App subdomain |
| `api.stackvertex.io` | CNAME | API Gateway Custom Domain | API endpoint |
| `www.stackvertex.io` | CNAME | CloudFront Distribution | Redirect to apex |
| `@` | MX | Google Workspace MX Records | Email (andy@stackvertex.io) |
| `@` | TXT | SPF, DKIM, DMARC | Email security |
| `_acme-challenge` | TXT | ACM Validation | SSL certificate (auto-created) |

### SSL/TLS Certificate (ACM)

- **Domain:** stackvertex.io
- **SANs:** *.stackvertex.io (wildcard)
- **Validation:** DNS (automated via Route53)
- **Renewal:** Automatic (AWS ACM)
- **TLS Version:** TLSv1.2_2021 minimum

### CloudFront Configuration

- **Price Class:** PriceClass_100 (US, Canada, Europe)
- **HTTP Version:** HTTP/2 + HTTP/3 (QUIC)
- **Compression:** Enabled (gzip, brotli)
- **Caching:**
  - Frontend (S3): 1 hour default TTL
  - API (/api/*): No cache
  - WebSocket (/ws): No cache
- **Custom Error Pages:** 404/403 → /index.html (SPA routing)

---

## Monitoring & Alerts

### CloudWatch Alarms (Production)

**Critical Alerts** (PagerDuty + Email)
- Lambda Errors > 5 in 5 min
- API Gateway 5XX > 3 in 5 min
- DynamoDB Throttles > 10 in 5 min
- GuardDuty HIGH Findings
- Root Account Usage

**Warning Alerts** (Email only)
- Lambda Errors > 20 in 5 min
- API Gateway 4XX > 100 in 5 min
- DynamoDB Read/Write Capacity > 80%
- CloudFront 5XX > 10 in 5 min

**SLA Monitoring**
- 99.9% Uptime Target
- Alert if < 99.5% over 24h

### CloudWatch Dashboard

```
https://console.aws.amazon.com/cloudwatch/home?region=eu-central-1#dashboards:name=StackVertex-Prod
```

Widgets:
- API Request Rate (req/s)
- API Latency (p50, p95, p99)
- Lambda Errors & Throttles
- DynamoDB Read/Write Units
- CloudFront Cache Hit Ratio
- Security Events (GuardDuty, Config)

---

## Destroy & Cleanup

### Production Destroy (vorsichtig!)

⚠️ **WARNUNG:** Production Destroy löscht ALLE Daten (irreversibel)!

**Schritt 1: Backup erstellen**
```bash
# DynamoDB Export
aws dynamodb export-table-to-point-in-time \
  --table-arn arn:aws:dynamodb:eu-central-1:ACCOUNT_ID:table/stackvertex-prod \
  --s3-bucket stackvertex-prod-backups \
  --export-format DYNAMODB_JSON

# S3 Backup
aws s3 sync s3://stackvertex-prod-customer-data s3://stackvertex-prod-backups/customer-data/
```

**Schritt 2: CloudFront Disable** (15-20 min)
```bash
# CloudFront Distribution ID
DIST_ID=$(terraform output -raw cloudfront_distribution_id)

# Disable Distribution
aws cloudfront get-distribution-config --id $DIST_ID > dist-config.json
# Edit: "Enabled": false
aws cloudfront update-distribution \
  --id $DIST_ID \
  --if-match ETAG \
  --distribution-config file://dist-config-disabled.json

# Warte 15-20 Minuten bis Status "Deployed"
```

**Schritt 3: Terraform Destroy**
```bash
cd infrastructure/terraform/environments/prod
terraform destroy -auto-approve

# Destroy-Zeit: ~20-30 Minuten
```

**Schritt 4: Manual Cleanup** (falls nötig)
```bash
cd infrastructure/scripts
./quick-destroy.sh prod
```

### Dev Destroy (fast)

Siehe [Dev Deployment → Destroy](#destroy-nach-max-340h)

---

## Troubleshooting

### ACM Certificate Stuck in "Pending Validation"

**Problem:** ACM Zertifikat bleibt in "Pending Validation"

**Lösung:**
```bash
# DNS Propagation prüfen
dig _acme-challenge.stackvertex.io TXT +short

# Route53 DNS Record prüfen
aws route53 list-resource-record-sets \
  --hosted-zone-id $(terraform output -raw route53_zone_id) \
  --query "ResourceRecordSets[?Type=='TXT']"

# Nameserver prüfen
dig NS stackvertex.io +short

# Falls Nameserver falsch → bei Domain-Registrar korrigieren
```

### CloudFront Deployment Timeout

**Problem:** CloudFront Distribution stuck in "InProgress"

**Lösung:**
```bash
# Status prüfen
aws cloudfront get-distribution --id $DIST_ID

# Warten (kann 20-30 min dauern)
# Falls > 30 min → AWS Support kontaktieren
```

### Lambda Out of Memory (OOM)

**Problem:** Lambda function terminates with OOM

**Lösung:**
```bash
# In prod/main.tf:
lambda_memory_size = 3008  # Von 2048 auf 3008 MB erhöhen

terraform apply -target=module.compute
```

### DynamoDB Throttling

**Problem:** `ProvisionedThroughputExceededException`

**Lösung:**
```bash
# Auto-Scaling Grenzen erhöhen
# In prod/main.tf (database_dynamodb module):
autoscaling_read_max  = 200  # Von 100 auf 200
autoscaling_write_max = 200

terraform apply -target=module.database_dynamodb
```

### API Gateway CORS Errors

**Problem:** `Access-Control-Allow-Origin` missing

**Lösung:**
```bash
# In prod/variables.tf:
cors_origins = "https://app.stackvertex.io,https://stackvertex.io"

terraform apply -target=module.compute
```

### S3 Bucket Not Empty (Destroy Error)

**Problem:** `BucketNotEmpty` error during destroy

**Lösung:**
```bash
# Empty buckets before destroy
aws s3 rm s3://stackvertex-prod-customer-data --recursive
aws s3 rm s3://stackvertex-prod-deployment-states --recursive
aws s3 rm s3://stackvertex-prod-workspace --recursive

# Retry destroy
terraform destroy
```

---

## Cost Estimates

### Dev Environment (Pluralsight - 4h)

| Service | Cost (4h) | Notes |
|---------|-----------|-------|
| DynamoDB | $0.01 | On-Demand, minimal usage |
| Lambda | $0.02 | Free tier eligible |
| API Gateway | $0.01 | Free tier eligible |
| S3 | $0.01 | Minimal storage |
| CloudWatch | $0.01 | 7 days retention |
| VPC | $0.00 | No NAT Gateway |
| **TOTAL** | **~$0.06** | Praktisch kostenlos |

### Production Environment (Monthly)

| Service | Cost/Month | Notes |
|---------|------------|-------|
| DynamoDB | $10-20 | Provisioned + Auto-Scaling |
| Lambda | $5-10 | ~1M requests |
| API Gateway | $3-5 | ~1M requests |
| S3 | $5-10 | 100 GB storage |
| CloudFront | $10-20 | 1 TB traffic |
| Route53 | $1 | Hosted Zone + queries |
| ACM | $0 | Free |
| WAF | $10 | Rate limiting + rules |
| CloudWatch | $5-10 | 30 days retention |
| NAT Gateway | $30-40 | **Teuerster Teil!** |
| KMS | $1 | 1 key |
| GuardDuty | $5-10 | Threat detection |
| Security Hub | $0.001 | Per check |
| Backups | $5-10 | 30 days retention |
| **TOTAL** | **~$90-150/month** | Skaliert mit Traffic |

**Cost Optimization:**
- NAT Gateway nur in prod (dev: disabled)
- CloudFront PriceClass_100 (nicht worldwide)
- DynamoDB Auto-Scaling (nicht fixed)
- Lambda Provisioned Concurrency nur wenn nötig
- S3 Lifecycle Policies (Glacier after 90 days)

---

## Next Steps

### MVP Launch Checklist

- [ ] Dev deployment getestet (Pluralsight)
- [ ] Production deployment erfolgreich
- [ ] Domain stackvertex.io konfiguriert
- [ ] SSL Zertifikat ISSUED
- [ ] CloudFront Distribution deployed
- [ ] Frontend build & deployed
- [ ] Backend Docker Image deployed
- [ ] API endpoints funktional
- [ ] Authentication working (JWT)
- [ ] Cost Calculation accurate
- [ ] Terraform Generation working
- [ ] Security Hub Score > 90%
- [ ] Load Testing passed (1000 req/s)
- [ ] Monitoring & Alerts configured
- [ ] Documentation complete
- [ ] 10 Beta Users onboarded

### Post-Launch

1. **Monitoring:** Daily CloudWatch Dashboard checks
2. **Security:** Weekly Security Hub reviews
3. **Performance:** Monthly load tests
4. **Cost:** Bi-weekly AWS Cost Explorer reviews
5. **Backups:** Monthly restore tests
6. **Disaster Recovery:** Quarterly DR drills

---

**Dokumentation:** [README.md](./README.md) | [DESTROY.md](./DESTROY.md) | [CHANGELOG.md](./CHANGELOG.md)

**Support:** andy@stackvertex.io

**Last Updated:** 2026-05-26
