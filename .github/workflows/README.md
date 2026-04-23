# GitHub Actions Workflows

Dieses Directory enthält die CI/CD Pipelines für OverCloud.

## Workflows

### `deploy.yml` - Haupt-Deployment-Workflow

**Trigger:**
- Push auf `main` → Deploy nach **prod**
- Push auf `develop` → Deploy nach **dev**
- Pull Request → Terraform Plan (kein Apply)
- Manual Dispatch → Deploy/Destroy beliebiges Environment

**Jobs:**
1. **test** - Führt alle Backend-Tests aus (pytest)
2. **build** - Baut Docker Image und pusht zu ECR
3. **terraform-plan** - Zeigt Terraform Plan (bei PRs)
4. **terraform-apply** - Deployed Infrastructure (bei push)
5. **terraform-destroy** - Zerstört Infrastructure (nur manual)

## GitHub Secrets Setup

Folgende Secrets müssen in GitHub hinterlegt werden:

### AWS Credentials

1. **AWS_ACCESS_KEY_ID**
   - Beschreibung: AWS Access Key für Deployment
   - Wie erstellen:
     ```bash
     aws iam create-user --user-name github-actions-overcloud
     aws iam attach-user-policy --user-name github-actions-overcloud \
       --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
     aws iam create-access-key --user-name github-actions-overcloud
     ```
   - Scope: Repository (oder Organization für alle Repos)

2. **AWS_SECRET_ACCESS_KEY**
   - Beschreibung: AWS Secret Access Key
   - Kommt aus dem `create-access-key` Output

### Database Credentials

3. **DB_MASTER_USERNAME**
   - Beschreibung: PostgreSQL Master Username
   - Beispiel: `overcloud_admin`
   - Scope: Repository

4. **DB_MASTER_PASSWORD**
   - Beschreibung: PostgreSQL Master Password (min. 16 chars)
   - Generieren:
     ```bash
     openssl rand -base64 24
     ```
   - Scope: Repository
   - ⚠️ **Niemals** in Code oder Logs!

### Terraform State

5. **TERRAFORM_STATE_BUCKET**
   - Beschreibung: S3 Bucket für Terraform State (aus Bootstrap)
   - Beispiel: `overcloud-terraform-state-123456789012`
   - Wie finden:
     ```bash
     cd infrastructure/terraform/bootstrap
     terraform output -raw terraform_state_bucket
     ```
   - Scope: Repository

## Secrets in GitHub hinzufügen

### Via GitHub UI

1. Gehe zu: `Settings` → `Secrets and variables` → `Actions`
2. Klicke auf `New repository secret`
3. Name eingeben (z.B. `AWS_ACCESS_KEY_ID`)
4. Value eingeben
5. Klicke `Add secret`

### Via GitHub CLI

```bash
# Install GitHub CLI
brew install gh

# Login
gh auth login

# Add Secrets
gh secret set AWS_ACCESS_KEY_ID --body "AKIAIOSFODNN7EXAMPLE"
gh secret set AWS_SECRET_ACCESS_KEY --body "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
gh secret set DB_MASTER_USERNAME --body "overcloud_admin"
gh secret set DB_MASTER_PASSWORD --body "$(openssl rand -base64 24)"
gh secret set TERRAFORM_STATE_BUCKET --body "overcloud-terraform-state-123456789012"
```

## Environments

Zusätzlich zu Secrets sollten GitHub Environments konfiguriert werden für Protection Rules:

### Dev Environment

```bash
gh api repos/:owner/:repo/environments/dev -X PUT
```

- **Protection Rules:** Keine (auto-deploy bei push)
- **Required Reviewers:** Keine

### Staging Environment

```bash
gh api repos/:owner/:repo/environments/staging -X PUT
```

- **Protection Rules:** 1 Reviewer benötigt
- **Required Reviewers:** Team Lead

### Prod Environment

```bash
gh api repos/:owner/:repo/environments/prod -X PUT
```

- **Protection Rules:**
  - 2 Reviewers benötigt
  - Branch Protection: nur `main` darf deployen
- **Required Reviewers:** 2x Senior Engineers

### Destroy Environments

Für `terraform-destroy` Job separate Environments:
- `dev-destroy`
- `staging-destroy`
- `prod-destroy`

Mit extra Protection (Admin Approval).

## Workflow Usage

### Automatic Deployment

**Dev Deployment:**
```bash
git checkout develop
git add .
git commit -m "feat: new feature"
git push origin develop
# → Triggered automatic deploy to dev
```

**Prod Deployment:**
```bash
git checkout main
git merge develop
git push origin main
# → Triggered automatic deploy to prod
```

### Manual Deployment

**Via GitHub UI:**
1. Gehe zu `Actions` Tab
2. Wähle `Deploy OverCloud to AWS`
3. Klicke `Run workflow`
4. Wähle:
   - Branch: `main` oder `develop`
   - Environment: `dev`, `staging`, `prod`
   - Action: `plan`, `apply`, `destroy`
5. Klicke `Run workflow`

**Via GitHub CLI:**
```bash
# Deploy dev
gh workflow run deploy.yml -f environment=dev -f action=apply

# Plan staging
gh workflow run deploy.yml -f environment=staging -f action=plan

# Destroy dev (⚠️ VORSICHT!)
gh workflow run deploy.yml -f environment=dev -f action=destroy
```

### Pull Request Preview

Bei jedem PR wird automatisch ein Terraform Plan erstellt:

