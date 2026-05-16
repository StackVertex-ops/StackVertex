# Quick Start: GitHub Environments Setup

## 🚀 Schritt-für-Schritt Anleitung

### Schritt 1: Branches erstellen

```bash
# 1. Staging Branch erstellen
git checkout -b staging develop
git push -u origin staging

# 2. Main Branch ist bereits vorhanden (als prod)
# Falls nicht, erstellen:
# git checkout -b main develop
# git push -u origin main
```

### Schritt 2: GitHub Environments in UI erstellen

#### 2.1 Repository Settings öffnen
```
https://github.com/AndySchw/OverCloud/settings/environments
```

#### 2.2 Environment "dev" erstellen
1. Klick auf **"New environment"**
2. Name: `dev`
3. **Deployment branches:** `develop` only
4. **Required reviewers:** Keine
5. Klick auf **"Configure environment"**
6. Secrets hinzufügen (siehe unten)

#### 2.3 Environment "staging" erstellen
1. Klick auf **"New environment"**
2. Name: `staging`
3. **Required reviewers:** ✅ Aktivieren → Andy auswählen
4. **Deployment branches:** `staging` only
5. Klick auf **"Configure environment"**
6. Secrets hinzufügen (siehe unten)

#### 2.4 Environment "prod" erstellen
1. Klick auf **"New environment"**
2. Name: `prod`
3. **Required reviewers:** ✅ Aktivieren → Andy auswählen
4. **Wait timer:** Optional: 5 minutes
5. **Deployment branches:** `main` only
6. Klick auf **"Configure environment"**
7. Secrets hinzufügen (siehe unten)

### Schritt 3: Secrets hinzufügen

#### Dev Secrets
```
Environment: dev
───────────────────────────────────────────────────
AWS_ACCESS_KEY_ID          = <DEV AWS Access Key>
AWS_SECRET_ACCESS_KEY      = <DEV AWS Secret Key>
DB_MASTER_USERNAME         = overcloud_admin
DB_MASTER_PASSWORD         = <DEV Password - min 16 chars>
TERRAFORM_STATE_BUCKET     = overcloud-dev-terraform-state
ALERT_EMAILS               = dev-alerts@overcloud.io
CORS_ORIGINS               = http://localhost:3000,https://dev.overcloud.io
```

#### Staging Secrets
```
Environment: staging
───────────────────────────────────────────────────
AWS_ACCESS_KEY_ID          = <STAGING AWS Access Key>
AWS_SECRET_ACCESS_KEY      = <STAGING AWS Secret Key>
DB_MASTER_USERNAME         = overcloud_admin
DB_MASTER_PASSWORD         = <STAGING Password - min 16 chars>
TERRAFORM_STATE_BUCKET     = overcloud-staging-terraform-state
ALERT_EMAILS               = staging-alerts@overcloud.io
SLACK_WEBHOOK_URL          = <Optional: Staging Slack Webhook>
CORS_ORIGINS               = https://staging.overcloud.io
```

#### Prod Secrets
```
Environment: prod
───────────────────────────────────────────────────
AWS_ACCESS_KEY_ID          = <PROD AWS Access Key>
AWS_SECRET_ACCESS_KEY      = <PROD AWS Secret Key>
DB_MASTER_USERNAME         = overcloud_admin
DB_MASTER_PASSWORD         = <PROD Password - min 20 chars>
TERRAFORM_STATE_BUCKET     = overcloud-prod-terraform-state
ALERT_EMAILS               = andy@overcloud.io,team@overcloud.io
SLACK_WEBHOOK_URL          = <PROD Slack Webhook>
PAGERDUTY_ENDPOINT         = <Optional: PagerDuty Integration>
CORS_ORIGINS               = https://app.overcloud.io
```

### Schritt 4: Terraform State Buckets erstellen

**Wichtig:** Terraform State Buckets müssen VOR dem ersten Deployment manuell erstellt werden.

