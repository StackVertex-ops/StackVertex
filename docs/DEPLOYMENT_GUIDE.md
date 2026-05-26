# StackVertex - Complete Deployment Guide

**Vollautomatisches AWS Deployment via CI/CD mit minimalem manuellen Setup**

---

## 📋 Inhaltsverzeichnis

1. [Auth & Organisation System](#auth--organisation-system)
2. [Data Model & Storage](#data-model--storage)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Terraform Automation](#terraform-automation)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Manuelles Setup (Minimal)](#manuelles-setup-minimal)

---

## 🔐 Auth & Organisation System

### Wie funktioniert Login & Organisations-Management?

**Multi-Tenant Architecture mit Organizations:**

```
┌─────────────┐
│    USER     │  ← Einzelperson (Email/Password Login)
└──────┬──────┘
       │
       │ Member of (1:n)
       │
       ▼
┌─────────────────┐
│  ORGANISATION   │  ← Team/Workspace (wie Slack Workspace)
│                 │
│  • Personal     │  ← Auto-erstellt bei Signup
│  • Team         │  ← Multi-User Organisation
│  • Enterprise   │  ← Mit SLA & Support
└──────┬──────────┘
       │
       │ Owns (1:n)
       │
       ▼
┌──────────────────┐
│  ARCHITECTURES   │  ← Cloud Architecturen
│  DEPLOYMENTS     │  ← Terraform Deployments
│  BILLING         │  ← Stripe Subscriptions
└──────────────────┘
```

### User Registration & Login Flow

**1. User registriert sich:**
```
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "secure123",
  "name": "Max Mustermann"
}
```

**Was passiert automatisch:**
- ✅ User wird erstellt (bcrypt Password Hash)
- ✅ **Personal Organisation** wird auto-erstellt
- ✅ User wird als **Owner** der Organisation hinzugefügt
- ✅ JWT Token wird generiert
- ✅ User ist eingeloggt

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Max Mustermann",
    "status": "active"
  }
}
```

**2. User loggt sich ein:**
```
POST /api/v1/auth/login
{
  "username": "user@example.com",  # OAuth2 nutzt "username" field
  "password": "secure123"
}
```

**Security Features:**
- ✅ Account Lockout nach 5 failed attempts (15 min)
- ✅ Rate Limiting (10 requests/min)
- ✅ JWT Token mit 24h Expiration
- ✅ Password Hashing mit bcrypt (72 byte limit)

**3. Authenticated Requests:**
```
GET /api/v1/architectures
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Organisation Membership

**User kann mehreren Organisationen angehören:**

```python
# User's Organisations abrufen
GET /api/v1/users/{user_id}/organisations

Response:
[
  {
    "id": "org-personal-uuid",
    "name": "Max's Personal Workspace",
    "type": "personal",
    "plan": "free",
    "role": "owner"  # User's Role in dieser Org
  },
  {
    "id": "org-team-uuid",
    "name": "Startup GmbH",
    "type": "team",
    "plan": "pro",
    "role": "member"  # Nur Member, kein Owner
  }
]
```

**Rollen in Organisationen:**
- **Owner:** Volle Rechte (Billing, Members, Delete Org)
- **Admin:** Fast alle Rechte (Members, Architectures)
- **Member:** Nur Architectures erstellen/editieren
- **Viewer:** Read-Only Access

**Organisation wechseln im Frontend:**
```javascript
// User wählt Organisation aus Dropdown
const currentOrg = localStorage.getItem('current_org_id');

// Alle API Calls nutzen diese Org
POST /api/v1/organisations/{currentOrg}/architectures
```

---

## 💾 Data Model & Storage

### Wo liegen die Daten?

**Single Table Design in DynamoDB:**

```
Table: stackvertex-prod-main
├── Users (PK=USER#{id}, SK=METADATA)
├── Organisations (PK=ORG#{id}, SK=METADATA)
├── Memberships (PK=ORG#{id}, SK=USER#{id})
├── Architectures (PK=ARCH#{id}, SK=METADATA)
├── Deployments (PK=DEPLOY#{id}, SK=METADATA)
└── Audit Logs (PK=AUDIT#{year-month}, SK={timestamp}#{id})
```

**GSI Indexes für schnelle Queries:**

**GSI1:** Email Lookup
```
GSI1PK = USER#EMAIL
GSI1SK = {email}
→ Für Login: find user by email
```

