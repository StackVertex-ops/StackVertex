# AWS Serverless Deployment Guide

Kompletter Guide für das Deployment von StackVertex auf AWS als Serverless Application.

## Architektur Überblick

```
┌──────────────────────────────────────────────────────────────┐
│                        Internet                               │
└────────────────┬─────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────┐
│              API Gateway (HTTP + WebSocket)                   │
│  - REST API für CRUD Operations                              │
│  - WebSocket für Real-time Updates                           │
└────────────────┬─────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────┐
│                  AWS Lambda (Container)                       │
│  - FastAPI Backend in Docker Container                       │
│  - Mangum ASGI Adapter                                       │
│  - Background Tasks via ThreadPool                           │
└────────┬───────────────┬─────────────────────────────────────┘
         │               │
         │               │
    ┌────▼────┐     ┌────▼────────────────────────────────┐
    │   VPC   │     │  AWS Secrets Manager                │
    │         │     │  - Database Credentials             │
    └────┬────┘     └─────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────────┐
    │       Aurora Serverless v2 (PostgreSQL)   │
    │       - Auto-scaling: 0.5-16 ACUs         │
    │       - Multi-AZ (prod only)              │
    └───────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    S3 Buckets                                │
│  - Terraform State (mit DynamoDB Locking)                   │
│  - Deployment States (Customer Deployments)                 │
│  - Lambda Code (ECR Repository)                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  CloudWatch                                  │
│  - Lambda Logs                                              │
│  - API Gateway Logs                                         │
│  - Database Metrics                                         │
│  - Custom Alarms                                            │
└─────────────────────────────────────────────────────────────┘
```

## Kosten-Übersicht

### Dev Environment (~$50-80/Monat)
- Aurora Serverless v2 (0.5-1 ACU): ~$43/Monat
- Lambda (5000 req/Tag, 512MB): ~$5/Monat
- API Gateway (5000 req/Tag): ~$0.50/Monat
- S3 + DynamoDB: ~$2/Monat
- **Total: ~$50/Monat**

### Production Environment (~$300-500/Monat)
- Aurora Serverless v2 (2-16 ACU, Multi-AZ): ~$350/Monat
- Lambda (50000 req/Tag, 1024MB): ~$30/Monat
- API Gateway (50000 req/Tag): ~$5/Monat
- S3 + DynamoDB: ~$10/Monat
- NAT Gateway: ~$32/Monat
- CloudWatch + SNS: ~$10/Monat
- **Total: ~$437/Monat**

## Voraussetzungen

### 1. AWS Account

- AWS Account mit Admin Access
- Region: `eu-central-1` (Frankfurt) empfohlen
- Alternative: `us-east-1`, `us-west-2`

### 2. Lokale Tools

```bash
# AWS CLI
brew install awscli
aws --version  # >= 2.0

# Terraform
brew install terraform
terraform --version  # >= 1.5.0

# Docker
brew install docker
docker --version  # >= 24.0

# Optional: jq für JSON parsing
brew install jq
```

### 3. AWS CLI Konfiguration

```bash
# Configure AWS CLI
aws configure
# AWS Access Key ID: [YOUR_KEY]
# AWS Secret Access Key: [YOUR_SECRET]
# Default region: eu-central-1
# Default output format: json

# Verify
aws sts get-caller-identity
```

## Deployment-Prozess

### Schritt 1: Bootstrap (Einmalig pro AWS Account)

Der Bootstrap erstellt die Terraform State Backend Infrastruktur.

```bash
cd infrastructure/scripts
./bootstrap.sh
```

**Was passiert:**
1. Prüft Prerequisites (AWS CLI, Terraform, jq)
2. Erkennt AWS Account ID und Region
3. Erstellt `terraform.tfvars` automatisch
4. Deployed S3 Bucket für Terraform State
5. Deployed DynamoDB Table für State Locking
6. Deployed S3 Bucket für Deployment States
7. Generiert `backend.tf` für alle Environments

