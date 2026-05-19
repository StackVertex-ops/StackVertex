# OverCloud - Automatisches Deployment Setup

> **Von 0 auf deployed in 30 Minuten**

Dieses Projekt ist vollständig für automatisches GitHub Actions Deployment vorbereitet.

## Quick Links

| Dokument | Wofür? | Wann nutzen? |
|----------|--------|--------------|
| **[DEPLOYMENT_QUICKSTART.md](docs/DEPLOYMENT_QUICKSTART.md)** | 5-Schritte Quick Start | Schnellster Weg zum Deployment |
| **[COMPLETE_DEPLOYMENT_GUIDE.md](docs/COMPLETE_DEPLOYMENT_GUIDE.md)** | Vollständiger Guide | Detaillierte Schritt-für-Schritt Anleitung |
| **[GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)** | CI/CD Details | Workflow-Details & Troubleshooting |
| **[GITHUB_SECRETS_CHECKLIST.md](docs/GITHUB_SECRETS_CHECKLIST.md)** | Secrets Reference | Secrets generieren & setzen |

---

## Was ist bereits fertig?

✅ **GitHub Actions Workflows:**
- Bootstrap (Terraform State Backend)
- Deploy (Backend + Frontend + Infrastructure)
- Tests (pytest, Coverage, Linting)
- Security Scans (Bandit, Safety, Semgrep, CodeQL)

✅ **Infrastructure as Code:**
- Terraform Module für alle AWS Services
- 3 Environments (dev, staging, prod)
- VPC, Aurora, Lambda, API Gateway, S3, CloudFront

✅ **Backend:**
- FastAPI (Python 3.11+)
- Docker Lambda Container
- PostgreSQL (Aurora Serverless v2)

✅ **Frontend:**
- Vite + Vanilla JS
- Tailwind CSS
- S3 + CloudFront Hosting

---

## Was musst du noch tun?

⏳ **3 Dinge:**

1. **GitHub Secrets setzen** (10 Secrets, ~5 Minuten)
2. **Bootstrap ausführen** (einmalig, ~3 Minuten)
3. **Git Push** → Automatisches Deployment startet!

---

## Quick Start (5 Schritte)

### 1. IAM User erstellen

```bash
aws iam create-user --user-name github-actions-overcloud
aws iam create-access-key --user-name github-actions-overcloud
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

**Kopiere:** `AccessKeyId` und `SecretAccessKey`!

### 2. Secrets generieren

```bash
# AWS Account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# DB Password
export DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# JWT Secret
export JWT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
```

### 3. GitHub Secrets setzen

Via GitHub CLI (schnellster Weg):

```bash
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..."
gh secret set AWS_SECRET_ACCESS_KEY --body "wJal..."
gh secret set AWS_REGION --body "eu-central-1"
gh secret set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID"
gh secret set DB_MASTER_USERNAME --body "admin"
gh secret set DB_MASTER_PASSWORD --body "$DB_PASSWORD"
gh secret set JWT_SECRET_KEY --body "$JWT_KEY"
gh secret set ALERT_EMAILS --body "schwarz23andy@gmail.com"
gh secret set CORS_ORIGINS --body "*"
```

Oder via Web UI: https://github.com/AndySchw/OverCloud/settings/secrets/actions

### 4. ECR Repositories erstellen

```bash
aws ecr create-repository --repository-name overcloud-dev-lambda --region eu-central-1
aws ecr create-repository --repository-name overcloud-staging-lambda --region eu-central-1
aws ecr create-repository --repository-name overcloud-prod-lambda --region eu-central-1
```

### 5. Bootstrap ausführen

Via GitHub Actions:
1. Gehe zu: https://github.com/AndySchw/OverCloud/actions/workflows/bootstrap.yml
2. Klicke **Run workflow**
3. Eingaben:
   - `aws_account_id`: (deine 12-stellige ID)
   - `aws_region`: `eu-central-1`
   - `project_name`: `overcloud`
4. Warte ~2-3 Minuten
5. Kopiere `TERRAFORM_STATE_BUCKET` aus Output

Via CLI:

```bash
gh workflow run bootstrap.yml \
  --field aws_account_id="$AWS_ACCOUNT_ID" \
  --field aws_region="eu-central-1" \
  --field project_name="overcloud"