**GSI2:** Organisation Membership
```
GSI2PK = USER#{user_id}
GSI2SK = ORG#{org_id}
→ Für: Get all orgs for a user
```

### Storage Tiers

**Kleine Items (<300KB):**
→ Direkt in DynamoDB

**Große Items (>300KB):**
→ Komprimiert in S3 (`stackvertex-prod-large-items`)
→ DynamoDB enthält nur S3 Pointer

**Customer Data (Terraform State, Generated Files):**
→ S3 Bucket: `stackvertex-prod-customer-data-{region}`
→ Verschlüsselt (AES-256 oder KMS)
→ Versioned (30-90 Tage Retention)

**Secrets (API Keys, Stripe Keys, JWT Secret):**
→ AWS Secrets Manager: `stackvertex/prod/*`
→ Encrypted at Rest
→ Rotation policies

### Data Isolation

**Multi-Tenant Data Isolation:**
```
Jede Organisation hat eigenen Namespace:
- Architectures: PK=ARCH#{arch_id}, Owner=ORG#{org_id}
- Deployments: PK=DEPLOY#{deploy_id}, Owner=ORG#{org_id}

Access Control:
1. User JWT → User ID
2. User ID → Organisations (via Membership)
3. Check: Architecture.owner_org_id IN user.organisations
```

**Kunde A kann niemals Daten von Kunde B sehen!**

---

## 🏗️ AWS Infrastructure Setup

### Was wird alles erstellt?

**Terraform erstellt ALLES automatisch:**

#### 1. **Networking** (VPC, Subnets, Security Groups)
```
VPC:
├── Public Subnets (2 AZs)  → ALB, NAT Gateways
├── Private Subnets (2 AZs) → ECS Tasks, Lambda
└── Database Subnets (2 AZs) → RDS Aurora

Security Groups:
├── ALB SG (Port 80, 443)
├── ECS SG (Port 8000 from ALB)
├── Aurora SG (Port 5432 from ECS)
└── Lambda SG (Outbound only)
```

#### 2. **Compute** (ECS Fargate oder Lambda)

**Option A: ECS Fargate (Empfohlen)**
```
ECS Cluster: stackvertex-prod
├── Service: stackvertex-backend
│   ├── Task Definition (2 vCPU, 4GB RAM)
│   ├── Desired Count: 2 (Multi-AZ)
│   ├── Auto Scaling (CPU 70%)
│   └── Health Checks (5 failed → replace)
└── ALB Target Group (Health: /health)
```

**Option B: Lambda (Serverless, aber Cold Starts)**
```
Lambda Functions:
├── stackvertex-api (Python 3.11)
│   ├── Memory: 512 MB
│   ├── Timeout: 30s
│   ├── Provisioned Concurrency: 2
│   └── API Gateway Integration
```

#### 3. **Database** (DynamoDB + Aurora Serverless)

**DynamoDB:**
```
Table: stackvertex-prod-main
├── Billing: PAY_PER_REQUEST (Auto-Scaling)
├── Point-in-Time Recovery: Enabled
├── Encryption: AWS Managed KMS
├── GSI1: Email Lookup
├── GSI2: User→Org Mapping
└── Backups: Continuous (35 Tage)
```

**Aurora Serverless v2 (Optional, für später):**
```
Cluster: stackvertex-prod-aurora
├── Engine: PostgreSQL 15.4
├── Capacity: 0.5 - 4 ACU (Auto-Scaling)
├── Multi-AZ: Yes
├── Encryption: Enabled
└── Backup: 7 Tage Retention
```

#### 4. **Storage** (S3 Buckets)

```
stackvertex-prod-large-items-{region}
├── Versioning: Enabled
├── Encryption: AES-256
├── Lifecycle: Glacier nach 90 Tagen
└── CORS: Configured for Frontend

stackvertex-prod-customer-data-{region}
├── Versioning: Enabled (30 Tage)
├── Encryption: KMS (Customer Managed)
├── Access: Private (AssumeRole only)
└── Lifecycle: Delete nach 365 Tagen

stackvertex-prod-frontend-{region}
├── Static Website Hosting
├── CloudFront Distribution
├── ACM Certificate (HTTPS)
└── Custom Domain (app.stackvertex.com)
```

#### 5. **Security** (IAM, Secrets Manager, WAF)

