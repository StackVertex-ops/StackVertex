# OverCloud Terraform Environments

Dieses Directory enthält die Terraform-Konfigurationen für alle OverCloud-Umgebungen.

## Übersicht

```
environments/
├── dev/           # Development environment (minimal resources)
├── staging/       # Staging environment (production-like)
└── prod/          # Production environment (high availability)
```

## Voraussetzungen

1. **Bootstrap** muss bereits gelaufen sein:
   ```bash
   cd ../bootstrap
   ./../../scripts/bootstrap.sh
   ```

2. **AWS CLI** konfiguriert mit den richtigen Credentials:
   ```bash
   aws sts get-caller-identity
   ```

3. **Terraform** >= 1.5.0 installiert

## Deployment-Prozess

### 1. Backend-Konfiguration prüfen

Nach dem Bootstrap sollte `backend.tf` automatisch erstellt worden sein:

```hcl
# backend.tf (auto-generated)
terraform {
  backend "s3" {
    bucket         = "overcloud-terraform-state-123456789012"
    key            = "environments/dev/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "overcloud-terraform-locks"
  }
}
```

Falls nicht vorhanden, erstelle sie manuell aus der Bootstrap-Output.

### 2. Variables konfigurieren

```bash
cd dev/  # oder staging/prod

# Kopiere Example-Datei
cp terraform.tfvars.example terraform.tfvars

# Editiere terraform.tfvars
vim terraform.tfvars
```

**Wichtig:**
- `db_master_password`: Min. 16 Zeichen, sicher generieren!
- `terraform_state_bucket`: Aus Bootstrap-Output kopieren

### 3. Terraform Init

```bash
terraform init
```

Dies:
- Lädt Provider (AWS)
- Konfiguriert S3 Backend
- Erstellt DynamoDB Lock Entry

### 4. Terraform Plan

```bash
terraform plan -out=tfplan
```

Prüfe den Plan sorgfältig:
- VPC + Subnets werden erstellt
- Aurora Serverless v2 Cluster (ca. $43/Monat für dev)
- Lambda Function + API Gateway
- S3 Buckets

### 5. Terraform Apply

```bash
terraform apply tfplan
```

**Dauer:** 10-15 Minuten (Aurora braucht am längsten)

### 6. Outputs anzeigen

```bash
terraform output deployment_summary
```

Beispiel Output:
```
✅ OverCloud Dev Environment Deployed!

🌐 API Endpoint:       https://abc123.execute-api.eu-central-1.amazonaws.com/
🔌 WebSocket Endpoint: wss://xyz789.execute-api.eu-central-1.amazonaws.com/dev

📦 ECR Repository:     123456789012.dkr.ecr.eu-central-1.amazonaws.com/overcloud-dev-lambda
🗄️  Deployment Bucket:  overcloud-dev-deployment-states-123456789012

💾 Database Endpoint:  overcloud-dev-aurora.cluster-abc.eu-central-1.rds.amazonaws.com
🔐 Database Secret:    arn:aws:secretsmanager:eu-central-1:123:secret:overcloud-dev-db...

📋 Next Steps:
1. Build & push Docker image to ECR
2. Update Lambda function with new image
3. Run database migrations (alembic upgrade head)
4. Test API endpoint
```

## Post-Deployment

### Docker Image bauen & deployen

```bash
# AWS ECR Login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com

# Build Image
cd ../../../../backend
docker build -t overcloud-dev-lambda .

# Tag & Push
docker tag overcloud-dev-lambda:latest \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com/overcloud-dev-lambda:latest

docker push \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com/overcloud-dev-lambda:latest

# Update Lambda
aws lambda update-function-code \
  --function-name overcloud-dev-api \
  --image-uri 123456789012.dkr.ecr.eu-central-1.amazonaws.com/overcloud-dev-lambda:latest
```

### Datenbank-Migrationen ausführen

Option A: Lokal (mit Database Secret):
```bash
# Secret holen
aws secretsmanager get-secret-value \
  --secret-id overcloud-dev-db-credentials \
  --query SecretString --output text | jq .

# DATABASE_URL setzen
export DATABASE_URL="postgresql://user:pass@host:5432/overcloud"

# Alembic Migration
cd backend
poetry run alembic upgrade head
```

Option B: Via Lambda (empfohlen):
- Create `/admin/migrate` endpoint in FastAPI
- Trigger via API call (mit Admin-Auth)

### API testen

```bash
# Health Check
curl https://abc123.execute-api.eu-central-1.amazonaws.com/health

# API Docs
open https://abc123.execute-api.eu-central-1.amazonaws.com/api/docs
```

## Environments im Detail

### Dev
- **Zweck:** Entwicklung, Testing
- **Kosten:** ~$50-80/Monat
- **Features:**
  - Aurora Serverless v2: 0.5-1 ACU
  - Kein NAT Gateway (Lambda ohne VPC internet access)
  - 7 Tage Log Retention
  - 90 Tage Deployment Retention
  - Keine CloudWatch Alarms
  - Skip Final Snapshot bei Destroy

