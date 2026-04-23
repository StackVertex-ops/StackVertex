# OverCloud Free Tier Setup Guide

Komplettes Setup für **Production-Ready Deployment** mit AWS Free Tier + $200 Credits.

## 🎯 Ziel-Architektur

```
yourdomain.com                    api.yourdomain.com
      ↓                                  ↓
  CloudFront                          CloudFront
  (+ SSL)                             (+ SSL)
      ↓                                  ↓
  S3 (Frontend)                    API Gateway
                                         ↓
                                      Lambda
                                    (OHNE VPC!)
                                         ↓
                            ┌────────────┴────────────┐
                            │                         │
                        DynamoDB                  S3 Buckets
                    (Permanent DB!)           (Customer Data)
```

**Kosten Jahr 1:** ~$2/Monat (mit Free Tier + $200 Credits)
**Kosten Jahr 2+:** ~$22/Monat

---

## Voraussetzungen

### 1. Neues AWS Account erstellen

**WICHTIG:** Nutze neues Account für $200 Credits + 12 Monate Free Tier!

```bash
# 1. AWS Account erstellen: https://aws.amazon.com/free/
# 2. Kreditkarte hinterlegen
# 3. $200 Credits aktivieren (wenn Angebot verfügbar)
# 4. IAM User für Terraform erstellen

aws iam create-user --user-name terraform-admin
aws iam attach-user-policy --user-name terraform-admin \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name terraform-admin
```

### 2. Domain registrieren

**Optionen:**

1. **Route53 (direkt bei AWS):**
   ```bash
   # Suche verfügbare Domain
   aws route53domains check-domain-availability --domain-name yourcompany.com
   
   # Register Domain (~$12/Jahr für .com)
   aws route53domains register-domain --domain-name yourcompany.com ...
   ```

2. **Externe Registrar (Namecheap, GoDaddy, etc.):**
   - Registriere Domain extern
   - Setze Nameservers später auf Route53

---

## Setup Schritt-für-Schritt

### Schritt 1: ACM Certificates erstellen (15 Minuten)

**WICHTIG:** ACM Certificates für CloudFront müssen in **us-east-1** erstellt werden!

```bash
cd infrastructure/terraform/modules/acm

# Provider für us-east-1
cat > provider_us_east_1.tf <<EOF
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
EOF

# Erstelle Certificates
terraform init
terraform plan \
  -var="project_name=overcloud" \
  -var="environment=prod" \
  -var="frontend_domain=yourdomain.com" \
  -var="api_domain=api.yourdomain.com" \
  -var="route53_zone_id=Z123456789ABC"  # Deine Zone ID

terraform apply
```

**DNS Validation:**
- Terraform erstellt automatisch DNS Records
- Warte ~5-10 Minuten auf Validation
- Certificate Status: `Issued` ✅

---

### Schritt 2: Route53 Hosted Zone (10 Minuten)

```bash
cd infrastructure/terraform/modules/route53

terraform init
terraform plan \
  -var="project_name=overcloud" \
  -var="environment=prod" \
  -var="domain_name=yourdomain.com" \
  -var="create_hosted_zone=true"

terraform apply
```

**Nameservers setzen:**

```bash
# Get Nameservers
terraform output hosted_zone_name_servers

# Output:
# [
#   "ns-123.awsdns-12.com",
#   "ns-456.awsdns-34.net",
#   "ns-789.awsdns-56.org",
#   "ns-012.awsdns-78.co.uk"
# ]
```

**Bei Domain Registrar:**
- Gehe zu DNS Settings
- Setze Custom Nameservers auf obige 4 Adressen
- Warte 24-48h auf Propagation (meist schneller)

---

### Schritt 3: Frontend S3 Bucket erstellen

```bash
# S3 Bucket für Static Website
aws s3 mb s3://yourcompany-frontend

# Public Access Block (CloudFront darf zugreifen)
aws s3api put-public-access-block \
  --bucket yourcompany-frontend \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

---

### Schritt 4: Complete Infrastructure Deploy

```bash
cd infrastructure/terraform/environments/prod-freetier

# Erstelle terraform.tfvars
cat > terraform.tfvars <<EOF
# Project
project_name = "overcloud"
environment  = "prod"
aws_region   = "eu-central-1"

