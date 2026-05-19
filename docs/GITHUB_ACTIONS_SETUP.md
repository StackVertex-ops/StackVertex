# GitHub Actions Deployment Setup

Vollständige Anleitung für das automatisierte Deployment von OverCloud via GitHub Actions.

## 📋 Übersicht

Das Deployment läuft in 3 Schritten:
1. **Bootstrap** (einmalig) → S3 + DynamoDB für Terraform State
2. **Git Push** → Automatisches Deployment (Backend + Frontend + Infrastructure)
3. **Health Check** → Automatische Verifikation

---

## 🔐 Erforderliche GitHub Secrets

Gehe zu: **Settings → Secrets and variables → Actions → New repository secret**

### AWS Credentials (Pflicht)

| Secret Name | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key für Deployment | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS Region | `eu-central-1` |
| `AWS_ACCOUNT_ID` | 12-stellige AWS Account ID | `123456789012` |

**Wie bekomme ich Access Keys?**

```bash
# Option 1: IAM User erstellen (empfohlen für Anfang)
aws iam create-user --user-name github-actions-overcloud

# Access Keys generieren
aws iam create-access-key --user-name github-actions-overcloud

# Admin Policy anhängen (MVP: Admin, später least privilege)
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# AWS Account ID anzeigen
aws sts get-caller-identity --query Account --output text
```

### Terraform State (nach Bootstrap)

| Secret Name | Beschreibung | Wird generiert in |
|-------------|--------------|-------------------|
| `TERRAFORM_STATE_BUCKET` | S3 Bucket für Terraform State | Bootstrap Workflow Output |

### Database Credentials (Pflicht)

| Secret Name | Beschreibung | Generieren mit |
|-------------|--------------|----------------|
| `DB_MASTER_USERNAME` | PostgreSQL Username | Frei wählbar (z.B. `admin`) |
| `DB_MASTER_PASSWORD` | PostgreSQL Password | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |

**Wichtig:** Password muss mindestens 16 Zeichen haben!

### Application Secrets (Pflicht)

| Secret Name | Beschreibung | Generieren mit |
|-------------|--------------|----------------|
| `JWT_SECRET_KEY` | JWT Token Signing Key | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |

### Monitoring & Alerts (Optional)

| Secret Name | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `ALERT_EMAILS` | Komma-getrennte Email-Adressen | `admin@example.com,ops@example.com` |
| `SLACK_WEBHOOK_URL` | Slack Webhook für Notifications | `https://hooks.slack.com/services/T00/B00/XXX` |
| `PAGERDUTY_ENDPOINT` | PagerDuty SNS Endpoint (Prod only) | `https://events.pagerduty.com/integration/xxx` |

### Frontend Config (Optional)

| Secret Name | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `CORS_ORIGINS` | Erlaubte CORS Origins | `https://app.overcloud.io` |

### Payment Integration (Optional)

| Secret Name | Beschreibung | Wo bekommen? |
|-------------|--------------|--------------|
| `STRIPE_SECRET_KEY` | Stripe API Key | https://dashboard.stripe.com/apikeys |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Secret | https://dashboard.stripe.com/webhooks |

### Error Tracking (Optional)

| Secret Name | Beschreibung | Wo bekommen? |
|-------------|--------------|--------------|
| `SENTRY_DSN` | Sentry Error Tracking | https://sentry.io/settings/projects/ |

---

## 🚀 Setup Schritte

### Schritt 1: AWS IAM User erstellen

```bash
# 1. IAM User für GitHub Actions erstellen
aws iam create-user --user-name github-actions-overcloud

# 2. Access Keys generieren
aws iam create-access-key --user-name github-actions-overcloud

# Output speichern:
# {
#   "AccessKey": {
#     "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
#     "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
#     ...
#   }
# }

# 3. Admin Policy anhängen (für MVP - später least privilege)
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# 4. Account ID anzeigen
aws sts get-caller-identity --query Account --output text
# Output: 123456789012
```

**Sicherheitshinweis:** AdministratorAccess ist für MVP OK. Für Production sollte eine Custom Policy mit least privilege verwendet werden (siehe unten).

### Schritt 2: Secrets generieren

