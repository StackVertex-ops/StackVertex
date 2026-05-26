# Vollständiger Deployment Guide

> **Von 0 auf deployed in 30 Minuten**

Dieser Guide führt dich KOMPLETT durch den Setup-Prozess für automatisches GitHub Actions Deployment.

**Was wird erstellt?**
- ✅ Terraform State Backend (S3 + DynamoDB)
- ✅ Dev/Staging/Prod Environments (VPC, Aurora, Lambda, API Gateway, S3, CloudFront)
- ✅ Automatisches Deployment via Git Push
- ✅ Health Checks & Monitoring

---

## Voraussetzungen

### Lokal installiert

```bash
# AWS CLI
aws --version
# Sollte: aws-cli/2.x.x oder höher

# AWS Credentials konfiguriert
aws sts get-caller-identity
# Sollte: Account ID + User ARN anzeigen

# Python 3.11+
python3 --version

# GitHub CLI (optional, empfohlen)
gh --version
```

### AWS Account

- AWS Account mit Admin-Zugriff
- Keine bestehenden StackVertex-Ressourcen (Fresh Start)
- Empfohlen: Neuer AWS Account für StackVertex

---

## Schritt 1: IAM User für GitHub Actions erstellen

**Warum?** GitHub Actions braucht AWS Access Keys für Deployment.

```bash
# 1. IAM User erstellen
aws iam create-user --user-name github-actions-stackvertex

# 2. Access Keys generieren
aws iam create-access-key --user-name github-actions-stackvertex

# ⚠️ WICHTIG: Output SOFORT speichern! Keys werden NUR EINMAL angezeigt!
# {
#   "AccessKey": {
#     "UserName": "github-actions-stackvertex",
#     "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",          <-- KOPIEREN!
#     "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/...", <-- KOPIEREN!
#     "Status": "Active",
#     "CreateDate": "2026-05-19T10:00:00Z"
#   }
# }

# 3. Admin Policy anhängen (MVP - später least privilege)
aws iam attach-user-policy \
  --user-name github-actions-stackvertex \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# 4. Account ID anzeigen
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# ✅ Access Keys gespeichert? Dann weiter!
```

**Sicherheitshinweis:** AdministratorAccess ist für MVP OK. Für Production siehe unten für Least Privilege Policy.

---

## Schritt 2: Secrets generieren

```bash
# DB Master Password (min 16 Zeichen)
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "DB_MASTER_PASSWORD: $DB_PASSWORD"

# JWT Secret Key (64+ Zeichen)
JWT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo "JWT_SECRET_KEY: $JWT_KEY"

# ⚠️ WICHTIG: Diese Werte SICHER SPEICHERN!
```

**Secrets Template erstellen (empfohlen):**

```bash
# Erstelle lokale secrets.txt (ist in .gitignore)
cat > /Users/andyschwarz/Documents/Privat/StackVertex/secrets.txt <<EOF
# StackVertex GitHub Secrets - $(date)
# ⚠️ NIEMALS COMMITTEN! ⚠️

AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJal...
AWS_REGION=eu-central-1
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
DB_MASTER_USERNAME=admin
DB_MASTER_PASSWORD=$DB_PASSWORD
JWT_SECRET_KEY=$JWT_KEY
ALERT_EMAILS=schwarz23andy@gmail.com
CORS_ORIGINS=*
EOF

echo "✅ Secrets gespeichert in secrets.txt"
```

---

## Schritt 3: GitHub Secrets setzen

### Option A: Via Web UI

1. Gehe zu: https://github.com/AndySchw/StackVertex/settings/secrets/actions
2. Klicke **New repository secret**
3. Füge ALLE 9 Secrets hinzu:

| Name | Value | Quelle |
|------|-------|--------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | Von Schritt 1 |
| `AWS_SECRET_ACCESS_KEY` | `wJal...` | Von Schritt 1 |
| `AWS_REGION` | `eu-central-1` | Deine Region |
| `AWS_ACCOUNT_ID` | `123456789012` | Von Schritt 1 |
| `DB_MASTER_USERNAME` | `admin` | Frei wählbar |
| `DB_MASTER_PASSWORD` | (generiert) | Von Schritt 2 |
| `JWT_SECRET_KEY` | (generiert) | Von Schritt 2 |
| `ALERT_EMAILS` | `schwarz23andy@gmail.com` | Deine Email |
| `CORS_ORIGINS` | `*` | Dev: `*`, Prod: Domain |

### Option B: Via GitHub CLI (schneller!)

```bash
# Secrets aus secrets.txt setzen (Werte anpassen!)
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..."
gh secret set AWS_SECRET_ACCESS_KEY --body "wJal..."
gh secret set AWS_REGION --body "eu-central-1"
gh secret set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID"
gh secret set DB_MASTER_USERNAME --body "admin"
gh secret set DB_MASTER_PASSWORD --body "$DB_PASSWORD"
gh secret set JWT_SECRET_KEY --body "$JWT_KEY"
gh secret set ALERT_EMAILS --body "schwarz23andy@gmail.com"
gh secret set CORS_ORIGINS --body "*"

# Verifizieren
gh secret list

# Sollte 9 Secrets zeigen
```

---

## Schritt 4: ECR Repositories erstellen

**Warum?** GitHub Actions pusht Docker Images zu ECR. Repositories müssen existieren.

```bash
# Dev Environment
aws ecr create-repository \
  --repository-name stackvertex-dev-lambda \
  --region eu-central-1 \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Staging Environment
aws ecr create-repository \
  --repository-name stackvertex-staging-lambda \
  --region eu-central-1 \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Production Environment
aws ecr create-repository \
  --repository-name stackvertex-prod-lambda \
  --region eu-central-1 \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Verifizieren
aws ecr describe-repositories \
  --query 'repositories[].repositoryName' \
  --output table \
  --region eu-central-1

# Sollte zeigen:
# -------------------------
# | stackvertex-dev-lambda   |
# | stackvertex-staging-lambda|
# | stackvertex-prod-lambda   |
# -------------------------
```

---

## Schritt 5: Bootstrap ausführen (EINMALIG!)

**Was macht Bootstrap?**
- Erstellt S3 Bucket für Terraform State
- Erstellt DynamoDB Table für State Locking
- Erstellt S3 Bucket für Customer Deployment States
- Generiert `backend.tf` Files für alle Environments

### Via GitHub Actions Web UI

1. Gehe zu: https://github.com/AndySchw/StackVertex/actions/workflows/bootstrap.yml
2. Klicke **Run workflow** (rechts oben, grüner Button)
3. Eingaben:
   - **aws_account_id**: `123456789012` (deine AWS Account ID)
   - **aws_region**: `eu-central-1`
   - **project_name**: `stackvertex`
4. Klicke **Run workflow**
5. Warte ~2-3 Minuten
6. ✅ Workflow sollte grün sein

### Via GitHub CLI

```bash
# Bootstrap Workflow starten
gh workflow run bootstrap.yml \
  --field aws_account_id="$AWS_ACCOUNT_ID" \
  --field aws_region="eu-central-1" \
  --field project_name="stackvertex"

# Workflow Status verfolgen
gh run watch

# Sollte zeigen:
# ✓ bootstrap Bootstrap Terraform State Backend main · abc1234
#   ✓ bootstrap in 2m34s (ID 1234567890)
```

### Bootstrap Output prüfen

```bash
# Letzten Bootstrap Run anschauen
gh run view --log | grep TERRAFORM_STATE_BUCKET

# Wichtige Zeile kopieren:
# TERRAFORM_STATE_BUCKET = stackvertex-terraform-state-123456789012
```

**WICHTIG:** Kopiere den `TERRAFORM_STATE_BUCKET` Namen aus dem Output!

---

## Schritt 6: TERRAFORM_STATE_BUCKET Secret setzen

