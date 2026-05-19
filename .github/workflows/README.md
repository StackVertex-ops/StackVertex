# GitHub Actions Workflows

Dieses Verzeichnis enthält alle CI/CD und Security Workflows für OverCloud.

## 🚀 Quick Start

**Neue Installation?**
- **Schnellster Weg:** [DEPLOYMENT_QUICKSTART.md](../../docs/DEPLOYMENT_QUICKSTART.md) - 5 Schritte, 15 Minuten
- **Vollständiger Guide:** [COMPLETE_DEPLOYMENT_GUIDE.md](../../docs/COMPLETE_DEPLOYMENT_GUIDE.md) - Detailliert, 30 Minuten
- **Secrets Checklist:** [GITHUB_SECRETS_CHECKLIST.md](../../docs/GITHUB_SECRETS_CHECKLIST.md) - Alle Secrets auf einen Blick
- **CI/CD Details:** [GITHUB_ACTIONS_SETUP.md](../../docs/GITHUB_ACTIONS_SETUP.md) - Workflow-Details

---

## 📋 Workflows Übersicht

### 1. `bootstrap.yml` - Terraform State Backend Setup (EINMALIG!)
**Trigger:** Manual Workflow Dispatch  
**Dauer:** ~2-3 Minuten  
**Status:** ⚠️ Nur einmalig ausführen!

**Was wird erstellt:**
- ✅ S3 Bucket für Terraform State
- ✅ S3 Bucket für Customer Deployment States
- ✅ DynamoDB Table für State Locking
- ✅ `backend.tf` Dateien für dev/staging/prod

**Wann ausführen:**
- EINMALIG pro AWS Account beim ersten Setup
- Nach `bootstrap` muss `TERRAFORM_STATE_BUCKET` Secret gesetzt werden

**Inputs:**
- `aws_account_id` - 12-stellige AWS Account ID
- `aws_region` - AWS Region (z.B. eu-central-1)
- `project_name` - Projektname (default: overcloud)

**Manuell starten:**
```bash
gh workflow run bootstrap.yml \
  --field aws_account_id="123456789012" \
  --field aws_region="eu-central-1" \
  --field project_name="overcloud"
```

---

### 2. `deploy.yml` - Vollständiges Deployment (Backend + Frontend + Infrastructure)
**Trigger:** Push auf main/staging/develop, PRs, Manual Dispatch  
**Dauer:** ~10-15 Minuten  
**Status:** ✅ Produktionsbereit

**Jobs:**
1. **test** - pytest + Coverage (80%+)
2. **build-frontend** - Vite Build → Upload Artifact
3. **build-backend** - Docker Build → Push to ECR
4. **terraform-plan** - Terraform Plan (bei PRs)
5. **terraform-apply** - Infrastructure Deployment (bei Push)
6. **deploy-frontend** - S3 Sync + CloudFront Invalidation
7. **health-check** - API + Frontend Verification

**Branch → Environment Mapping:**
| Branch | Environment | Auto-Deploy? | Approval? |
|--------|-------------|--------------|-----------|
| `develop` | dev | ✅ Ja | ❌ Nein |
| `staging` | staging | ✅ Ja | ❌ Nein |
| `main` | prod | ✅ Ja | ⚠️ Optional |

**Deployment Pipeline:**
```
┌─────┐   ┌───────┐   ┌────────┐   ┌───────────┐   ┌────────┐   ┌──────┐
│Tests│ → │Frontend│ → │Backend │ → │Terraform  │ → │Deploy  │ → │Health│
│     │   │Build   │   │Build   │   │Apply      │   │Frontend│   │Check │
└─────┘   └───────┘   └────────┘   └───────────┘   └────────┘   └──────┘
```

**Manuell starten:**
```bash
gh workflow run deploy.yml \
  --field environment="dev" \
  --field action="apply"
```

---

### 3. `test.yml` - Tests & Code Quality
**Trigger:** Push/PR auf main/master/develop  
**Dauer:** ~3-5 Minuten  
**Status:** ✅ Produktionsbereit

