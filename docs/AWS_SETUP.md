# AWS Setup für StackVertex Backend

Dieses Dokument beschreibt die AWS-Infrastruktur für das StackVertex Backend und was noch konfiguriert werden muss.

---

## 📋 Übersicht

**Status:** AWS Account vorhanden, aber noch nicht komplett eingerichtet ⚠️

**Benötigte AWS Services:**
- **DynamoDB:** Haupt-Datenbank für User, Architectures, Deployments
- **S3:** Large Item Storage (>300KB)
- **Secrets Manager:** Verschlüsselte Credentials (AWS Roles, Stripe Keys)
- **CloudWatch Logs:** Application Logging
- **IAM:** Roles & Permissions
- **ECS Fargate** oder **Lambda:** Backend Hosting
- **API Gateway:** (optional) für Lambda
- **VPC:** (optional) für ECS

---

## 🎯 Quick Start Checklist

### ✅ Was bereits existiert
- [x] AWS Account vorhanden
- [ ] IAM User/Role für CI/CD (GitHub Actions)
- [ ] DynamoDB Tabelle erstellt
- [ ] S3 Bucket erstellt
- [ ] Secrets Manager konfiguriert
- [ ] CloudWatch Logs eingerichtet
- [ ] ECS Cluster / Lambda Functions deployed
- [ ] API Domain konfiguriert (z.B. api.stackvertex.com)

---

## 🔧 Setup Steps

### 1. IAM Setup

#### A) CI/CD User (GitHub Actions)

Erstelle IAM User: **`stackvertex-github-actions`**

**Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:PublishVersion"
      ],
      "Resource": "arn:aws:lambda:*:*:function:stackvertex-*"
    }
  ]
}
```

**GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`: Access Key des Users
- `AWS_SECRET_ACCESS_KEY`: Secret Key
- `AWS_REGION`: z.B. `us-east-1`

#### B) Backend Execution Role

Erstelle IAM Role: **`stackvertex-backend-execution-role`**

