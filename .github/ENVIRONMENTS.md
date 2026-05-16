# GitHub Environments Setup Guide

## Übersicht

Dieses Dokument beschreibt die Konfiguration der GitHub Environments für OverCloud. Environments ermöglichen:
- ✅ **Environment-spezifische Secrets** (z.B. verschiedene DB-Passwörter)
- ✅ **Manual Approvals** für Staging & Production (verhindert versehentliche Deployments)
- ✅ **Deployment Protection Rules** (nur von bestimmten Branches)
- ✅ **Deployment History** (wer hat wann deployed)

## Branch-Strategie

```
develop ──────────► dev (auto-deploy, no approval)
   │
   └─► PR ──────► staging (auto-deploy after merge, manual approval)
                      │
                      └─► PR ──────► main ──────► prod (auto-deploy after merge, manual approval)
```

**Branch → Environment Mapping:**
- `develop` → **dev** (automatisch, keine Approval)
- `staging` → **staging** (automatisch nach merge, **Manual Approval** required)
- `main` → **prod** (automatisch nach merge, **Manual Approval** required)

## GitHub UI Setup (Manuelle Schritte)

### 1. Repository Settings öffnen
1. Gehe zu: `https://github.com/AndySchw/OverCloud`
2. Klicke auf **Settings** Tab
3. Klicke auf **Environments** (linke Sidebar)

### 2. Environment "dev" erstellen

**Name:** `dev`

**Deployment Protection Rules:**
- ❌ Required reviewers: Keine (auto-deploy)
- ✅ Deployment branches: `develop` only
- ❌ Wait timer: Keine

**Environment Secrets:**
```
AWS_ACCESS_KEY_ID          = <DEV AWS Access Key>
AWS_SECRET_ACCESS_KEY      = <DEV AWS Secret Key>
DB_MASTER_USERNAME         = overcloud_admin
DB_MASTER_PASSWORD         = <DEV DB Password - min 16 chars>
TERRAFORM_STATE_BUCKET     = overcloud-dev-terraform-state
ALERT_EMAILS               = dev-alerts@overcloud.io
SLACK_WEBHOOK_URL          = <Optional: Dev Slack Channel>
CORS_ORIGINS               = http://localhost:3000,https://dev.overcloud.io
```

### 3. Environment "staging" erstellen

**Name:** `staging`

**Deployment Protection Rules:**
- ✅ **Required reviewers:** Andy (mindestens 1 Approval)
- ✅ Deployment branches: `staging` only
- ❌ Wait timer: Keine

**Environment Secrets:**
```
AWS_ACCESS_KEY_ID          = <STAGING AWS Access Key>
AWS_SECRET_ACCESS_KEY      = <STAGING AWS Secret Key>
DB_MASTER_USERNAME         = overcloud_admin
DB_MASTER_PASSWORD         = <STAGING DB Password - min 16 chars, DIFFERENT from dev>
TERRAFORM_STATE_BUCKET     = overcloud-staging-terraform-state
ALERT_EMAILS               = staging-alerts@overcloud.io
SLACK_WEBHOOK_URL          = <Optional: Staging Slack Channel>
CORS_ORIGINS               = https://staging.overcloud.io
```

### 4. Environment "prod" erstellen

**Name:** `prod`

**Deployment Protection Rules:**
- ✅ **Required reviewers:** Andy + 1 other (mindestens 2 Approvals) - wenn Team wächst
- ✅ **Prevent self-review:** Enabled (wenn Team >1 Person)
- ✅ Deployment branches: `main` only
- ⏳ **Wait timer:** 5 minutes (optional - Zeit zum Abbrechen falls nötig)

**Environment Secrets:**
```
AWS_ACCESS_KEY_ID          = <PROD AWS Access Key - SEPARATE ACCOUNT empfohlen>
AWS_SECRET_ACCESS_KEY      = <PROD AWS Secret Key>
DB_MASTER_USERNAME         = overcloud_admin
DB_MASTER_PASSWORD         = <PROD DB Password - min 20 chars, HOCHSICHER>
TERRAFORM_STATE_BUCKET     = overcloud-prod-terraform-state
ALERT_EMAILS               = andy@overcloud.io,team@overcloud.io
SLACK_WEBHOOK_URL          = <PROD Slack Critical Alerts Channel>
PAGERDUTY_ENDPOINT         = <Optional: PagerDuty Integration URL>
CORS_ORIGINS               = https://app.overcloud.io
```

## Secrets Übersicht

### Repository-Level Secrets (für alle Environments)
Diese Secrets bleiben auf Repository-Level (nicht environment-spezifisch):

