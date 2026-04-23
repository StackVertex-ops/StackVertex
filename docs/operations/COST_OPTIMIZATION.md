# OverCloud Cost Optimization Guide

Kompletter Guide zur Kostenoptimierung für Startup/MVP Phase.

## 🎯 Kosten-Realität für Startups

### Problem: Traditionelle Cloud-Architektur

```
Aurora Serverless v2: $43/Monat MINIMUM (auch ohne Traffic!)
+ NAT Gateway: $32/Monat
+ Monitoring: $34/Monat
= $109/Monat BEVOR der erste User da ist!
```

**Für ein MVP/Startup ist das zu teuer!**

---

## Ultra-Low-Cost Architektur

### Strategie: Pay-per-Use statt Fixkosten

```
Fixkosten eliminieren:
❌ Aurora → ✅ DynamoDB (Free Tier)
❌ NAT Gateway → ✅ Lambda ohne VPC
❌ Umfangreiches Monitoring → ✅ Minimal Monitoring
```

---

## Option 1: DynamoDB + Lambda (Empfohlen)

### Architektur

```
User → API Gateway → Lambda (OHNE VPC) → DynamoDB
                               ↓
                          S3 Buckets
```

**Änderungen:**
1. **Aurora** → **DynamoDB** (Single-Table-Design)
2. **Lambda in VPC** → **Lambda OHNE VPC** (kein NAT Gateway!)
3. **PostgreSQL Schema** → **NoSQL Single-Table**

### Single-Table-Design

```python
# DynamoDB Table Schema
{
  "PK": "USER#uuid",           # Partition Key
  "SK": "METADATA",             # Sort Key
  "Type": "User",
  "email": "user@example.com",
  ...
}

{
  "PK": "ARCH#uuid",
  "SK": "v#001",
  "Type": "Architecture",
  "name": "My Architecture",
  "architecture_json": {...},
  ...
}

{
  "PK": "DEPLOY#uuid",
  "SK": "METADATA",
  "Type": "Deployment",
  "status": "running",
  ...
}
```

**Queries:**
- Get User: `PK = USER#uuid AND SK = METADATA`
- Get Architecture + Versions: `PK = ARCH#uuid AND SK BEGINS_WITH "v#"`
- List Deployments: `GSI1: Type = Deployment` (Global Secondary Index)

---

### Dev Kosten: **$0.90/Monat**

| Service | Free Tier | Usage (100 req/Tag) | Kosten |
|---------|-----------|---------------------|--------|
| Lambda Requests | 1M/Monat | 3k/Monat | **$0.00** |
| Lambda Compute | 400k GB-s | 15k GB-s | **$0.00** |
| API Gateway | 1M Requests | 3k | **$0.00** |
| DynamoDB Read | 200M RCU | 1M RCU | **$0.00** |
| DynamoDB Write | 25M WCU | 100k WCU | **$0.00** |
| DynamoDB Storage | 25 GB | 0.5 GB | **$0.00** |
| S3 Storage | 5 GB | 1 GB | **$0.23** |
| S3 Requests | 20k GET, 2k PUT | 500 GET, 50 PUT | **$0.00** |
| CloudWatch Logs | 5 GB | 1 GB | **$0.00** |
| Secrets Manager | - | 1 Secret | **$0.40** |
| CloudTrail | Management Events | Included | **$0.00** |
| GuardDuty | 30 Tage Trial | Included | **$0.00** |
| **TOTAL** | | | **$0.63/Monat** |

---

### Prod Kosten (Wenig Traffic): **$18/Monat**

**Annahmen:**
- 10.000 Requests/Tag = 300k/Monat
- 50 aktive User
- 10 GB Customer Data

| Service | Berechnung | Kosten |
|---------|------------|--------|
| Lambda | 300k - 1M Free = 0 | **$0.00** |
| API Gateway | 300k - 1M Free = 0 | **$0.00** |
| DynamoDB | Alles im Free Tier | **$0.00** |
| S3 Storage | 10 GB × $0.023 | **$0.23** |
| S3 Requests | 100k GET, 10k PUT | **$0.50** |
| CloudWatch Logs | 20 GB × $0.50 | **$10.00** |
| CloudWatch Metrics | 20 × $0.30 | **$6.00** |
| GuardDuty | Basic | **$5.00** |
| Secrets Manager | 2 Secrets × $0.40 | **$0.80** |
| **TOTAL** | | **$22.53/Monat** |

