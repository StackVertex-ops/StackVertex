# StackVertex Infrastructure

Komplette AWS Serverless Infrastruktur für StackVertex - gebaut mit Terraform.

## Architektur Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Internet / Users                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  API Gateway    │
                    │  - HTTP API     │
                    │  - WebSocket    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Lambda         │
                    │  - FastAPI      │
                    │  - Container    │
                    └───┬─────────┬───┘
                        │         │
            ┌───────────┘         └────────────┐
            │                                   │
    ┌───────▼────────┐                 ┌───────▼────────┐
    │   Aurora       │                 │   S3 Buckets   │
    │ Serverless v2  │                 │ - Customer Data│
    │ (PostgreSQL)   │                 │ - Deployments  │
    └────────────────┘                 │ - Terraform    │
                                       └────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Security                             │
│                                                                      │
│  CloudWatch      CloudTrail      GuardDuty      Security Hub        │
│  - Metrics       - API Audit     - Threats      - Compliance        │
│  - Logs          - S3 Events     - Findings     - CIS/AWS FBS       │
│  - Alarms        - Lambda Calls  - Alerts       - Score             │
│  - Dashboard                                                         │
│                                                                      │
│                    ↓ Alerts ↓                                        │
│              SNS → Email + Slack                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Struktur

```
infrastructure/
├── terraform/
│   ├── bootstrap/              # Terraform State Backend (S3 + DynamoDB)
│   ├── modules/                # Wiederverwendbare Module
│   │   ├── networking/         # VPC, Subnets, Security Groups
│   │   ├── database/           # Aurora Serverless v2
│   │   ├── compute/            # Lambda + API Gateway
│   │   ├── storage/            # S3 Buckets (Customer Data, Deployments)
│   │   ├── monitoring/         # CloudWatch, Alarms, SNS
│   │   └── security/           # CloudTrail, GuardDuty, Security Hub
│   └── environments/           # Environment-spezifische Configs
│       ├── dev/                # Development
│       ├── staging/            # Staging (planned)
│       └── prod/               # Production (planned)
└── scripts/
    └── bootstrap.sh            # Automatisches Bootstrap Setup
```

## Module Details

### 1. Networking (`modules/networking/`)

**Erstellt:**
- VPC mit Public + Private Subnets (2 AZs)
- Internet Gateway
- NAT Gateway (optional, für private subnets)
- Route Tables
- Security Groups für Lambda, Aurora, Redis
- VPC Endpoints (S3, optional andere)

**Outputs:**
- VPC ID
- Subnet IDs (public/private)
- Security Group IDs

**Kosten:** ~$0-32/Monat (NAT Gateway wenn aktiviert)

---

### 2. Database (`modules/database/`)

**Erstellt:**
- Aurora Serverless v2 Cluster (PostgreSQL 15.4)
- DB Subnet Group
- Secrets Manager Secret (DB Credentials)
- CloudWatch Alarms (CPU, Connections, Storage)

**Features:**
- Auto-Scaling: 0.5-16 ACUs
- Backup Retention: 3-35 Tage
- Encryption at rest (AES256)
- Multi-AZ (prod only)
- Performance Insights (optional)

**Outputs:**
- Database Endpoint
- Secret ARN
- Connection String

**Kosten:** ~$43-350/Monat (je nach ACU Usage)

---

### 3. Compute (`modules/compute/`)

**Erstellt:**
- Lambda Function (Container Image)
- ECR Repository
- API Gateway HTTP API
- API Gateway WebSocket API (optional)
- Lambda Function URL (optional)
- IAM Roles & Policies
- CloudWatch Log Groups
- CloudWatch Alarms

**Features:**
- Docker-based Deployment
- VPC Integration
- Environment Variables (DB, S3, etc.)
- Auto-scaling
- Image Lifecycle Policy (keep last 5)

**Outputs:**
- Lambda Function Name/ARN
- ECR Repository URL
- API Endpoints (HTTP + WebSocket)

**Kosten:** ~$5-30/Monat (je nach Invocations)