```
CODECOV_TOKEN              = <Codecov Upload Token>
GITHUB_TOKEN               = <Automatisch vorhanden, nicht manuell setzen>
```

### Environment-Spezifische Secrets
Diese Secrets sind **pro Environment** unterschiedlich:

| Secret Name               | Dev | Staging | Prod | Beschreibung |
|---------------------------|-----|---------|------|--------------|
| AWS_ACCESS_KEY_ID         | ✅  | ✅      | ✅   | AWS Access Key für Terraform |
| AWS_SECRET_ACCESS_KEY     | ✅  | ✅      | ✅   | AWS Secret Key für Terraform |
| DB_MASTER_USERNAME        | ✅  | ✅      | ✅   | Aurora PostgreSQL Admin User |
| DB_MASTER_PASSWORD        | ✅  | ✅      | ✅   | Aurora PostgreSQL Admin Password |
| TERRAFORM_STATE_BUCKET    | ✅  | ✅      | ✅   | S3 Bucket für Terraform State |
| ALERT_EMAILS              | ✅  | ✅      | ✅   | Email-Adressen für CloudWatch Alarms |
| SLACK_WEBHOOK_URL         | ⭕  | ⭕      | ✅   | Slack Webhook für kritische Alerts |
| PAGERDUTY_ENDPOINT        | ❌  | ❌      | ⭕   | PagerDuty für 24/7 On-Call (optional) |
| CORS_ORIGINS              | ✅  | ✅      | ✅   | Erlaubte CORS Origins |

**Legende:**
- ✅ Required
- ⭕ Optional (empfohlen)
- ❌ Nicht benötigt

## Deployment Workflow

### Development (develop branch)
```bash
# 1. Feature entwickeln
git checkout -b feature/my-feature develop
# ... code changes ...
git commit -m "Add feature X"

# 2. PR zu develop erstellen
gh pr create --base develop --title "Add feature X"

# 3. Nach Merge: Auto-Deploy zu dev
# ✅ Keine Approval nötig
# ✅ Tests laufen automatisch
# ✅ Terraform apply auf dev environment
```

### Staging (staging branch)
```bash
# 1. develop nach staging mergen
git checkout staging
git merge develop

# 2. Push zu staging branch
git push origin staging

# 3. GitHub Actions startet
# ⏳ Wartet auf Manual Approval (1 Reviewer)
# 👤 Andy muss in GitHub UI auf "Approve and deploy" klicken
# ✅ Terraform apply auf staging environment
```

### Production (main branch)
```bash
# 1. staging nach main mergen (via PR)
gh pr create --base main --head staging --title "Release v1.2.3"

# 2. PR Review & Merge
# Code Review durchführen
# QA Testing in Staging verifizieren
# PR mergen

# 3. GitHub Actions startet
# ⏳ Wartet auf Manual Approval (2 Reviewers für Prod)
# ⏱️ 5 Minuten Wait Timer (optional)
# 👤 Andy + Team Member müssen approven
# ✅ Terraform apply auf prod environment
```

## Approval Process

### Staging Approval
1. GitHub Actions Workflow pausiert bei `terraform-apply` Job
2. Email-Benachrichtigung an Reviewer
3. Reviewer öffnet: `https://github.com/AndySchw/OverCloud/actions`
4. Klickt auf pausierte Workflow-Run
5. Klickt auf **"Review deployments"** Button
6. Wählt `staging` Environment aus
7. Optional: Kommentar hinzufügen (z.B. "Tests passed, deploying")
8. Klickt auf **"Approve and deploy"**
9. Workflow fährt fort mit Terraform Apply

### Production Approval
- Gleicher Prozess wie Staging
- Benötigt aber 2 Approvals (wenn konfiguriert)
- 5 Minuten Wait Timer gibt Zeit zum Abbrechen
- Kann mit "Reject deployment" abgelehnt werden

## Security Best Practices

### 1. Separate AWS Accounts
**Empfohlen für Production:**
```
Dev Account:     123456789012 (aws-dev)
Staging Account: 234567890123 (aws-staging)  
Prod Account:    345678901234 (aws-prod) ← SEPARATE ACCOUNT
```

**Warum:**
- Prod-Fehler können dev/staging nicht beeinflussen
- IAM Isolation (dev kann nicht auf prod zugreifen)
- Compliance-Anforderungen (ISO 27001, SOC 2)
- Cost Tracking pro Account

### 2. Secret Rotation
**Regelmäßig rotieren:**
- AWS Access Keys: Alle 90 Tage
- DB Master Password: Alle 180 Tage
- Slack Webhook URLs: Bei Verdacht auf Leak

