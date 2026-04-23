# OverCloud Quick Start Guide

Schnellstart-Anleitung um OverCloud in 30 Minuten auf AWS zu deployen.

## Voraussetzungen (5 Minuten)

### 1. AWS Account

- AWS Account mit Admin Access
- Region: `eu-central-1` (Frankfurt)

### 2. Lokale Tools installieren

```bash
# AWS CLI
brew install awscli

# Terraform
brew install terraform

# Docker
brew install docker

# Optional: jq
brew install jq
```

### 3. AWS CLI konfigurieren

```bash
aws configure
# AWS Access Key ID: [YOUR_KEY]
# AWS Secret Access Key: [YOUR_SECRET]  
# Default region: eu-central-1
# Default output format: json

# Verify
aws sts get-caller-identity
# Output: Your Account ID
```

---

## Schritt 1: Bootstrap (10 Minuten)

Erstellt die Terraform State Backend Infrastruktur.

```bash
# Clone Repository
git clone https://github.com/YOUR_ORG/overcloud.git
cd overcloud

# Run Bootstrap
cd infrastructure/scripts
./bootstrap.sh
```

**Was passiert:**
1. Prüft Prerequisites
2. Erkennt AWS Account ID
3. Erstellt S3 Bucket für Terraform State
4. Erstellt DynamoDB Table für State Locking
5. Generiert Backend Config für alle Environments

**Output:**
```
✅ Bootstrap Complete!

📦 Created Resources:
   - State Bucket: overcloud-terraform-state-123456789012
   - Locks Table: overcloud-terraform-locks
   - Deployment Bucket: overcloud-deployment-states-123456789012

📝 Next Steps:
   1. cd ../terraform/environments/dev
   2. terraform init
   3. terraform plan
   4. terraform apply
```

---

## Schritt 2: Dev Environment Deploy (15 Minuten)

```bash
cd ../terraform/environments/dev

# 1. Configure Variables
cp terraform.tfvars.example terraform.tfvars

# 2. Edit terraform.tfvars
vim terraform.tfvars
```

**Minimum Configuration:**

```hcl
# terraform.tfvars
project_name = "overcloud"
environment  = "dev"
aws_region   = "eu-central-1"

# Database Credentials (CHANGE THESE!)
db_master_username = "overcloud_admin"
db_master_password = "YOUR_SECURE_PASSWORD_MIN_16_CHARS"

# From Bootstrap Output
terraform_state_bucket = "overcloud-terraform-state-123456789012"

# Alerts (optional for dev)
alert_emails = ["your-email@example.com"]
```

**Generate strong password:**
```bash
openssl rand -base64 24
```

**Deploy Infrastructure:**

```bash
# 3. Initialize Terraform
terraform init

# 4. Plan (review changes)
terraform plan -out=tfplan

# 5. Apply
terraform apply tfplan
```

**Duration:** ~10-15 Minuten (Aurora braucht am längsten)

**Output:**
```
Apply complete! Resources: 42 added, 0 changed, 0 destroyed.

Outputs:

api_endpoint = "https://abc123.execute-api.eu-central-1.amazonaws.com/"
websocket_endpoint = "wss://xyz789.execute-api.eu-central-1.amazonaws.com/dev"
ecr_repository_url = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/overcloud-dev-lambda"
database_endpoint = "overcloud-dev-aurora.cluster-abc.eu-central-1.rds.amazonaws.com"

cloudwatch_dashboard_url = "https://console.aws.amazon.com/.../overcloud-dev-overview"
```

---

## Schritt 3: Backend Deploy (10 Minuten)

### Build & Push Docker Image

```bash
# Get ECR URL from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)

# ECR Login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build Image
cd ../../../../../backend
docker build -f Dockerfile.lambda -t overcloud-dev-lambda .

# Tag
docker tag overcloud-dev-lambda:latest $ECR_URL:latest
docker tag overcloud-dev-lambda:latest $ECR_URL:$(git rev-parse --short HEAD)

# Push
docker push $ECR_URL:latest
docker push $ECR_URL:$(git rev-parse --short HEAD)
```

### Update Lambda

```bash
# Update Lambda Function
aws lambda update-function-code \
  --function-name overcloud-dev-api \
  --image-uri $ECR_URL:latest \
  --region eu-central-1

# Wait for update
aws lambda wait function-updated \
  --function-name overcloud-dev-api \
  --region eu-central-1

echo "✅ Lambda updated!"
```

---