**IAM Roles:**
```
stackvertex-prod-ecs-execution-role
├── Permissions: ECR Pull, CloudWatch Logs, Secrets Manager
└── Trust: ECS Tasks Service

stackvertex-prod-ecs-task-role
├── Permissions: DynamoDB, S3, Secrets Manager (Read)
└── Trust: ECS Tasks

stackvertex-prod-github-actions-role
├── Permissions: ECR Push, ECS Update, S3 Deploy
└── Trust: GitHub OIDC (No Access Keys!)
```

**Secrets Manager:**
```
stackvertex/prod/jwt-secret
stackvertex/prod/stripe-secret-key
stackvertex/prod/stripe-webhook-secret
stackvertex/prod/sentry-dsn
stackvertex/prod/database-password (wenn Aurora)
```

**WAF (Web Application Firewall):**
```
Rules:
├── Rate Limiting (2000 req/5min per IP)
├── Geo Blocking (nur EU + US)
├── SQL Injection Protection
└── XSS Protection
```

#### 6. **Monitoring** (CloudWatch, Alarms, Logging)

```
CloudWatch Logs:
├── /stackvertex/backend (30 Tage Retention)
├── /stackvertex/ecs-tasks (7 Tage)
└── /stackvertex/alb (30 Tage)

Alarms:
├── ECS CPU > 80% (5 min) → SNS
├── ECS Memory > 90% → SNS
├── ALB 5xx > 10/min → SNS
├── DynamoDB Throttling → SNS
└── API Latency > 2s (p95) → SNS

SNS Topic: stackvertex-prod-alerts
└── Email: alerts@stackvertex.com
```

#### 7. **Frontend** (CloudFront + S3)

```
CloudFront Distribution:
├── Origin: S3 Static Website
├── Default Root: index.html
├── SSL Certificate: ACM
├── Custom Domain: app.stackvertex.com
├── Cache Policy: 24h (HTML), 1 Jahr (Assets)
└── Geo Restriction: None
```

---

## 🤖 Terraform Automation

### Verzeichnisstruktur

```
infrastructure/terraform/
├── bootstrap/              # Einmaliges Setup
│   ├── main.tf            # S3 Backend + DynamoDB Lock Table
│   ├── outputs.tf
│   └── variables.tf
├── modules/
│   ├── networking/        # VPC, Subnets, SGs
│   ├── compute/           # ECS oder Lambda
│   ├── database/          # Aurora Serverless
│   ├── database-dynamodb/ # DynamoDB Tables
│   ├── storage/           # S3 Buckets
│   ├── security/          # IAM, Secrets Manager
│   ├── monitoring/        # CloudWatch, Alarms
│   ├── frontend/          # CloudFront + S3
│   └── cloudfront/        # CDN Distribution
└── environments/
    ├── dev/               # Development
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── terraform.tfvars
    │   └── outputs.tf
    ├── staging/           # Staging (Optional)
    └── prod/              # Production
        ├── main.tf
        ├── variables.tf
        ├── terraform.tfvars (Secrets in GitHub!)
        └── outputs.tf
```

### Terraform Modules

**Jedes Modul ist wiederverwendbar:**

```hcl
# environments/prod/main.tf

module "networking" {
  source = "../../modules/networking"
  
  project_name = "stackvertex"
  environment  = "prod"
  vpc_cidr     = "10.0.0.0/16"
  
  enable_nat_gateway   = true
  enable_vpc_endpoints = true
}

module "database_dynamodb" {
  source = "../../modules/database-dynamodb"
  
  project_name = "stackvertex"
  environment  = "prod"
  
  table_name   = "stackvertex-prod-main"
  billing_mode = "PAY_PER_REQUEST"
  
  enable_pitr       = true
  enable_encryption = true
}

module "compute_ecs" {
  source = "../../modules/compute"
  
  project_name  = "stackvertex"
  environment   = "prod"
  
  vpc_id            = module.networking.vpc_id
  private_subnets   = module.networking.private_subnet_ids
  alb_subnets       = module.networking.public_subnet_ids
  
  container_image   = "${aws_ecr_repository.backend.repository_url}:latest"
  container_port    = 8000
  desired_count     = 2
  cpu               = "2048"
  memory            = "4096"
  
  environment_variables = {
    DYNAMODB_TABLE_NAME = module.database_dynamodb.table_name
    S3_LARGE_ITEMS_BUCKET = module.storage.large_items_bucket_name
    ENV = "production"
  }
  
  secrets = {
    SECRET_KEY = "stackvertex/prod/jwt-secret"
    STRIPE_SECRET_KEY = "stackvertex/prod/stripe-secret-key"
  }
}

module "frontend" {
  source = "../../modules/frontend"
  
  project_name = "stackvertex"
  environment  = "prod"
  
  domain_name = "app.stackvertex.com"
  
  enable_cloudfront = true
  enable_waf        = true
}
```