**Was wird geprüft:**
- ✅ pytest Unit Tests (alle Repositories)
- ✅ Test Coverage (Minimum: 80%)
- ✅ Code Linting (ruff)
- ✅ Type Checking (mypy)
- 📊 Coverage Report als PR Comment
- 📦 Coverage HTML Report als Artifact

**Matrix:** Python 3.11 + 3.12

**Lokal ausführen:**
```bash
cd backend
poetry run pytest --cov=app --cov-report=term-missing
poetry run ruff check .
poetry run mypy app
```

---

### 4. `security-scan.yml` - Security Scanning
**Trigger:** Push/PR auf main/master/develop + Wöchentlich (Montags 9:00 UTC)

**Security Checks:**
1. **Secret Scanning (GitGuardian)** - Erkennt AWS Keys, API Tokens, Passwörter
2. **Bandit** - Python Security Linter (SQL Injection, Unsafe Code)
3. **Safety** - Dependency Vulnerabilities (CVEs)
4. **Semgrep** - SAST (Static Application Security Testing)
5. **CodeQL** - GitHub Code Analysis (Deep semantic analysis)

### 3. `dependency-review.yml` - Dependency Security (PR only)
**Trigger:** Pull Requests auf main/master

**Prüft:** Neue Dependencies auf Vulnerabilities + License Compliance

## 🔧 Lokale Nutzung

### Tests
\`\`\`bash
cd backend
poetry run pytest tests/unit/ --cov=app/repositories --cov-report=term-missing
\`\`\`

### Security Scans
\`\`\`bash
poetry run bandit -r app
poetry run safety check
poetry run ruff check .
poetry run mypy app
\`\`\`

### Frontend Build
\`\`\`bash
cd frontend
npm ci
npm run build
npm run preview  # Preview build
\`\`\`

## 🔐 Erforderliche GitHub Secrets

### Pflicht (für Deployment)

| Secret Name | Beschreibung | Wie bekommen? |
|-------------|--------------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | `aws iam create-access-key` |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | `aws iam create-access-key` |
| `AWS_REGION` | AWS Region | `eu-central-1` |
| `AWS_ACCOUNT_ID` | 12-stellige Account ID | `aws sts get-caller-identity` |
| `DB_MASTER_USERNAME` | PostgreSQL User | Frei wählbar |
| `DB_MASTER_PASSWORD` | PostgreSQL Password | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET_KEY` | JWT Signing Key | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `TERRAFORM_STATE_BUCKET` | S3 Bucket Name | Nach Bootstrap Workflow |
| `ALERT_EMAILS` | Email für Alerts | `your@email.com` |
| `CORS_ORIGINS` | Erlaubte Origins | `*` (dev) oder Domain (prod) |

### Optional (CI/CD)

- `GITGUARDIAN_API_KEY` - GitGuardian Secret Scanning
- `CODECOV_TOKEN` - Coverage Reports
- `SLACK_WEBHOOK_URL` - Slack Notifications
- `PAGERDUTY_ENDPOINT` - PagerDuty Alerts (Prod)
- `STRIPE_SECRET_KEY` - Stripe Payments
- `SENTRY_DSN` - Error Tracking

**Vollständige Setup-Anleitung:** [GITHUB_ACTIONS_SETUP.md](../../docs/GITHUB_ACTIONS_SETUP.md)

**Quick Checklist:** [GITHUB_SECRETS_CHECKLIST.md](../../docs/GITHUB_SECRETS_CHECKLIST.md)

## 📊 Status Badges

\`\`\`markdown
[![Tests](https://github.com/AndySchw/OverCloud/actions/workflows/test.yml/badge.svg)](https://github.com/AndySchw/OverCloud/actions/workflows/test.yml)
[![Security](https://github.com/AndySchw/OverCloud/actions/workflows/security.yml/badge.svg)](https://github.com/AndySchw/OverCloud/actions/workflows/security.yml)
\`\`\`

## 🚨 Bei Failures

**Coverage < 80%:** Siehe `htmlcov/index.html` Artifact  
**Secrets gefunden:** Secret rotieren (NIEMALS aus History löschen!)  
**Vulnerable Dependency:** \`poetry update <package>\`  
**Security Issue:** Artifact Reports anschauen

Details: Siehe Workflow Logs