## Schritt 4: Database Migrations (5 Minuten)

```bash
# Get Database Credentials
DB_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id overcloud-dev-db-credentials \
  --region eu-central-1 \
  --query SecretString \
  --output text)

# Extract values
DB_HOST=$(echo $DB_SECRET | jq -r .host)
DB_USER=$(echo $DB_SECRET | jq -r .username)
DB_PASS=$(echo $DB_SECRET | jq -r .password)
DB_NAME=$(echo $DB_SECRET | jq -r .database)

# Set DATABASE_URL
export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:5432/$DB_NAME"

# Run Migrations
cd backend
poetry install
poetry run alembic upgrade head
```

**Output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_add_versioning
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003_add_deployments
```

---

## Schritt 5: Test API (2 Minuten)

```bash
# Get API Endpoint
API_URL=$(cd ../infrastructure/terraform/environments/dev && terraform output -raw api_endpoint)

# Health Check
curl $API_URL/health

# Expected Response:
{
  "status": "healthy",
  "version": "0.1.0"
}

# API Docs
open $API_URL/api/docs
```

### Test CRUD Operations

```bash
# Create Architecture
curl -X POST $API_URL/api/v1/architectures \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Architecture",
    "description": "Quick Start Test",
    "architecture_json": {
      "version": "1.0.0",
      "metadata": {
        "name": "Simple Web App",
        "description": "Test deployment"
      },
      "provider": {
        "type": "aws",
        "region": "eu-central-1"
      },
      "components": []
    }
  }'

# Expected: 201 Created
{
  "id": "uuid-here",
  "name": "Test Architecture",
  "created_at": "2026-04-18T10:30:00Z",
  ...
}

# List Architectures
curl $API_URL/api/v1/architectures

# Expected: 200 OK
{
  "items": [...],
  "total": 1,
  "page": 1
}
```

---

## Schritt 6: Setup Monitoring (5 Minuten)

### CloudWatch Dashboard

```bash
# Get Dashboard URL
DASHBOARD_URL=$(cd infrastructure/terraform/environments/dev && terraform output -raw cloudwatch_dashboard_url)

# Open Dashboard
open "$DASHBOARD_URL"
```

**Dashboard zeigt:**
- Lambda Invocations, Errors, Duration
- API Gateway Requests, 4XX/5XX, Latency
- Aurora CPU, Connections, ACUs
- S3 Storage

### Email Alerts

**SNS Subscription Confirmation:**

1. Check Email Inbox
2. Find Email: "AWS Notification - Subscription Confirmation"
3. Click Link "Confirm subscription"
4. Done! ✅

**Slack Alerts (Optional):**

```bash
# 1. Create Slack Webhook
# In Slack: Apps → Incoming Webhooks → Add

# 2. Add to terraform.tfvars
echo 'slack_webhook_url = "https://hooks.slack.com/services/..."' >> terraform.tfvars

# 3. Re-apply
terraform apply
```

---

## Schritt 7: Security Check (3 Minuten)

### CloudTrail

```bash
# Verify CloudTrail is logging
aws cloudtrail get-trail-status \
  --name overcloud-dev-trail \
  --region eu-central-1

# Expected:
{
  "IsLogging": true,
  "LatestDeliveryTime": "2026-04-18T10:30:00Z"
}
```

### GuardDuty

```bash
# Get Detector ID
DETECTOR_ID=$(aws guardduty list-detectors \
  --region eu-central-1 \
  --query 'DetectorIds[0]' \
  --output text)

# Check Status
aws guardduty get-detector \
  --detector-id $DETECTOR_ID \
  --region eu-central-1

# Expected:
{
  "Status": "ENABLED",
  "FindingPublishingFrequency": "ONE_HOUR"
}
```

### Security Hub

```bash
# Get Security Score
aws securityhub get-findings \
  --region eu-central-1 \
  --filters 'ComplianceStatus=[{Value=FAILED,Comparison=EQUALS}]' \
  --max-results 10

# Expected: Empty or minimal findings (new deployment)
```

---

## Fertig! 🎉

**Du hast jetzt:**

✅ **Infrastruktur:**
- VPC mit Public/Private Subnets
- Aurora Serverless v2 Database
- Lambda Function (FastAPI)
- API Gateway (HTTP + WebSocket)
- S3 Buckets (Customer Data, Deployments, Terraform State)

✅ **Monitoring:**
- CloudWatch Dashboard
- 11 CloudWatch Alarms
- Email/Slack Alerts
- CloudTrail (API Audit)
- GuardDuty (Threat Detection)
- Security Hub (Compliance)

✅ **Security:**
- Encryption at rest (S3, Aurora, Secrets)
- Encryption in transit (HTTPS, TLS)
- Private subnets für Database
- Security Groups (minimal access)
- No public S3 buckets

---

## Nächste Schritte

### Frontend Deployment

```bash
cd frontend

