# Quick Deploy Guide

> **Ziel:** Deployment in 15 Minuten

## Voraussetzungen

- AWS CLI konfiguriert
- GitHub CLI installiert (optional)
- Python 3.11+

## 5 Schritte zum Deployment

### 1. IAM User erstellen (2 Min)

```bash
aws iam create-user --user-name github-actions-overcloud
aws iam create-access-key --user-name github-actions-overcloud
aws iam attach-user-policy \
  --user-name github-actions-overcloud \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

**Kopiere Access Key ID und Secret Access Key!**

### 2. Secrets generieren (1 Min)

```bash
export DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export JWT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
```

### 3. GitHub Secrets setzen (5 Min)

**Via GitHub CLI:**

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

**Oder via Web UI:** https://github.com/AndySchw/OverCloud/settings/secrets/actions

### 4. ECR Repositories erstellen (2 Min)

```bash
aws ecr create-repository --repository-name overcloud-dev-lambda --region eu-central-1
aws ecr create-repository --repository-name overcloud-staging-lambda --region eu-central-1
aws ecr create-repository --repository-name overcloud-prod-lambda --region eu-central-1
```

### 5. Bootstrap + Deploy (5 Min)

**Bootstrap:**

```bash
gh workflow run bootstrap.yml \
  --field aws_account_id="$AWS_ACCOUNT_ID" \
  --field aws_region="eu-central-1" \
  --field project_name="overcloud"

# Warte ~2 Min, dann:
gh secret set TERRAFORM_STATE_BUCKET --body "overcloud-terraform-state-$AWS_ACCOUNT_ID"
```

**Deploy:**

```bash
git checkout develop
git commit --allow-empty -m "test: First deployment"
git push origin develop
```

## Fertig!

Nach ~10-15 Minuten ist Dev Environment deployed.

**Check Deployment:**

```bash
gh run watch
```

**URLs:**

```bash
cd infrastructure/terraform/environments/dev
terraform output
```

---

**Vollständige Dokumentation:** Siehe [docs/DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md)