1. Erstelle PR von Feature Branch → `develop`
2. GitHub Actions erstellt Terraform Plan
3. Plan wird als Kommentar im PR gepostet
4. Review Plan vor Merge
5. Nach Merge: Automatisches Apply

## Workflow Outputs

### Successful Deployment

```
✅ Deployment successful!

🌐 API Endpoint: https://abc123.execute-api.eu-central-1.amazonaws.com/
🔌 WebSocket: wss://xyz789.execute-api.eu-central-1.amazonaws.com/dev

📋 Next Steps:
1. Run database migrations (if not automated)
2. Test API endpoints
3. Monitor CloudWatch logs
```

### Failed Deployment

Workflow stoppt und zeigt Fehler:
- Terraform Plan Errors
- Terraform Apply Errors
- AWS Permission Errors

**Troubleshooting:**
1. Check GitHub Actions Logs
2. Verify AWS Credentials
3. Check Terraform State Lock (DynamoDB)
4. Verify all Secrets sind gesetzt

## Debugging

### View Workflow Logs

**Via GitHub UI:**
1. `Actions` Tab → Wähle Workflow Run
2. Klicke auf Job (z.B. `terraform-apply`)
3. Expandiere Steps für Details

**Via GitHub CLI:**
```bash
# List recent runs
gh run list --workflow=deploy.yml

# View specific run
gh run view <RUN_ID>

# Download logs
gh run download <RUN_ID>
```

### Re-run Failed Jobs

**Via UI:**
- Klicke `Re-run failed jobs` im Workflow Run

**Via CLI:**
```bash
gh run rerun <RUN_ID> --failed
```

## Cost Optimization

### Branch Strategy

Nicht jeder Push sollte deployen! Nutze Feature Branches:

```
main (prod)      ← stable, tagged releases
  ↑
  merge
  ↑
develop (dev)    ← integration branch, auto-deploy
  ↑
  merge
  ↑
feature/xyz      ← development, NO auto-deploy (nur PR plan)
```

### Caching

Workflow nutzt Caching für:
- Poetry dependencies (`actions/cache`)
- Terraform providers (automatisch via `hashicorp/setup-terraform`)

### Concurrency Limits

Terraform State Locking verhindert parallele Runs automatisch (DynamoDB).

## Security Best Practices

### Secrets Rotation

**Rotate AWS Credentials alle 90 Tage:**
```bash
# Create new key
aws iam create-access-key --user-name github-actions-overcloud

# Update GitHub Secrets
gh secret set AWS_ACCESS_KEY_ID --body "NEW_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "NEW_SECRET_KEY"

# Delete old key (nach Verify!)
aws iam delete-access-key --user-name github-actions-overcloud \
  --access-key-id OLD_KEY_ID
```

**Rotate DB Password:**
```bash
# Generate new password
NEW_PW=$(openssl rand -base64 24)

# Update Secret
gh secret set DB_MASTER_PASSWORD --body "$NEW_PW"

# Update in AWS Secrets Manager via Terraform
# → Re-run terraform apply
```

### Least Privilege

Der `github-actions-overcloud` IAM User sollte nicht `AdministratorAccess` haben!

**Bessere Policy:**
- EC2, VPC, RDS, Lambda, API Gateway - Full Access
- S3 - Only OverCloud buckets
- Secrets Manager - Only OverCloud secrets
- IAM - PassRole only

Siehe `infrastructure/iam/github-actions-policy.json` für Details.

### Audit Logs

GitHub Actions Logs werden für 90 Tage gespeichert.

Für längere Retention:
- Aktiviere GitHub Advanced Security
- Oder: Export Logs zu S3 via Lambda

## Monitoring

### Workflow Notifications

**Slack Integration:**
```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**Email Notifications:**
GitHub sendet automatisch bei Workflow Failure.

Konfiguriere unter: `Settings` → `Notifications`

### Metrics

Track Workflow Metrics:
- Deployment Frequency (DORA)
- Mean Time to Recovery
- Change Failure Rate

Via GitHub API:
```bash
gh api repos/:owner/:repo/actions/workflows/deploy.yml/runs \
  --jq '.workflow_runs[] | {conclusion, created_at, updated_at}'
```

## Troubleshooting Common Issues

### Error: "Terraform state locked"

**Ursache:** Vorheriger Workflow wurde abgebrochen, Lock nicht released

**Lösung:**
```bash
# Get Lock ID from error message
LOCK_ID="abc-123-def"

# Force unlock
cd infrastructure/terraform/environments/dev
terraform force-unlock $LOCK_ID
```

### Error: "ECR: Image not found"

**Ursache:** Docker Build fehlgeschlagen, aber Terraform versucht Image zu nutzen

**Lösung:**
1. Check Docker Build Logs im `build` Job
2. Fix Dockerfile Errors
3. Re-run Workflow

### Error: "InvalidParameterException: No updates are to be performed"

**Ursache:** Lambda Image URI hat sich nicht geändert

**Lösung:** Normal, kein Fehler. Lambda updated nur bei neuem Image.

### Error: "AccessDenied" beim S3 State Backend

**Ursache:** AWS Credentials haben keine S3 Access oder falsches Bucket

**Lösung:**
1. Verify `TERRAFORM_STATE_BUCKET` Secret
2. Check IAM Policy für S3 Access
3. Verify Bucket existiert:
   ```bash
   aws s3 ls s3://overcloud-terraform-state-123456789012
   ```

## Links

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Terraform GitHub Actions](https://developer.hashicorp.com/terraform/tutorials/automation/github-actions)
- [AWS Actions](https://github.com/aws-actions)
