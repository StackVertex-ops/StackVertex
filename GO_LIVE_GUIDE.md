# OverCloud - Go-Live Step-by-Step Guide

**Version:** 1.0.0  
**Datum:** 2026-05-18  
**Ziel:** Von 0 bis Production deployed in ~4-6 Stunden

---

## 📋 Übersicht

Dieser Guide führt dich Schritt-für-Schritt durch das Production Deployment.

**Zeitplan:**
- Phase 1: Vorbereitung (1h)
- Phase 2: AWS Setup (1h)
- Phase 3: Terraform Deploy (1-2h)
- Phase 4: Application Deploy (1h)
- Phase 5: DNS & SSL (30min)
- Phase 6: Monitoring Setup (30min)
- Phase 7: Testing (1h)

**Total:** ~6 Stunden

---

## Phase 1: Vorbereitung (1 Stunde)

### Schritt 1.1: Prerequisites checken

**Was du brauchst:**
```bash
# 1. AWS Account
- [ ] AWS Account vorhanden
- [ ] Billing aktiviert
- [ ] Credit Card hinterlegt

# 2. Domain
- [ ] Domain registriert (z.B. overcloud.io)
- [ ] Zugriff auf DNS Management

# 3. Tools installiert
- [ ] Terraform >= 1.5.0
- [ ] AWS CLI >= 2.0
- [ ] Docker (für Backend)
- [ ] Git
- [ ] jq (JSON processor)
```

**Installation prüfen:**
```bash
terraform --version  # >= 1.5.0
aws --version        # >= 2.0
docker --version
git --version
jq --version
```

---

### Schritt 1.2: AWS CLI konfigurieren

**AWS Access Keys erstellen:**
```bash
# 1. AWS Console öffnen
open https://console.aws.amazon.com/iam/

# 2. IAM → Users → Create User
Name: terraform-deployer
Permissions: AdministratorAccess (für Deployment)

# 3. Security Credentials → Create Access Key
Type: CLI
```

**AWS CLI konfigurieren:**
```bash
aws configure

# Eingaben:
AWS Access Key ID: <dein-access-key>
AWS Secret Access Key: <dein-secret-key>
Default region: eu-central-1  # oder deine Region
Default output: json
```

**Test:**
```bash
aws sts get-caller-identity

# Output sollte zeigen:
# {
#   "UserId": "AIDA...",
#   "Account": "123456789",
#   "Arn": "arn:aws:iam::123456789:user/terraform-deployer"
# }
```

---

### Schritt 1.3: Repository vorbereiten

**Code committen:**
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud

# Alle Änderungen committen
git status
git add .
git commit -m "[deploy] Prepare for production deployment"

# Optional: Push zu GitHub
git push origin main
```

**Production Branch erstellen:**
```bash
# Production Branch (Best Practice)
git checkout -b production
git push -u origin production
```

---

## Phase 2: AWS Setup (1 Stunde)

### Schritt 2.1: S3 Bucket für Terraform State erstellen

**Warum:** Terraform State muss zentral gespeichert werden (nicht lokal!)

```bash
# Bucket Name (muss global unique sein)
BUCKET_NAME="overcloud-terraform-state-$(aws sts get-caller-identity --query Account --output text)"
REGION="eu-central-1"

# Bucket erstellen
aws s3 mb "s3://$BUCKET_NAME" --region $REGION

# Versioning aktivieren (wichtig!)
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

# Encryption aktivieren
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Public Access blockieren
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "✅ Terraform State Bucket erstellt: $BUCKET_NAME"
```

---

### Schritt 2.2: DynamoDB Table für State Locking erstellen

**Warum:** Verhindert dass 2 Personen gleichzeitig Terraform laufen lassen

```bash
TABLE_NAME="overcloud-terraform-locks"

aws dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION

echo "✅ DynamoDB Lock Table erstellt: $TABLE_NAME"
```

---

### Schritt 2.3: Backend Config erstellen

**Datei erstellen:**
```bash
cd infrastructure/terraform/environments/prod-dynamodb

cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "prod/terraform.tfstate"
    region         = "$REGION"
    encrypt        = true
    dynamodb_table = "$TABLE_NAME"
  }
}
EOF

echo "✅ Backend Config erstellt"
```

---

### Schritt 2.4: Secrets erstellen

**Secrets Manager für sensible Daten:**
```bash
# 1. JWT Secret (32+ Zeichen random)
JWT_SECRET=$(openssl rand -base64 32)

