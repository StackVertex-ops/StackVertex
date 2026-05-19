# GitHub Secrets Checklist

Quick Reference für alle erforderlichen GitHub Secrets.

## ✅ Minimale Secrets für MVP Start

Copy-Paste diese Commands um Secrets zu generieren:

```bash
# 1. AWS Account ID anzeigen
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"

# 2. DB Password generieren (min 16 chars)
export DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
echo "DB_MASTER_PASSWORD: $DB_PASSWORD"

# 3. JWT Secret Key generieren (64 chars)
export JWT_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
echo "JWT_SECRET_KEY: $JWT_KEY"
```

### Secrets Liste (10 Pflicht-Secrets)

| ✅ | Secret Name | Value | Hinweis |
|----|-------------|-------|---------|
| ☐ | `AWS_ACCESS_KEY_ID` | `AKIA...` | Von IAM User (Schritt 1) |
| ☐ | `AWS_SECRET_ACCESS_KEY` | `wJal...` | Von IAM User (Schritt 1) |
| ☐ | `AWS_REGION` | `eu-central-1` | Deine bevorzugte Region |
| ☐ | `AWS_ACCOUNT_ID` | `123456789012` | 12 Stellen (siehe oben) |
| ☐ | `DB_MASTER_USERNAME` | `admin` | Frei wählbar |
| ☐ | `DB_MASTER_PASSWORD` | (generiert) | Min 16 Zeichen! (siehe oben) |
| ☐ | `JWT_SECRET_KEY` | (generiert) | 64+ Zeichen! (siehe oben) |
| ☐ | `ALERT_EMAILS` | `your@email.com` | Deine Email |
| ☐ | `CORS_ORIGINS` | `*` | Dev: `*`, Prod: Domain |
| ☐ | `TERRAFORM_STATE_BUCKET` | (nach Bootstrap) | Aus Bootstrap Output |

### Optional (kann später hinzugefügt werden)

| Secret Name | Woher? | Wofür? |
|-------------|--------|--------|
| `SLACK_WEBHOOK_URL` | https://api.slack.com/messaging/webhooks | Notifications |
| `PAGERDUTY_ENDPOINT` | https://www.pagerduty.com | 24/7 Alerts |
| `STRIPE_SECRET_KEY` | https://dashboard.stripe.com/apikeys | Payments |
| `SENTRY_DSN` | https://sentry.io | Error Tracking |

---

## 🚀 Setup Commands

### IAM User erstellen + Access Keys

```bash
# 1. User erstellen
aws iam create-user --user-name github-actions-overcloud

# 2. Access Keys generieren (OUTPUT KOPIEREN!)
aws iam create-access-key --user-name github-actions-overcloud

# 3. Admin Policy anhängen (MVP)
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# 4. Account ID anzeigen
aws sts get-caller-identity --query Account --output text
```

### Secrets generieren

```bash
# DB Password (32 chars)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT Secret (64 chars)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Secrets in GitHub setzen

```bash
# Option 1: Manuell über Web UI
# Gehe zu: https://github.com/AndySchw/OverCloud/settings/secrets/actions
# Settings → Secrets and variables → Actions → New repository secret

# Option 2: Via GitHub CLI (empfohlen - schneller!)
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..."
gh secret set AWS_SECRET_ACCESS_KEY --body "wJal..."
gh secret set AWS_REGION --body "eu-central-1"
gh secret set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID"
gh secret set DB_MASTER_USERNAME --body "admin"
gh secret set DB_MASTER_PASSWORD --body "$DB_PASSWORD"
gh secret set JWT_SECRET_KEY --body "$JWT_KEY"
gh secret set ALERT_EMAILS --body "schwarz23andy@gmail.com"
gh secret set CORS_ORIGINS --body "*"

# Später (nach Bootstrap):
gh secret set TERRAFORM_STATE_BUCKET --body "overcloud-terraform-state-$AWS_ACCOUNT_ID"
```

---

## 📋 Verifizierung

### Secrets Liste anzeigen

```bash
# Via GitHub CLI
gh secret list

# Expected Output:
# AWS_ACCESS_KEY_ID        Updated 2026-05-18
# AWS_SECRET_ACCESS_KEY    Updated 2026-05-18
# AWS_REGION               Updated 2026-05-18
# AWS_ACCOUNT_ID           Updated 2026-05-18
# DB_MASTER_USERNAME       Updated 2026-05-18
# DB_MASTER_PASSWORD       Updated 2026-05-18
# JWT_SECRET_KEY           Updated 2026-05-18
# ALERT_EMAILS             Updated 2026-05-18
# CORS_ORIGINS             Updated 2026-05-18
```

### Test Deployment

```bash
# Leerer Commit zum Testen
git commit --allow-empty -m "test: Verify GitHub Actions setup"
git push origin develop

# Gehe zu GitHub Actions Tab und beobachte Workflow
```

---

## 🔒 Security Checks

### ✅ Secret Rotation Schedule

| Secret | Rotation Interval | Wie? |
|--------|-------------------|------|
| `AWS_ACCESS_KEY_ID` | 90 Tage | `aws iam create-access-key` + alte löschen |
| `DB_MASTER_PASSWORD` | 180 Tage | Terraform apply mit neuer Variable |
| `JWT_SECRET_KEY` | 365 Tage | Neue generieren + alte Session invalidieren |

### ✅ Secret Validation

```bash
# Test AWS Credentials
AWS_ACCESS_KEY_ID="..." AWS_SECRET_ACCESS_KEY="..." \
  aws sts get-caller-identity

# Test DB Password Stärke (min 16 chars)
echo -n "your-password" | wc -c  # Sollte >= 16 sein

# Test JWT Key Stärke (min 64 chars)
echo -n "your-jwt-key" | wc -c  # Sollte >= 64 sein
```

---

## ❌ Häufige Fehler

### Error: "Secret not found"

**Ursache:** Secret-Name falsch geschrieben (case-sensitive!)

**Lösung:** Exakte Namen verwenden (siehe Liste oben)

### Error: "Invalid AWS credentials"

**Ursache:** Access Keys falsch kopiert oder abgelaufen

**Lösung:**
```bash
# Neue Access Keys generieren
aws iam create-access-key --user-name github-actions-overcloud
```

### Error: "DB Password zu kurz"

**Ursache:** Password < 16 Zeichen

**Lösung:**
```bash
# Neues 32-Zeichen Password generieren
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🎯 Nach Secret Setup

1. ✅ Alle Pflicht-Secrets gesetzt
2. ⏳ **Bootstrap Workflow ausführen** (siehe `GITHUB_ACTIONS_SETUP.md`)
3. ⏳ `TERRAFORM_STATE_BUCKET` Secret setzen (nach Bootstrap)
4. ⏳ Test Deployment durchführen
5. ⏳ Secrets Rotation Reminder setzen (90 Tage)

---

**Vollständige Dokumentation:** `docs/GITHUB_ACTIONS_SETUP.md`
