# StackVertex Terraform Environments

Übersicht über die drei Deployment-Environments: dev, staging, und production.

## Environment-Vergleich

| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| **Zweck** | Lokale Entwicklung & Testing | Pre-Production Testing | Customer-Facing Production |
| **VPC CIDR** | 10.0.0.0/16 | 10.1.0.0/16 | 10.2.0.0/16 |
| **Availability Zones** | 2 | 2 | 3 (High Availability) |
| **NAT Gateway** | ❌ Disabled (Cost Saving) | ✅ Enabled | ✅ Enabled |
| **VPC Endpoints** | ✅ Enabled | ✅ Enabled | ✅ Enabled |
| | | | |
| **Aurora Min Capacity** | 0.5 ACU | 1 ACU | 2 ACU |
| **Aurora Max Capacity** | 1 ACU | 4 ACU | 16 ACU (Auto-Scaling) |
| **Backup Retention** | 3 days | 7 days | 30 days |
| **Deletion Protection** | ❌ Disabled | ❌ Disabled | ✅ Enabled |
| **Final Snapshot** | Skip | Create | Create (Mandatory) |
| **Performance Insights** | ❌ Disabled | ✅ Enabled | ✅ Enabled |
| | | | |
| **Lambda Timeout** | 30s | 60s | 120s |
| **Lambda Memory** | 512 MB | 1024 MB | 2048 MB |
| **Lambda Log Level** | DEBUG | INFO | WARNING |
| **Reserved Concurrency** | None | None | Optional (100+) |
| | | | |
| **Log Retention** | 7 days | 14 days | 30 days |
| **CloudWatch Alarms** | ❌ Disabled | ✅ Enabled | ✅ Enabled (Strict) |
| **Alarm Thresholds** | Tolerant (20+ errors) | Medium (10+ errors) | Strict (3-5 errors) |
| **PagerDuty Integration** | ❌ No | ❌ No | ✅ Yes (24/7 On-Call) |
| | | | |
| **S3 Encryption** | AES256 (Standard) | aws:kms (KMS Key) | aws:kms (KMS Key + Rotation) |
| **S3 Versioning** | ✅ Enabled | ✅ Enabled | ✅ Enabled |
| **S3 Glacier Archive** | ❌ Disabled | ✅ After 90 days | ✅ After 90 days |
| **Version Retention** | 30 days | 60 days | 90 days |
| **Deployment Retention** | 90 days | 180 days | 365 days |
| | | | |
| **CloudTrail Retention** | 90 days | 180 days | 365 days |
| **CloudTrail Multi-Region** | ❌ Single-Region | ❌ Single-Region | ✅ Multi-Region (Compliance) |
| **GuardDuty Frequency** | 1 Hour | 15 Minutes | 15 Minutes |
| **Security Hub** | ❌ Optional | ✅ Enabled | ✅ Enabled (Mandatory) |
| **AWS Config** | ❌ Disabled | ❌ Disabled | ✅ Enabled (Compliance) |
| | | | |
| **CORS Origins** | `*` (Allow All) | `https://staging.stackvertex.example.com` | `https://app.stackvertex.io` |
| **API Rate Limiting** | Generous | Medium | Strict |
| **Uptime SLA** | No SLA | No SLA | 99.9% |

---

## Deployment Workflow

```
┌────────┐       ┌─────────┐       ┌────────────┐
│  Dev   │  -->  │ Staging │  -->  │ Production │
└────────┘       └─────────┘       └────────────┘
   │                 │                    │
   │                 │                    │
Feature Dev     Integration          Live Traffic
Testing         Testing              Customer-Facing
No Approval     No Approval          ✅ REQUIRES APPROVAL
```

### Development (dev)
- **Trigger:** Jeder Push zu `develop` Branch
- **Approval:** Keine (automatisch)
- **Rollback:** Einfach (kein Customer Impact)
- **Kosten:** Minimal (~50-100€/Monat)

### Staging (staging)
- **Trigger:** Jeder Push zu `main` Branch (automatisch nach merge)
- **Approval:** Keine (automatisch)
- **Rollback:** Einfach (kein Customer Impact)
- **Kosten:** Mittel (~150-300€/Monat)
- **Zweck:** Pre-Production Testing, Load Testing, Security Scans

### Production (prod)
- **Trigger:** Manual Workflow Dispatch oder Tag-Push (`v*`)
- **Approval:** ✅ **REQUIRED** (GitHub Environment Protection)
- **Rollback:** Rollback-Plan erforderlich
- **Kosten:** Hoch (~500-2000€/Monat, je nach Traffic)
- **Zweck:** Live Customer Traffic, 99.9% Uptime SLA

---

## Setup-Anleitung

### 1. Terraform Bootstrap (einmalig)

```bash
cd infrastructure/terraform/bootstrap
terraform init
terraform apply -var="environment=dev"
terraform apply -var="environment=staging"
terraform apply -var="environment=prod"
```

Das erstellt:
- S3 Buckets für Terraform State
- DynamoDB Tables für State Locking
- IAM Roles für CI/CD

### 2. Environment Deployment

```bash
# Dev Environment
cd infrastructure/terraform/environments/dev
terraform init
terraform plan
terraform apply

# Staging Environment
cd ../staging
terraform init
terraform plan
terraform apply

# Production Environment (mit Vorsicht!)
cd ../prod
terraform init
terraform plan
terraform apply  # REQUIRES MANUAL APPROVAL
```

### 3. GitHub Secrets konfigurieren

Für jedes Environment müssen Secrets in GitHub konfiguriert werden:

**Dev Secrets:**
- `DEV_DB_MASTER_PASSWORD`
- `DEV_ALERT_EMAILS` (optional)