```bash
# DB Password (min 16 chars)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT Secret Key (64 chars)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Schritt 3: GitHub Secrets setzen

1. Gehe zu Repository → **Settings**
2. Sidebar: **Secrets and variables** → **Actions**
3. Klicke **New repository secret**
4. Füge alle Pflicht-Secrets hinzu:

**Minimale Secrets für MVP:**
```
AWS_ACCESS_KEY_ID=<von Schritt 1>
AWS_SECRET_ACCESS_KEY=<von Schritt 1>
AWS_REGION=eu-central-1
AWS_ACCOUNT_ID=<von Schritt 1>
DB_MASTER_USERNAME=admin
DB_MASTER_PASSWORD=<von Schritt 2>
JWT_SECRET_KEY=<von Schritt 2>
ALERT_EMAILS=deine@email.com
SLACK_WEBHOOK_URL=<optional>
CORS_ORIGINS=*
```

### Schritt 4: Bootstrap ausführen (einmalig!)

1. Gehe zu **Actions** Tab
2. Wähle Workflow: **Bootstrap Terraform State Backend**
3. Klicke **Run workflow**
4. Eingaben:
   - **aws_account_id**: `123456789012` (deine AWS Account ID)
   - **aws_region**: `eu-central-1`
   - **project_name**: `overcloud`
5. Klicke **Run workflow** (grüner Button)

**Was passiert:**
- S3 Bucket für Terraform State wird erstellt
- DynamoDB Table für State Locking wird erstellt
- `backend.tf` Dateien werden generiert
- Automatischer Commit mit Backend Config

**Output:**
```
✅ Terraform State Backend erfolgreich erstellt!

📦 S3 Buckets:
  - Terraform State: overcloud-terraform-state-123456789012
  - Deployment States: overcloud-deployment-states-123456789012

🔒 DynamoDB Lock Table:
  - overcloud-terraform-locks

📋 WICHTIG: Füge dieses Secret zu GitHub hinzu:
  TERRAFORM_STATE_BUCKET = overcloud-terraform-state-123456789012
```

### Schritt 5: TERRAFORM_STATE_BUCKET Secret setzen

Kopiere den Bucket-Namen aus dem Bootstrap Output und füge ihn als Secret hinzu:

```
TERRAFORM_STATE_BUCKET=overcloud-terraform-state-123456789012
```

### Schritt 6: Automatisches Deployment testen

Jetzt ist alles bereit! Deployment erfolgt automatisch:

```bash
# Dev Deployment (automatisch)
git checkout develop
git commit --allow-empty -m "Test dev deployment"
git push origin develop

# Staging Deployment (automatisch)
git checkout staging
git merge develop
git push origin staging

# Production Deployment (manuelle Approval erforderlich!)
git checkout main
git merge staging
git push origin main
```

**Branch → Environment Mapping:**
- `develop` branch → **dev** environment
- `staging` branch → **staging** environment
- `main` branch → **prod** environment (REQUIRES APPROVAL)

---

## 🔄 Deployment Workflow

### Was passiert bei einem Git Push?

```
┌─────────────┐
│  Git Push   │
│  (develop)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Job 1: Tests                       │
│  - pytest (Backend)                 │
│  - Coverage Check (80%+)            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Job 2: Build Frontend              │
│  - npm ci                           │
│  - npm run build                    │
│  - Upload artifact                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Job 3: Build Backend               │
│  - Docker build                     │
│  - Push to ECR                      │
│  - Tag: latest + git SHA            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Job 4: Terraform Apply             │
│  - terraform init                   │
│  - terraform apply (auto-approve)   │
│  - Create/Update:                   │
│    - VPC + Networking               │
│    - Aurora Serverless DB           │
│    - Lambda Function                │
│    - API Gateway                    │
│    - S3 Buckets                     │
│    - CloudFront CDN                 │
│    - CloudWatch Alarms              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Job 5: Deploy Frontend             │
│  - Download build artifact          │
│  - aws s3 sync to S3 bucket         │
│  - CloudFront cache invalidation    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Job 6: Health Check                │
│  - Test API /health endpoint        │
│  - Test Frontend availability       │
│  - Verify deployment success        │
└──────┬──────────────────────────────┘
       │
       ▼
    ✅ Done!
```

### Deployment Dauer

| Environment | Dauer (ca.) |
|-------------|-------------|
| Dev | 8-12 Minuten |
| Staging | 10-15 Minuten |
| Prod | 12-20 Minuten (inkl. Manual Approval) |

---

## 🔒 Security Best Practices

### Production IAM Policy (Least Privilege)

Für Production sollte statt `AdministratorAccess` eine Custom Policy verwendet werden:

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
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::overcloud-terraform-state-*/*"
    }
  ]
}
```

### GitHub Environments (Production Protection)

