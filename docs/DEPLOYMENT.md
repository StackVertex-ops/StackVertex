# StackVertex - Deployment Guide

## Prerequisites

### Required Tools
- **AWS CLI** v2+ (`aws configure`)
- **Terraform** v1.5+ (via GitHub Actions)
- **GitHub CLI** (`gh auth login`)
- **Poetry** (Python dependency management)
- **Node.js** v18+ (Frontend build)

### Required Secrets

#### GitHub Secrets (Required)
1. `AWS_ACCESS_KEY_ID` - IAM user with deployment permissions
2. `AWS_SECRET_ACCESS_KEY` - IAM user secret
3. `ADMIN_CREATION_SECRET` - Random 32+ char token (see below)

#### Generate ADMIN_CREATION_SECRET
```bash
openssl rand -base64 48
```

Add to GitHub: `Settings` → `Secrets` → `New repository secret`

---

## Deployment Steps

### 1. Bootstrap (One-Time Setup)

Creates S3 bucket for Terraform state and ECR for Docker images.

```bash
gh workflow run bootstrap.yml \
  -f aws_account_id="YOUR_AWS_ACCOUNT_ID" \
  -f aws_region="eu-central-1" \
  -f project_name="stackvertex"
```

**What it does:**
- Creates `stackvertex-terraform-state` S3 bucket
- Creates `stackvertex-ecr-backend` ECR repository
- Sets up DynamoDB for state locking
- Outputs: State bucket name, ECR URI

**Duration:** ~2 minutes

---

### 2. Deploy Infrastructure

Deploys VPC, Lambda, API Gateway, DynamoDB, S3, CloudWatch.

#### Option A: Via Script (Recommended)
```bash
./infrastructure/scripts/deploy-dev.sh
```

Interactive menu:
1. **Complete Deployment** - Bootstrap + Infrastructure (first time)
2. **Infrastructure Only** - Skip bootstrap (updates)
3. **Frontend Only** - Update frontend files

#### Option B: Via GitHub CLI
```bash
gh workflow run deploy.yml \
  -f environment=dev \
  -f action=apply
```

**What it deploys:**
- **Networking**: VPC, Subnets, NAT Gateway, Security Groups
- **Compute**: Lambda Functions (API backend)
- **Storage**: S3 (frontend + customer data), DynamoDB (database)
- **API**: API Gateway HTTP API
- **Monitoring**: CloudWatch Logs + Alarms
- **Security**: IAM Roles, KMS encryption

**Duration:** ~8-12 minutes

**Outputs:**
- Frontend URL: `http://stackvertex-dev-frontend.s3-website.eu-central-1.amazonaws.com`
- API URL: `https://{api-id}.execute-api.eu-central-1.amazonaws.com`

---

### 3. Create Admin User (Post-Deployment)

**IMPORTANT:** After first deployment, create an admin user to login.

#### Option A: Local Script (Recommended)
```bash
cd infrastructure/scripts
export ADMIN_CREATION_SECRET="<your-secret-from-github>"
./create-admin-user.sh
```

Interactive prompts:
- Environment (dev/staging/prod)
- Admin Email
- Admin Name
- Force creation (yes/no)

#### Option B: GitHub Actions
```bash
gh workflow run create-admin.yml \
  -f environment=dev \
  -f admin_email="admin@stackvertex.io" \
  -f admin_name="Admin User"
```

**Credentials:**
- Password shown in terminal (local) or artifact (GitHub Actions)
- Download artifact within 24h (expires after)
- **Store password securely** (password manager)

**Security:**
- Requires `ADMIN_CREATION_SECRET` environment variable
- Dual-layer protection (AWS access + secret token)
- Cannot create admin without both

---

### 4. Verify Deployment

#### Frontend
```bash
curl -I http://stackvertex-dev-frontend.s3-website.eu-central-1.amazonaws.com
# Expect: HTTP/1.1 200 OK
```

#### Backend API
```bash
API_URL="https://<api-id>.execute-api.eu-central-1.amazonaws.com"
curl $API_URL/health
# Expect: {"status":"healthy"}
```

#### Login
1. Open frontend URL in browser
2. Navigate to `/login.html`
3. Enter admin email + password
4. Should redirect to `/dashboard.html`

---

## Environment Configuration

### Dev Environment
- **Purpose**: Development & testing
- **Data Retention**: 7 days
- **Backup**: Disabled
- **Public Access**: Frontend via S3 website
- **Auth**: Full authentication required

### Staging Environment
- **Purpose**: Pre-production testing
- **Data Retention**: 30 days
- **Backup**: Daily snapshots
- **Public Access**: CloudFront only
- **Auth**: Full authentication required

### Production Environment
- **Purpose**: Live user traffic
- **Data Retention**: 90 days
- **Backup**: Hourly snapshots + point-in-time recovery
- **Public Access**: CloudFront with custom domain
- **Auth**: Full authentication + 2FA (when available)

---

## Destroy Infrastructure

### Via Script
```bash
./infrastructure/scripts/destroy-dev.sh
```

Interactive menu:
1. **GitHub Actions** (recommended) - Clean destroy via workflow
2. **Cleanup Script** (fast) - Direct AWS CLI deletion
3. **Terraform Destroy** (manual) - Terraform state-based

### Via GitHub Actions
```bash
gh workflow run destroy.yml \
  -f environment=dev \
  -f confirm_destroy="DESTROY" \
  -f skip_approval=true
```