### Terraform State Management

**Remote State in S3 + DynamoDB Locking:**

```hcl
# environments/prod/backend.tf
terraform {
  backend "s3" {
    bucket         = "stackvertex-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "stackvertex-terraform-locks"
  }
}
```

**Bootstrap Script erstellt State Backend:**
```bash
cd infrastructure/terraform/bootstrap
terraform init
terraform apply  # Erstellt S3 Bucket + DynamoDB Table
```

---

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

**Vollautomatisches Deployment bei Git Push:**

```yaml
# .github/workflows/deploy-production.yml

name: Deploy to Production

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'infrastructure/**'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: stackvertex-backend
  ECS_SERVICE: stackvertex-backend
  ECS_CLUSTER: stackvertex-prod

jobs:
  terraform:
    name: Terraform Plan & Apply
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write  # OIDC Token für AWS
      contents: read
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_GITHUB_ACTIONS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0
      
      - name: Terraform Init
        working-directory: infrastructure/terraform/environments/prod
        run: terraform init
      
      - name: Terraform Plan
        working-directory: infrastructure/terraform/environments/prod
        run: terraform plan -out=tfplan
      
      - name: Terraform Apply
        working-directory: infrastructure/terraform/environments/prod
        run: terraform apply -auto-approve tfplan

  build-and-deploy:
    name: Build & Deploy Backend
    needs: terraform
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write
      contents: read
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_GITHUB_ACTIONS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, Tag, and Push Image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG backend/
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS Service
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service ${{ env.ECS_SERVICE }} \
            --force-new-deployment
      
      - name: Wait for Deployment
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services ${{ env.ECS_SERVICE }}
      
      - name: Verify Deployment
        run: |
          TASK_ARN=$(aws ecs list-tasks \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service-name ${{ env.ECS_SERVICE }} \
            --desired-status RUNNING \
            --query 'taskArns[0]' \
            --output text)
          
          echo "Latest Task: $TASK_ARN"
          
          aws ecs describe-tasks \
            --cluster ${{ env.ECS_CLUSTER }} \
            --tasks $TASK_ARN

  deploy-frontend:
    name: Deploy Frontend
    needs: build-and-deploy
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_GITHUB_ACTIONS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Build Frontend
        working-directory: frontend
        run: npm run build
      
      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist/ s3://stackvertex-prod-frontend-${AWS_REGION}/ \
            --delete \
            --cache-control "public, max-age=31536000, immutable"
      
      - name: Invalidate CloudFront
        run: |
          DISTRIBUTION_ID=$(aws cloudfront list-distributions \
            --query "DistributionList.Items[?Origins.Items[?DomainName=='stackvertex-prod-frontend-${AWS_REGION}.s3.amazonaws.com']].Id" \
            --output text)
          
          aws cloudfront create-invalidation \
            --distribution-id $DISTRIBUTION_ID \
            --paths "/*"

  notify:
    name: Notify Deployment
    needs: [terraform, build-and-deploy, deploy-frontend]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: Deployment Success
        if: ${{ needs.deploy-frontend.result == 'success' }}
        run: |
          echo "🚀 Deployment successful!"
          echo "Backend: https://api.stackvertex.com"
          echo "Frontend: https://app.stackvertex.com"
      
      - name: Deployment Failed
        if: ${{ needs.deploy-frontend.result == 'failure' }}
        run: |
          echo "❌ Deployment failed!"
          exit 1
```

### Secrets in GitHub

**Nur EINE Secret manuell hinzufügen:**

```
GitHub Repository → Settings → Secrets → Actions

Name: AWS_GITHUB_ACTIONS_ROLE_ARN
Value: arn:aws:iam::123456789012:role/stackvertex-github-actions-role
```

**Keine Access Keys! Wir nutzen OIDC (OpenID Connect):**
- ✅ Keine langlebigen Credentials
- ✅ Automatische Rotation
- ✅ AWS vertraut GitHub direkt

---