### Staging
- **Zweck:** Pre-Production Testing
- **Kosten:** ~$150-200/Monat
- **Features:**
  - Aurora Serverless v2: 1-4 ACU
  - NAT Gateway (wenn nötig)
  - 30 Tage Log Retention
  - 365 Tage Deployment Retention
  - CloudWatch Alarms aktiv
  - Final Snapshot bei Destroy

### Prod
- **Zweck:** Production
- **Kosten:** ~$300-500/Monat
- **Features:**
  - Aurora Serverless v2: 2-16 ACU (Multi-AZ)
  - NAT Gateway + VPC Endpoints
  - 90 Tage Log Retention
  - 730 Tage Deployment Retention
  - Alle CloudWatch Alarms + SNS
  - Performance Insights aktiv
  - Final Snapshot + 35 Tage Backup Retention

## State Management

### State-Datei Location
```
s3://overcloud-terraform-state-123456789012/
└── environments/
    ├── dev/terraform.tfstate
    ├── staging/terraform.tfstate
    └── prod/terraform.tfstate
```

### State Locks
DynamoDB Table: `overcloud-terraform-locks`

Bei `terraform plan/apply` wird automatisch ein Lock erstellt.

**Stuck Lock?**
```bash
terraform force-unlock <LOCK_ID>
```

### State Backup
S3 Versioning ist aktiv → alte Versionen werden gespeichert.

**Rollback zu alter Version:**
```bash
# Liste Versionen
aws s3api list-object-versions \
  --bucket overcloud-terraform-state-123456789012 \
  --prefix environments/dev/terraform.tfstate

# Download alte Version
aws s3api get-object \
  --bucket overcloud-terraform-state-123456789012 \
  --key environments/dev/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup

# Restore
mv terraform.tfstate.backup terraform.tfstate
terraform state push terraform.tfstate
```

## Troubleshooting

### Error: Backend-Initialisierung fehlgeschlagen
**Ursache:** Backend noch nicht erstellt
**Lösung:** Bootstrap ausführen (`../../scripts/bootstrap.sh`)

### Error: Insufficient IAM permissions
**Ursache:** AWS Credentials haben nicht genug Rechte
**Lösung:** Prüfe IAM-Rolle, benötigt werden: EC2, VPC, RDS, Lambda, S3, Secrets Manager

### Error: Aurora Serverless v2 not available in region
**Ursache:** Aurora Serverless v2 ist nicht in allen Regionen verfügbar
**Lösung:** Nutze `eu-central-1`, `us-east-1`, oder `us-west-2`

### Error: Database password too short
**Ursache:** Passwort < 16 Zeichen
**Lösung:** Generiere starkes Passwort (z.B. `openssl rand -base64 24`)

### Lambda Cold Start Issues
**Ursache:** Lambda in VPC hat langsamen Cold Start
**Lösung:**
- Provisioned Concurrency aktivieren (kostet extra)
- Lambda außerhalb VPC deployen (wenn DB via Internet erreichbar)
- VPC Endpoints nutzen (reduziert latency)

## Cleanup

### Destroy Environment

**⚠️ ACHTUNG:** Das löscht ALLES (inkl. Datenbank)!

```bash
# Plan Destroy
terraform plan -destroy

# Destroy
terraform destroy
```

Bei Production:
1. Finale Backup erstellen
2. Deployment States sichern
3. DNS-Einträge entfernen
4. Erst dann destroy

### Nur bestimmte Resources destroyen

```bash
# Destroy nur Lambda
terraform destroy -target=module.compute.aws_lambda_function.api

# Destroy nur Database
terraform destroy -target=module.database
```

## CI/CD Integration

Siehe `../../../.github/workflows/terraform-deploy.yml` für GitHub Actions Pipeline.

**Automatischer Workflow:**
1. PR erstellt → Terraform Plan
2. PR gemerged → Terraform Apply (dev)
3. Tag erstellt → Terraform Apply (staging/prod)

## Kosten-Optimierung

### Dev Environment
- Nutze `skip_final_snapshot = true`
- Kurze Log Retention (7 Tage)
- Kein NAT Gateway
- Minimale Aurora Kapazität (0.5 ACU)

### Alle Environments
- VPC Endpoints nutzen (spart NAT Gateway traffic)
- S3 Lifecycle Rules (alte Deployments archivieren)
- Lambda Memory optimieren (512 MB ist oft genug)
- Aurora Auto-Pause (wenn möglich, aktuell nicht in Serverless v2)

### Kosten überwachen

```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2026-04-01,End=2026-04-18 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=TAG,Key=Environment

# Oder via AWS Console
# → Cost Explorer → Filter by Tag:Environment=dev
```

## Weitere Dokumentation

- [AWS Deployment Guide](../../../docs/deployment/AWS_DEPLOYMENT.md)
- [Terraform Bootstrap](../bootstrap/README.md)
- [CI/CD Pipeline](../../../docs/deployment/CICD.md)