**Output:**
```
✅ Bootstrap Complete!

📦 Created Resources:
   - State Bucket: stackvertex-terraform-state-123456789012
   - Locks Table: stackvertex-terraform-locks
   - Deployment Bucket: stackvertex-deployment-states-123456789012

📝 Next Steps:
   1. cd ../environments/dev
   2. terraform init
   3. terraform plan
   4. terraform apply
```

**Wichtig:**
- Bootstrap nur **einmal** pro AWS Account ausführen
- State Bucket hat `prevent_destroy = true` (Schutz gegen versehentliches Löschen)
- Notiere die Bucket Namen für später

### Schritt 2: Environment Variables konfigurieren

```bash
cd infrastructure/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars
```

**Pflichtfelder:**
```hcl
project_name = "stackvertex"
environment  = "dev"
aws_region   = "eu-central-1"

# Database (CHANGE THESE!)
db_master_username = "stackvertex_admin"
db_master_password = "IhrSicheresPasswortMin16Zeichen!"

# From Bootstrap Output
terraform_state_bucket = "stackvertex-terraform-state-123456789012"
```

**Passwort generieren:**
```bash
openssl rand -base64 24
```

### Schritt 3: Terraform Init

```bash
terraform init
```

**Output:**
```
Initializing the backend...
Initializing modules...
Initializing provider plugins...

Terraform has been successfully initialized!
```

### Schritt 4: Terraform Plan

```bash
terraform plan -out=tfplan
```

**Prüfe den Plan:**
- 40+ Ressourcen werden erstellt
- VPC mit 2 AZs
- Aurora Serverless v2 Cluster
- Lambda Function + API Gateway
- S3 Buckets
- Security Groups
- IAM Roles

**Geschätzte Kosten:** ~$50/Monat für dev

### Schritt 5: Terraform Apply

```bash
terraform apply tfplan
```

**Dauer:** ~10-15 Minuten (Aurora Cluster braucht am längsten)

**Output:**
```
Apply complete! Resources: 42 added, 0 changed, 0 destroyed.

Outputs:

deployment_summary = <<EOT

✅ StackVertex Dev Environment Deployed!

🌐 API Endpoint:       https://abc123.execute-api.eu-central-1.amazonaws.com/
🔌 WebSocket Endpoint: wss://xyz789.execute-api.eu-central-1.amazonaws.com/dev

📦 ECR Repository:     123456789012.dkr.ecr.eu-central-1.amazonaws.com/stackvertex-dev-lambda
🗄️  Deployment Bucket:  stackvertex-dev-deployment-states-123456789012

💾 Database Endpoint:  stackvertex-dev-aurora.cluster-abc.eu-central-1.rds.amazonaws.com
🔐 Database Secret:    arn:aws:secretsmanager:eu-central-1:123:secret:stackvertex-dev-db-creds-abc123

📋 Next Steps:
1. Build & push Docker image to ECR
2. Update Lambda function with new image
3. Run database migrations (alembic upgrade head)
4. Test API endpoint
```

### Schritt 6: Docker Image bauen & deployen

```bash
# ECR Login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com

# Build Image
cd ../../../../../backend
docker build -f Dockerfile.lambda -t stackvertex-dev-lambda .

# Tag
ECR_REPO="123456789012.dkr.ecr.eu-central-1.amazonaws.com/stackvertex-dev-lambda"
docker tag stackvertex-dev-lambda:latest $ECR_REPO:latest
docker tag stackvertex-dev-lambda:latest $ECR_REPO:$(git rev-parse --short HEAD)

# Push
docker push $ECR_REPO:latest
docker push $ECR_REPO:$(git rev-parse --short HEAD)
```

### Schritt 7: Lambda Function updaten

Lambda wurde von Terraform erstellt, aber ohne Image. Jetzt updaten:

```bash
aws lambda update-function-code \
  --function-name stackvertex-dev-api \
  --image-uri $ECR_REPO:latest \
  --region eu-central-1
```

**Warte auf Update:**
```bash
aws lambda wait function-updated \
  --function-name stackvertex-dev-api \
  --region eu-central-1

echo "✅ Lambda updated!"
```