## 🛠️ Manuelles Setup (Minimal)

**Was muss EINMAL manuell gemacht werden:**

### 1. AWS Account vorbereiten

```bash
# AWS CLI installieren
brew install awscli  # macOS
# oder: curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# AWS Account konfigurieren (mit Admin Credentials)
aws configure
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name: us-east-1
# Default output format: json
```

### 2. Bootstrap Terraform State Backend

```bash
cd infrastructure/terraform/bootstrap

# Terraform initialisieren
terraform init

# State Backend erstellen (S3 + DynamoDB)
terraform apply

# Output:
# ✅ S3 Bucket: stackvertex-terraform-state
# ✅ DynamoDB Table: stackvertex-terraform-locks
```

### 3. IAM Role für GitHub Actions erstellen

```bash
cd infrastructure/terraform/github-actions

# Erstellt OIDC Provider + IAM Role
terraform init
terraform apply

# Output:
# ✅ Role ARN: arn:aws:iam::123456789012:role/stackvertex-github-actions-role

# Kopiere ARN und füge in GitHub Secrets ein!
```

### 4. Domain & SSL Certificate (Optional)

```bash
# Domain in Route53 registrieren
aws route53 create-hosted-zone --name stackvertex.com

# SSL Certificate in ACM anfordern
aws acm request-certificate \
  --domain-name stackvertex.com \
  --subject-alternative-names *.stackvertex.com \
  --validation-method DNS

# DNS Validation Records in Route53 hinzufügen
# (Terraform Module macht das automatisch)
```

### 5. Secrets in AWS Secrets Manager

```bash
# JWT Secret
aws secretsmanager create-secret \
  --name stackvertex/prod/jwt-secret \
  --secret-string "$(openssl rand -base64 32)"

# Stripe Keys
aws secretsmanager create-secret \
  --name stackvertex/prod/stripe-secret-key \
  --secret-string "sk_live_..."

aws secretsmanager create-secret \
  --name stackvertex/prod/stripe-webhook-secret \
  --secret-string "whsec_..."
```

### 6. GitHub Secrets konfigurieren

```
GitHub Repository → Settings → Secrets → Actions

Secrets:
├── AWS_GITHUB_ACTIONS_ROLE_ARN (arn:aws:iam::...)
└── (Alle anderen Secrets sind in AWS Secrets Manager!)
```

### 7. Ersten Deployment triggern

```bash
# Code pushen
git add .
git commit -m "Initial infrastructure setup"
git push origin main

# GitHub Actions deployed automatisch:
# 1. Terraform Apply (VPC, ECS, DynamoDB, S3, etc.)
# 2. Docker Build & Push zu ECR
# 3. ECS Service Update
# 4. Frontend Deploy zu S3 + CloudFront

# Nach ~10 Minuten:
# ✅ Backend: https://api.stackvertex.com
# ✅ Frontend: https://app.stackvertex.com
```

---

## 📊 Zusammenfassung

### Was ist automatisiert?

**100% Infrastructure as Code:**
- ✅ VPC, Subnets, Security Groups
- ✅ ECS Cluster, Service, Task Definition
- ✅ DynamoDB Table mit GSI
- ✅ S3 Buckets (3x)
- ✅ IAM Roles & Policies
- ✅ CloudWatch Logs & Alarms
- ✅ CloudFront Distribution
- ✅ ACM Certificate
- ✅ Route53 DNS Records

**Deployment Pipeline:**
- ✅ Terraform Plan & Apply
- ✅ Docker Build & Push
- ✅ ECS Service Update
- ✅ Frontend S3 Sync
- ✅ CloudFront Invalidation
- ✅ Health Checks

### Was muss manuell gemacht werden?

**Nur 3 Dinge (einmalig):**
1. AWS Account Setup + CLI Config (5 min)
2. Terraform Bootstrap (2 min)
3. GitHub Secret hinzufügen (1 min)

**Gesamt: ~10 Minuten Setup → dann ALLES automatisch! 🚀**

### Kosten Schätzung

**Development/Staging (min):**
- ECS Fargate: 2 Tasks × 0.5 vCPU × $0.04/h = ~$30/Monat
- DynamoDB: Pay-per-request = ~$5/Monat (low traffic)
- S3: 10 GB = ~$0.23/Monat
- CloudWatch: ~$5/Monat
- **Total: ~$40-50/Monat**