---

### Prod Kosten (Moderate Traffic): **$45/Monat**

**Annahmen:**
- 100.000 Requests/Tag = 3M/Monat
- 500 aktive User
- 50 GB Customer Data

| Service | Berechnung | Kosten |
|---------|------------|--------|
| Lambda | (3M - 1M) × $0.20/1M | **$0.40** |
| Lambda Compute | (600k - 400k) GB-s × $0.00001667 | **$3.33** |
| API Gateway | (3M - 1M) × $1/1M | **$2.00** |
| DynamoDB Read | (10M - 200M Free) = 0 | **$0.00** |
| DynamoDB Write | (1M - 25M Free) = 0 | **$0.00** |
| DynamoDB Storage | (15 GB - 25 GB Free) = 0 | **$0.00** |
| S3 Storage | 50 GB × $0.023 | **$1.15** |
| S3 Requests | 1M GET × $0.0004/1k | **$0.40** |
| CloudWatch Logs | 50 GB × $0.50 | **$25.00** |
| CloudWatch Metrics | 50 × $0.30 | **$15.00** |
| GuardDuty | | **$10.00** |
| Secrets Manager | 2 × $0.40 | **$0.80** |
| **TOTAL** | | **$58.08/Monat** |

---

## Option 2: Neon Serverless Postgres

**Neon.tech - Serverless PostgreSQL:**

```
Lambda → Neon Postgres (Extern gehostet)
       → S3
```

### Neon Pricing

| Tier | Storage | Compute | Kosten |
|------|---------|---------|--------|
| **Free** | 0.5 GB | 100h/Monat | **$0** |
| **Launch** | 10 GB | Unlimitiert | **$19/Monat** |
| **Scale** | 50 GB | Unlimitiert + Autoscaling | **$69/Monat** |

### Vorteile
- ✅ **Echtes PostgreSQL** (kein NoSQL lernen)
- ✅ **Bestehender Code funktioniert**
- ✅ **Branching** (DB-Branches wie Git!)
- ✅ **Autoscaling** (Scale-to-Zero)

### Nachteile
- ❌ **Externer Service** (Vendor Lock-in)
- ❌ **Daten außerhalb AWS**
- ❌ **Latency** (extern gehostet)

### Total Kosten mit Neon

**Dev:** $0 (Free Tier) + $0.50 (S3) = **$0.50/Monat**

**Prod (wenig Traffic):** $19 (Neon) + $15 (Lambda + S3 + CloudWatch) = **$34/Monat**

---

## Option 3: Supabase

**Supabase - Backend-as-a-Service:**

```
Frontend → Supabase (Auth + DB + Storage + Functions)
         → Lambda (nur für Terraform Execution)
```

### Supabase Pricing

| Tier | Features | Kosten |
|------|----------|--------|
| **Free** | 500 MB DB, 1 GB Storage, 2 GB Bandwidth | **$0** |
| **Pro** | 8 GB DB, 100 GB Storage, 50 GB Bandwidth | **$25/Monat** |

### Vorteile
- ✅ **All-in-One** (Auth, DB, Storage, Real-time)
- ✅ **Einfache Integration**
- ✅ **Auto-generated REST API**

### Nachteile
- ❌ **Hoher Vendor Lock-in**
- ❌ **Weniger Kontrolle**
- ❌ **Migration schwierig**

---

## Kostenvergleich

| Option | Dev | Prod (wenig) | Prod (moderate) | Skaliert zu | Migration zu Aurora |
|--------|-----|--------------|-----------------|-------------|---------------------|
| **DynamoDB** | **$0.63** | **$23** | **$58** | Millions Requests | Mittel (Schema-Change) |
| **Neon** | **$0.50** | **$34** | **$88** | Hunderttausende | Einfach (DROP/CREATE) |
| **Supabase** | **$0** | **$25** | **$75** | Begrenzt | Schwer |
| **Aurora (aktuell)** | **$107** | **$725** | **$1,029** | Unlimited | Bereits da |

---

## 🎯 Empfohlener Migration Path

### Phase 1: MVP (0-100 User) - **DynamoDB**

**Kosten:** $0.63/Monat (dev), $23/Monat (prod)

```bash
# Deploy DynamoDB Version
cd infrastructure/terraform/environments/dev-dynamodb
terraform init
terraform apply

# Backend Code-Änderungen
# app/db/dynamodb.py - DynamoDB Client
# app/models/ - Pydantic Models (statt SQLAlchemy)
# app/crud/ - DynamoDB CRUD Operations
```