**Staging Secrets:**
- `STAGING_DB_MASTER_PASSWORD`
- `STAGING_ALERT_EMAILS`
- `STAGING_SLACK_WEBHOOK_URL` (optional)

**Production Secrets:**
- `PROD_DB_MASTER_PASSWORD`
- `PROD_ALERT_EMAILS` (required)
- `PROD_SLACK_WEBHOOK_URL` (required)
- `PROD_PAGERDUTY_ENDPOINT` (required für 24/7)

---

## Kosten-Übersicht (Schätzung)

### Development (~50-100€/Monat)
- Aurora Serverless: 0.5-1 ACU @ ~$0.12/ACU-hour = ~20-40€
- NAT Gateway: ❌ $0 (disabled)
- CloudWatch: ~5-10€
- S3 Storage: ~5-10€
- Lambda: ~5-10€

### Staging (~150-300€/Monat)
- Aurora Serverless: 1-4 ACU @ ~$0.12/ACU-hour = ~40-120€
- NAT Gateway: ~$35/Monat
- CloudWatch: ~15-30€
- S3 Storage: ~10-20€
- Lambda: ~10-30€
- KMS: ~$1/Monat

### Production (~500-2000€/Monat)
- Aurora Serverless: 2-16 ACU @ ~$0.12/ACU-hour = ~150-1200€
- NAT Gateway: ~$35/Monat (pro AZ = $105 für 3 AZs)
- CloudWatch: ~50-150€
- S3 Storage: ~30-100€
- Lambda: ~50-200€
- KMS: ~$1/Monat
- WAF (optional): ~$20/Monat
- Security Hub: ~$10/Monat

**Hinweis:** Kosten variieren stark je nach Traffic und Nutzung. Diese Schätzungen sind Baseline-Kosten ohne Traffic.

---

## Best Practices

### Development
✅ **DO:**
- Experimentieren und schnell iterieren
- Debug-Logging nutzen
- Ressourcen nach Feierabend herunterfahren (cost saving)

❌ **DON'T:**
- Produktionsdaten verwenden
- Langfristige Daten speichern
- Echte Customer-Credentials nutzen

### Staging
✅ **DO:**
- Produktionsähnliche Tests durchführen
- Load Testing und Security Scans
- Integration Testing mit echten AWS Services
- Migrations vor Prod-Deployment testen

❌ **DON'T:**
- Echte Customer-Daten verwenden
- Skipping von Tests vor Prod-Deploy
- Ungetestete Breaking Changes

### Production
✅ **DO:**
- **IMMER** durch Staging deployen vorher
- Backups vor Major Changes
- Monitoring und Alerting aktiviert halten
- Rollback-Plan bereithalten
- Regular Security Audits

❌ **DON'T:**
- Direkt auf Prod deployen ohne Staging-Test
- Manual Changes ohne Terraform
- Deletion Protection deaktivieren
- Monitoring/Logging deaktivieren
- Root Account für normale Operations

---

## Disaster Recovery

### RTO & RPO Targets

| Environment | RTO (Recovery Time) | RPO (Data Loss) |
|-------------|---------------------|-----------------|
| Dev | 24 hours | 24 hours |
| Staging | 4 hours | 1 hour |
| **Production** | **1 hour** | **15 minutes** |

### Backup Strategy

**Dev:**
- PITR: 3 days
- Snapshots: None (skip final snapshot)

**Staging:**
- PITR: 7 days
- Snapshots: Daily (7 days retention)

**Production:**
- PITR: 30 days
- Snapshots: Daily (30 days), Weekly (90 days), Monthly (1 year)
- Cross-Region Replication: eu-west-1 (Disaster Recovery)

---

## Monitoring & Alerts

### Alert Routing

```
┌──────────────┐
│   CloudWatch │
│    Alarms    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  SNS Topics  │
│  - Critical  │  --> PagerDuty (Prod only)
│  - Warning   │  --> Email
│  - Info      │  --> Slack
└──────────────┘
```

### Alert Examples

**Critical (Prod):**
- API 5XX > 3 in 5 minutes → PagerDuty + Email
- Database CPU > 90% → PagerDuty + Email
- Lambda Errors > 5 in 5 minutes → PagerDuty

**Warning (All Envs):**
- API 4XX > threshold → Email + Slack
- Deployment Failure → Email + Slack
- GuardDuty Finding (Medium) → Email

**Info (All Envs):**
- Successful Deployment → Slack
- Config Compliance Change → Slack

---

## Compliance & Security

### Dev
- ❌ Keine Compliance-Anforderungen
- Basic Security (IAM, Encryption at Rest)

### Staging
- ✅ Security Hub enabled
- ✅ GuardDuty enabled
- ✅ KMS Encryption

### Production
- ✅ **DSGVO-compliant**
- ✅ **ISO 27001-ready**
- ✅ **SOC 2-ready**
- ✅ Multi-Region CloudTrail
- ✅ AWS Config Rules
- ✅ Security Hub Compliance Scanning
- ✅ GuardDuty Threat Detection
- ✅ 365 days Audit Log Retention

---

## Next Steps

1. ✅ Environments erstellt (dev, staging, prod)
2. ⏳ Backup Module erstellen (`infrastructure/terraform/modules/backup/`)
3. ⏳ WAF Module erstellen (`infrastructure/terraform/modules/waf/`)
4. ⏳ GitHub Environments konfigurieren (staging, prod mit Approvals)
5. ⏳ CI/CD Pipeline erweitern (deploy.yml)

Siehe `/Users/andyschwarz/.claude/plans/dreamy-wondering-moler.md` für den vollständigen Roadmap.