---

### 4. Storage (`modules/storage/`)

**Erstellt 4 S3 Buckets:**

1. **Deployment States Bucket**
   - Terraform State Files von Customer Deployments
   - Versioning, Encryption
   - Lifecycle: 30d → IA, 90d → Glacier, 730d → Delete

2. **Customer Data Bucket**
   - Application Data der Kunden (Files, Backups, Assets)
   - Versioning (optional)
   - Encryption (AES256 oder KMS)
   - Lifecycle: 30d → IA, 90d → Intelligent-Tiering
   - CORS Support (optional)
   - Bucket Policy: Nur Lambda Zugriff

3. **Terraform Workspaces Bucket** (optional)
   - Temporäre Files während Deployment
   - Auto-delete nach 7 Tagen

4. **Lambda Code Bucket**
   - Metadata für Lambda Deployments
   - Versioning

**Outputs:**
- Bucket IDs/ARNs
- KMS Key (wenn erstellt)

**Kosten:** ~$2-10/Monat (je nach Storage)

---

### 5. Monitoring (`modules/monitoring/`)

**Erstellt:**
- CloudWatch Dashboard (Gesamtübersicht)
- SNS Topics (3 Severity Levels)
- Email/Slack Subscriptions
- CloudWatch Alarms (11 Alarms):
  - Lambda: Errors, Throttles, Duration
  - API Gateway: 4XX, 5XX, Latency
  - Aurora: CPU, Connections, Storage
  - Security: Deployment Failures, Unauthorized Access
- Log Metric Filters (Custom Metrics)
- Saved Insights Queries
- Composite Alarm (System Health)

**Alert Levels:**
- **Critical:** Sofort handeln (Email + Slack)
- **Warning:** Untersuchen (Email)
- **Info:** FYI (Email)

**Outputs:**
- SNS Topic ARNs
- Dashboard URL
- Alarm Names

**Kosten:** ~$34/Monat (dev), ~$100/Monat (prod)

---

### 6. Security (`modules/security/`)

**Erstellt:**
- CloudTrail (API Audit)
  - Alle AWS API Calls
  - S3 Data Events
  - Lambda Invocations
  - CloudWatch Integration
- GuardDuty (Threat Detection)
  - S3 Protection
  - High/Critical → SNS Alert
- Security Hub (Compliance)
  - CIS AWS Foundations Benchmark
  - AWS Foundational Security Best Practices
  - Critical/High Findings → SNS Alert
- Security Metric Filters:
  - Root Account Usage
  - Unauthorized API Calls
  - IAM Policy Changes
  - S3 Bucket Policy Changes

**Outputs:**
- CloudTrail Name/ARN
- GuardDuty Detector ID
- Security Hub ARN
- Security Console URLs

**Kosten:** ~$30/Monat (dev), ~$65/Monat (prod)

---

## Environments

### Dev (`environments/dev/`)

**Ziel:** Entwicklung, Testing

**Konfiguration:**
- VPC CIDR: 10.0.0.0/16
- Aurora: 0.5-1 ACU
- Kein NAT Gateway
- 7 Tage Log Retention
- 90 Tage Deployment Retention
- Keine Alarms per default
- Security Hub optional

**Kosten:** ~$80-120/Monat

**Deploy:**
```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
```

---

### Staging (`environments/staging/`) - GEPLANT

**Ziel:** Pre-Production Testing

**Konfiguration:**
- Aurora: 1-4 ACU
- NAT Gateway optional
- 30 Tage Log Retention
- 365 Tage Deployment Retention
- Alarms aktiv
- Security Hub aktiv

**Kosten:** ~$200/Monat

---

### Prod (`environments/prod/`) - GEPLANT

**Ziel:** Production

**Konfiguration:**
- Aurora: 2-16 ACU (Multi-AZ)
- NAT Gateway + VPC Endpoints
- 90 Tage Log Retention
- 730 Tage Deployment Retention
- Alle Alarms aktiv
- Security Hub aktiv
- Performance Insights aktiv
- GuardDuty 15-Minuten Frequency
- Final Snapshot bei Destroy