```bash
# Aus Bootstrap Output (oder aus AWS)
TERRAFORM_STATE_BUCKET="stackvertex-terraform-state-$AWS_ACCOUNT_ID"

# Secret setzen
gh secret set TERRAFORM_STATE_BUCKET --body "$TERRAFORM_STATE_BUCKET"

# Verifizieren
gh secret list | grep TERRAFORM_STATE_BUCKET
# Sollte zeigen: TERRAFORM_STATE_BUCKET  Updated 2s ago
```

---

## Schritt 7: Test Deployment (Dev Environment)

Jetzt ist alles bereit! Teste das automatische Deployment.

```bash
# Zu develop Branch wechseln (oder erstellen)
git checkout develop 2>/dev/null || git checkout -b develop

# Leerer Commit zum Testen
git commit --allow-empty -m "test: Verify GitHub Actions deployment setup"

# Push triggert automatisches Deployment!
git push origin develop

# Workflow verfolgen
gh run watch

# Oder im Browser: https://github.com/AndySchw/StackVertex/actions
```

**Was passiert jetzt?** (Dauer: ~10-15 Minuten)

```
1. ✅ Tests laufen (pytest, Coverage 80%+)
2. ✅ Frontend wird gebaut (Vite → dist/)
3. ✅ Backend Docker Image wird gebaut (Dockerfile.lambda)
4. ✅ Image wird zu ECR gepusht (Tag: latest + SHA)
5. ✅ Terraform apply erstellt Infrastructure:
   - VPC + Public/Private Subnets
   - Aurora Serverless PostgreSQL (min 0.5 ACU)
   - Lambda Function (FastAPI Backend)
   - API Gateway (REST API)
   - S3 Bucket + CloudFront (Frontend)
   - CloudWatch Alarms & Logs
   - IAM Roles & Policies
6. ✅ Frontend wird zu S3 deployed
7. ✅ CloudFront Cache wird invalidiert
8. ✅ Health Checks laufen
```

### Deployment erfolgreich?

```bash
# Terraform Outputs anschauen
cd /Users/andyschwarz/Documents/Privat/StackVertex/infrastructure/terraform/environments/dev
terraform init -backend-config="bucket=$TERRAFORM_STATE_BUCKET"
terraform output

# Sollte zeigen:
# api_endpoint = "https://abc123.execute-api.eu-central-1.amazonaws.com/dev"
# frontend_url = "https://d1234567890.cloudfront.net"
# websocket_endpoint = "wss://xyz789.execute-api.eu-central-1.amazonaws.com/dev"
```

**Test API:**

```bash
# API Health Check
API_ENDPOINT=$(cd /Users/andyschwarz/Documents/Privat/StackVertex/infrastructure/terraform/environments/dev && terraform output -raw api_endpoint)
curl "$API_ENDPOINT/health"

# Sollte JSON zurückgeben:
# {"status":"healthy","environment":"dev","version":"0.1.0"}
```

**Test Frontend:**

```bash
# Frontend URL öffnen
FRONTEND_URL=$(cd /Users/andyschwarz/Documents/Privat/StackVertex/infrastructure/terraform/environments/dev && terraform output -raw frontend_url)
open "$FRONTEND_URL"

# Sollte StackVertex UI im Browser öffnen
```

---

## Schritt 8: Staging & Production Deployment

### Staging Deployment

```bash
# Staging Branch erstellen (falls nicht vorhanden)
git checkout staging 2>/dev/null || git checkout -b staging

# develop mergen
git merge develop

# Push (triggert Staging Deployment)
git push origin staging

# Workflow verfolgen
gh run watch
```

### Production Deployment (REQUIRES APPROVAL!)

```bash
# Main Branch (falls nicht vorhanden)
git checkout main 2>/dev/null || git checkout -b main

# staging mergen
git merge staging

# Push (Deployment wartet auf Manual Approval!)
git push origin main

# GitHub UI öffnen für Approval
open "https://github.com/AndySchw/StackVertex/actions"

# ⚠️ WICHTIG: Production Deployment benötigt manuelle Freigabe!
# Gehe zu Actions → Klicke auf laufenden Workflow → "Review deployments" → Approve
```