```

### 6. Final Secret setzen

```bash
gh secret set TERRAFORM_STATE_BUCKET --body "overcloud-terraform-state-$AWS_ACCOUNT_ID"
```

### 7. Test Deployment

```bash
git checkout develop
git commit --allow-empty -m "test: First deployment"
git push origin develop

# Workflow verfolgen
gh run watch
```

**Fertig!** Nach ~10-15 Minuten ist Dev Environment deployed.

---

## Branch → Environment Mapping

| Branch | Environment | Auto-Deploy? | Approval? |
|--------|-------------|--------------|-----------|
| `develop` | dev | ✅ Ja | ❌ Nein |
| `staging` | staging | ✅ Ja | ❌ Nein |
| `main` | prod | ✅ Ja | ⚠️ Optional |

---

## Deployment Flow

```
Git Push → Tests → Build → Terraform → Deploy → Health Check ✅
```

**Jobs:**
1. **Tests** - pytest + Coverage (80%+) + Linting
2. **Build Frontend** - Vite build → Artifact
3. **Build Backend** - Docker Image → ECR
4. **Terraform Apply** - Infrastructure Deployment
5. **Deploy Frontend** - S3 Sync + CloudFront Invalidation
6. **Health Check** - API + Frontend Verification

**Dauer:** 10-15 Minuten pro Environment

---

## Was wird erstellt?

**Pro Environment (dev/staging/prod):**

- ✅ VPC mit Public/Private Subnets (2 AZs)
- ✅ NAT Gateway (für Private Subnets)
- ✅ Aurora Serverless PostgreSQL v2
- ✅ Lambda Function (FastAPI Backend Container)
- ✅ API Gateway (REST + WebSocket)
- ✅ S3 Bucket + CloudFront (Frontend CDN)
- ✅ CloudWatch Alarms & Logs
- ✅ IAM Roles (Least Privilege)

---

## Monitoring & URLs

Nach erfolgreichem Deployment:

```bash
# Terraform Outputs anzeigen
cd infrastructure/terraform/environments/dev
terraform output

# API URL
terraform output -raw api_endpoint
# → https://abc123.execute-api.eu-central-1.amazonaws.com/dev

# Frontend URL
terraform output -raw frontend_url
# → https://d1234567890.cloudfront.net

# Health Check
curl "$(terraform output -raw api_endpoint)/health"
```

---

## Troubleshooting

| Error | Lösung |
|-------|--------|
| "No such bucket: terraform-state" | Bootstrap nicht ausgeführt oder Secret fehlt |
| "ECR repository not found" | ECR Repositories erstellen (Schritt 4) |
| "Access Denied" | IAM User Policy fehlt |
| "Coverage < 80%" | Tests schreiben oder Threshold temporär senken |

**Vollständige Troubleshooting-Anleitung:** [COMPLETE_DEPLOYMENT_GUIDE.md](docs/COMPLETE_DEPLOYMENT_GUIDE.md#troubleshooting)

---

## Kosten

**Erwartete AWS Kosten (MVP):**

| Environment | Monatlich (ca.) |
|-------------|-----------------|
| Dev | $27 |
| Staging | $46 |
| Prod | $190 |
| **Total** | **$263** |

**Hinweis:** Bei geringem Traffic (Dev) oft <$5/Monat dank AWS Free Tier.

---

## Nächste Schritte nach Deployment

1. ✅ Dev Deployment erfolgreich
2. ⏳ Staging Deployment testen
3. ⏳ Production Deployment (mit Approval)
4. ⏳ Custom Domain konfigurieren (Route53 + ACM)
5. ⏳ GitHub Environment Protection für Prod
6. ⏳ Monitoring Dashboard (CloudWatch)
7. ⏳ Slack Notifications
8. ⏳ Backup Strategy (RDS Snapshots)

---

## Support

**Dokumentation:**
- [Quick Start](docs/DEPLOYMENT_QUICKSTART.md)
- [Vollständiger Guide](docs/COMPLETE_DEPLOYMENT_GUIDE.md)
- [GitHub Actions Setup](docs/GITHUB_ACTIONS_SETUP.md)
- [Secrets Checklist](docs/GITHUB_SECRETS_CHECKLIST.md)

**Bei Problemen:**
- GitHub Issues: https://github.com/AndySchw/OverCloud/issues
- Email: schwarz23andy@gmail.com

---

**Stand:** 2026-05-19  
**Version:** 1.0.0