**Dauer:** 2-3 Tage Umbau

---

### Phase 2: Growth (100-1000 User) - **Neon oder weiter DynamoDB**

**Kosten:** $34-58/Monat

**Option A: Weiter DynamoDB**
- Einfach, bereits implementiert
- Kosten: ~$58/Monat
- Performance: Exzellent

**Option B: Migration zu Neon**
- Zurück zu SQL
- Kosten: ~$34/Monat (günstiger!)
- Performance: Gut

```bash
# Migration zu Neon (falls gewünscht)
# 1. Export DynamoDB → JSON
# 2. Transform zu SQL
# 3. Import in Neon
# 4. Backend Code: Zurück zu SQLAlchemy
```

**Dauer:** 1 Woche

---

### Phase 3: Scale (1000+ User) - **Aurora Serverless v2**

**Kosten:** Ab $200/Monat

**Trigger:**
- DynamoDB Kosten > $100/Monat
- Komplexe Queries benötigt
- Multi-Region Replication

```bash
# Migration zu Aurora
cd infrastructure/terraform/environments/prod
# Nutze Aurora Module (bereits vorhanden!)
terraform apply

# Daten-Migration
# Von DynamoDB → Aurora (Custom Script)
# Von Neon → Aurora (pg_dump/pg_restore)
```

**Dauer:** 1-2 Wochen

---

## Code-Beispiele

### DynamoDB Single-Table Repository

```python
# app/db/dynamodb.py
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('overcloud-dev-main')

class ArchitectureRepository:
    """DynamoDB Repository für Architectures."""
    
    def create(self, architecture):
        """Create new architecture."""
        item = {
            'PK': f'ARCH#{architecture.id}',
            'SK': f'v#{architecture.version:03d}',
            'Type': 'Architecture',
            'GSI1PK': f'USER#{architecture.user_id}',
            'GSI1SK': architecture.created_at.isoformat(),
            'id': str(architecture.id),
            'name': architecture.name,
            'architecture_json': architecture.architecture_json,
            'created_at': architecture.created_at.isoformat(),
        }
        table.put_item(Item=item)
        return architecture
    
    def get(self, architecture_id, version=None):
        """Get architecture by ID."""
        if version:
            sk = f'v#{version:03d}'
        else:
            # Get latest version
            response = table.query(
                KeyConditionExpression=Key('PK').eq(f'ARCH#{architecture_id}'),
                ScanIndexForward=False,  # Descending
                Limit=1
            )
            if not response['Items']:
                return None
            return response['Items'][0]
        
        response = table.get_item(
            Key={'PK': f'ARCH#{architecture_id}', 'SK': sk}
        )
        return response.get('Item')
    
    def list_by_user(self, user_id, limit=50):
        """List architectures by user."""
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'USER#{user_id}'),
            Limit=limit
        )
        return response['Items']
```

---

### Migration Script: Aurora → DynamoDB

```python
# scripts/migrate_aurora_to_dynamodb.py
import asyncio
from app.db.session import SessionLocal
from app.models.architecture import Architecture
from app.db.dynamodb import ArchitectureRepository

async def migrate():
    """Migrate all data from Aurora to DynamoDB."""
    db = SessionLocal()
    dynamo_repo = ArchitectureRepository()
    
    # Get all architectures
    architectures = db.query(Architecture).all()
    
    print(f"Migrating {len(architectures)} architectures...")
    
    for arch in architectures:
        dynamo_repo.create(arch)
        print(f"✅ Migrated: {arch.name}")
    
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## Monitoring bei Low-Cost

### Minimal Monitoring Setup

**Was behalten:**
- ✅ CloudWatch Logs (Free Tier: 5 GB)
- ✅ GuardDuty (Critical Security)
- ✅ 5 Critical Alarms (Lambda Errors, API 5XX, etc.)

**Was weglassen (für MVP):**
- ❌ CloudWatch Dashboard ($3/Dashboard)
- ❌ Viele Metrics ($0.30/Metric)
- ❌ Security Hub ($10/Monat)
- ❌ CloudTrail Data Events ($2/100k)
- ❌ VPC Flow Logs ($0.50/GB)

**Savings:** ~$50/Monat

---

### Free Monitoring Alternativen

**1. Sentry (Error Tracking)**
- Free Tier: 5k Events/Monat
- Bessere Error Insights als CloudWatch

```python
# app/main.py
import sentry_sdk
sentry_sdk.init(dsn="https://...", environment="production")
```

**2. UptimeRobot (Health Checks)**
- Free: 50 Monitors, 5 Min Intervall
- Email Alerts

**3. Logtail (Log Management)**
- Free Tier: 1 GB Logs/Monat
- Bessere Search als CloudWatch Insights

---

## Terraform Config: Ultra-Low-Cost

```hcl
# terraform/environments/dev-lowcost/main.tf