**Production (empfohlen):**
- ECS Fargate: 2 Tasks × 2 vCPU × $0.04/h = ~$120/Monat
- DynamoDB: ~$50/Monat (moderate traffic)
- S3: 50 GB = ~$1.15/Monat
- CloudFront: 100 GB Transfer = ~$8.50/Monat
- Aurora Serverless (optional): ~$100-200/Monat
- **Total: ~$180-380/Monat**

---

---

## 💳 Billing & Voucher System Deployment

### Voucher-System Setup

**DynamoDB GSI erstellen (für Voucher-Listing):**

Vouchers nutzen einen Global Secondary Index für schnelles Listing:

```hcl
# infrastructure/terraform/modules/database/dynamodb.tf

resource "aws_dynamodb_table" "main" {
  name           = "stackvertex-${var.environment}-main"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"
  
  # ... existing attributes ...
  
  # GSI für Voucher-Listing
  global_secondary_index {
    name               = "GSI1"
    hash_key           = "GSI1PK"
    range_key          = "GSI1SK"
    projection_type    = "ALL"
  }
}
```

**Terraform Apply:**

```bash
cd infrastructure/terraform/environments/prod
terraform plan   # Prüfen
terraform apply  # GSI wird erstellt (~5 Minuten)
```

**Wichtig:** GSI-Erstellung dauert einige Minuten. Warte bis Status = `ACTIVE`.

**Prüfen:**
```bash
aws dynamodb describe-table \
  --table-name stackvertex-prod-main \
  --query "Table.GlobalSecondaryIndexes[?IndexName=='GSI1'].IndexStatus" \
  --output text
# Output: ACTIVE (✅ Ready)
```

### Stripe Integration (Optional für MVP)

**Stripe Secrets in AWS Secrets Manager:**

```bash
# Stripe API Keys (von Stripe Dashboard)
aws secretsmanager create-secret \
  --name stackvertex-prod-stripe-secret-key \
  --secret-string "sk_live_xyz..."

aws secretsmanager create-secret \
  --name stackvertex-prod-stripe-webhook-secret \
  --secret-string "whsec_xyz..."
```

**Environment Variables (ECS Task Definition):**

```json
{
  "environment": [
    {"name": "STRIPE_SECRET_KEY", "value": "from-secrets-manager"},
    {"name": "STRIPE_WEBHOOK_SECRET", "value": "from-secrets-manager"},
    {"name": "STRIPE_PRICE_STARTER", "value": "price_xyz..."},
    {"name": "STRIPE_PRICE_PRO", "value": "price_abc..."},
    {"name": "STRIPE_PRICE_ENTERPRISE", "value": "price_def..."}
  ]
}
```

**Stripe Products & Prices erstellen:**

```bash
# STARTER Plan
stripe prices create \
  --product prod_starter \
  --unit_amount 1000 \
  --currency eur \
  --recurring interval=month

# PRO Plan
stripe prices create \
  --product prod_pro \
  --unit_amount 5000 \
  --currency eur \
  --recurring interval=month

# ENTERPRISE Plan
stripe prices create \
  --product prod_enterprise \
  --unit_amount 25000 \
  --currency eur \
  --recurring interval=month
```

**Webhook Endpoint registrieren:**

```bash
# In Stripe Dashboard: Developers → Webhooks → Add Endpoint
# URL: https://api.stackvertex.com/api/v1/webhooks/stripe
# Events:
#   - customer.subscription.created
#   - customer.subscription.updated
#   - customer.subscription.deleted
#   - invoice.payment_succeeded
#   - invoice.payment_failed
```

### Admin UI freischalten

**SuperAdmin User erstellen:**

```bash
# Via Backend API (nach Deployment)
curl -X POST https://api.stackvertex.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@stackvertex.com",
    "password": "secure-password-here",
    "name": "SuperAdmin"
  }'

# User ID aus Response notieren
# → USER_ID="uuid-hier"

# Manuell SuperAdmin-Rolle setzen (via DynamoDB Console oder Script)
aws dynamodb update-item \
  --table-name stackvertex-prod-main \
  --key '{"PK": {"S": "USER#'$USER_ID'"}, "SK": {"S": "METADATA"}}' \
  --update-expression "SET system_role = :role" \
  --expression-attribute-values '{":role": {"S": "superadmin"}}'
```

**Admin-Dashboard Access:**