### Schritt 8: Datenbank Migrationen

**Option A: Lokal (über VPN/Bastion)**

Falls VPN oder Bastion Host existiert:

```bash
# Get Database Secret
DB_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id stackvertex-dev-db-credentials \
  --region eu-central-1 \
  --query SecretString \
  --output text)

DB_HOST=$(echo $DB_SECRET | jq -r .host)
DB_USER=$(echo $DB_SECRET | jq -r .username)
DB_PASS=$(echo $DB_SECRET | jq -r .password)
DB_NAME=$(echo $DB_SECRET | jq -r .database)

export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:5432/$DB_NAME"

# Run Alembic
cd backend
poetry run alembic upgrade head
```

**Option B: Via Lambda Admin Endpoint**

Erstelle einen `/admin/migrate` Endpoint in FastAPI:

```python
# app/api/admin.py
from alembic.config import Config
from alembic import command

@router.post("/migrate")
async def run_migrations():
    """Run Alembic migrations (Admin only)."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    return {"status": "migrations completed"}
```

Dann via API call:

```bash
curl -X POST https://abc123.execute-api.eu-central-1.amazonaws.com/admin/migrate \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Option C: EC2 Bastion Host**

Für Production empfohlen:

```bash
# Create Bastion in Terraform
module "bastion" {
  source = "../../modules/bastion"
  vpc_id = module.networking.vpc_id
  subnet_id = module.networking.public_subnet_ids[0]
}

# SSH to Bastion
ssh -i bastion-key.pem ec2-user@bastion-ip

# Run migrations from Bastion
DATABASE_URL="..." alembic upgrade head
```

### Schritt 9: Test Deployment

```bash
# Health Check
curl https://abc123.execute-api.eu-central-1.amazonaws.com/health

# Response:
{
  "status": "healthy",
  "version": "0.1.0"
}

# API Docs
open https://abc123.execute-api.eu-central-1.amazonaws.com/api/docs

# Create Architecture
curl -X POST https://abc123.execute-api.eu-central-1.amazonaws.com/api/v1/architectures \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Architecture",
    "description": "Test from deployment",
    "architecture_json": {...}
  }'
```

## CI/CD mit GitHub Actions

### Setup

1. **GitHub Secrets erstellen:**

```bash
# Install GitHub CLI
brew install gh
gh auth login

# Add Secrets
gh secret set AWS_ACCESS_KEY_ID --body "YOUR_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "YOUR_SECRET_KEY"
gh secret set DB_MASTER_USERNAME --body "stackvertex_admin"
gh secret set DB_MASTER_PASSWORD --body "$(openssl rand -base64 24)"
gh secret set TERRAFORM_STATE_BUCKET --body "stackvertex-terraform-state-123456789012"
```

2. **Workflow ist bereits konfiguriert:**

`.github/workflows/deploy.yml` deployt automatisch:
- Push auf `develop` → Deploy nach **dev**
- Push auf `main` → Deploy nach **prod**
- Pull Request → Terraform Plan (kein Apply)

### Manual Deployment

```bash
# Deploy dev
gh workflow run deploy.yml -f environment=dev -f action=apply

# Destroy dev
gh workflow run deploy.yml -f environment=dev -f action=destroy
```

Siehe `.github/workflows/README.md` für Details.

## Monitoring & Debugging

### CloudWatch Logs

```bash
# Lambda Logs
aws logs tail /aws/lambda/stackvertex-dev-api --follow

# API Gateway Logs
aws logs tail /aws/apigateway/stackvertex-dev-http-api --follow

# Filter für Errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/stackvertex-dev-api \
  --filter-pattern "ERROR"
```

### Lambda Invocation

```bash
# Test Lambda direkt
aws lambda invoke \
  --function-name stackvertex-dev-api \
  --payload '{"rawPath": "/health", "requestContext": {"http": {"method": "GET"}}}' \
  response.json

cat response.json
```

### Database Connection

```bash
# Get DB Endpoint
DB_ENDPOINT=$(terraform output -raw database_endpoint)