# NO VPC (kein NAT Gateway = -$32/Monat)
# NO Aurora (= -$43/Monat)
# Minimal Monitoring (= -$30/Monat)

module "dynamodb" {
  source = "../../modules/database-dynamodb"
  
  project_name = "overcloud"
  environment  = "dev"
  
  enable_pitr   = false  # Dev: kein Backup
  enable_alarms = false  # Dev: keine Alarms
}

module "compute" {
  source = "../../modules/compute"
  
  # Lambda OHNE VPC!
  enable_vpc = false  # Wichtig!
  
  # Environment Variables
  additional_environment_variables = {
    DYNAMODB_TABLE = module.dynamodb.table_name
    USE_DYNAMODB   = "true"
  }
}

module "storage" {
  source = "../../modules/storage"
  
  # Minimal Storage
  enable_customer_data_lifecycle = true
  customer_data_version_retention_days = 30  # Kurz
}

# NO Monitoring Module (nutze Free Tier Services)
# NO Security Module (nur GuardDuty Essential)
```

---

## Kosten senken: Checkliste

### Dev Environment

- [ ] Lambda OHNE VPC (kein NAT Gateway)
- [ ] DynamoDB statt Aurora
- [ ] Nur Critical Alerts (5 statt 50)
- [ ] Kein CloudWatch Dashboard
- [ ] Log Retention: 3 Tage (statt 7)
- [ ] Kein Security Hub
- [ ] Kein Multi-AZ

**Savings: $107 → $0.63** (-99%!)

---

### Prod Environment (wenig Traffic)

- [ ] DynamoDB statt Aurora (solange < 1000 User)
- [ ] Lambda OHNE VPC (solange keine DB in VPC)
- [ ] Minimal Monitoring (20 Metrics statt 200)
- [ ] GuardDuty statt Security Hub
- [ ] Log Retention: 30 Tage (statt 90)
- [ ] Single-Region (kein Multi-Region Trail)

**Savings: $1,029 → $23** (-98%!)

---

## Wann auf Aurora wechseln?

**Trigger:**

1. **User-Anzahl:**
   - > 1.000 aktive User pro Monat
   - > 100.000 Requests pro Tag

2. **DynamoDB Kosten:**
   - DynamoDB Storage > 25 GB (dann nicht mehr Free Tier)
   - DynamoDB Read/Write > Free Tier ($100+/Monat)

3. **Feature-Bedarf:**
   - Komplexe SQL Queries (JOINs, Aggregationen)
   - ACID Transactions über mehrere Tables
   - Foreign Keys, Constraints

4. **Revenue:**
   - MRR > $5.000 (dann sind $200/Monat OK)

---

## Zusammenfassung

| Phase | User | Requests/Tag | DB | Kosten/Monat | % von Revenue |
|-------|------|--------------|----|--------------| --------------|
| **MVP** | 0-100 | < 1k | DynamoDB | **$0.63** | - |
| **Early** | 100-1k | 1k-10k | DynamoDB | **$23** | < 5% |
| **Growth** | 1k-10k | 10k-100k | DynamoDB/Neon | **$58** | < 2% |
| **Scale** | 10k+ | 100k+ | Aurora | **$200+** | < 1% |

**Regel:** Infrastructure Kosten sollten < 5% vom Revenue sein!

---

## Next Steps

1. **Entscheide dich:**
   - Start mit DynamoDB? → Ich erstelle die vollständige Implementation
   - Start mit Neon? → Ich erstelle die Config
   - Start mit Aurora (teuer)? → Bereits vorhanden

2. **Ich implementiere:**
   - DynamoDB Repositories (3-4 Tage)
   - Migration Scripts
   - Ultra-Low-Cost Terraform Config
   - Cost Monitoring Dashboard

Was bevorzugst du? 🚀