**What it destroys:**
- All AWS resources (VPC, Lambda, S3, DynamoDB, etc.)
- Waits for Lambda ENIs to detach (up to 10 min)
- Verifies cleanup via resource tagging

**Duration:** ~5-8 minutes

**Safety Features:**
- Requires `confirm_destroy="DESTROY"` input
- Manual approval step (unless `skip_approval=true`)
- Pre-destroy ENI cleanup
- Post-destroy verification

---

## Troubleshooting

### Bootstrap Failed: "Bucket already exists"
**Solution:** Bucket exists in another region or account
```bash
aws s3 ls | grep stackvertex-terraform-state
# If exists → delete or use different project name
```

### Deploy Failed: "DynamoDB table not found"
**Cause:** Bootstrap not completed
**Solution:** Run bootstrap first

### Deploy Failed: "Lambda CreateNetworkInterface permission denied"
**Cause:** Missing AWSLambdaVPCAccessExecutionRole
**Solution:** Already fixed in latest version, re-deploy

### VPC Won't Delete
**Cause:** Lambda ENIs still attached
**Solution:** Destroy workflow now waits for ENI deletion automatically

### Frontend 403 Forbidden
**Cause:** Bucket policy blocks public access
**Solution:** Dev uses `enable_public_website_access = true` (check terraform)

### Cannot Login: "Invalid credentials"
**Cause:** Admin user not created yet
**Solution:** Run `./create-admin-user.sh`

### Backend API 401 Unauthorized
**Cause:** Missing or expired JWT token
**Solution:** 
1. Check localStorage for `access_token`
2. Token expires after 24h → re-login
3. Check browser console for errors

---

## Monitoring & Logs

### CloudWatch Logs
```bash
# API Logs
aws logs tail /aws/lambda/stackvertex-dev-api --follow

# Infrastructure Logs
aws logs tail /aws/lambda/stackvertex-dev-terraform --follow
```

### GitHub Actions Logs
```bash
# Latest deploy run
gh run list --workflow=deploy.yml --limit 1

# View logs
gh run view <run-id> --log
```

### DynamoDB Audit Logs
```bash
# Query recent admin actions
aws dynamodb scan \
  --table-name stackvertex-dev-audit-log \
  --filter-expression "action = :action" \
  --expression-attribute-values '{":action":{"S":"admin.create_superadmin"}}'
```

---

## Rollback

### Rollback to Previous Version

#### 1. Identify Last Good Commit
```bash
git log --oneline -10
```

#### 2. Checkout Previous Version
```bash
git checkout <commit-hash>
```

#### 3. Re-deploy
```bash
gh workflow run deploy.yml -f environment=dev -f action=apply
```

#### 4. Return to Latest
```bash
git checkout main
```

### Rollback via Terraform State

```bash
cd infrastructure/terraform/environments/dev
terraform state list
# Find resources to rollback
terraform state pull > backup.tfstate
```

---

## Security Best Practices

### Pre-Deployment Checklist
- [ ] `ADMIN_CREATION_SECRET` set in GitHub Secrets (32+ chars)
- [ ] AWS MFA enabled on deployment user
- [ ] No hardcoded credentials in code
- [ ] `.env` files in `.gitignore`
- [ ] Secrets stored in AWS Secrets Manager (prod)

### Post-Deployment Checklist
- [ ] Admin user created
- [ ] Admin password changed after first login
- [ ] CloudWatch alarms configured
- [ ] Backup strategy tested
- [ ] SSL certificates configured (staging/prod)
- [ ] Rate limiting enabled

### Monthly Tasks
- [ ] Review CloudWatch logs for anomalies
- [ ] Rotate AWS access keys
- [ ] Update dependencies (npm audit, safety check)
- [ ] Verify backup retention policies

### Quarterly Tasks
- [ ] Rotate `ADMIN_CREATION_SECRET`
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Update security documentation

---

## Cost Optimization

### Dev Environment (~$50-80/month)
- **VPC**: NAT Gateway ($32/month) + Elastic IPs
- **Lambda**: ~$5/month (free tier eligible)
- **DynamoDB**: On-Demand pricing (~$2/month low traffic)
- **S3**: ~$1/month (frontend + logs)
- **API Gateway**: ~$3.50/1M requests

### Optimization Tips
1. **Dev:** Delete environment when not in use (`destroy-dev.sh`)
2. **Staging:** Schedule shutdown after business hours
3. **Prod:** Use reserved capacity for predictable workloads
4. **All:** Enable S3 lifecycle policies (already configured)

---

## Support

### Documentation
- **Security:** [docs/SECURITY.md](./SECURITY.md)
- **Testing:** [backend/tests/README.md](../backend/tests/README.md)
- **Development:** [.claude/CLAUDE.md](../.claude/CLAUDE.md)

### Issues
- GitHub Issues: For bugs and feature requests
- Security Issues: Email `security@stackvertex.io` (do not disclose publicly)

---

## Quick Reference

```bash
# Deploy
./infrastructure/scripts/deploy-dev.sh

# Create Admin
export ADMIN_CREATION_SECRET="<secret>"
./infrastructure/scripts/create-admin-user.sh

# Destroy
./infrastructure/scripts/destroy-dev.sh

# Logs
aws logs tail /aws/lambda/stackvertex-dev-api --follow

# Health Check
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/health
```