```bash
# AWS CLI verwenden (für jedes Environment)

# Dev
aws s3 mb s3://overcloud-dev-terraform-state --region eu-central-1
aws s3api put-bucket-versioning --bucket overcloud-dev-terraform-state --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket overcloud-dev-terraform-state --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Staging
aws s3 mb s3://overcloud-staging-terraform-state --region eu-central-1
aws s3api put-bucket-versioning --bucket overcloud-staging-terraform-state --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket overcloud-staging-terraform-state --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Prod
aws s3 mb s3://overcloud-prod-terraform-state --region eu-central-1
aws s3api put-bucket-versioning --bucket overcloud-prod-terraform-state --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket overcloud-prod-terraform-state --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

**Alternative:** Terraform Bootstrap Script verwenden (wenn vorhanden):
```bash
cd infrastructure/terraform
./scripts/bootstrap-backend.sh dev
./scripts/bootstrap-backend.sh staging
./scripts/bootstrap-backend.sh prod
```

### Schritt 5: ECR Repositories erstellen

```bash
# Dev
aws ecr create-repository --repository-name overcloud-dev-lambda --region eu-central-1

# Staging
aws ecr create-repository --repository-name overcloud-staging-lambda --region eu-central-1

# Prod
aws ecr create-repository --repository-name overcloud-prod-lambda --region eu-central-1
```

### Schritt 6: Ersten Deployment testen

#### 6.1 Dev Deployment (automatisch)
```bash
# Push zu develop branch
git checkout develop
git push origin develop

# GitHub Actions deployt automatisch zu dev
# Kein Approval nötig
```

#### 6.2 Staging Deployment (mit Approval)
```bash
# Push zu staging branch
git checkout staging
git merge develop
git push origin staging

# GitHub Actions startet
# ⏳ Wartet auf Approval
# Gehe zu: https://github.com/AndySchw/OverCloud/actions
# Klick auf pausierte Workflow
# Klick auf "Review deployments" → Approve
```

#### 6.3 Prod Deployment (mit Approval)
```bash
# Merge staging zu main via PR
gh pr create --base main --head staging --title "Initial Production Deployment"

# PR review und merge
# GitHub Actions startet
# ⏳ Wartet auf Approval (+ 5min Wait Timer)
# Approve in GitHub Actions Tab
```

## ✅ Checkliste

- [ ] Staging Branch erstellt
- [ ] Dev Environment in GitHub erstellt + Secrets
- [ ] Staging Environment in GitHub erstellt + Secrets + Approval
- [ ] Prod Environment in GitHub erstellt + Secrets + Approval
- [ ] Terraform State Buckets erstellt (3x)
- [ ] ECR Repositories erstellt (3x)
- [ ] Test-Deployment zu dev erfolgreich
- [ ] Test-Deployment zu staging erfolgreich (mit Approval)
- [ ] Test-Deployment zu prod erfolgreich (mit Approval)

## 🆘 Troubleshooting

### "Bucket does not exist" Error
**Problem:** Terraform State Bucket existiert nicht.  
**Lösung:** Siehe "Schritt 4: Terraform State Buckets erstellen"

### "Repository does not exist" Error
**Problem:** ECR Repository existiert nicht.  
**Lösung:** Siehe "Schritt 5: ECR Repositories erstellen"

### "Environment not found" Error
**Problem:** GitHub Environment noch nicht erstellt.  
**Lösung:** Siehe "Schritt 2: GitHub Environments in UI erstellen"

### "Secret not found" Error
**Problem:** Environment Secret fehlt oder falsch geschrieben.  
**Lösung:** 
- Secrets sind case-sensitive: `DB_MASTER_PASSWORD` ≠ `db_master_password`
- Alle erforderlichen Secrets prüfen (siehe Schritt 3)
- Environment auswählen: Settings → Environments → [env] → Secrets

### Workflow hängt bei "Waiting for approval"
**Lösung:**
1. Gehe zu: https://github.com/AndySchw/OverCloud/actions
2. Klick auf laufenden Workflow
3. Klick auf "Review deployments"
4. Wähle Environment aus
5. Klick auf "Approve and deploy"

## 📚 Weitere Dokumentation

Siehe [`ENVIRONMENTS.md`](./ENVIRONMENTS.md) für vollständige Dokumentation.

---

**Quick Start abgeschlossen?** 🎉  
Nächste Schritte: Phase 2 - Security & Compliance