**Kosten:** ~$500-700/Monat

---

## Deployment Prozess

### 1. Bootstrap (Einmalig)

Erstellt Terraform State Backend:

```bash
cd scripts
./bootstrap.sh
```

**Erstellt:**
- S3 Bucket für Terraform State
- DynamoDB Table für State Locking
- S3 Bucket für Deployment States
- Backend Config Files für alle Environments

---

### 2. Environment Deployment

```bash
cd terraform/environments/dev

# 1. Configure Variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # DB Password, Alert Emails, etc.

# 2. Initialize
terraform init

# 3. Plan
terraform plan -out=tfplan

# 4. Apply
terraform apply tfplan
```

**Dauer:** ~10-15 Minuten (Aurora Cluster)

---

### 3. Docker Image Deploy

```bash
# ECR Login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin <ECR_URL>

# Build
cd backend
docker build -f Dockerfile.lambda -t stackvertex-dev-lambda .

# Tag & Push
docker tag stackvertex-dev-lambda:latest <ECR_URL>:latest
docker push <ECR_URL>:latest

# Update Lambda
aws lambda update-function-code \
  --function-name stackvertex-dev-api \
  --image-uri <ECR_URL>:latest
```

---

### 4. Database Migrations

```bash
# Get DB Credentials
aws secretsmanager get-secret-value \
  --secret-id stackvertex-dev-db-credentials

# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/stackvertex"

# Run Migrations
cd backend
poetry run alembic upgrade head
```

---

## CI/CD Pipeline

GitHub Actions Workflow (`.github/workflows/deploy.yml`):

**Trigger:**
- Push auf `main` → Deploy **prod**
- Push auf `develop` → Deploy **dev**
- Pull Request → Terraform Plan
- Manual Dispatch → Deploy/Destroy any environment

**Jobs:**
1. **test** - Pytest (80%+ coverage required)
2. **build** - Docker Image → ECR
3. **terraform-plan** - Show changes (PRs)
4. **terraform-apply** - Deploy infrastructure
5. **terraform-destroy** - Destroy (manual only)

**GitHub Secrets erforderlich:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_MASTER_USERNAME`
- `DB_MASTER_PASSWORD`
- `TERRAFORM_STATE_BUCKET`

---

## Monitoring & Alerts

### CloudWatch Dashboard

```bash
# URL nach Deployment
terraform output cloudwatch_dashboard_url

# Oder manuell
open "https://console.aws.amazon.com/cloudwatch/home?region=eu-central-1#dashboards:name=stackvertex-dev-overview"
```

**Enthält:**
- Lambda: Invocations, Errors, Duration, Throttles
- API Gateway: Requests, 4XX/5XX, Latency
- Aurora: CPU, Connections, ACUs, Read/Write Latency
- S3: Storage Size, Object Count
- Error Rate: Errors / Invocations

---

### Alerts Konfigurieren

**terraform.tfvars:**
```hcl
alert_emails = [
  "admin@company.com",
  "ops-team@company.com"
]

slack_webhook_url = "https://hooks.slack.com/services/..."
```

**Nach Apply:**
- Confirmation Email für jede Adresse
- Klick auf Link zum Bestätigen
- Dann: Alerts werden zugestellt

---

### Alert Severity

**Critical (Rot):**
- Lambda Errors > 10
- API 5XX Errors > 5
- Aurora CPU > 80%
- Deployment Failures > 3
- Root Account Usage
- GuardDuty High/Critical

**Warning (Gelb):**
- Lambda Duration > 80% timeout
- API 4XX Errors > 50
- API Latency > 2s
- Aurora Connections > 80%
- IAM/S3 Policy Changes

**Info (Blau):**
- Alarm Recovery
- System Events

---

## Security Monitoring

### CloudTrail

**Alle API Calls werden geloggt:**
```bash
# Console
terraform output security_monitoring_urls
# → cloudtrail: https://...