# Domain
domain_name        = "yourdomain.com"
frontend_subdomain = ""        # Root domain
api_subdomain      = "api"     # api.yourdomain.com

# Certificates (from ACM in us-east-1)
frontend_certificate_arn = "arn:aws:acm:us-east-1:123:certificate/abc-123"
api_certificate_arn      = "arn:aws:acm:us-east-1:123:certificate/def-456"

# Terraform State (from Bootstrap)
terraform_state_bucket = "overcloud-terraform-state-123456789012"

# Alerts
alert_emails = ["your-email@example.com"]
EOF

# Deploy!
terraform init
terraform plan
terraform apply
```

**Deployment erstellt:**
- ✅ DynamoDB Tables (Main + WebSocket)
- ✅ Lambda Function (ohne VPC!)
- ✅ API Gateway (HTTP + WebSocket)
- ✅ S3 Buckets (Customer Data, Deployments)
- ✅ CloudFront Distributions (Frontend + API)
- ✅ Route53 DNS Records
- ✅ Minimal Monitoring (Free Tier optimiert)

**Dauer:** ~15-20 Minuten

---

### Schritt 5: Frontend Deploy

```bash
cd frontend

# Build
npm run build

# Deploy zu S3
aws s3 sync dist/ s3://yourcompany-frontend --delete

# Invalidate CloudFront Cache
DISTRIBUTION_ID=$(terraform output -raw frontend_distribution_id)
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

**Test:**
```bash
open https://yourdomain.com
# → Sollte Frontend zeigen! 🎉
```

---

### Schritt 6: Backend Deploy

```bash
# ECR Login
ECR_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build & Push
cd backend
docker build -f Dockerfile.lambda -t overcloud-lambda .
docker tag overcloud-lambda:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Update Lambda
aws lambda update-function-code \
  --function-name overcloud-prod-api \
  --image-uri $ECR_URL:latest
```

**Test API:**
```bash
curl https://api.yourdomain.com/health
# → {"status": "healthy"} 🎉
```

---

## Free Tier Optimierungen

### Was ist aktiviert

✅ **DynamoDB** - 25 GB Storage + 200M Reads permanent free
✅ **Lambda** - 1M Requests + 400k GB-s pro Monat
✅ **API Gateway** - 1M Requests pro Monat
✅ **CloudFront** - 1 TB Transfer + 10M Requests
✅ **S3** - 5 GB Storage + 20k GET + 2k PUT
✅ **CloudWatch** - 5 GB Logs + 10 Metrics

### Was ist NICHT aktiviert (zu teuer)

❌ **Aurora** - Minimum $43/Monat → DynamoDB stattdessen
❌ **NAT Gateway** - $32/Monat → Lambda ohne VPC
❌ **VPC Endpoints** - $7/Monat pro Endpoint → Not needed
❌ **Security Hub** - $10/Monat → GuardDuty reicht
❌ **Multi-AZ** - 2x Kosten → Single AZ für Start OK

---

## Monitoring im Free Tier

### CloudWatch (Free Tier: 5 GB Logs, 10 Metrics)

```bash
# Logs live ansehen
aws logs tail /aws/lambda/overcloud-prod-api --follow

# Metrics abfragen
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=overcloud-prod-api \
  --start-time 2026-04-19T00:00:00Z \
  --end-time 2026-04-19T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### GuardDuty (30 Tage Trial, dann ~$5/Monat)

```bash
# Status checken
aws guardduty list-detectors
aws guardduty get-detector --detector-id <ID>

# Findings
aws guardduty list-findings --detector-id <ID>
```

### Free Monitoring Alternativen

**1. Sentry (Error Tracking)**
```python
# Free Tier: 5k Events/Monat
import sentry_sdk
sentry_sdk.init(dsn="https://...")
```

**2. UptimeRobot**
- Free: 50 Monitors
- Health Check alle 5 Minuten
- Email Alerts

---

## Kosten-Tracking

### AWS Cost Explorer aktivieren

```bash
# Check aktuelle Kosten
aws ce get-cost-and-usage \
  --time-period Start=2026-04-01,End=2026-04-19 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

### Budget Alert

```bash
# Budget erstellen: $50/Monat
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json
```