# Test Connection (from VPC or Bastion)
psql -h $DB_ENDPOINT -U stackvertex_admin -d stackvertex
```

### Metrics Dashboard

CloudWatch Dashboard automatisch erstellt:

```bash
# Open Dashboard
open "https://console.aws.amazon.com/cloudwatch/home?region=eu-central-1#dashboards:name=StackVertex-Dev"
```

**Wichtige Metriken:**
- Lambda Invocations
- Lambda Errors
- Lambda Duration
- API Gateway Requests
- Aurora CPU Utilization
- Aurora Connections

## Troubleshooting

### Error: Lambda Cold Start Timeout

**Problem:** Lambda in VPC hat langsamen Cold Start (10+ Sekunden)

**Lösung:**
1. Erhöhe Lambda Timeout:
   ```hcl
   lambda_timeout = 60
   ```

2. Oder: Provisioned Concurrency aktivieren:
   ```hcl
   resource "aws_lambda_provisioned_concurrency_config" "api" {
     function_name = aws_lambda_function.api.function_name
     provisioned_concurrent_executions = 1
   }
   ```

3. Oder: VPC Endpoints nutzen (reduziert Latency):
   ```hcl
   enable_vpc_endpoints = true
   ```

### Error: Database Connection Failed

**Problem:** Lambda kann nicht auf Aurora zugreifen

**Checks:**
1. Security Group erlaubt Lambda → Aurora (Port 5432)?
   ```bash
   aws ec2 describe-security-groups \
     --group-ids $(terraform output -raw aurora_security_group_id)
   ```

2. Lambda ist im richtigen Subnet?
   ```bash
   aws lambda get-function-configuration \
     --function-name stackvertex-dev-api \
     --query VpcConfig
   ```

3. Database Secret ist korrekt?
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id stackvertex-dev-db-credentials
   ```

### Error: Terraform State Locked

**Problem:** Vorheriger Terraform Run wurde abgebrochen

**Lösung:**
```bash
# Get Lock ID from error message
terraform force-unlock <LOCK_ID>
```

### Error: Lambda Out of Memory

**Problem:** Lambda OOM Error in CloudWatch

**Lösung:**
```hcl
# Erhöhe Memory
lambda_memory_size = 1024  # war 512
```

**Analyze:**
```bash
# Memory Report
aws logs filter-log-events \
  --log-group-name /aws/lambda/stackvertex-dev-api \
  --filter-pattern "Max Memory Used"
```

### Error: Aurora Scaling Issues

**Problem:** Aurora skaliert nicht schnell genug

**Lösung:**
```hcl
# Erhöhe min_capacity
min_capacity = 1  # war 0.5
```

## Disaster Recovery

### State Backup

Terraform State wird automatisch in S3 versioniert:

```bash
# List State Versions
aws s3api list-object-versions \
  --bucket stackvertex-terraform-state-123456789012 \
  --prefix environments/dev/terraform.tfstate

# Restore alte Version
aws s3api get-object \
  --bucket stackvertex-terraform-state-123456789012 \
  --key environments/dev/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup
```

### Database Backup

Aurora automatische Backups sind aktiviert:

```bash
# List Snapshots
aws rds describe-db-cluster-snapshots \
  --db-cluster-identifier stackvertex-dev-aurora

# Create Manual Snapshot
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier stackvertex-dev-aurora \
  --db-cluster-snapshot-identifier stackvertex-dev-manual-$(date +%Y%m%d)

# Restore from Snapshot
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier stackvertex-dev-aurora-restored \
  --snapshot-identifier stackvertex-dev-manual-20260418 \
  --engine aurora-postgresql
```

### Complete Environment Recreation

Falls alles verloren geht:

```bash
# 1. Bootstrap (creates state backend)
cd infrastructure/scripts
./bootstrap.sh

# 2. Restore Terraform State (from S3 version)
cd ../terraform/environments/dev
aws s3 cp s3://stackvertex-terraform-state-123456789012/environments/dev/terraform.tfstate?versionId=<VERSION> terraform.tfstate

# 3. Import existing resources (falls nötig)
terraform import module.database.aws_rds_cluster.aurora stackvertex-dev-aurora

# 4. Re-apply
terraform init
terraform plan
terraform apply
```