# Query Events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutBucketPolicy
```

---

### GuardDuty

**Automatische Threat Detection:**
```bash
# Console
terraform output security_monitoring_urls
# → guardduty: https://...

# Findings
aws guardduty list-findings \
  --detector-id <DETECTOR_ID>
```

**High/Critical Findings → SNS Alert**

---

### Security Hub

**Compliance Dashboard:**
```bash
# Console
terraform output security_monitoring_urls
# → security_hub: https://...
```

**Standards:**
- CIS AWS Foundations Benchmark
- AWS Foundational Security Best Practices

**Critical/High Findings → SNS Alert**

---

## Kosten Übersicht

### Dev Environment (~$120/Monat)

| Service | Kosten/Monat |
|---------|--------------|
| Aurora Serverless v2 (0.5-1 ACU) | $43 |
| Lambda (5k req/Tag) | $5 |
| API Gateway | $1 |
| S3 (10 GB) | $2 |
| CloudWatch (Logs + Metrics + Alarms) | $34 |
| CloudTrail | $2 |
| GuardDuty | $10 |
| Security Hub (optional) | $10 |
| VPC (kein NAT) | $0 |
| **TOTAL** | **~$107/Monat** |

---

### Production Environment (~$600/Monat)

| Service | Kosten/Monat |
|---------|--------------|
| Aurora Serverless v2 (2-16 ACU, Multi-AZ) | $350 |
| Lambda (50k req/Tag, 1GB) | $30 |
| API Gateway | $5 |
| S3 (100 GB) | $10 |
| CloudWatch | $165 |
| CloudTrail | $20 |
| GuardDuty | $20 |
| Security Hub | $10 |
| NAT Gateway | $32 |
| VPC Endpoints | $15 |
| **TOTAL** | **~$657/Monat** |

---

## Troubleshooting

### Error: Backend initialization failed

**Problem:** Terraform State Backend existiert nicht

**Lösung:**
```bash
cd scripts
./bootstrap.sh
```

---

### Error: Database password too short

**Problem:** Password < 16 Zeichen

**Lösung:**
```bash
# Generate strong password
openssl rand -base64 24

# In terraform.tfvars
db_master_password = "<GENERATED_PASSWORD>"
```

---

### Error: Lambda Cold Start Timeout

**Problem:** Lambda in VPC hat langsamen Cold Start

**Lösungen:**
1. Lambda Timeout erhöhen (60s)
2. Provisioned Concurrency aktivieren
3. VPC Endpoints nutzen (reduziert Latency)

---

### Error: Terraform State Locked

**Problem:** Vorheriger Run wurde abgebrochen

**Lösung:**
```bash
terraform force-unlock <LOCK_ID>
```

---

## Wichtige Befehle

```bash
# Deployment Status
terraform output deployment_summary

# Dashboard öffnen
open $(terraform output -raw cloudwatch_dashboard_url)

# Lambda Logs live
aws logs tail /aws/lambda/stackvertex-dev-api --follow

# Database Connection Test
psql -h $(terraform output -raw database_endpoint) -U stackvertex_admin -d stackvertex

# Cost Report
aws ce get-cost-and-usage \
  --time-period Start=2026-04-01,End=2026-04-18 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"

# Security Findings
aws guardduty list-findings --detector-id <ID>
aws securityhub get-findings --filters 'ComplianceStatus=[{Value=FAILED}]'
```

---

## Weitere Dokumentation

- [AWS Deployment Guide](../docs/deployment/AWS_DEPLOYMENT.md)
- [Monitoring & Security Guide](../docs/operations/MONITORING_SECURITY.md)
- [GitHub Actions Setup](../.github/workflows/README.md)
- [Bootstrap Script](./scripts/README.md)
- [Environment Setup](./terraform/environments/README.md)

---

## Support

**Issues:** https://github.com/YOUR_ORG/stackvertex/issues

**Slack:** #stackvertex-ops

**Email:** ops@company.com

---

## License

Proprietary - StackVertex Internal