**Rotation-Prozess:**
1. Neues Secret in AWS/Slack generieren
2. Secret in GitHub Environment updaten
3. Deployment durchführen (testet neues Secret)
4. Altes Secret deaktivieren (erst nach erfolgreicher Deployment)

### 3. Access Control
**GitHub Repository Permissions:**
- **Admin:** Andy (nur Owner)
- **Write:** Team Members (können push to develop)
- **Read:** External Contributors (nur PRs)

**Environment-Specific Protection:**
- **dev:** Jeder mit Write-Access
- **staging:** Nur Approvers (Andy)
- **prod:** Nur Approvers + Wait Timer

## Monitoring

### Deployment History
**Überprüfen:**
```
https://github.com/AndySchw/OverCloud/deployments
```

**Zeigt:**
- Wer hat deployed
- Wann wurde deployed
- Welcher Commit wurde deployed
- Deployment Status (success/failure)

### Rollback Process
**Bei fehlgeschlagener Production-Deployment:**

1. **Automatischer Rollback (empfohlen):**
```bash
# Revert merge commit auf main
git revert -m 1 <merge-commit-hash>
git push origin main
# Workflow deployed automatisch vorherige Version
```

2. **Manueller Rollback via Workflow Dispatch:**
```bash
# In GitHub UI:
# Actions → Deploy OverCloud → Run workflow
# Environment: prod
# Action: apply
# Commit: <vorheriger-commit-hash>
```

## Troubleshooting

### Problem: "Environment not found"
**Lösung:** Environment noch nicht in GitHub UI erstellt. Siehe "GitHub UI Setup" oben.

### Problem: "Waiting for approval" hängt
**Lösung:** 
1. Gehe zu Actions Tab
2. Klicke auf laufenden Workflow
3. Klicke auf "Review deployments"
4. Approve oder Reject

### Problem: "Secret not found"
**Lösung:**
1. Gehe zu Settings → Environments → [env] → Secrets
2. Überprüfe ob alle erforderlichen Secrets vorhanden sind
3. Secrets sind case-sensitive: `DB_MASTER_PASSWORD` ≠ `db_master_password`

### Problem: Deployment failed nach Approval
**Lösung:**
1. Check Workflow Logs in Actions Tab
2. Häufige Fehler:
   - Terraform State locked (parallel deployment läuft)
   - AWS Credentials expired/falsch
   - Terraform plan errors (ungültige Konfiguration)
3. Fix error, dann re-run workflow

## Checkliste für initiales Setup

### ✅ GitHub UI Setup
- [ ] Environment "dev" erstellt
- [ ] Environment "staging" erstellt (mit Manual Approval)
- [ ] Environment "prod" erstellt (mit Manual Approval + Wait Timer)
- [ ] Alle Secrets für "dev" hinzugefügt
- [ ] Alle Secrets für "staging" hinzugefügt
- [ ] Alle Secrets für "prod" hinzugefügt

### ✅ Branch Setup
- [ ] `develop` Branch existiert
- [ ] `staging` Branch erstellt: `git checkout -b staging develop && git push -u origin staging`
- [ ] `main` Branch ist production-ready
- [ ] Branch Protection Rules konfiguriert (siehe unten)

### ✅ AWS Setup
- [ ] Dev AWS Account/User konfiguriert
- [ ] Staging AWS Account/User konfiguriert
- [ ] Prod AWS Account/User konfiguriert (empfohlen: separater Account)
- [ ] Terraform State Buckets erstellt (pro Environment)
- [ ] ECR Repositories erstellt (pro Environment)

### ✅ Test Deployment
- [ ] Test-Deployment zu dev erfolgreich
- [ ] Test-Deployment zu staging erfolgreich (mit Approval)
- [ ] Test-Deployment zu prod erfolgreich (mit Approval)

## Branch Protection Rules

**Empfohlene Settings für `main` Branch:**

1. Gehe zu: Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1 (oder 2 wenn Team größer)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require status checks to pass before merging
     - Required checks: `test`, `build`
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators (auch Andy muss PRs machen)

**Empfohlene Settings für `staging` Branch:**
- Gleiche Regeln wie `main`, aber weniger streng (1 Approval reicht)

**Empfohlene Settings für `develop` Branch:**
- ✅ Require status checks: `test`
- ⭕ Require approvals: Optional (0 oder 1)

## Weitere Ressourcen

- [GitHub Environments Docs](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

**Last Updated:** 2026-05-15  
**Maintainer:** Andy Schwarz
