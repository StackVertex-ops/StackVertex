# OverCloud - Pre-Deployment Checklist

**Quick Reference für Andy**  
**Geschätzte Zeit:** 2-4 Stunden (einmalig)

---

## ☑️ Phase 1: AWS Account Setup (30 Min)

### AWS CLI Installation

```bash
# macOS
brew install awscli

# Verify
aws --version  # Should be >= 2.0
```

### AWS Credentials konfigurieren

```bash
aws configure

# Eingaben:
# AWS Access Key ID: [DEIN_KEY]
# AWS Secret Access Key: [DEIN_SECRET]
# Default region: eu-central-1
# Default output format: json

# Test
aws sts get-caller-identity
# → Zeigt Account ID + User ARN
```

### Terraform Bootstrap

```bash
cd infrastructure/scripts
./bootstrap.sh

# Was passiert:
# ✅ Erstellt S3 Bucket für Terraform State
# ✅ Erstellt DynamoDB Table für State Locking
# ✅ Erstellt backend.tf für alle Environments
# ✅ Erstellt .env.aws für Backend

# Output speichern:
# - State Bucket Name
# - Locks Table Name
# - Deployment Bucket Name
```

**✅ Fertig wenn:**
- `aws s3 ls | grep overcloud-terraform-state` → Bucket existiert
- `aws dynamodb list-tables | grep overcloud-terraform-locks` → Table existiert

---

## ☑️ Phase 2: Secrets Management (20 Min)

### JWT Secret generieren

```bash
# Generate strong random key
openssl rand -base64 32

# Output kopieren, dann:
aws secretsmanager create-secret \
  --name overcloud/prod/jwt-secret \
  --description "JWT signing secret" \
  --secret-string "PASTE_GENERATED_KEY_HERE"
```

### Sentry DSN (Error Tracking)

```bash
# 1. Account erstellen: https://sentry.io
# 2. Projekt anlegen: overcloud-backend
# 3. DSN kopieren (Format: https://xxx@sentry.io/xxx)

# 4. In AWS Secrets Manager speichern:
aws secretsmanager create-secret \
  --name overcloud/prod/sentry-dsn \
  --description "Sentry Error Tracking DSN" \
  --secret-string "https://xxx@sentry.io/xxx"
```

### Stripe Keys (OPTIONAL für Billing)

```bash
# Falls Billing aktiviert wird:
aws secretsmanager create-secret \
  --name overcloud/prod/stripe-secret-key \
  --secret-string "sk_live_..."

aws secretsmanager create-secret \
  --name overcloud/prod/stripe-webhook-secret \
  --secret-string "whsec_..."
```

**✅ Fertig wenn:**
```bash
aws secretsmanager list-secrets | grep overcloud
# → Mindestens 2 Secrets (jwt-secret, sentry-dsn)
```

---

## ☑️ Phase 3: GitHub Secrets (10 Min)

### Secrets hinzufügen

**GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Wert | Wo finden? |
|-------------|------|------------|
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | `aws configure list` |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUt...` | Aus AWS IAM Console |
| `AWS_REGION` | `eu-central-1` | Deine gewählte Region |

**Alternative: GitHub CLI**

```bash
# Install GitHub CLI
brew install gh

# Login
gh auth login

# Set secrets
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY
gh secret set AWS_REGION

# Verify
gh secret list
```

**✅ Fertig wenn:**
- `gh secret list` zeigt 3 Secrets

---

## ☑️ Phase 4: Environment Configuration (10 Min)

### Dev Environment

```bash
cd infrastructure/terraform/environments/dev

# 1. Copy example
cp terraform.tfvars.example terraform.tfvars

# 2. Edit terraform.tfvars
nano terraform.tfvars

# Setzen:
# - aws_region = "eu-central-1"
# - db_master_password = "GenerateStrongPassword123!" (falls Aurora verwendet)
# - terraform_state_bucket = "overcloud-terraform-state-{account_id}" (aus Bootstrap)

# 3. Save & Exit (Ctrl+X, Y, Enter)
```

### Staging Environment

```bash
cd ../staging
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# Gleiche Anpassungen wie dev
```

### Production Environment

```bash
cd ../prod
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# WICHTIG: Produktions-Passwörter verwenden!
# - Starke Passwörter (20+ Zeichen)
# - cors_origins = "https://app.overcloud.io"
# - alert_emails = "deine-email@example.com"
```

**✅ Fertig wenn:**
- `terraform.tfvars` existiert in allen 3 Environments
- Keine Platzhalter wie `CHANGEME` mehr vorhanden

---

## ☑️ Phase 5: Infrastructure Deployment (1-2h)

### Dev Deployment (Test)

```bash
cd infrastructure/terraform/environments/dev