aws secretsmanager create-secret \
    --name "overcloud/prod/jwt-secret" \
    --secret-string "$JWT_SECRET" \
    --region $REGION

# 2. Database Password (Aurora - falls später nötig)
DB_PASSWORD=$(openssl rand -base64 24)

aws secretsmanager create-secret \
    --name "overcloud/prod/db-password" \
    --secret-string "$DB_PASSWORD" \
    --region $REGION

# 3. Stripe Keys (später setzen wenn Stripe aktiviert)
# aws secretsmanager create-secret \
#     --name "overcloud/prod/stripe-secret-key" \
#     --secret-string "sk_live_..." \
#     --region $REGION

echo "✅ Secrets erstellt"
```

---

## Phase 3: Terraform Deploy (1-2 Stunden)

### Schritt 3.1: Environment Variables setzen

**Datei erstellen:**
```bash
cd infrastructure/terraform/environments/prod-dynamodb

cat > terraform.tfvars << EOF
# Project
project_name = "overcloud"
environment  = "production"
aws_region   = "eu-central-1"
dr_region    = "us-east-1"  # Disaster Recovery

# Networking
vpc_cidr = "10.0.0.0/16"

# Domain (deine Domain!)
domain_name = "overcloud.io"

# Alerts (deine Email!)
alert_emails = ["schwarz23andy@gmail.com"]

# Optional: Slack Webhook
# slack_webhook_url = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# CORS Origins (Production Domain)
cors_origins = ["https://overcloud.io", "https://www.overcloud.io"]

# Stripe (später aktivieren)
# stripe_enabled = true
EOF

echo "✅ tfvars erstellt"
```

---

### Schritt 3.2: Terraform Init

**Initialisierung:**
```bash
cd infrastructure/terraform/environments/prod-dynamodb

terraform init

# Output sollte zeigen:
# ✅ Backend configured (S3)
# ✅ Providers initialized
# ✅ Modules downloaded
```

**Bei Fehler:**
```bash
# Falls Backend-Config falsch:
rm -rf .terraform
# Korrigiere backend.tf
terraform init -reconfigure
```

---

### Schritt 3.3: Terraform Plan

**Deployment planen:**
```bash
terraform plan -out=prod.tfplan

# Review Output (WICHTIG!):
# - Wie viele Resources erstellt werden
# - Geschätzte Kosten (ca. $240/Monat)
# - Keine Destruktive Aktionen (delete, replace)

# Plan speichern
terraform show -json prod.tfplan > prod-plan.json
```

**Plan reviewen:**
```bash
# Anzahl Resources
terraform show prod.tfplan | grep "# "

# Kosten schätzen (optional: Infracost)
# infracost breakdown --path prod.tfplan
```

---

### Schritt 3.4: Terraform Apply

**⚠️ WICHTIG:** Erst hier werden Kosten fällig!

```bash
# Finale Review
less prod.tfplan

# Apply (dauert 20-40 Minuten!)
terraform apply prod.tfplan

# Bei Fragen mit "yes" bestätigen

# Warte... (~30 Min)
# ✅ VPC erstellt
# ✅ Subnets erstellt
# ✅ NAT Gateway erstellt
# ✅ Security Groups erstellt
# ✅ DynamoDB Tables erstellt
# ✅ S3 Buckets erstellt
# ✅ Lambda Placeholder erstellt
# ✅ CloudWatch Logs erstellt
# ✅ WAF erstellt
# ✅ etc.
```

**Nach Completion:**
```bash
# Outputs anzeigen
terraform output

# Wichtige Outputs:
# - dynamodb_table_name
# - s3_bucket_name
# - lambda_function_name
# - api_gateway_url
```

---

### Schritt 3.5: Terraform State sichern

**State Backup:**
```bash
# Backup erstellen (lokal)
terraform state pull > prod-state-backup-$(date +%Y%m%d).json

# Sicher aufbewahren (z.B. verschlüsseltes USB)
```

---

## Phase 4: Application Deploy (1 Stunde)

### Schritt 4.1: Backend Docker Image bauen

**Docker Image für Lambda:**
```bash
cd backend

# Dockerfile prüfen
cat Dockerfile

# Image bauen
docker build -t overcloud-backend:prod .

# Test lokal (optional)
docker run -p 8000:8000 \
  -e SECRET_KEY="$(openssl rand -base64 32)" \
  -e DYNAMODB_TABLE_NAME="overcloud-prod-main" \
  overcloud-backend:prod