## Cleanup

### Destroy Environment

**⚠️ VORSICHT:** Löscht ALLE Ressourcen inkl. Datenbank!

```bash
cd infrastructure/terraform/environments/dev

# Plan Destroy
terraform plan -destroy

# Destroy
terraform destroy
```

**Production Cleanup Checklist:**
1. ✅ Finale Database Snapshot erstellt
2. ✅ Deployment States gesichert (S3 Bucket)
3. ✅ CloudWatch Logs exportiert
4. ✅ DNS-Einträge entfernt
5. ✅ Users benachrichtigt
6. ✅ Dann: `terraform destroy`

### Bootstrap Cleanup (SELTEN!)

Nur ausführen wenn komplette Infrastruktur weg soll:

```bash
cd infrastructure/terraform/bootstrap

# Entferne prevent_destroy
sed -i '' 's/prevent_destroy = true/prevent_destroy = false/' main.tf

# Destroy
terraform destroy

# ⚠️ Danach: Terraform State ist WEG!
```

## Security Best Practices

### 1. Credentials Rotation

```bash
# Rotate Database Password
NEW_PW=$(openssl rand -base64 24)

# Update Secret
aws secretsmanager update-secret \
  --secret-id stackvertex-dev-db-credentials \
  --secret-string "{\"username\":\"stackvertex_admin\",\"password\":\"$NEW_PW\",...}"

# Modify Aurora Master Password
aws rds modify-db-cluster \
  --db-cluster-identifier stackvertex-dev-aurora \
  --master-user-password "$NEW_PW" \
  --apply-immediately
```

### 2. IAM Least Privilege

Lambda Execution Role sollte nur benötigte Permissions haben:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:stackvertex-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::stackvertex-*-deployment-states-*/*"
    }
  ]
}
```

### 3. Network Security

- Lambda in Private Subnets
- Aurora nicht öffentlich erreichbar
- Security Groups: Minimal Rules
- VPC Endpoints für AWS Services (kein Internet)

### 4. Audit Logging

Alle API Calls werden geloggt:

```bash
# CloudTrail Events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::RDS::DBCluster
```

## Performance Optimization

### Lambda

```hcl
# Optimale Einstellungen für FastAPI
lambda_memory_size = 512   # Sweet spot für FastAPI
lambda_timeout     = 30    # Genug für API Calls

# Provisioned Concurrency (nur prod)
provisioned_concurrent_executions = 2  # Verhindert Cold Starts
```

### Aurora

```hcl
# Dev: Minimal
min_capacity = 0.5
max_capacity = 1

# Prod: Auto-scaling
min_capacity = 2
max_capacity = 16
```

### API Gateway

- HTTP API (günstiger als REST API)
- Caching aktivieren (nur prod):
  ```hcl
  cache_cluster_enabled = true
  cache_cluster_size    = "0.5"
  ```

## Kosten-Optimierung

### 1. Aurora Serverless v2 Pause

Aktuell nicht unterstützt, aber geplant von AWS.

**Workaround:** Destroy dev environment über Nacht:
```bash
# Jeden Abend um 20 Uhr
terraform destroy -auto-approve

# Jeden Morgen um 8 Uhr
terraform apply -auto-approve
```

### 2. S3 Lifecycle Rules

Bereits konfiguriert:
- Deployment States → Glacier nach 90 Tagen
- State File Versions → Gelöscht nach 365 Tagen

### 3. CloudWatch Log Retention

```hcl
log_retention_days = 7   # Dev
log_retention_days = 30  # Prod
```

### 4. NAT Gateway vermeiden

Dev Environment nutzt kein NAT Gateway ($32/Monat gespart).

Lambda hat keinen Internet-Zugriff, nur AWS Services via VPC Endpoints.

## Weitere Ressourcen

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html)
- [FastAPI on Lambda](https://www.mangum.io/)