# 1. Initialize (connects to S3 backend)
terraform init

# 2. Plan (preview changes)
terraform plan -out=tfplan

# Review output:
# - Wie viele Resources werden erstellt? (~30-50)
# - Estimated cost? (sollte ~50€/Monat sein)

# 3. Apply
terraform apply tfplan

# Dauer: ~10-15 Minuten
# Warte bis "Apply complete!"

# 4. Get outputs
terraform output

# Notiere:
# - api_endpoint
# - dynamodb_table_name
# - s3_bucket_name
```

**✅ Fertig wenn:**
```bash
# API erreichbar?
curl $(terraform output -raw api_endpoint)/health
# → {"status":"healthy"}

# DynamoDB existiert?
aws dynamodb describe-table --table-name $(terraform output -raw dynamodb_table_name)
# → Table Status: ACTIVE
```

### Staging Deployment

```bash
cd ../staging
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Dauer: ~15-20 Minuten
```

### Production Deployment

```bash
cd ../prod
terraform init

# WICHTIG: Plan sorgfältig prüfen!
terraform plan -out=tfplan

# Check:
# - Deletion Protection enabled?
# - Backup Retention = 30 days?
# - Multi-AZ deployment?

# Apply (PRODUCTION!)
terraform apply tfplan

# Dauer: ~20-30 Minuten
```

**✅ Fertig wenn:**
- Alle 3 Environments deployed
- Alle Health Checks grün
- Keine Errors in CloudWatch Logs

---

## ☑️ Phase 6: Monitoring Setup (1h)

### Sentry (Error Tracking)

```bash
# Schon erledigt in Phase 2 (DSN erstellt)

# Test:
curl https://api.overcloud.io/api/v1/test/sentry

# Check: Sentry Dashboard → Issues
# → Error sollte erscheinen
```

**Guide:** `docs/operations/SENTRY_SETUP.md`

### UptimeRobot (Uptime Monitoring)

```bash
# 1. Account erstellen: https://uptimerobot.com
# 2. Monitor anlegen:
#    - Type: HTTPS
#    - URL: https://api.overcloud.io/health
#    - Interval: 5 minutes
#    - Alert: Email (deine Adresse)

# 3. Test Alert triggern:
#    - Backend kurz stoppen
#    - Warte 5 Min
#    - Email sollte ankommen
```

**Guide:** `docs/operations/UPTIME_MONITORING_SETUP.md`

### Backup Test

```bash
cd infrastructure/terraform/scripts

# Test Backup Restore
./test-backup-restore.sh dev

# Dauer: ~10-15 Min
# Output: ✅ Restore successful + Data integrity verified
```

**Guide:** `docs/operations/BACKUP_TESTING.md`

**✅ Fertig wenn:**
- Sentry empfängt Errors
- UptimeRobot sendet Alerts
- Backup Test erfolgreich

---

## ☑️ Phase 7: Application Deployment (30 Min)

### Backend Deployment (via GitHub Actions)

```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud

# Push code to trigger deployment
git add .
git commit -m "[deploy] Initial production deployment"
git push origin main

# Watch GitHub Actions:
# https://github.com/{user}/OverCloud/actions

# Workflow Steps:
# 1. ✅ Run Tests (643 tests)
# 2. ✅ Build Docker Image
# 3. ✅ Push to ECR
# 4. ✅ Update ECS Service
# 5. ✅ Deploy Frontend to S3
# 6. ✅ Invalidate CloudFront

# Dauer: ~10-15 Min
```

**✅ Fertig wenn:**
- GitHub Actions Status: ✅ Success
- ECS Service Running: `aws ecs describe-services --cluster overcloud-prod --services overcloud-backend`
- Frontend deployed: `curl https://app.overcloud.io/`

### Frontend Verification

```bash
# Check Frontend
curl -I https://app.overcloud.io/
# → HTTP/2 200

# Check API
curl https://api.overcloud.io/health
# → {"status":"healthy"}

# Check Version
curl https://api.overcloud.io/
# → {"message":"OverCloud API","version":"1.0.0"}
```

---

## ☑️ Phase 8: Manual Testing (30 Min)

### Health Checks

```bash
# API Health
curl https://api.overcloud.io/health
# → {"status":"healthy"}

# Database Connection (indirect)
curl -X POST https://api.overcloud.io/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "name": "Test User"
  }'
# → {"access_token":"...", "user":{...}}
```

### End-to-End Test