# Test in Browser: http://localhost:8000/health
```

---

### Schritt 4.2: ECR Repository erstellen

**Elastic Container Registry:**
```bash
REGION="eu-central-1"
REPO_NAME="overcloud-backend"

# Repository erstellen
aws ecr create-repository \
    --repository-name "$REPO_NAME" \
    --region $REGION

# Repository URL
REPO_URL=$(aws ecr describe-repositories \
    --repository-names "$REPO_NAME" \
    --region $REGION \
    --query 'repositories[0].repositoryUri' \
    --output text)

echo "✅ ECR Repository: $REPO_URL"
```

---

### Schritt 4.3: Docker Image zu ECR pushen

**Login + Push:**
```bash
# ECR Login
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $REPO_URL

# Tag Image
docker tag overcloud-backend:prod $REPO_URL:latest
docker tag overcloud-backend:prod $REPO_URL:v1.0.0

# Push
docker push $REPO_URL:latest
docker push $REPO_URL:v1.0.0

echo "✅ Image gepusht: $REPO_URL:latest"
```

---

### Schritt 4.4: Lambda Function Update

**Lambda mit neuem Image:**
```bash
FUNCTION_NAME="overcloud-prod-backend"

# Update Lambda Function Code
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --image-uri "$REPO_URL:latest" \
    --region $REGION

# Warte auf Update
aws lambda wait function-updated \
    --function-name "$FUNCTION_NAME" \
    --region $REGION

# Environment Variables setzen
aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --environment Variables="{
        ENV=production,
        SECRET_KEY=/aws/secretsmanager/overcloud/prod/jwt-secret,
        DYNAMODB_TABLE_NAME=overcloud-prod-main,
        S3_LARGE_ITEMS_BUCKET=overcloud-prod-large-items,
        ENABLE_SENTRY=true,
        SENTRY_DSN=https://xxx@sentry.io/yyy
    }" \
    --region $REGION

echo "✅ Lambda Function updated"
```

---

### Schritt 4.5: Frontend zu S3 deployen

**Frontend Build:**
```bash
cd frontend

# Dependencies installieren (falls nicht schon)
npm install

# Production Build
npm run build

# Output in dist/
ls -la dist/
```

**Upload zu S3:**
```bash
BUCKET_NAME="overcloud-prod-frontend"

# Sync zu S3
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --delete \
    --region $REGION

# Cache Headers setzen
aws s3 cp dist/ "s3://$BUCKET_NAME/" \
    --recursive \
    --metadata-directive REPLACE \
    --cache-control "public,max-age=31536000,immutable" \
    --exclude "*.html" \
    --region $REGION

# HTML ohne Cache
aws s3 cp dist/ "s3://$BUCKET_NAME/" \
    --recursive \
    --metadata-directive REPLACE \
    --cache-control "no-cache" \
    --include "*.html" \
    --region $REGION

echo "✅ Frontend deployed zu S3"
```

---

## Phase 5: DNS & SSL (30 Minuten)

### Schritt 5.1: SSL Certificate erstellen (ACM)

**AWS Certificate Manager:**
```bash
DOMAIN="overcloud.io"
REGION="us-east-1"  # WICHTIG: CloudFront braucht us-east-1!

# Certificate Request
CERT_ARN=$(aws acm request-certificate \
    --domain-name "$DOMAIN" \
    --subject-alternative-names "www.$DOMAIN" "api.$DOMAIN" \
    --validation-method DNS \
    --region us-east-1 \
    --query 'CertificateArn' \
    --output text)

echo "Certificate ARN: $CERT_ARN"

# Validation Records abrufen
aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region us-east-1 \
    --query 'Certificate.DomainValidationOptions'

# Output zeigt DNS Records für Validation
```

---

### Schritt 5.2: DNS Records erstellen

**Route 53 (oder dein DNS Provider):**
```bash
# Hole Validation Records
aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region us-east-1 \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# Output:
# {
#   "Name": "_abc123.overcloud.io.",
#   "Type": "CNAME",
#   "Value": "_xyz456.acm-validations.aws."
# }

# Erstelle diesen CNAME Record bei deinem DNS Provider!
```

**Warte auf Validation:**
```bash
# ACM validiert automatisch (5-30 Minuten)
aws acm wait certificate-validated \
    --certificate-arn "$CERT_ARN" \
    --region us-east-1