---

## Workflow Übersicht

### Branch → Environment Mapping

| Branch | Environment | Auto-Deploy? | Approval? |
|--------|-------------|--------------|-----------|
| `develop` | dev | ✅ Ja | ❌ Nein |
| `staging` | staging | ✅ Ja | ❌ Nein |
| `main` | prod | ✅ Ja | ⚠️ Optional (empfohlen) |

### Deployment Jobs

```
┌─────────────┐
│ Git Push    │
└──────┬──────┘
       ▼
┌───────────────────────┐
│ Job 1: Tests          │
│ - pytest              │
│ - Coverage 80%+       │
└──────┬────────────────┘
       ▼
┌───────────────────────┐
│ Job 2: Build Frontend │
│ - npm run build       │
└──────┬────────────────┘
       ▼
┌───────────────────────┐
│ Job 3: Build Backend  │
│ - Docker build        │
│ - Push to ECR         │
└──────┬────────────────┘
       ▼
┌───────────────────────┐
│ Job 4: Terraform      │
│ - terraform apply     │
└──────┬────────────────┘
       ▼
┌───────────────────────┐
│ Job 5: Deploy Frontend│
│ - S3 sync             │
│ - CF invalidation     │
└──────┬────────────────┘
       ▼
┌───────────────────────┐
│ Job 6: Health Check   │
└───────────────────────┘
       ▼
    ✅ Done!
```

---

## Monitoring & Logs

### GitHub Actions Status

```bash
# Aktuelle Workflows
gh run list --limit 10

# Bestimmten Run anschauen
gh run view <run-id> --log

# Failed Runs
gh run list --status failure
```

### AWS CloudWatch Logs

```bash
# Lambda Logs (Backend)
aws logs tail /aws/lambda/stackvertex-dev-api --follow --region eu-central-1

# API Gateway Logs
aws logs tail /aws/apigateway/stackvertex-dev --follow --region eu-central-1
```

### Terraform Outputs

```bash
# Alle Outputs
cd /Users/andyschwarz/Documents/Privat/StackVertex/infrastructure/terraform/environments/dev
terraform output

# Bestimmten Output
terraform output -raw api_endpoint
```

---

## Troubleshooting

### Error: "No such bucket: terraform-state"

**Problem:** Bootstrap nicht ausgeführt oder Secret fehlt.

**Lösung:**
```bash
# Prüfe Secret
gh secret list | grep TERRAFORM_STATE_BUCKET

# Falls nicht vorhanden: Bootstrap erneut ausführen (Schritt 5)
```

### Error: "ECR repository does not exist"

**Problem:** ECR Repository fehlt.

**Lösung:**
```bash
aws ecr create-repository --repository-name stackvertex-dev-lambda --region eu-central-1
```

### Error: "Access Denied"

**Problem:** IAM User hat keine Permissions.

**Lösung:**
```bash
# Prüfe Policy
aws iam list-attached-user-policies --user-name github-actions-stackvertex

# Policy anhängen
aws iam attach-user-policy \
  --user-name github-actions-stackvertex \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

### Error: "Terraform state locked"

**Problem:** Vorheriges Deployment abgebrochen.

**Lösung:**
```bash
# Lock entfernen
aws dynamodb delete-item \
  --table-name stackvertex-terraform-locks \
  --key "{\"LockID\":{\"S\":\"$TERRAFORM_STATE_BUCKET/dev/terraform.tfstate-md5\"}}" \
  --region eu-central-1
```

### Tests schlagen fehl (Coverage < 80%)

**Problem:** Code Coverage zu niedrig.

**Lösung:**
```bash
# Coverage Report lokal
cd backend
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html