```bash
# 1. Register User
TOKEN=$(curl -s -X POST https://api.overcloud.io/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test"}' \
  | jq -r '.access_token')

# 2. Create Organisation (auto-created, check)
curl -s https://api.overcloud.io/api/v1/users/me/organisations \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# 3. Create Architecture
curl -X POST https://api.overcloud.io/api/v1/architectures \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Architecture",
    "description": "E2E Test",
    "architecture_data": {"components":[]}
  }'
# → {"id":"...", "name":"Test Architecture"}

# 4. Verify in DynamoDB
aws dynamodb query \
  --table-name overcloud-prod-main \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk":{"S":"ARCH#..."}}'
```

**✅ Fertig wenn:**
- Alle API Endpoints funktionieren
- DynamoDB Read/Write funktioniert
- S3 Upload funktioniert (Large Items)
- Frontend lädt

---

## ☑️ Final Checklist

### Infrastructure

- [ ] AWS Account konfiguriert
- [ ] Terraform Bootstrap erfolgreich
- [ ] Secrets in AWS Secrets Manager
- [ ] GitHub Secrets gesetzt
- [ ] Dev Environment deployed
- [ ] Staging Environment deployed
- [ ] Production Environment deployed

### Monitoring

- [ ] Sentry Account + DSN konfiguriert
- [ ] Sentry empfängt Test-Error
- [ ] UptimeRobot Monitor angelegt
- [ ] UptimeRobot sendet Alerts
- [ ] Backup Test erfolgreich

### Application

- [ ] Backend deployed via GitHub Actions
- [ ] Frontend deployed zu S3 + CloudFront
- [ ] API Health Check grün
- [ ] User Registration funktioniert
- [ ] JWT Token wird generiert
- [ ] DynamoDB Read/Write funktioniert

### Security

- [ ] HTTPS erzwungen
- [ ] Security Headers aktiv (HSTS, CSP)
- [ ] Rate Limiting aktiv
- [ ] WAF Rules aktiviert
- [ ] Keine Secrets in Git
- [ ] MFA aktiviert auf AWS Root Account

### Documentation

- [ ] `DEPLOYMENT_READY_REPORT.md` gelesen
- [ ] `docs/DEPLOYMENT_GUIDE.md` gelesen
- [ ] `docs/operations/` Runbooks bekannt
- [ ] Incident Response Plan bekannt

---

## 🚀 Go-Live!

**Wenn alle Checkboxen ✅ sind:**

```bash
# DNS umstellen (falls eigene Domain)
# Route53 Record erstellen oder ändern:
# api.overcloud.io → ALB DNS Name
# app.overcloud.io → CloudFront Distribution

# Status kommunizieren
echo "🎉 OverCloud is LIVE!"
```

---

## 📞 Bei Problemen

### Terraform Errors

```bash
# State locked?
terraform force-unlock {LOCK_ID}

# Resources already exist?
terraform import {resource_type}.{name} {aws_id}

# Plan vs Apply mismatch?
terraform refresh
terraform plan -out=tfplan
terraform apply tfplan
```

### AWS Access Issues

```bash
# Credentials expired?
aws sts get-caller-identity

# Permissions missing?
aws iam get-user-policy --user-name {USER}

# Region falsch?
echo $AWS_REGION
aws configure get region
```

### GitHub Actions Failed

```bash
# Check logs
gh run list
gh run view {RUN_ID} --log

# Re-run
gh run rerun {RUN_ID}

# Secrets missing?
gh secret list
```

---

## 📚 Quick Reference

| Dokument | Zweck |
|----------|-------|
| `DEPLOYMENT_READY_REPORT.md` | Detaillierter Status Report |
| `docs/DEPLOYMENT_GUIDE.md` | Vollständige Deployment-Anleitung (30 Seiten) |
| `docs/AWS_SETUP.md` | AWS Account Setup Details |
| `docs/operations/RUNBOOK_ROLLBACK.md` | Deployment zurückrollen |
| `docs/operations/SENTRY_SETUP.md` | Error Tracking aktivieren |
| `docs/operations/UPTIME_MONITORING_SETUP.md` | Uptime Monitoring |
| `docs/operations/INCIDENT_RESPONSE_PLAN.md` | Bei Production Incidents |

---

**Geschätzte Gesamtzeit:** 4-6 Stunden (einmalig)

**Danach:** Vollautomatisches Deployment via Git Push 🚀

**Status Check:** Siehe `DEPLOYMENT_READY_REPORT.md` für Details

**Bei Fragen:** Alle Guides sind in `docs/` verfügbar

**Viel Erfolg, Andy! 🎉**