**Trust Policy (für ECS/Lambda):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["ecs-tasks.amazonaws.com", "lambda.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/stackvertex-*",
        "arn:aws:dynamodb:*:*:table/stackvertex-*/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::stackvertex-*",
        "arn:aws:s3:::stackvertex-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:stackvertex/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/stackvertex/*"
    }
  ]
}
```

---

### 2. DynamoDB Setup

**Tabelle erstellen:**
```bash
aws dynamodb create-table \
  --table-name stackvertex-prod-main \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
    AttributeName=GSI2PK,AttributeType=S \
    AttributeName=GSI2SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    IndexName=GSI2,KeySchema=[{AttributeName=GSI2PK,KeyType=HASH},{AttributeName=GSI2SK,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=StackVertex Key=Environment,Value=Production
```

**Point-in-Time Recovery aktivieren:**
```bash
aws dynamodb update-continuous-backups \
  --table-name stackvertex-prod-main \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

**Encryption aktivieren:**
```bash
aws dynamodb update-table \
  --table-name stackvertex-prod-main \
  --sse-specification Enabled=true,SSEType=KMS
```

---

### 3. S3 Setup

**Bucket erstellen:**
```bash
aws s3api create-bucket \
  --bucket stackvertex-prod-large-items \
  --region us-east-1

aws s3api put-bucket-encryption \
  --bucket stackvertex-prod-large-items \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

aws s3api put-bucket-versioning \
  --bucket stackvertex-prod-large-items \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-lifecycle-configuration \
  --bucket stackvertex-prod-large-items \
  --lifecycle-configuration file://s3-lifecycle.json
```

**s3-lifecycle.json:**
```json
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    },
    {
      "Id": "TransitionToIA",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        }
      ]
    }
  ]
}
```

---

### 4. Secrets Manager Setup

**Secrets erstellen:**

```bash
# JWT Secret Key
aws secretsmanager create-secret \
  --name stackvertex/prod/jwt-secret \
  --description "JWT signing secret for StackVertex Backend" \
  --secret-string "$(openssl rand -base64 32)"

# Stripe Keys
aws secretsmanager create-secret \
  --name stackvertex/prod/stripe-secret-key \
  --description "Stripe API Secret Key" \
  --secret-string "sk_live_..."

aws secretsmanager create-secret \
  --name stackvertex/prod/stripe-webhook-secret \
  --description "Stripe Webhook Signing Secret" \
  --secret-string "whsec_..."

# Sentry DSN (optional)
aws secretsmanager create-secret \
  --name stackvertex/prod/sentry-dsn \
  --description "Sentry Error Tracking DSN" \
  --secret-string "https://...@sentry.io/..."
```

---

### 5. CloudWatch Logs Setup

**Log Group erstellen:**
```bash
aws logs create-log-group \
  --log-group-name /stackvertex/backend

aws logs put-retention-policy \
  --log-group-name /stackvertex/backend \
  --retention-in-days 30
```

---

### 6. ECS Fargate Setup (Option A: Container-based)

#### A) ECR Repository erstellen
```bash
aws ecr create-repository \
  --repository-name stackvertex-backend \
  --image-scanning-configuration scanOnPush=true

aws ecr put-lifecycle-policy \
  --repository-name stackvertex-backend \
  --lifecycle-policy-text file://ecr-lifecycle.json
```

**ecr-lifecycle.json:**
```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
```

#### B) ECS Cluster erstellen
```bash
aws ecs create-cluster \
  --cluster-name stackvertex-prod \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1,base=1
```

#### C) Task Definition
Siehe `backend/ecs-task-definition.json` (wird noch erstellt)

#### D) Service erstellen
```bash
aws ecs create-service \
  --cluster stackvertex-prod \
  --service-name stackvertex-backend \
  --task-definition stackvertex-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

### 7. Lambda Setup (Option B: Serverless)

**Lambda Function erstellen:**
```bash
# Build deployment package first
cd backend
poetry export -f requirements.txt --output requirements.txt
pip install -r requirements.txt -t lambda_package/
cp -r app lambda_package/
cd lambda_package && zip -r ../stackvertex-backend.zip .

# Create Lambda
aws lambda create-function \
  --function-name stackvertex-backend \
  --runtime python3.11 \
  --handler app.lambda_handler.handler \
  --role arn:aws:iam::ACCOUNT_ID:role/stackvertex-backend-execution-role \
  --zip-file fileb://stackvertex-backend.zip \
  --environment Variables="{
    DYNAMODB_TABLE_NAME=stackvertex-prod-main,
    S3_LARGE_ITEMS_BUCKET=stackvertex-prod-large-items,
    AWS_REGION=us-east-1,
    LOG_JSON_FORMAT=true,
    ENABLE_CLOUDWATCH=true,
    ENV=production
  }" \
  --timeout 30 \
  --memory-size 512
```

**API Gateway Integration:**
```bash
aws apigatewayv2 create-api \
  --name stackvertex-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:ACCOUNT_ID:function:stackvertex-backend
```

---

## 🔐 Environment Variables für Backend

**Production (.env):**
```bash
# App
APP_NAME=StackVertex API
DEBUG=false
ENV=production

# Database
DYNAMODB_TABLE_NAME=stackvertex-prod-main
# DYNAMODB_ENDPOINT_URL nicht setzen (use real DynamoDB)

# S3
S3_LARGE_ITEMS_BUCKET=stackvertex-prod-large-items
LARGE_ITEM_THRESHOLD=300000

# AWS
AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID und AWS_SECRET_ACCESS_KEY nicht setzen (use IAM Role)

# Security (from Secrets Manager)
SECRET_KEY=<loaded from Secrets Manager>

# Stripe (from Secrets Manager)
STRIPE_SECRET_KEY=<loaded from Secrets Manager>
STRIPE_WEBHOOK_SECRET=<loaded from Secrets Manager>
STRIPE_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_JSON_FORMAT=true
ENABLE_CLOUDWATCH=true
ENABLE_SENTRY=true
SENTRY_DSN=<loaded from Secrets Manager>

# CORS
CORS_ORIGINS=https://app.stackvertex.com,https://www.stackvertex.com
```

---

## 🚀 Deployment

### Via CI/CD (GitHub Actions)
```bash
# Push to main branch
git push origin main

# GitHub Actions wird automatisch:
# 1. Tests ausführen
# 2. Docker Image bauen
# 3. Image zu ECR pushen
# 4. ECS Service updaten ODER Lambda Function updaten
```

### Manuelles Deployment (ECS)
```bash
# Build & Push Image
docker build -t stackvertex-backend backend/
docker tag stackvertex-backend:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/stackvertex-backend:latest
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/stackvertex-backend:latest

# Update Service
aws ecs update-service \
  --cluster stackvertex-prod \
  --service stackvertex-backend \
  --force-new-deployment
```

### Manuelles Deployment (Lambda)
```bash
# Build & Deploy
cd backend
./scripts/build_lambda.sh
aws lambda update-function-code \
  --function-name stackvertex-backend \
  --zip-file fileb://stackvertex-backend.zip
```

---

## 🔍 Monitoring & Debugging

### CloudWatch Logs
```bash
# Tail logs
aws logs tail /stackvertex/backend --follow

# Query errors
aws logs filter-log-events \
  --log-group-name /stackvertex/backend \
  --filter-pattern "ERROR"
```

### Sentry Dashboard
https://sentry.io/organizations/stackvertex/issues/

### ECS Service Status
```bash
aws ecs describe-services \
  --cluster stackvertex-prod \
  --services stackvertex-backend
```

### Lambda Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=stackvertex-backend \
  --start-time 2026-05-15T00:00:00Z \
  --end-time 2026-05-15T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

---

## 📋 Noch zu erledigen (TODO)

- [ ] **IAM Setup:** CI/CD User + Execution Role erstellen
- [ ] **DynamoDB:** Tabelle `stackvertex-prod-main` erstellen
- [ ] **S3:** Bucket `stackvertex-prod-large-items` erstellen
- [ ] **Secrets Manager:** Alle Secrets (JWT, Stripe, Sentry) hinterlegen
- [ ] **CloudWatch:** Log Group `/stackvertex/backend` erstellen
- [ ] **ECR:** Repository `stackvertex-backend` erstellen
- [ ] **ECS/Lambda:** Deployment-Target wählen und konfigurieren
- [ ] **Domain:** API Domain (z.B. api.stackvertex.com) mit Route53 + ALB/API Gateway
- [ ] **SSL Zertifikat:** ACM Certificate für HTTPS
- [ ] **WAF:** (optional) für zusätzliche Security
- [ ] **Backup:** Automatische DynamoDB Backups konfigurieren

---

## 💡 Best Practices

✅ **Use IAM Roles** statt Access Keys (für ECS/Lambda)  
✅ **Secrets Manager** für alle Credentials  
✅ **Encryption at Rest** für DynamoDB + S3  
✅ **CloudWatch Alarms** für Errors, High Latency, etc.  
✅ **Multi-AZ Deployment** für ECS (mindestens 2 Tasks in unterschiedlichen AZs)  
✅ **Auto Scaling** basierend auf CPU/Memory Usage  
✅ **Blue/Green Deployments** für Zero-Downtime Updates  

---

**Letztes Update:** 2026-05-15
**Autor:** Claude Sonnet 4.5