# Temporär Threshold senken (backend/pyproject.toml)
# addopts = "--cov-fail-under=60"
```

---

## Security Best Practices

### Production IAM Policy (Least Privilege)

Für Production statt AdministratorAccess:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "rds:*",
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "cloudfront:*",
        "cloudwatch:*",
        "logs:*",
        "iam:GetRole",
        "iam:PassRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "dynamodb:*",
        "ecr:*",
        "secretsmanager:*",
        "sns:*",
        "sqs:*",
        "events:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### GitHub Environment Protection

1. Gehe zu: https://github.com/AndySchw/StackVertex/settings/environments
2. Erstelle Environment: `prod`
3. Aktiviere **Required reviewers** (1-2 Personen)
4. Aktiviere **Wait timer** (5 Minuten Bedenkzeit)

---

## Kosten Monitoring

### Erwartete Kosten (MVP)

| Service | Dev | Staging | Prod | Monatlich |
|---------|-----|---------|------|-----------|
| Lambda (API) | $5 | $10 | $50 | $65 |
| Aurora Serverless | $15 | $25 | $100 | $140 |
| API Gateway | $3 | $5 | $20 | $28 |
| S3 + CloudFront | $2 | $3 | $10 | $15 |
| CloudWatch | $2 | $3 | $10 | $15 |
| **Total** | **$27** | **$46** | **$190** | **$263** |

**Hinweis:** Bei geringem Traffic (Dev) oft <$5/Monat dank AWS Free Tier.

### Aktuelle Kosten prüfen

```bash
# Kosten aktueller Monat
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --region us-east-1
```

---

## Zusammenfassung

### Was wurde erstellt?

**Pro Environment (dev/staging/prod):**
- VPC mit Public/Private Subnets in 2 AZs
- NAT Gateway (für Private Subnets)
- Aurora Serverless PostgreSQL (v2)
- Lambda Function (FastAPI Backend via Container)
- API Gateway (REST API + WebSocket)
- S3 Bucket (Frontend Static Files)
- CloudFront Distribution (CDN)
- CloudWatch Alarms (Errors, CPU, Memory)
- IAM Roles (Least Privilege)

### Deployment URLs

Nach erfolgreichem Deployment:

```bash
# Dev
API:      https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev
Frontend: https://<cf-id>.cloudfront.net
```

**Später mit Custom Domain:**
- Dev: `https://dev.stackvertex.io`
- Staging: `https://staging.stackvertex.io`
- Prod: `https://app.stackvertex.io`

---

## Nächste Schritte

Nach erfolgreichem Setup:

1. ✅ Bootstrap erfolgreich
2. ✅ Alle Secrets gesetzt
3. ✅ Dev Deployment funktioniert
4. ⏳ **Custom Domain konfigurieren** (Route53 + ACM Certificate)
5. ⏳ **GitHub Environment Protection** für Prod
6. ⏳ **Slack Notifications** einrichten
7. ⏳ **Monitoring Dashboard** (CloudWatch)
8. ⏳ **Backup Strategy** (RDS Snapshots)
9. ⏳ **IAM auf Least Privilege** umstellen
10. ⏳ **WAF Rules** für Production

---

## Support & Dokumentation

**Weitere Guides:**
- [GitHub Actions Setup](./GITHUB_ACTIONS_SETUP.md) - Detaillierte CI/CD Doku
- [GitHub Secrets Checklist](./GITHUB_SECRETS_CHECKLIST.md) - Secrets Reference
- [Infrastructure Overview](./INFRASTRUCTURE_READY.md) - Architektur
- [Terraform Environments](../infrastructure/terraform/environments/ENVIRONMENTS.md) - Config

**Workflows:**
- [Bootstrap Workflow](../.github/workflows/bootstrap.yml)
- [Deploy Workflow](../.github/workflows/deploy.yml)
- [Test Workflow](../.github/workflows/test.yml)
- [Security Workflow](../.github/workflows/security-scan.yml)

**Bei Problemen:**
- GitHub Issues: https://github.com/AndySchw/StackVertex/issues
- Email: schwarz23andy@gmail.com

---

**Stand:** 2026-05-19  
**Version:** 1.0.0  
**Autor:** Andy Schwarz + Claude Sonnet 4.5
