# OverCloud Backend Scripts

Utility Scripts für Administration, Seeding & Maintenance.

---

## Admin Scripts

### create_superadmin.py

Erstellt einen SuperAdmin User für System-Administration.

**Usage:**

```bash
# Mit automatisch generiertem Passwort
python scripts/create_superadmin.py \
  --email admin@overcloud.io \
  --name "Super Admin"

# Mit eigenem Passwort
python scripts/create_superadmin.py \
  --email admin@overcloud.io \
  --name "Super Admin" \
  --password "YourSecurePassword123!"

# Force creation (auch wenn bereits SuperAdmin existiert)
python scripts/create_superadmin.py \
  --email admin2@overcloud.io \
  --name "Second Admin" \
  --force
```

**Sicherheit:**
- Password: Mindestens 20 Zeichen, zufällig generiert
- 2FA: Nach erstem Login aktivieren (coming soon)
- Audit Log: Alle Admin-Aktionen werden geloggt

**Environment:**

Benötigt DynamoDB Table und AWS Credentials:

```bash
# .env
DYNAMODB_TABLE_NAME=overcloud
AWS_REGION=eu-central-1
```

**Siehe auch:** `/docs/ADMIN_SYSTEM.md` für Details zum Admin System.

---

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
