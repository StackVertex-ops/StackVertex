# OverCloud Backend Scripts

## Seed Data Script

Befüllt die Datenbank mit realistischen AWS-Beispiel-Architekturen.

### Verwendung

```bash
# Beispiel-Architekturen hinzufügen (wenn nicht vorhanden)
./scripts/seed.sh

# Datenbank zurücksetzen und neu befüllen
./scripts/seed.sh --reset

# Alternativ: Direkter Python-Aufruf
.venv/bin/python scripts/seed_data.py
.venv/bin/python scripts/seed_data.py --reset
```

### Enthaltene Beispiel-Architekturen

#### 1. Simple Web Application
- **Komponenten**: 14
- **Kosten**: ~$385/Monat
- **Use Case**: Klassische Web-App mit High Availability
- **Stack**: VPC, ALB, EC2 Auto Scaling, RDS MySQL, S3, CloudFront
- **Highlights**: Multi-AZ, Auto Scaling, CDN, vollständig schema-konform

#### 2. Serverless REST API
- **Komponenten**: 8
- **Kosten**: ~$15.50/Monat
- **Use Case**: Cost-optimierte API mit Scale-to-Zero
- **Stack**: API Gateway, Lambda Functions, DynamoDB, CloudWatch
- **Highlights**: Komplett serverless, Pay-per-Use, ideal für MVPs

#### 3. Data Analytics Pipeline
- **Komponenten**: 13
- **Kosten**: ~$485/Monat
- **Use Case**: ETL-Pipeline für Big Data Processing
- **Stack**: S3 Data Lake, Lambda Triggers, AWS Glue, Athena, EventBridge
- **Highlights**: Batch Processing, SQL-Queries auf S3, Lifecycle Policies

### Features

- ✅ Vollständig schema-konform (architecture-v1.0.0.schema.json)
- ✅ Realistische AWS-Services und Konfigurationen
- ✅ Detaillierte Cost Estimates mit Breakdown
- ✅ Security Evaluations mit Recommendations
- ✅ Scalability und Availability Scores
- ✅ Alternative Architektur-Vorschläge
- ✅ Komplette Requirements und Decisions

### Datenbank-Status

Nach dem Seeding kannst du die Architekturen über die API abrufen:

```bash
# Alle Architekturen
curl http://localhost:8000/api/v1/architectures

# Einzelne Architektur (ID aus Seed-Output verwenden)
curl http://localhost:8000/api/v1/architectures/{id}
```