echo "✅ Certificate validiert"
```

---

### Schritt 5.3: CloudFront Distribution erstellen

**Distribution Config:**
```json
{
  "DistributionConfig": {
    "CallerReference": "overcloud-prod-$(date +%s)",
    "Aliases": {
      "Quantity": 2,
      "Items": ["overcloud.io", "www.overcloud.io"]
    },
    "DefaultRootObject": "index.html",
    "Origins": {
      "Quantity": 2,
      "Items": [
        {
          "Id": "S3-Frontend",
          "DomainName": "overcloud-prod-frontend.s3.amazonaws.com",
          "S3OriginConfig": {
            "OriginAccessIdentity": ""
          }
        },
        {
          "Id": "API-Gateway",
          "DomainName": "<api-gateway-id>.execute-api.eu-central-1.amazonaws.com",
          "CustomOriginConfig": {
            "HTTPPort": 80,
            "HTTPSPort": 443,
            "OriginProtocolPolicy": "https-only"
          }
        }
      ]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3-Frontend",
      "ViewerProtocolPolicy": "redirect-to-https",
      ...
    },
    "CacheBehaviors": {
      "Items": [
        {
          "PathPattern": "/api/*",
          "TargetOriginId": "API-Gateway",
          ...
        }
      ]
    },
    "ViewerCertificate": {
      "ACMCertificateArn": "$CERT_ARN",
      "SSLSupportMethod": "sni-only",
      "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "Enabled": true
  }
}
```

**Erstellen:**
```bash
# Via Terraform (empfohlen) oder AWS CLI
# Siehe: infrastructure/terraform/modules/frontend/
```

---

### Schritt 5.4: DNS A Records erstellen

**Route 53:**
```bash
HOSTED_ZONE_ID="<deine-hosted-zone-id>"
CLOUDFRONT_DOMAIN="<xyz123>.cloudfront.net"

# A Record (Alias zu CloudFront)
aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch '{
      "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "overcloud.io",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z2FDTNDATAQYW2",
            "DNSName": "'"$CLOUDFRONT_DOMAIN"'",
            "EvaluateTargetHealth": false
          }
        }
      }]
    }'

echo "✅ DNS Record erstellt"
```

**Test:**
```bash
# Warte 5-10 Minuten (DNS Propagation)
nslookup overcloud.io

# Sollte auf CloudFront IP zeigen
```

---

## Phase 6: Monitoring Setup (30 Minuten)

### Schritt 6.1: Sentry aktivieren

**Sentry Account:**
```bash
# 1. Gehe zu sentry.io
# 2. Erstelle Projekt "overcloud-backend"
# 3. Kopiere DSN

# 4. Update Lambda Environment
aws lambda update-function-configuration \
    --function-name "overcloud-prod-backend" \
    --environment Variables="{
        ...
        ENABLE_SENTRY=true,
        SENTRY_DSN=https://xxx@sentry.io/yyy
    }" \
    --region eu-central-1
```

---

### Schritt 6.2: UptimeRobot konfigurieren

**Monitor erstellen:**
```
1. Gehe zu uptimerobot.com
2. Add Monitor:
   - Type: HTTPS
   - URL: https://api.overcloud.io/health
   - Name: OverCloud API - Production
   - Interval: 5 minutes
   - Alert: schwarz23andy@gmail.com
3. Save
```

---

### Schritt 6.3: CloudWatch Alarms testen

**Alarm Status prüfen:**
```bash
aws cloudwatch describe-alarms \
    --alarm-name-prefix "overcloud-prod" \
    --region eu-central-1

# Check:
# - Lambda Error Rate Alarm
# - API Gateway 5XX Alarm
# - DynamoDB Throttle Alarm
```

---

## Phase 7: Testing (1 Stunde)

### Schritt 7.1: Smoke Tests

**Basic Health:**
```bash
# 1. Health Endpoint
curl https://api.overcloud.io/health
# Expected: {"status":"healthy","version":"0.1.0"}

# 2. Frontend
curl -I https://overcloud.io
# Expected: 200 OK

# 3. HTTPS Redirect
curl -I http://overcloud.io
# Expected: 301 → https://overcloud.io
```

---

### Schritt 7.2: Manuelle Tests durchführen

**Test-Checkliste abarbeiten:**
```bash
# Öffne MANUAL_TESTING_CHECKLIST.md
# Arbeite alle Tests durch
# Dokumentiere Ergebnisse
```

**Kritische Tests (Minimum):**
- [ ] User Registration
- [ ] User Login
- [ ] Create Architecture
- [ ] Generate Terraform
- [ ] Health Endpoint
- [ ] HTTPS funktioniert
- [ ] Sentry Error Tracking

---

### Schritt 7.3: Performance Test

**Response Times:**
```bash
# curl mit Timing
curl -w "@curl-format.txt" -o /dev/null -s https://api.overcloud.io/health