**budget.json:**
```json
{
  "BudgetName": "OverCloud-Monthly",
  "BudgetLimit": {
    "Amount": "50",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

**Alert bei 80%:**
```json
{
  "Threshold": 80,
  "ThresholdType": "PERCENTAGE",
  "NotificationType": "ACTUAL",
  "Subscribers": [
    {
      "SubscriptionType": "EMAIL",
      "Address": "your-email@example.com"
    }
  ]
}
```

---

## High Availability

### CloudFront Multi-Region (Automatic)

CloudFront hat automatisch **Edge Locations weltweit**:
- Europa: Frankfurt, London, Paris, ...
- USA: Virginia, Oregon, ...
- Asien: Tokyo, Singapore, ...

**Kein Setup nötig - funktioniert automatisch!** ✅

### DynamoDB Global Tables (Optional)

**Für echte Multi-Region:**

```hcl
# In DynamoDB Module
resource "aws_dynamodb_table" "main" {
  # ...
  
  replica {
    region_name = "us-east-1"
  }
  
  replica {
    region_name = "eu-central-1"
  }
}
```

**Kosten:** ~2x DynamoDB Kosten (aber immer noch im Free Tier!)

---

## Disaster Recovery

### Backups

**DynamoDB:**
```hcl
# Point-in-Time Recovery (kostenlos!)
point_in_time_recovery {
  enabled = true
}
```

**S3:**
```bash
# Versioning aktiviert - alte Versionen bleiben
aws s3api get-bucket-versioning --bucket yourcompany-frontend
```

**Lambda:**
```bash
# Docker Images in ECR - keep last 5 versions
# Automatisch via Lifecycle Policy
```

### Recovery

**Kompletter Infrastructure Rebuild:**
```bash
# Von Terraform State
terraform init
terraform apply

# Dauer: ~15 Minuten
# → Alles wieder online!
```

---

## Skalierung

### Wann kommt der Free Tier nicht mehr aus?

**Limits:**
- Lambda: 1M Requests/Monat → ~33k Requests/Tag
- API Gateway: 1M Requests/Monat
- CloudFront: 1 TB Transfer
- DynamoDB: 200M Reads, 25M Writes

**Bei 100k Requests/Tag:**
- Lambda: ~3M/Monat → $0.40 extra
- API Gateway: ~3M/Monat → $2 extra
- **Total: ~$25/Monat** (immer noch günstig!)

**Bei 1M Requests/Tag:**
- **Total: ~$100/Monat**
- **Dann überlegen:** Aurora statt DynamoDB?

---

## Troubleshooting

### CloudFront zeigt 504 Gateway Timeout

**Problem:** API Gateway oder Lambda antwortet nicht

**Check:**
```bash
# Lambda Logs
aws logs tail /aws/lambda/overcloud-prod-api --follow

# Lambda Errors?
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=overcloud-prod-api \
  --start-time 2026-04-19T10:00:00Z \
  --end-time 2026-04-19T11:00:00Z \
  --period 300 \
  --statistics Sum
```

### Domain nicht erreichbar

**Check DNS Propagation:**
```bash
# Nameservers gesetzt?
dig NS yourdomain.com

# A Record korrekt?
dig A yourdomain.com
dig A api.yourdomain.com
```

**DNS Checker:**
https://dnschecker.org

### SSL Certificate Validation hängt

**Problem:** DNS Records nicht korrekt

**Check:**
```bash
# Validation Records existieren?
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABC \
  | grep _acme-challenge
```

**Fix:** Terraform re-apply für Route53 Records

---

## Zusammenfassung

**Du hast jetzt:**

✅ **Production-Ready Infrastructure**
- Custom Domain mit HTTPS
- CloudFront CDN (global)
- High Availability
- Auto-Scaling

✅ **Ultra-Low-Cost**
- Jahr 1: ~$2/Monat
- Jahr 2+: ~$22/Monat
- DynamoDB permanent free

✅ **Einfach änderbar**
- Alles via Terraform
- Module sind austauschbar
- Gut dokumentiert

✅ **Monitoring & Security**
- CloudWatch Logs & Metrics
- GuardDuty Threat Detection
- Email Alerts
- Budget Tracking

**Next Steps:**
1. Frontend entwickeln
2. Backend API implementieren
3. User onboarden
4. Skalieren wenn nötig!

🚀 **Let's build!**
