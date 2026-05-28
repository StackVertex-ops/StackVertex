# 🚀 Pluralsight Sandbox - Quick Start

**4 Stunden Zeit-Limit** ⏰

---

## Vorbereitung (einmalig pro Session)

### 1. GitHub CLI Auth Check

```bash
# Auth Status prüfen
gh auth status

# Falls nicht eingeloggt:
gh auth login
# → GitHub.com
# → HTTPS  
# → Login via Browser
```

---

## Deployment - 3 einfache Schritte

### Schritt 1: GitHub Secrets Setup (5 min)

```bash
cd ~/Documents/Privat/OverCloud/infrastructure/scripts

# Script ausführen (fragt interaktiv nach Credentials)
./setup-github-secrets.sh
```

**Das Script fragt nach:**
- AWS Access Key ID (von Pluralsight)
- AWS Secret Access Key (von Pluralsight)
- Slack Webhook (optional)

**Generiert automatisch:**
- SECRET_KEY (für JWT)

---

### Schritt 2: Deployment starten (25-30 min)

```bash
# Deployment via GitHub Actions
./deploy-pluralsight-actions.sh
```

**Das Script macht:**
1. Bootstrap (S3 State + DynamoDB Lock) - ~5 min
2. Infrastructure Deploy (Terraform) - ~20 min
3. Zeigt Deployment Summary

**Output:**
- API Endpoint
- DynamoDB Table Name
- ECR Repository
- Frontend Bucket

---

### Schritt 3: Testing (2-3h)

Features testen:
- API Health Check
- Authentication
- Architecture Designer
- Terraform Generation
- Cost Calculation
- Admin Panel
- etc.

**GitHub Actions Logs checken:**
```bash
# Workflow Logs anzeigen
gh run list
gh run view <run-id> --log

# Oder via GitHub UI:
# https://github.com/StackVertex-ops/StackVertex/actions
```

---

## Destroy (bei 3:30h!)

### Option A: GitHub Actions (empfohlen)

```bash
./destroy-pluralsight.sh actions
```

### Option B: Terraform (lokal)

```bash
./destroy-pluralsight.sh terraform
```

### Option C: Quick Destroy (schnellste)

```bash
./destroy-pluralsight.sh quick
```

---

## Timeline

```
0:00 - 0:05   Setup GitHub Secrets
0:05 - 0:35   Deployment (GitHub Actions)
0:35 - 3:30   Testing
3:30 - 3:50   Destroy
3:50 - 4:00   Verify
```

---

## Troubleshooting

### "gh not found"

```bash
# GitHub CLI installieren
brew install gh

# Auth
gh auth login
```

### "GitHub Secrets fehlen"

```bash
# Erneut setzen
./setup-github-secrets.sh
```

### "Workflow failed"

```bash
# Logs checken
gh run list
gh run view <run-id> --log

# Oder GitHub UI:
# https://github.com/StackVertex-ops/StackVertex/actions
```

### "Destroy hängt"

```bash
# Quick Destroy nutzen
./destroy-pluralsight.sh quick
```

---

## Scripts Übersicht

| Script | Zweck | Dauer |
|--------|-------|-------|
| `setup-github-secrets.sh` | GitHub Secrets setzen | 2 min |
| `deploy-pluralsight-actions.sh` | Full Deployment via Actions | 25-30 min |
| `destroy-pluralsight.sh actions` | Destroy via Actions | 15-20 min |
| `destroy-pluralsight.sh quick` | Schnelles Destroy | 10-15 min |

---

## One-Liner (Copy-Paste)

```bash
# Kompletter Workflow
cd ~/Documents/Privat/OverCloud/infrastructure/scripts && \
./setup-github-secrets.sh && \
./deploy-pluralsight-actions.sh

# Nach Testing (bei 3:30h):
./destroy-pluralsight.sh actions
```

---

## GitHub Actions UI

Alternativ kannst du auch direkt über GitHub UI deployen:

1. **https://github.com/StackVertex-ops/StackVertex/actions**
2. **"Deploy StackVertex to AWS"** auswählen
3. **"Run workflow"** klicken
4. Optionen:
   - Branch: `main`
   - Environment: `dev`
   - Action: `apply`
5. **Run workflow** bestätigen

---

**Ready!** 🚀