# Format (curl-format.txt):
time_namelookup:  %{time_namelookup}s\n
time_connect:  %{time_connect}s\n
time_total:  %{time_total}s\n

# Expected: < 200ms
```

---

## Phase 8: Go-Live! 🚀

### Schritt 8.1: Final Checklist

**Pre-Launch:**
- [ ] Terraform deployed ohne Errors
- [ ] Backend Lambda funktioniert
- [ ] Frontend deployed
- [ ] DNS zeigt auf CloudFront
- [ ] SSL Certificate aktiv
- [ ] Sentry empfängt Events
- [ ] UptimeRobot überwacht
- [ ] CloudWatch Alarms aktiv
- [ ] Backup aktiviert (DynamoDB PITR)
- [ ] Kritische Tests bestanden

---

### Schritt 8.2: Launch!

**Announcement:**
```
✅ OverCloud ist LIVE!
🌐 https://overcloud.io
📧 support@overcloud.io

Features:
- Infrastructure Designer
- Terraform Generation
- Cost Estimation
- User Management
```

---

### Schritt 8.3: Post-Launch Monitoring

**Erste 24 Stunden:**
```bash
# 1. Logs überwachen
aws logs tail /aws/lambda/overcloud-prod-backend --follow

# 2. Sentry Dashboard checken
open https://sentry.io

# 3. UptimeRobot Dashboard
open https://uptimerobot.com

# 4. CloudWatch Dashboard
open https://console.aws.amazon.com/cloudwatch
```

---

## 🐛 Troubleshooting

### Problem: Terraform Apply schlägt fehl

**Lösung:**
```bash
# Logs prüfen
terraform apply 2>&1 | tee terraform-error.log

# Häufige Fehler:
# - Quota exceeded → AWS Support kontaktieren
# - Permission denied → IAM Policies prüfen
# - Resource exists → Import oder umbenennen
```

---

### Problem: Lambda Cold Start zu langsam

**Lösung:**
```bash
# Provisioned Concurrency aktivieren
aws lambda put-provisioned-concurrency-config \
    --function-name overcloud-prod-backend \
    --provisioned-concurrent-executions 2 \
    --qualifier '$LATEST'

# Kosten: +$10-20/Monat, aber < 100ms Cold Start
```

---

### Problem: CloudFront Cache zu aggressiv

**Lösung:**
```bash
# Cache Invalidation erstellen
DISTRIBUTION_ID="<cloudfront-id>"

aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*"

# Dauert 5-15 Minuten
```

---

### Problem: DNS nicht erreichbar

**Lösung:**
```bash
# DNS Propagation prüfen
dig overcloud.io

# Warte 30-60 Minuten
# DNS Propagation kann dauern

# Teste mit Google DNS
nslookup overcloud.io 8.8.8.8
```

---

## 📚 Post-Launch Tasks

### Woche 1:
- [ ] Daily Logs Review (Sentry, CloudWatch)
- [ ] Performance Monitoring (Response Times)
- [ ] Cost Monitoring (AWS Budget Alerts)
- [ ] User Feedback sammeln

### Woche 2:
- [ ] Backup Restore Test durchführen
- [ ] Security Scan (OWASP ZAP)
- [ ] Load Test (Apache Bench)
- [ ] Documentation Update

### Monat 1:
- [ ] Monthly Cost Review
- [ ] Security Audit
- [ ] Performance Optimization
- [ ] Feature Roadmap

---

## ✅ Success Criteria

**Production ist erfolgreich wenn:**
- ✅ 99.9% Uptime (Woche 1)
- ✅ < 500ms Response Time (p95)
- ✅ 0 Security Incidents
- ✅ < $300/Monat Kosten
- ✅ 10+ registrierte User
- ✅ 5+ erstellte Architectures

---

**Congratulations! 🎉 OverCloud ist live!**

**Support:**
- Sentry: Automatische Error Alerts
- UptimeRobot: Downtime Alerts
- CloudWatch: Performance Monitoring
- Docs: Siehe /docs/operations/

**Next:** User Onboarding, Marketing, Feedback Loop

---

**Version:** 1.0.0  
**Autor:** Claude Sonnet 4.5  
**Datum:** 2026-05-18