# Build
npm run build

# Deploy to S3 (static hosting)
aws s3 sync dist/ s3://overcloud-dev-frontend --delete

# Setup CloudFront (optional)
```

### CI/CD Pipeline

```bash
# Setup GitHub Secrets
gh secret set AWS_ACCESS_KEY_ID --body "YOUR_KEY"
gh secret set AWS_SECRET_ACCESS_KEY --body "YOUR_SECRET"
gh secret set DB_MASTER_USERNAME --body "overcloud_admin"
gh secret set DB_MASTER_PASSWORD --body "YOUR_PASSWORD"
gh secret set TERRAFORM_STATE_BUCKET --body "overcloud-terraform-state-123456789012"

# Push to GitHub
git push origin develop

# → Automatic deployment to dev! 🚀
```

### Production Deployment

```bash
# 1. Create prod environment
cp -r infrastructure/terraform/environments/dev \
      infrastructure/terraform/environments/prod

# 2. Adjust prod settings
vim infrastructure/terraform/environments/prod/main.tf
# - min_capacity = 2
# - max_capacity = 16
# - enable_cloudwatch_alarms = true
# - enable_multi_region_trail = true

# 3. Deploy
cd infrastructure/terraform/environments/prod
terraform init
terraform plan
terraform apply

# 4. Update CI/CD
# Push to main branch → auto-deploy to prod
```

---

## Troubleshooting

### Error: "Terraform state locked"

```bash
# Get Lock ID from error message
terraform force-unlock <LOCK_ID>
```

### Error: "Database connection failed"

```bash
# Check Security Groups
aws ec2 describe-security-groups \
  --group-ids $(terraform output -raw aurora_security_group_id)

# Verify Lambda can reach Aurora
aws lambda get-function-configuration \
  --function-name overcloud-dev-api \
  --query VpcConfig
```

### Error: "Lambda timeout"

```bash
# Increase timeout
# In terraform/modules/compute/main.tf:
timeout = 60  # was 30

terraform apply
```

### Error: "Out of memory"

```bash
# Increase memory
# In terraform/modules/compute/main.tf:
memory_size = 1024  # was 512

terraform apply
```

---

## Kosten Übersicht

**Dev Environment:** ~$120/Monat

| Service | Kosten |
|---------|--------|
| Aurora (0.5-1 ACU) | $43 |
| Lambda (5k req/Tag) | $5 |
| API Gateway | $1 |
| S3 | $2 |
| CloudWatch | $34 |
| CloudTrail | $2 |
| GuardDuty | $10 |
| Security Hub | $10 |
| **TOTAL** | **~$107** |

**Kosten reduzieren:**
- Destroy dev environment über Nacht: `terraform destroy`
- Disable Security Hub in dev: `enable_security_hub = false`
- Reduce log retention: `log_retention_days = 3`

---

## Wichtige Links

- **Dokumentation:**
  - [AWS Deployment Guide](deployment/AWS_DEPLOYMENT.md)
  - [Monitoring & Security](operations/MONITORING_SECURITY.md)
  - [Architecture Details](architecture/INFRASTRUCTURE.md)

- **AWS Consoles:**
  - [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=eu-central-1#dashboards:)
  - [Lambda Functions](https://console.aws.amazon.com/lambda/home?region=eu-central-1#/functions)
  - [API Gateway](https://console.aws.amazon.com/apigateway/home?region=eu-central-1)
  - [Aurora Databases](https://console.aws.amazon.com/rds/home?region=eu-central-1#databases:)

- **Terraform:**
  ```bash
  terraform output        # Show all outputs
  terraform state list    # List all resources
  terraform show          # Show current state
  ```

---

## Support

**Probleme?**

1. Check [Troubleshooting](#troubleshooting) oben
2. Check CloudWatch Logs: `aws logs tail /aws/lambda/overcloud-dev-api --follow`
3. Check GitHub Issues: `https://github.com/YOUR_ORG/overcloud/issues`
4. Slack: `#overcloud-support`

---

**Viel Erfolg! 🚀**