```bash
# Login als SuperAdmin
# → Frontend: https://app.stackvertex.com/admin-vouchers.html
# → Vouchers erstellen, verwalten, Stats einsehen
```

### Deployment-Reihenfolge

**1. Database Migration (DynamoDB GSI):**
```bash
cd infrastructure/terraform/environments/prod
terraform apply  # GSI1 erstellen
```

**2. Backend Deployment (mit Voucher API):**
```bash
git push origin main  # CI/CD deployed automatisch
# → Backend inkl. Voucher-Endpoints wird deployed
```

**3. Frontend Deployment (Billing & Admin UI):**
```bash
# Bereits in CI/CD enthalten
# → Pricing-Page, Billing-Page, Admin-Vouchers-Page werden deployed
```

**4. SuperAdmin User erstellen:**
```bash
# Via API (siehe oben)
# → Manuell system_role = superadmin setzen
```

**5. Test:**
```bash
# Pricing-Page öffnen
curl https://app.stackvertex.com/pricing.html
# → Tiers anzeigen, Kostenrechner testen

# Voucher erstellen (als SuperAdmin)
curl -X POST https://api.stackvertex.com/api/v1/admin/vouchers \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "LAUNCH100",
    "discount_type": "percentage",
    "discount_value": 100,
    "applies_to": "both",
    "max_uses": 100,
    "valid_until": "2026-12-31T23:59:59Z"
  }'

# Voucher validieren (als normaler User)
curl -X POST https://api.stackvertex.com/api/v1/voucher/validate \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "LAUNCH100"}'
# → {"valid": true, "discount_value": 100, ...}
```

### Monitoring

**CloudWatch Dashboards erstellen:**

```hcl
# infrastructure/terraform/modules/monitoring/cloudwatch_dashboard.tf

resource "aws_cloudwatch_dashboard" "vouchers" {
  dashboard_name = "stackvertex-vouchers-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title = "Voucher Redemptions"
          metrics = [
            ["StackVertex/Vouchers", "VoucherRedemptions", { stat = "Sum" }]
          ]
        }
      },
      {
        type = "metric"
        properties = {
          title = "Total Discount (EUR)"
          metrics = [
            ["StackVertex/Billing", "VoucherDiscount", { stat = "Sum" }]
          ]
        }
      }
    ]
  })
}
```

**Alarms für High Usage:**

```hcl
resource "aws_cloudwatch_metric_alarm" "high_voucher_usage" {
  alarm_name          = "stackvertex-high-voucher-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "VoucherRedemptions"
  namespace           = "StackVertex/Vouchers"
  period              = 3600  # 1 hour
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "Alert when >50 voucher redemptions per hour"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### Troubleshooting

**Problem: Voucher API gibt 500 Error**

```bash
# Check Backend Logs
aws logs tail /ecs/stackvertex-backend-prod --follow

# Häufige Ursache: DynamoDB GSI nicht vorhanden
aws dynamodb describe-table \
  --table-name stackvertex-prod-main \
  --query "Table.GlobalSecondaryIndexes[?IndexName=='GSI1']"
```

**Problem: SuperAdmin kann keine Vouchers erstellen**

```bash
# Check system_role
aws dynamodb get-item \
  --table-name stackvertex-prod-main \
  --key '{"PK": {"S": "USER#'$USER_ID'"}, "SK": {"S": "METADATA"}}' \
  --query "Item.system_role.S"
# Output: superadmin (erwartet)
```

**Problem: Voucher-Rabatt nicht in Invoice**

```bash
# Check Subscription hat voucher_code
aws dynamodb query \
  --table-name stackvertex-prod-main \
  --key-condition-expression "PK = :pk AND SK = :sk" \
  --expression-attribute-values '{
    ":pk": {"S": "ORG#'$ORG_ID'"},
    ":sk": {"S": "SUBSCRIPTION"}
  }' \
  --query "Items[0].voucher_code.S"
# Output: FRIEND2026 (erwartet)
```

---

**Nächste Schritte:**
1. Bootstrap ausführen (`terraform apply` in bootstrap/)
2. GitHub Secret setzen
3. Code pushen → CI/CD deployed automatisch
4. Nach 10 Minuten: App ist live! 🎉
5. **NEU:** SuperAdmin erstellen + Gutscheinsystem testen

Bei Fragen: Schau in `docs/AWS_SETUP.md`, `docs/billing-system.md`, `VOUCHER_SYSTEM.md` oder frag mich!
