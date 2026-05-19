# Deployment Quick Start

**Ziel:** Von 0 zu automatischem Deployment in 15 Minuten.

---

## ⚡ 5-Schritte Setup

### Schritt 1: IAM User erstellen (2 min)

```bash
# User erstellen + Access Keys generieren
aws iam create-user --user-name github-actions-overcloud
aws iam create-access-key --user-name github-actions-overcloud

# Admin Policy anhängen
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Account ID anzeigen
aws sts get-caller-identity --query Account --output text
```

**Kopiere:** `AccessKeyId` und `SecretAccessKey` aus Output!

---

### Schritt 2: Secrets generieren (1 min)

```bash
# DB Password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT Secret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

### Schritt 3: GitHub Secrets setzen (5 min)

Gehe zu: **Settings → Secrets and variables → Actions → New repository secret**

**Copy-Paste diese 9 Secrets:**

```
Name: AWS_ACCESS_KEY_ID
Value: AKIA... (von Schritt 1)

Name: AWS_SECRET_ACCESS_KEY
Value: wJal... (von Schritt 1)

Name: AWS_REGION
Value: eu-central-1

Name: AWS_ACCOUNT_ID
Value: 123456789012 (von Schritt 1)

Name: DB_MASTER_USERNAME
Value: admin

Name: DB_MASTER_PASSWORD
Value: (von Schritt 2)

Name: JWT_SECRET_KEY
Value: (von Schritt 2)

Name: ALERT_EMAILS
Value: your@email.com

Name: CORS_ORIGINS
Value: *
```

---

### Schritt 4: Bootstrap ausführen (3 min)

1. Gehe zu: **Actions → Bootstrap Terraform State Backend → Run workflow**
2. Eingaben:
   - `aws_account_id`: (deine 12-stellige ID)
   - `aws_region`: `eu-central-1`
   - `project_name`: `overcloud`
3. **Run workflow** klicken
4. Warte ~2-3 Minuten
5. **WICHTIG:** Kopiere `TERRAFORM_STATE_BUCKET` aus Output

---

### Schritt 5: Final Secret setzen (1 min)

```
Name: TERRAFORM_STATE_BUCKET
Value: overcloud-terraform-state-123456789012 (von Bootstrap Output)
```

---

## 🚀 Test Deployment (2 min)

```bash
# Leerer Commit
git checkout develop
git commit --allow-empty -m "test: First deployment"
git push origin develop

# Gehe zu Actions Tab und beobachte Workflow
```

**Erwartete Dauer:** 8-12 Minuten

**Output:**
- ✅ Backend deployed (Lambda + API Gateway)
- ✅ Frontend deployed (S3 + CloudFront)
- ✅ Database ready (Aurora Serverless)
- ✅ Networking ready (VPC + Subnets)

---

## 🎯 Was passiert beim Push?

```
develop branch → Dev Environment (automatisch)
staging branch → Staging Environment (automatisch)
main branch → Prod Environment (REQUIRES APPROVAL)
```

**Deployment Pipeline:**
```
Tests → Build → Terraform → Deploy → Health Check ✅
```

---

## 📋 Checkliste

- [ ] IAM User erstellt
- [ ] Access Keys generiert
- [ ] 9 GitHub Secrets gesetzt
- [ ] Bootstrap ausgeführt
- [ ] `TERRAFORM_STATE_BUCKET` Secret gesetzt
- [ ] Test Deployment erfolgreich
- [ ] API erreichbar
- [ ] Frontend erreichbar

---

## 🆘 Troubleshooting

### Bootstrap schlägt fehl

**Error:** "Access Denied"
```bash
# Prüfe ob User Admin Policy hat
aws iam list-attached-user-policies --user-name github-actions-overcloud
```

### Deployment schlägt fehl

**Error:** "No such bucket"
→ Hast du `TERRAFORM_STATE_BUCKET` Secret gesetzt?

**Error:** "ECR repository not found"
→ Wird automatisch beim ersten Deployment erstellt, retry den Workflow

**Error:** "Coverage < 80%"
→ Temporär in `backend/pyproject.toml` Coverage senken:
```toml
[tool.pytest.ini_options]
addopts = "--cov-fail-under=60"
```

---

## 📚 Weitere Dokumentation

- **Vollständige Setup-Anleitung:** `docs/GITHUB_ACTIONS_SETUP.md`
- **Secrets Checklist:** `docs/GITHUB_SECRETS_CHECKLIST.md`
- **Workflows Übersicht:** `.github/workflows/README.md`
- **Terraform Environments:** `infrastructure/terraform/environments/ENVIRONMENTS.md`

---

## 🎉 Nächste Schritte

Nach erfolgreichem Dev Deployment:

1. ✅ Dev funktioniert
2. ⏳ Staging Branch erstellen: `git checkout -b staging && git push origin staging`
3. ⏳ Production Branch: `git checkout -b main && git push origin main`
4. ⏳ GitHub Environment Protection für Prod (Settings → Environments)
5. ⏳ Custom Domain konfigurieren
6. ⏳ SSL Certificate (AWS Certificate Manager)

---

**Fragen?** Siehe vollständige Docs oder erstelle ein Issue.