Für Production sollte GitHub Environment Protection konfiguriert werden:

1. Gehe zu **Settings → Environments**
2. Erstelle Environment: `prod`
3. Aktiviere **Required reviewers** (z.B. 2 Approvals)
4. Aktiviere **Wait timer** (z.B. 5 Minuten Bedenkzeit)

---

## 🐛 Troubleshooting

### Error: "No such bucket: terraform-state"

**Problem:** Bootstrap wurde nicht ausgeführt oder `TERRAFORM_STATE_BUCKET` Secret fehlt.

**Lösung:**
1. Führe Bootstrap Workflow aus (siehe Schritt 4)
2. Setze `TERRAFORM_STATE_BUCKET` Secret (siehe Schritt 5)

### Error: "ECR repository does not exist"

**Problem:** ECR Repository wurde noch nicht erstellt.

**Lösung:**
ECR Repositories werden automatisch bei erstem Deployment erstellt. Wenn das fehlschlägt:

```bash
aws ecr create-repository --repository-name overcloud-dev-lambda --region eu-central-1
aws ecr create-repository --repository-name overcloud-staging-lambda --region eu-central-1
aws ecr create-repository --repository-name overcloud-prod-lambda --region eu-central-1
```

### Error: "Access Denied" bei S3 Sync

**Problem:** IAM User hat keine S3 Permissions.

**Lösung:**
```bash
# Policy mit S3 Full Access anhängen
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Error: "Terraform state locked"

**Problem:** Vorheriges Deployment wurde abgebrochen, Lock ist noch aktiv.

**Lösung:**
```bash
# DynamoDB Lock manuell entfernen
aws dynamodb delete-item \
  --table-name overcloud-terraform-locks \
  --key '{"LockID":{"S":"overcloud-terraform-state-123456789012/dev/terraform.tfstate-md5"}}' \
  --region eu-central-1
```

### Tests schlagen fehl mit Coverage < 80%

**Problem:** Code Coverage ist unter 80%.

**Lösung:**
1. Fehlende Tests schreiben
2. Oder temporär Coverage Requirement senken in `backend/pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   addopts = "--cov=app --cov-report=term-missing --cov-fail-under=60"
   ```

### Frontend Build schlägt fehl

**Problem:** Node.js Dependencies fehlen oder sind veraltet.

**Lösung:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📊 Monitoring

### Deployment Status überprüfen

**GitHub Actions:**
- Gehe zu **Actions** Tab
- Sieh dir laufende/abgeschlossene Workflows an
- Bei Fehler: Klicke auf Job → Siehe Logs

**AWS CloudWatch:**
```bash
# Lambda Logs anschauen
aws logs tail /aws/lambda/overcloud-dev-api --follow

# API Gateway Access Logs
aws logs tail /aws/apigateway/overcloud-dev --follow
```

### Cost Monitoring

```bash
# Aktuelle Monat-zu-Datum Kosten
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=SERVICE

# Kosten nach Environment
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --filter file://filter.json
```

### CloudWatch Alarms

Alarms werden automatisch erstellt für:
- API 5XX Errors > Threshold
- Lambda Errors > Threshold
- Database CPU > 90%
- Database Connections > 80% Max

Notifications gehen an `ALERT_EMAILS` und optional `SLACK_WEBHOOK_URL`.

---

## 🎯 Next Steps

Nach erfolgreichem Setup:

1. ✅ Bootstrap erfolgreich
2. ✅ Alle Secrets gesetzt
3. ✅ Dev Deployment funktioniert
4. ⏳ **Custom Domain konfigurieren** (siehe `docs/operations/custom-domain.md`)
5. ⏳ **SSL Certificate beantragen** (AWS Certificate Manager)
6. ⏳ **Production Deployment Protection** (GitHub Environments)
7. ⏳ **Monitoring Dashboard** (CloudWatch Dashboard)
8. ⏳ **Backup Strategy** (siehe `docs/operations/backup-restore.md`)

---

## 📚 Weitere Ressourcen

- [AWS Setup Guide](./AWS_SETUP.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Infrastructure Overview](./INFRASTRUCTURE_READY.md)
- [Terraform Environments](../infrastructure/terraform/environments/ENVIRONMENTS.md)
- [GitHub Workflows README](../.github/workflows/README.md)

---

**Bei Fragen oder Problemen:**
- Siehe [GitHub Issues](https://github.com/AndySchw/OverCloud/issues)
- Kontakt: schwarz23andy@gmail.com
