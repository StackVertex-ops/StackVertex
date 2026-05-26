# Terraform Generation & Deployment - Master Plan

**Datum:** 2026-03-26
**Status:** 🔬 In Planung
**Komplexität:** ⭐⭐⭐⭐⭐ (Sehr hoch)

---

## 🎯 Vision

**Was wollen wir erreichen?**

1. User konfiguriert Cloud-Infrastruktur über **detaillierte Forms** (nicht nur High-Level Requirements)
2. System generiert **vollständige JSON-Architektur-Definition**
3. Backend generiert **Terraform HCL Code** aus JSON
4. User kann Terraform **exportieren** oder **direkt deployen** (in eigene Cloud)
5. Jeder Kunde nutzt **eigenes Cloud-Konto** mit **sicheren Credentials** (wie GitHub Secrets)
6. System bietet **Anleitungen** für Cloud-Setup (für Anfänger)

---

## 🧩 Die 7 Kernprobleme

### 1. Wie bekommen wir aktuelle AWS-Daten?
### 2. Wie detailliert muss die JSON sein?
### 3. Wie generieren wir Terraform aus JSON?
### 4. Wie bauen wir Credentials ein?
### 5. Wie designen wir die detaillierten Service-Forms?
### 6. Wie modellieren wir Netzwerk-Infrastruktur (VPC, etc.)?
### 7. Wie deployen wir Terraform sicher?

---

## 1️⃣ Problem: Aktuelle AWS-Daten

### Herausforderung
AWS hat hunderte Services mit tausenden Optionen:
- EC2: 400+ Instance-Typen (t2.micro, c5.xlarge, m6i.2xlarge, ...)
- RDS: 20+ Engines (MySQL 5.7, 8.0, PostgreSQL 13, 14, 15, ...)
- Regions: 30+ Regionen, ständig neue hinzu
- AMIs: Täglich neue Images
- Instance-Features ändern sich (z.B. neue CPU-Generationen)

**Problem:** Wie halten wir unsere Forms aktuell?

---

### Lösungsansätze

#### Option A: Statische Daten + Manuelle Updates ❌
**Wie:**
- Hardcoded Listen in JSON-Dateien
- Developer updated manuell

**Vorteile:**
- Einfach zu implementieren
- Keine API-Calls nötig

**Nachteile:**
- ❌ Veraltet schnell
- ❌ Hoher Wartungsaufwand
- ❌ Keine neuen Instance-Typen verfügbar

**Bewertung:** Nicht skalierbar, nicht praktikabel

---

#### Option B: AWS Pricing API ⚠️
**Wie:**
```python
import boto3

pricing = boto3.client('pricing', region_name='us-east-1')

# Hole alle EC2 Instance-Typen
response = pricing.get_products(
    ServiceCode='AmazonEC2',
    Filters=[
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'EU (Frankfurt)'},
        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'}
    ]
)
```

**Vorteile:**
- ✅ Immer aktuelle Daten
- ✅ Offizielle AWS API

**Nachteile:**
- ⚠️ Nur Pricing-Daten (keine Features)
- ⚠️ Komplexe Response-Struktur
- ⚠️ Langsam (große Datenmengen)

**Bewertung:** Gut für Preise, unvollständig für Features

---

#### Option C: AWS SSM Parameter Store (Public Parameters) ✅
**Wie:**
```python
import boto3

ssm = boto3.client('ssm', region_name='eu-central-1')

# Hole neueste Amazon Linux 2 AMI
response = ssm.get_parameter(
    Name='/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2'
)
ami_id = response['Parameter']['Value']
```

**Vorteile:**
- ✅ Automatisch aktualisiert von AWS
- ✅ Schnell
- ✅ Für AMIs sehr gut

**Nachteile:**
- ⚠️ Nur für bestimmte Ressourcen (AMIs, etc.)
- ⚠️ Nicht für Instance-Typen

**Bewertung:** Perfekt für AMIs, ergänzend nutzen

---

#### Option D: AWS Service Catalog / CloudFormation Resource Specifications ✅✅
**Wie:**
```bash
# AWS publiziert CloudFormation Resource Specifications als JSON
curl https://d1uauaxba7bl26.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json
```

**Beispiel-Struktur:**
```json
{
  "ResourceTypes": {
    "AWS::EC2::Instance": {
      "Properties": {
        "InstanceType": {
          "PrimitiveType": "String",
          "Required": false,
          "Documentation": "..."
        },
        "ImageId": {
          "PrimitiveType": "String",
          "Required": true
        }
      }
    }
  }
}
```

**Vorteile:**
- ✅ Offizielle AWS-Spezifikationen
- ✅ Alle Ressourcen-Typen
- ✅ Validierungsregeln
- ✅ Täglich aktualisiert

**Nachteile:**
- ⚠️ Keine konkreten Werte (z.B. welche Instance-Typen existieren)
- ⚠️ Nur Schema, nicht Daten

**Bewertung:** Gut für Validierung, nicht für Auswahloptionen

---

#### Option E: Terraform AWS Provider Schema ✅✅✅ (EMPFEHLUNG)
**Wie:**
```bash
# Terraform Provider hat Schema mit allen Ressourcen
terraform providers schema -json > aws_provider_schema.json
```

**Beispiel:**
```json
{
  "provider_schemas": {
    "registry.terraform.io/hashicorp/aws": {
      "resource_schemas": {
        "aws_instance": {
          "block": {
            "attributes": {
              "instance_type": {
                "type": "string",
                "description": "Instance type to use",
                "required": true
              },
              "ami": {
                "type": "string",
                "description": "AMI to use",
                "required": true
              }
            }
          }
        }
      }
    }
  }
}
```

**PLUS:**
- Terraform Data Sources für dynamische Werte:

```hcl
# Hole verfügbare Instance-Typen
data "aws_ec2_instance_types" "available" {
  filter {
    name   = "current-generation"
    values = ["true"]
  }
}

# Hole neueste Amazon Linux AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}
```

**Vorteile:**
- ✅ Terraform-native (wir generieren eh Terraform)
- ✅ Schema + Data Sources für Werte
- ✅ Sehr gut dokumentiert
- ✅ Community-Support

**Nachteile:**
- ⚠️ Data Sources brauchen Credentials (für manche Abfragen)
- ⚠️ Kann langsam sein (API-Calls)

**Bewertung:** ⭐⭐⭐⭐⭐ Beste Lösung

---

#### Option F: Hybrid-Ansatz ✅✅✅✅ (FINAL RECOMMENDATION)

**Strategie:**
```
1. Statische Defaults (für MVP)
   - Hardcoded Liste von häufigen Instance-Typen (t3.micro, t3.small, ...)
   - Kuratierte Auswahl (nicht alle 400+ Typen)

2. Terraform Data Sources (für Produktion)
   - AMIs werden dynamisch abgerufen
   - Verfügbarkeit wird geprüft

3. Periodisches Update (Background Job)
   - Cronjob lädt 1x täglich CloudFormation Specs
   - Updated interne Datenbank mit neuen Optionen
   - Forms bleiben aktuell ohne API-Calls bei jedem Request

4. User kann "Erweitert" wählen
   - Standard: Dropdown mit 20 häufigen Instance-Typen
   - Erweitert: Freitext-Input für beliebige Typen
```

**Implementierung:**
```python
# backend/app/services/aws_metadata_sync.py

import boto3
import requests
from datetime import datetime

class AWSMetadataSync:
    """Synchronisiert AWS-Metadaten periodisch"""

    def sync_instance_types(self):
        """Hole aktuelle Instance-Typen von AWS Pricing API"""
        # Implementierung...
        pass

    def sync_ami_data(self):
        """Hole AMI-Daten von SSM Parameter Store"""
        # Implementierung...
        pass

    def sync_cloudformation_specs(self):
        """Lade CloudFormation Resource Specifications"""
        url = "https://d1uauaxba7bl26.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json"
        response = requests.get(url)
        # Parse und speichere in DB
        pass
```

**Datenbank-Schema:**
```sql
CREATE TABLE aws_instance_types (
    id UUID PRIMARY KEY,
    instance_type VARCHAR(50) UNIQUE NOT NULL,  -- z.B. "t3.micro"
    vcpu INTEGER,
    memory_gb DECIMAL,
    network_performance VARCHAR(50),
    current_generation BOOLEAN DEFAULT true,
    category VARCHAR(50),  -- "general", "compute", "memory", "storage"
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE TABLE aws_amis (
    id UUID PRIMARY KEY,
    ami_id VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    architecture VARCHAR(20),  -- "x86_64", "arm64"
    region VARCHAR(20),
    owner VARCHAR(50),  -- "amazon", "aws-marketplace"
    last_updated TIMESTAMP DEFAULT NOW()
);
```

**API Endpoint:**
```python
# backend/app/api/aws_metadata.py

@router.get("/aws/instance-types")
async def get_instance_types(
    category: str = None,
    db: Session = Depends(get_db)
):
    """Hole verfügbare Instance-Typen (aus Cache)"""
    query = db.query(AWSInstanceType)
    if category:
        query = query.filter(AWSInstanceType.category == category)

    return query.filter(AWSInstanceType.current_generation == True).all()

@router.get("/aws/amis")
async def get_amis(
    region: str,
    architecture: str = "x86_64",
    db: Session = Depends(get_db)
):
    """Hole verfügbare AMIs für Region"""
    return db.query(AWSAMI).filter(
        AWSAMI.region == region,
        AWSAMI.architecture == architecture
    ).all()
```

**Cronjob:**
```bash
# .github/workflows/sync-aws-metadata.yml (oder Celery Task)

name: Sync AWS Metadata
on:
  schedule:
    - cron: '0 2 * * *'  # Täglich um 2 Uhr nachts

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Sync
        run: |
          python backend/scripts/sync_aws_metadata.py
```

---

### ✅ Entscheidung: Hybrid-Ansatz

**MVP (Phase 1):**
- Statische JSON-Dateien mit kuratierten Listen
- Häufigste Instance-Typen (20-30 Stück)
- Standard-AMIs (Amazon Linux 2, Ubuntu 22.04, etc.)

**Production (Phase 2):**
- Täglicher Sync-Job
- Datenbank mit aktuellen Optionen
- API-Endpoints für Frontend

**Advanced (Phase 3):**
- Terraform Data Sources im generierten Code
- Dynamische Abfragen zur Deploy-Zeit

---

### 🔧 Technische Umsetzung: Daten-Sync

**Setup:**
```
┌──────────────────────────────────────────────────────┐
│  StackVertex Firmen-Account (AWS)                      │
│                                                       │
│  - Nur für Daten-Abfragen, KEIN Deployment          │
│  - Terraform CLI installiert                         │
│  - AWS CLI installiert                               │
│  - Cronjob läuft täglich                             │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ AWS API Calls (Read-Only)
                    │ terraform providers schema
                    │ aws ec2 describe-instance-types
                    ▼
┌──────────────────────────────────────────────────────┐
│  StackVertex Backend (Python)                          │
│                                                       │
│  - Empfängt Sync-Daten                               │
│  - Speichert in PostgreSQL                           │
│  - Stellt über API bereit                            │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ API GET /aws/instance-types
                    ▼
┌──────────────────────────────────────────────────────┐
│  Frontend (Forms)                                    │
│                                                       │
│  - Lädt aktuelle Daten                               │
│  - Zeigt in Dropdowns                                │
└──────────────────────────────────────────────────────┘
```

**Wichtig:**
- StackVertex-Account wird **NUR** für Abfragen genutzt
- Kein Deployment in StackVertex-Account
- Kunden deployen in **ihren eigenen** Accounts (mit ihren Credentials)

---

### Sync-Script (Backend)

```python
# backend/scripts/sync_aws_metadata.py

import boto3
import subprocess
import json
from app.database import SessionLocal
from app.models import AWSInstanceType, AWSAMI

# StackVertex Firmen-Account Credentials (aus Environment)
AWS_ACCESS_KEY = os.environ['OVERCLOUD_AWS_ACCESS_KEY']
AWS_SECRET_KEY = os.environ['OVERCLOUD_AWS_SECRET_KEY']
AWS_REGION = 'eu-central-1'

def sync_terraform_schema():
    """Hole Terraform Provider Schema"""
    print("Syncing Terraform AWS Provider Schema...")

    # terraform providers schema -json
    result = subprocess.run(
        ['terraform', 'providers', 'schema', '-json'],
        capture_output=True,
        text=True,
        cwd='/tmp'  # Temporäres Terraform-Verzeichnis
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return

    schema = json.loads(result.stdout)

    # Speichere in DB oder Datei
    with open('aws_provider_schema.json', 'w') as f:
        json.dump(schema, f, indent=2)

    print("✓ Terraform schema synced")

def sync_instance_types():
    """Hole aktuelle EC2 Instance-Typen"""
    print("Syncing EC2 Instance Types...")

    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    # Hole alle Instance-Typen
    paginator = ec2.get_paginator('describe_instance_types')
    db = SessionLocal()

    try:
        for page in paginator.paginate():
            for instance_type in page['InstanceTypes']:
                # Speichere in DB
                db_instance = AWSInstanceType(
                    instance_type=instance_type['InstanceType'],
                    vcpu=instance_type['VCpuInfo']['DefaultVCpus'],
                    memory_gb=instance_type['MemoryInfo']['SizeInMiB'] / 1024,
                    network_performance=instance_type.get('NetworkInfo', {}).get('NetworkPerformance', 'Unknown'),
                    current_generation=instance_type.get('CurrentGeneration', False),
                    category=_categorize_instance_type(instance_type['InstanceType'])
                )
                db.merge(db_instance)  # Update or Insert

        db.commit()
        print(f"✓ Synced instance types")
    finally:
        db.close()

def sync_amis():
    """Hole Standard-AMIs"""
    print("Syncing AMIs...")

    ssm = boto3.client(
        'ssm',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    # Amazon Linux 2
    ami_al2 = ssm.get_parameter(
        Name='/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2'
    )['Parameter']['Value']

    # Ubuntu 22.04
    ami_ubuntu = ssm.get_parameter(
        Name='/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id'
    )['Parameter']['Value']

    db = SessionLocal()
    try:
        db.merge(AWSAMI(
            ami_id=ami_al2,
            name='Amazon Linux 2',
            description='Amazon Linux 2 AMI (HVM) - Kernel 5.10, SSD Volume Type',
            architecture='x86_64',
            region=AWS_REGION,
            owner='amazon'
        ))
        db.merge(AWSAMI(
            ami_id=ami_ubuntu,
            name='Ubuntu Server 22.04 LTS',
            description='Canonical, Ubuntu, 22.04 LTS, amd64 jammy image',
            architecture='x86_64',
            region=AWS_REGION,
            owner='canonical'
        ))
        db.commit()
        print("✓ Synced AMIs")
    finally:
        db.close()

def _categorize_instance_type(instance_type: str) -> str:
    """Kategorisiere Instance-Typ"""
    prefix = instance_type.split('.')[0]
    categories = {
        't': 'general',
        'm': 'general',
        'c': 'compute',
        'r': 'memory',
        'x': 'memory',
        'i': 'storage',
        'd': 'storage',
        'p': 'gpu',
        'g': 'gpu'
    }
    return categories.get(prefix[0], 'other')

if __name__ == '__main__':
    sync_terraform_schema()
    sync_instance_types()
    sync_amis()
    print("✓ All AWS metadata synced")
```

**Cronjob (täglich):**
```bash
# Cronjob auf StackVertex-Server oder GitHub Actions

0 2 * * * cd /app/backend && python scripts/sync_aws_metadata.py
```

**GitHub Actions Alternative:**
```yaml
# .github/workflows/sync-aws-metadata.yml

name: Sync AWS Metadata
on:
  schedule:
    - cron: '0 2 * * *'  # Täglich 2 Uhr
  workflow_dispatch:  # Manuell trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          pip install boto3 psycopg2-binary sqlalchemy

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Run Sync
        env:
          OVERCLOUD_AWS_ACCESS_KEY: ${{ secrets.OVERCLOUD_AWS_ACCESS_KEY }}
          OVERCLOUD_AWS_SECRET_KEY: ${{ secrets.OVERCLOUD_AWS_SECRET_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          python backend/scripts/sync_aws_metadata.py
```

---

## 2️⃣ Problem: Wie detailliert muss die JSON sein?

### Anforderungen

**Grundprinzip:** Die JSON muss **alles** enthalten, was Terraform braucht.

**Beispiel VPC + EC2:**
```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Simple Web App",
    "provider": "aws",
    "region": "eu-central-1"
  },
  "architecture": {
    "network": {
      "vpcs": [
        {
          "id": "vpc-main",
          "cidr_block": "10.0.0.0/16",
          "enable_dns_hostnames": true,
          "enable_dns_support": true,
          "tags": {
            "Name": "main-vpc",
            "Environment": "production"
          },
          "subnets": [
            {
              "id": "subnet-public-1a",
              "cidr_block": "10.0.1.0/24",
              "availability_zone": "eu-central-1a",
              "map_public_ip_on_launch": true,
              "type": "public",
              "tags": {
                "Name": "public-subnet-1a"
              }
            },
            {
              "id": "subnet-private-1a",
              "cidr_block": "10.0.10.0/24",
              "availability_zone": "eu-central-1a",
              "map_public_ip_on_launch": false,
              "type": "private",
              "tags": {
                "Name": "private-subnet-1a"
              }
            }
          ],
          "internet_gateway": {
            "id": "igw-main",
            "tags": {
              "Name": "main-igw"
            }
          },
          "nat_gateways": [
            {
              "id": "nat-1a",
              "subnet_id": "subnet-public-1a",
              "tags": {
                "Name": "nat-1a"
              }
            }
          ],
          "route_tables": [
            {
              "id": "rtb-public",
              "subnet_ids": ["subnet-public-1a"],
              "routes": [
                {
                  "destination_cidr_block": "0.0.0.0/0",
                  "gateway_id": "igw-main"
                }
              ],
              "tags": {
                "Name": "public-route-table"
              }
            },
            {
              "id": "rtb-private",
              "subnet_ids": ["subnet-private-1a"],
              "routes": [
                {
                  "destination_cidr_block": "0.0.0.0/0",
                  "nat_gateway_id": "nat-1a"
                }
              ],
              "tags": {
                "Name": "private-route-table"
              }
            }
          ]
        }
      ],
      "security_groups": [
        {
          "id": "sg-web",
          "name": "web-server-sg",
          "description": "Security group for web servers",
          "vpc_id": "vpc-main",
          "ingress_rules": [
            {
              "description": "HTTP from anywhere",
              "from_port": 80,
              "to_port": 80,
              "protocol": "tcp",
              "cidr_blocks": ["0.0.0.0/0"]
            },
            {
              "description": "HTTPS from anywhere",
              "from_port": 443,
              "to_port": 443,
              "protocol": "tcp",
              "cidr_blocks": ["0.0.0.0/0"]
            }
          ],
          "egress_rules": [
            {
              "description": "All outbound traffic",
              "from_port": 0,
              "to_port": 0,
              "protocol": "-1",
              "cidr_blocks": ["0.0.0.0/0"]
            }
          ],
          "tags": {
            "Name": "web-sg"
          }
        }
      ]
    },
    "compute": {
      "instances": [
        {
          "id": "ec2-web-1",
          "instance_type": "t3.micro",
          "ami": "ami-0123456789abcdef0",  // Oder: "data.aws_ami.amazon_linux.id"
          "subnet_id": "subnet-public-1a",
          "vpc_security_group_ids": ["sg-web"],
          "associate_public_ip_address": true,
          "key_name": "my-key-pair",
          "user_data": "#!/bin/bash\nyum update -y\nyum install -y httpd\nsystemctl start httpd",
          "root_block_device": {
            "volume_size": 20,
            "volume_type": "gp3",
            "delete_on_termination": true,
            "encrypted": true
          },
          "tags": {
            "Name": "web-server-1",
            "Environment": "production"
          }
        }
      ]
    },
    "storage": {
      "s3_buckets": [
        {
          "id": "s3-assets",
          "bucket_name": "my-app-assets-${random_id}",
          "acl": "private",
          "versioning": {
            "enabled": true
          },
          "server_side_encryption_configuration": {
            "rule": {
              "apply_server_side_encryption_by_default": {
                "sse_algorithm": "AES256"
              }
            }
          },
          "tags": {
            "Name": "assets-bucket"
          }
        }
      ]
    },
    "database": {
      "rds_instances": [
        {
          "id": "rds-main",
          "engine": "postgres",
          "engine_version": "15.3",
          "instance_class": "db.t3.micro",
          "allocated_storage": 20,
          "storage_type": "gp3",
          "storage_encrypted": true,
          "db_name": "myapp",
          "username": "admin",
          "password": "${var.db_password}",  // Aus Secrets
          "vpc_security_group_ids": ["sg-database"],
          "db_subnet_group_name": "rds-subnet-group",
          "multi_az": false,
          "backup_retention_period": 7,
          "skip_final_snapshot": false,
          "final_snapshot_identifier": "rds-main-final-snapshot",
          "tags": {
            "Name": "main-database"
          }
        }
      ]
    }
  },
  "relationships": [
    {
      "from": "ec2-web-1",
      "to": "rds-main",
      "type": "uses",
      "description": "Web server connects to database"
    },
    {
      "from": "ec2-web-1",
      "to": "s3-assets",
      "type": "reads",
      "description": "Web server reads static assets"
    }
  ]
}
```

---

### JSON-Schema-Struktur

**Hierarchie:**
```
architecture
├── network (VPC, Subnets, Routing, Security Groups)
├── compute (EC2, Lambda, ECS, EKS)
├── storage (S3, EBS, EFS)
├── database (RDS, DynamoDB, ElastiCache)
├── load_balancing (ALB, NLB, CLB)
├── dns (Route53)
├── monitoring (CloudWatch)
└── iam (Roles, Policies)
```

**Detailgrad:**
- ✅ **Alle Terraform-Required-Felder** müssen in JSON sein
- ✅ **Optionale Felder** mit sinnvollen Defaults
- ✅ **Relationships** für Abhängigkeiten
- ✅ **Variablen** für Secrets (`${var.xyz}`)

---

### Validierung

**JSON Schema (Draft 2020-12):**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://stackvertex.io/schemas/architecture-v1.json",
  "title": "StackVertex Architecture Schema",
  "type": "object",
  "required": ["version", "metadata", "architecture"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "metadata": {
      "type": "object",
      "required": ["name", "provider", "region"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "provider": { "enum": ["aws", "azure", "gcp"] },
        "region": { "type": "string" }
      }
    },
    "architecture": {
      "type": "object",
      "properties": {
        "network": { "$ref": "#/$defs/network" },
        "compute": { "$ref": "#/$defs/compute" }
      }
    }
  },
  "$defs": {
    "network": {
      "type": "object",
      "properties": {
        "vpcs": {
          "type": "array",
          "items": { "$ref": "#/$defs/vpc" }
        }
      }
    },
    "vpc": {
      "type": "object",
      "required": ["id", "cidr_block"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "cidr_block": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+\\.\\d+/\\d+$" }
      }
    }
  }
}
```

---

## 3️⃣ Problem: Terraform-Generation

### Ansatz: Template-Based Generation

**Jinja2 Templates für Terraform:**

```python
# backend/app/core/terraform_generator/generator.py

from jinja2 import Environment, FileSystemLoader
import json

class TerraformGenerator:
    """Generiert Terraform HCL aus StackVertex JSON"""

    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('templates/terraform'))

    def generate(self, architecture_json: dict) -> str:
        """Haupt-Methode: JSON → Terraform HCL"""

        # 1. Validiere JSON
        self._validate_architecture(architecture_json)

        # 2. Generiere einzelne Ressourcen
        terraform_code = ""

        # Provider & Backend
        terraform_code += self._generate_provider(architecture_json['metadata'])

        # Network (VPC, Subnets, etc.)
        if 'network' in architecture_json['architecture']:
            terraform_code += self._generate_network(architecture_json['architecture']['network'])

        # Compute (EC2, etc.)
        if 'compute' in architecture_json['architecture']:
            terraform_code += self._generate_compute(architecture_json['architecture']['compute'])

        # Storage (S3, etc.)
        if 'storage' in architecture_json['architecture']:
            terraform_code += self._generate_storage(architecture_json['architecture']['storage'])

        # Database (RDS, etc.)
        if 'database' in architecture_json['architecture']:
            terraform_code += self._generate_database(architecture_json['architecture']['database'])

        # 3. Generiere Outputs
        terraform_code += self._generate_outputs(architecture_json)

        return terraform_code

    def _generate_provider(self, metadata: dict) -> str:
        """Generiert Provider-Konfiguration"""
        template = self.env.get_template('provider.tf.j2')
        return template.render(
            provider=metadata['provider'],
            region=metadata['region']
        )

    def _generate_network(self, network: dict) -> str:
        """Generiert Netzwerk-Ressourcen"""
        template = self.env.get_template('network.tf.j2')
        return template.render(network=network)
```

**Template-Beispiel:** `templates/terraform/network.tf.j2`
```hcl
{% for vpc in network.vpcs %}
# VPC: {{ vpc.id }}
resource "aws_vpc" "{{ vpc.id }}" {
  cidr_block           = "{{ vpc.cidr_block }}"
  enable_dns_hostnames = {{ vpc.enable_dns_hostnames | lower }}
  enable_dns_support   = {{ vpc.enable_dns_support | lower }}

  tags = {
    {% for key, value in vpc.tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}

{% if vpc.internet_gateway %}
# Internet Gateway: {{ vpc.internet_gateway.id }}
resource "aws_internet_gateway" "{{ vpc.internet_gateway.id }}" {
  vpc_id = aws_vpc.{{ vpc.id }}.id

  tags = {
    {% for key, value in vpc.internet_gateway.tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}
{% endif %}

{% for subnet in vpc.subnets %}
# Subnet: {{ subnet.id }}
resource "aws_subnet" "{{ subnet.id }}" {
  vpc_id                  = aws_vpc.{{ vpc.id }}.id
  cidr_block              = "{{ subnet.cidr_block }}"
  availability_zone       = "{{ subnet.availability_zone }}"
  map_public_ip_on_launch = {{ subnet.map_public_ip_on_launch | lower }}

  tags = {
    {% for key, value in subnet.tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}
{% endfor %}

{% for sg in network.security_groups %}
{% if sg.vpc_id == vpc.id %}
# Security Group: {{ sg.id }}
resource "aws_security_group" "{{ sg.id }}" {
  name        = "{{ sg.name }}"
  description = "{{ sg.description }}"
  vpc_id      = aws_vpc.{{ vpc.id }}.id

  {% for rule in sg.ingress_rules %}
  ingress {
    description = "{{ rule.description }}"
    from_port   = {{ rule.from_port }}
    to_port     = {{ rule.to_port }}
    protocol    = "{{ rule.protocol }}"
    cidr_blocks = [{% for cidr in rule.cidr_blocks %}"{{ cidr }}"{% if not loop.last %}, {% endif %}{% endfor %}]
  }
  {% endfor %}

  {% for rule in sg.egress_rules %}
  egress {
    description = "{{ rule.description }}"
    from_port   = {{ rule.from_port }}
    to_port     = {{ rule.to_port }}
    protocol    = "{{ rule.protocol }}"
    cidr_blocks = [{% for cidr in rule.cidr_blocks %}"{{ cidr }}"{% if not loop.last %}, {% endif %}{% endfor %}]
  }
  {% endfor %}

  tags = {
    {% for key, value in sg.tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}
{% endif %}
{% endfor %}

{% endfor %}
```

---

### Alternative: Python Terraform Bindings

**cdktf (Cloud Development Kit for Terraform):**
```python
from cdktf import App, TerraformStack
from imports.aws import AwsProvider, Vpc, Subnet

class MyStack(TerraformStack):
    def __init__(self, scope, id, architecture_json):
        super().__init__(scope, id)

        # Provider
        AwsProvider(self, "aws",
            region=architecture_json['metadata']['region']
        )

        # VPC
        for vpc_data in architecture_json['architecture']['network']['vpcs']:
            vpc = Vpc(self, vpc_data['id'],
                cidr_block=vpc_data['cidr_block'],
                enable_dns_hostnames=vpc_data['enable_dns_hostnames'],
                tags=vpc_data['tags']
            )

            # Subnets
            for subnet_data in vpc_data['subnets']:
                Subnet(self, subnet_data['id'],
                    vpc_id=vpc.id,
                    cidr_block=subnet_data['cidr_block'],
                    availability_zone=subnet_data['availability_zone'],
                    tags=subnet_data['tags']
                )

app = App()
MyStack(app, "my-stack", architecture_json)
app.synth()
```

**Vorteile CDKTF:**
- ✅ Type-Safety
- ✅ Python (kein Template-Parsing)
- ✅ Wiederverwendbare Konstrukte

**Nachteile:**
- ⚠️ Komplexer Setup
- ⚠️ Weniger Kontrolle über generierten Code
- ⚠️ Größere Dependencies

**Entscheidung:** Template-Based (Jinja2) für MVP, CDKTF für später evaluieren

---

## 4️⃣ Problem: Credentials Management

### Anforderungen

1. **Write-Only:** User kann Credentials setzen, aber **nie wieder sehen**
2. **Encrypted at Rest:** In DB verschlüsselt speichern
3. **Encrypted in Transit:** HTTPS/TLS
4. **Per-User:** Jeder User hat eigene Credentials
5. **Multi-Cloud:** AWS, Azure, GCP
6. **Rotation:** User kann Credentials updaten
7. **Auditlog:** Wer hat wann welche Credentials verwendet?

---

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                                                              │
│  User gibt AWS Access Key + Secret Key ein                  │
│  → Werden sofort verschlüsselt und an Backend gesendet      │
│  → Nach Speichern: Nur "****" anzeigen (wie GitHub)         │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS (TLS 1.3)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│                                                              │
│  1. Empfange Credentials (über HTTPS)                       │
│  2. Validiere (AWS STS GetCallerIdentity)                   │
│  3. Verschlüssle mit Fernet (oder AWS KMS)                  │
│  4. Speichere in DB                                          │
│  5. Lösche aus Memory                                        │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       PostgreSQL                             │
│                                                              │
│  credentials_table:                                          │
│  - id (UUID)                                                 │
│  - user_id (FK)                                              │
│  - provider (aws, azure, gcp)                                │
│  - encrypted_access_key (BYTEA)                              │
│  - encrypted_secret_key (BYTEA)                              │
│  - created_at                                                │
│  - last_used_at                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### Implementierung

#### DB-Schema

```sql
CREATE TABLE cloud_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,  -- 'aws', 'azure', 'gcp'
    region VARCHAR(50),  -- Optional: Default-Region

    -- Verschlüsselte Credentials
    encrypted_credentials BYTEA NOT NULL,  -- JSON mit allen Credentials

    -- Metadata
    credential_name VARCHAR(255),  -- User-freundlicher Name (z.B. "Production AWS")
    is_default BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    last_validated_at TIMESTAMP,

    -- Constraints
    UNIQUE(user_id, provider, credential_name),
    CHECK (provider IN ('aws', 'azure', 'gcp'))
);

CREATE INDEX idx_credentials_user ON cloud_credentials(user_id);
CREATE INDEX idx_credentials_provider ON cloud_credentials(provider);

-- Audit Log
CREATE TABLE credential_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_id UUID NOT NULL REFERENCES cloud_credentials(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,  -- 'deploy', 'validate', 'plan'
    architecture_id UUID REFERENCES architectures(id),
    success BOOLEAN,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

#### Verschlüsselung

**Option A: Fernet (Python Cryptography)**

```python
# backend/app/core/encryption.py

from cryptography.fernet import Fernet
import os
import json

class CredentialEncryption:
    """Verschlüsselt/Entschlüsselt Cloud-Credentials"""

    def __init__(self):
        # Lade Encryption Key aus Environment (NIEMALS in Code!)
        encryption_key = os.environ.get('CREDENTIAL_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY not set!")

        self.cipher = Fernet(encryption_key.encode())

    def encrypt(self, credentials: dict) -> bytes:
        """Verschlüsselt Credentials"""
        json_str = json.dumps(credentials)
        return self.cipher.encrypt(json_str.encode())

    def decrypt(self, encrypted_data: bytes) -> dict:
        """Entschlüsselt Credentials"""
        decrypted = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted.decode())

# Generiere Key (einmalig):
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# → Speichere in .env: CREDENTIAL_ENCRYPTION_KEY=...
```

**Vorteile:**
- ✅ Einfach
- ✅ Schnell
- ✅ Symmetric Encryption

**Nachteile:**
- ⚠️ Key muss sicher gespeichert werden
- ⚠️ Wenn Key verloren → alle Credentials verloren

---

**Option B: AWS KMS (für Production)**

```python
# backend/app/core/encryption_kms.py

import boto3
import json
import base64

class KMSCredentialEncryption:
    """Verschlüsselt mit AWS KMS"""

    def __init__(self):
        self.kms = boto3.client('kms')
        self.key_id = os.environ.get('AWS_KMS_KEY_ID')

    def encrypt(self, credentials: dict) -> bytes:
        """Verschlüsselt mit KMS"""
        json_str = json.dumps(credentials)
        response = self.kms.encrypt(
            KeyId=self.key_id,
            Plaintext=json_str.encode()
        )
        return response['CiphertextBlob']

    def decrypt(self, encrypted_data: bytes) -> dict:
        """Entschlüsselt mit KMS"""
        response = self.kms.decrypt(
            CiphertextBlob=encrypted_data
        )
        return json.loads(response['Plaintext'].decode())
```

**Vorteile:**
- ✅ AWS-managed Keys
- ✅ Automatische Rotation
- ✅ Audit-Trail (CloudTrail)
- ✅ Key kann nicht geklaut werden

**Nachteile:**
- ⚠️ AWS-Abhängigkeit (für StackVertex selbst)
- ⚠️ Kosten (minimal)

**Entscheidung:** Fernet für MVP, KMS für Production

---

#### API-Endpoints

```python
# backend/app/api/credentials.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.encryption import CredentialEncryption
from app.models import CloudCredential
from app.schemas.credentials import CredentialCreate, CredentialResponse
from app.services.aws_validator import validate_aws_credentials

router = APIRouter()
encryptor = CredentialEncryption()

@router.post("/credentials", response_model=CredentialResponse)
async def create_credential(
    credential: CredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Speichere neue Cloud-Credentials"""

    # 1. Validiere Credentials (Test-Call zu Cloud-Provider)
    if credential.provider == "aws":
        is_valid = await validate_aws_credentials(
            access_key=credential.access_key,
            secret_key=credential.secret_key,
            region=credential.region
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid AWS credentials")

    # 2. Verschlüssle
    encrypted = encryptor.encrypt({
        "access_key": credential.access_key,
        "secret_key": credential.secret_key,
        # Weitere provider-spezifische Felder
    })

    # 3. Speichere in DB
    db_credential = CloudCredential(
        user_id=current_user.id,
        provider=credential.provider,
        region=credential.region,
        encrypted_credentials=encrypted,
        credential_name=credential.name,
        is_default=credential.is_default
    )
    db.add(db_credential)
    db.commit()

    # 4. Response (OHNE Secrets!)
    return CredentialResponse(
        id=db_credential.id,
        provider=db_credential.provider,
        name=db_credential.credential_name,
        region=db_credential.region,
        is_default=db_credential.is_default,
        created_at=db_credential.created_at,
        access_key_preview=credential.access_key[:8] + "****"  # Nur Preview
    )

@router.get("/credentials", response_model=List[CredentialResponse])
async def list_credentials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste alle Credentials des Users (ohne Secrets)"""
    credentials = db.query(CloudCredential).filter(
        CloudCredential.user_id == current_user.id
    ).all()

    return [
        CredentialResponse(
            id=cred.id,
            provider=cred.provider,
            name=cred.credential_name,
            access_key_preview="****" + cred.id[:4]  # Nur Hinweis
        )
        for cred in credentials
    ]

@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lösche Credentials"""
    credential = db.query(CloudCredential).filter(
        CloudCredential.id == credential_id,
        CloudCredential.user_id == current_user.id
    ).first()

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    db.delete(credential)
    db.commit()
    return {"message": "Credential deleted"}
```

---

#### Frontend (Credentials-Seite)

```javascript
// frontend/src/js/pages/credentials.js

async function addAWSCredentials(formData) {
    const payload = {
        provider: 'aws',
        name: formData.name,
        region: formData.region,
        access_key: formData.accessKey,
        secret_key: formData.secretKey,
        is_default: formData.isDefault
    };

    try {
        const response = await apiClient.post('/api/v1/credentials', payload);

        // Nach Speichern: Formular leeren!
        document.getElementById('aws-form').reset();

        alert('AWS Credentials erfolgreich gespeichert!');

        // Liste aktualisieren
        await loadCredentialsList();
    } catch (error) {
        alert('Fehler beim Speichern: ' + error.message);
    }
}

function renderCredentialsList(credentials) {
    return `
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Provider</th>
                    <th>Region</th>
                    <th>Access Key</th>
                    <th>Erstellt</th>
                    <th>Aktionen</th>
                </tr>
            </thead>
            <tbody>
                ${credentials.map(cred => `
                    <tr>
                        <td>${cred.name}</td>
                        <td>${cred.provider.toUpperCase()}</td>
                        <td>${cred.region}</td>
                        <td>********${cred.access_key_preview}</td>
                        <td>${formatDate(cred.created_at)}</td>
                        <td>
                            <button onclick="deleteCredential('${cred.id}')">
                                Löschen
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}
```

---

### Validierung

```python
# backend/app/services/aws_validator.py

import boto3
from botocore.exceptions import ClientError

async def validate_aws_credentials(access_key: str, secret_key: str, region: str) -> bool:
    """Prüfe ob AWS Credentials gültig sind"""
    try:
        # Test-Call: STS GetCallerIdentity
        sts = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        response = sts.get_caller_identity()

        # Erfolgreich wenn Account-ID zurückkommt
        return 'Account' in response
    except ClientError as e:
        # Invalid credentials
        return False
```

---

## 5️⃣ Problem: Service-Forms Design

### Herausforderung

AWS hat **hunderte** Services mit **tausenden** Konfigurationsoptionen. Wie bauen wir benutzerfreundliche Forms?

---

### Lösung: Hierarchisches Menü + Wizards

**UI-Struktur:**

```
┌─────────────────────────────────────────────────────────┐
│  [☰ Services]  ▼                                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ▼ Network                                              │
│    ○ VPC                         [+ Add VPC]            │
│    ○ Subnets                     [+ Add Subnet]         │
│    ○ Security Groups             [+ Add Security Group] │
│    ○ Internet Gateway            [+ Add IGW]            │
│    ○ NAT Gateway                 [+ Add NAT]            │
│    ○ Route Tables                [+ Add Route Table]    │
│                                                          │
│  ▼ Compute                                              │
│    ○ EC2 Instances               [+ Launch Instance]    │
│    ○ Auto Scaling Groups         [+ Create ASG]         │
│    ○ Lambda Functions            [+ Create Function]    │
│                                                          │
│  ▼ Storage                                              │
│    ○ S3 Buckets                  [+ Create Bucket]      │
│    ○ EBS Volumes                 [+ Create Volume]      │
│                                                          │
│  ▼ Database                                             │
│    ○ RDS Instances               [+ Create DB]          │
│    ○ DynamoDB Tables             [+ Create Table]       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### Multi-Step Wizard (Beispiel: EC2 Instance)

**Step 1: Basic Settings**
```
┌────────────────────────────────────────┐
│  Launch EC2 Instance - Step 1/4        │
├────────────────────────────────────────┤
│  Instance Name: [___________________]  │
│                                         │
│  Instance Type:                        │
│    ○ t3.micro   (1 vCPU, 1 GB RAM)    │
│    ○ t3.small   (2 vCPU, 2 GB RAM)    │
│    ○ t3.medium  (2 vCPU, 4 GB RAM)    │
│    ○ Custom...                         │
│                                         │
│  AMI:                                  │
│    ● Amazon Linux 2 (Recommended)      │
│    ○ Ubuntu 22.04 LTS                  │
│    ○ Custom AMI ID: [_____________]    │
│                                         │
│  [Cancel]           [Next: Network →]  │
└────────────────────────────────────────┘
```

**Step 2: Network Settings**
```
┌────────────────────────────────────────┐
│  Launch EC2 Instance - Step 2/4        │
├────────────────────────────────────────┤
│  VPC: [vpc-main ▼]                     │
│                                         │
│  Subnet: [subnet-public-1a ▼]         │
│                                         │
│  Security Group:                       │
│    ● Create new security group         │
│      Name: [web-sg______________]      │
│                                         │
│      Inbound Rules:                    │
│      ┌─────────────────────────────┐  │
│      │ HTTP (80)   0.0.0.0/0  [x]  │  │
│      │ HTTPS (443) 0.0.0.0/0  [x]  │  │
│      └─────────────────────────────┘  │
│      [+ Add Rule]                      │
│                                         │
│    ○ Use existing: [existing-sg ▼]     │
│                                         │
│  Public IP: [✓] Assign public IP       │
│                                         │
│  [← Back]                    [Next →]  │
└────────────────────────────────────────┘
```

**Step 3: Storage**
```
┌────────────────────────────────────────┐
│  Launch EC2 Instance - Step 3/4        │
├────────────────────────────────────────┤
│  Root Volume:                          │
│    Size: [20] GB                       │
│    Type: [gp3 ▼] (General Purpose SSD)│
│    [✓] Encrypted                       │
│    [✓] Delete on Termination           │
│                                         │
│  Additional Volumes:                   │
│    [+ Add Volume]                      │
│                                         │
│  [← Back]                    [Next →]  │
└────────────────────────────────────────┘
```

**Step 4: Advanced (Optional)**
```
┌────────────────────────────────────────┐
│  Launch EC2 Instance - Step 4/4        │
├────────────────────────────────────────┤
│  User Data (Startup Script):          │
│  ┌────────────────────────────────┐   │
│  │ #!/bin/bash                     │   │
│  │ yum update -y                   │   │
│  │ yum install -y httpd            │   │
│  │ systemctl start httpd           │   │
│  └────────────────────────────────┘   │
│                                         │
│  IAM Role: [None ▼]                    │
│                                         │
│  Monitoring:                           │
│    [✓] Detailed Monitoring (CloudWatch)│
│                                         │
│  Tags:                                 │
│    Environment: [production]           │
│    [+ Add Tag]                         │
│                                         │
│  [← Back]      [Create Instance]       │
└────────────────────────────────────────┘
```

---

### Form-Komponenten (Wiederverwendbar)

```javascript
// frontend/src/js/components/service-forms/

// Base Components
- input-field.js         // Text/Number Input
- select-dropdown.js     // Dropdown mit Search
- checkbox.js            // Checkbox
- radio-group.js         // Radio Buttons
- tag-input.js           // Key-Value Tags
- cidr-input.js          // CIDR Block (mit Validierung)
- security-rule-editor.js // Ingress/Egress Rules

// AWS-Specific
- instance-type-selector.js  // EC2 Instance Type Picker
- ami-selector.js            // AMI Auswahl (mit Search)
- vpc-selector.js            // VPC Dropdown
- subnet-selector.js         // Subnet Dropdown (filtered by VPC)
- sg-selector.js             // Security Group Selector
```

---

### Defaults (SEHR WICHTIG!)

```javascript
// frontend/src/js/lib/aws-defaults.js

export const AWS_DEFAULTS = {
    vpc: {
        cidr_block: '10.0.0.0/16',
        enable_dns_hostnames: true,
        enable_dns_support: true,
        subnets: [
            {
                cidr_block: '10.0.1.0/24',
                availability_zone_suffix: 'a',
                type: 'public',
                map_public_ip_on_launch: true
            },
            {
                cidr_block: '10.0.10.0/24',
                availability_zone_suffix: 'a',
                type: 'private',
                map_public_ip_on_launch: false
            }
        ],
        internet_gateway: true,
        nat_gateway: true  // In public subnet
    },

    ec2: {
        instance_type: 't3.micro',
        ami: 'data.aws_ami.amazon_linux_2.id',  // Dynamisch
        root_volume: {
            size: 20,
            type: 'gp3',
            encrypted: true,
            delete_on_termination: true
        },
        monitoring: false,
        associate_public_ip: true
    },

    rds: {
        engine: 'postgres',
        engine_version: '15.3',
        instance_class: 'db.t3.micro',
        allocated_storage: 20,
        storage_type: 'gp3',
        storage_encrypted: true,
        multi_az: false,
        backup_retention_period: 7,
        skip_final_snapshot: false
    },

    s3: {
        acl: 'private',
        versioning: true,
        encryption: 'AES256',
        block_public_access: true
    }
};
```

**Verwendung:**
```javascript
function openVPCWizard() {
    const form = document.getElementById('vpc-form');

    // Pre-fill mit Defaults
    form.querySelector('#cidr-block').value = AWS_DEFAULTS.vpc.cidr_block;
    form.querySelector('#enable-dns-hostnames').checked = AWS_DEFAULTS.vpc.enable_dns_hostnames;

    // User kann anpassen
    // ...
}
```

---

## 6️⃣ Problem: Netzwerk-Modellierung

### Defaults statt Auto-Create

**Prinzip:** User entscheidet **bewusst**, welche Ressourcen er erstellen will.

❌ **NICHT:** VPC automatisch im Hintergrund generieren
✅ **SONDERN:** VPC-Form mit sinnvollen Defaults vorausfüllen

---

### VPC-Form mit Pre-filled Defaults

**User-Flow:**
```
1. User klickt "Network" → "Add VPC"
   ↓
2. VPC-Form öffnet sich mit vorausgefüllten Feldern:
   - CIDR Block: 10.0.0.0/16
   - DNS Hostnames: ✓
   - DNS Support: ✓
   - Name Tag: "main-vpc"
   ↓
3. User kann Werte anpassen ODER direkt übernehmen
   ↓
4. User klickt "Create VPC"
   ↓
5. VPC wird zur Architecture JSON hinzugefügt
   ↓
6. User sieht VPC in der Liste (kann weitere Subnets hinzufügen)
```

**Implementierung:**
```javascript
// frontend/src/js/pages/network-builder.js

function openVPCForm() {
    const form = document.getElementById('vpc-form');

    // Pre-fill mit Defaults (aus aws-defaults.js)
    form.querySelector('#vpc-name').value = 'main-vpc';
    form.querySelector('#cidr-block').value = AWS_DEFAULTS.vpc.cidr_block;  // '10.0.0.0/16'
    form.querySelector('#enable-dns-hostnames').checked = AWS_DEFAULTS.vpc.enable_dns_hostnames;
    form.querySelector('#enable-dns-support').checked = AWS_DEFAULTS.vpc.enable_dns_support;

    // User kann jetzt anpassen oder direkt submitten
    showModal('vpc-form-modal');
}

function submitVPCForm() {
    const formData = extractFormData(document.getElementById('vpc-form'));

    // Füge zur Architecture JSON hinzu
    if (!architecture.network.vpcs) {
        architecture.network.vpcs = [];
    }

    architecture.network.vpcs.push({
        id: `vpc-${generateShortId()}`,
        cidr_block: formData.cidr_block,
        enable_dns_hostnames: formData.enable_dns_hostnames,
        enable_dns_support: formData.enable_dns_support,
        tags: {
            Name: formData.name
        },
        subnets: [],  // Leer, User fügt später hinzu
        internet_gateway: null,
        nat_gateways: [],
        route_tables: []
    });

    // Update UI
    renderNetworkOverview();
    closeModal('vpc-form-modal');
}
```

**Wichtig:**
- User hat volle Kontrolle
- Nichts wird automatisch erstellt
- Defaults helfen, schnell loszulegen
- Alles ist transparent

---

### Quick-Start Template (Optional)

**Für Einsteiger:** "Standard Web App Network" Template

```javascript
function applyWebAppNetworkTemplate() {
    // User klickt "Quick Start: Web App Network"
    // → VPC + 2 Subnets + IGW + NAT + Routes werden GLEICHZEITIG zur JSON hinzugefügt

    const region = architecture.metadata.region;

    architecture.network = {
        vpcs: [
            {
                id: 'vpc-main',
                cidr_block: '10.0.0.0/16',
                enable_dns_hostnames: true,
                enable_dns_support: true,
                tags: { Name: 'main-vpc' },

                subnets: [
                    {
                        id: 'subnet-public-1a',
                        cidr_block: '10.0.1.0/24',
                        availability_zone: `${region}a`,
                        type: 'public',
                        map_public_ip_on_launch: true,
                        tags: { Name: 'public-subnet-1a' }
                    },
                    {
                        id: 'subnet-private-1a',
                        cidr_block: '10.0.10.0/24',
                        availability_zone: `${region}a`,
                        type: 'private',
                        map_public_ip_on_launch: false,
                        tags: { Name: 'private-subnet-1a' }
                    }
                ],

                internet_gateway: {
                    id: 'igw-main',
                    tags: { Name: 'main-igw' }
                },

                nat_gateways: [
                    {
                        id: 'nat-1a',
                        subnet_id: 'subnet-public-1a',
                        tags: { Name: 'nat-1a' }
                    }
                ],

                route_tables: [
                    {
                        id: 'rtb-public',
                        subnet_ids: ['subnet-public-1a'],
                        routes: [
                            { destination_cidr_block: '0.0.0.0/0', gateway_id: 'igw-main' }
                        ],
                        tags: { Name: 'public-route-table' }
                    },
                    {
                        id: 'rtb-private',
                        subnet_ids: ['subnet-private-1a'],
                        routes: [
                            { destination_cidr_block: '0.0.0.0/0', nat_gateway_id: 'nat-1a' }
                        ],
                        tags: { Name: 'private-route-table' }
                    }
                ]
            }
        ],
        security_groups: []
    };

    // Info-Message
    showNotification('✓ Standard Web App Network wurde hinzugefügt. Du kannst alle Komponenten unter "Network" anpassen.');

    // Render
    renderNetworkOverview();
}
```

**UI:**
```
┌──────────────────────────────────────────┐
│  Network Configuration                    │
├──────────────────────────────────────────┤
│                                           │
│  No VPCs configured yet.                 │
│                                           │
│  [+ Add VPC Manually]                    │
│                                           │
│  Or use a template:                      │
│  [Quick Start: Web App Network]          │
│  [Quick Start: Serverless (no VPC)]      │
│                                           │
└──────────────────────────────────────────┘
```

---

### Zusammenhänge validieren

**Beispiel: EC2 braucht Subnet, Subnet braucht VPC**

```javascript
// Validierung beim Hinzufügen
function validateEC2Instance(instance, architecture) {
    const errors = [];

    // 1. Subnet existiert?
    const subnet = architecture.network.vpcs
        .flatMap(vpc => vpc.subnets)
        .find(s => s.id === instance.subnet_id);

    if (!subnet) {
        errors.push(`Subnet "${instance.subnet_id}" existiert nicht. Bitte erstelle erst ein Subnet.`);
    }

    // 2. Security Group existiert?
    for (const sg_id of instance.vpc_security_group_ids) {
        const sg = architecture.network.security_groups.find(s => s.id === sg_id);
        if (!sg) {
            errors.push(`Security Group "${sg_id}" existiert nicht.`);
        }
    }

    return errors;
}
```

---

## 7️⃣ Problem: Terraform Deployment

### Deployment-Flow

```
1. User klickt "Deploy" in Architecture Detail View
   ↓
2. Frontend: POST /api/v1/deployments
   {
     "architecture_id": "...",
     "credential_id": "...",
     "dry_run": false
   }
   ↓
3. Backend:
   a) Lade Architecture JSON
   b) Generiere Terraform Code
   c) Schreibe in temporäres Verzeichnis
   d) Hole Credentials (entschlüsselt)
   e) Setze AWS Env Vars
   f) terraform init
   g) terraform plan
   h) (optional) terraform apply
   ↓
4. Stream Output zurück zu Frontend (WebSocket/SSE)
   ↓
5. Speichere Deployment-Status in DB
```

---

### Implementierung

```python
# backend/app/services/terraform_deployer.py

import subprocess
import tempfile
import os
from pathlib import Path

class TerraformDeployer:
    """Führt Terraform-Deployments aus"""

    async def deploy(
        self,
        architecture_json: dict,
        credentials: dict,
        dry_run: bool = True
    ) -> dict:
        """Deploy Architecture mit Terraform"""

        # 1. Generiere Terraform Code
        tf_generator = TerraformGenerator()
        terraform_code = tf_generator.generate(architecture_json)

        # 2. Erstelle temporäres Verzeichnis
        with tempfile.TemporaryDirectory() as tmpdir:
            # 3. Schreibe Terraform-Dateien
            tf_dir = Path(tmpdir)
            (tf_dir / 'main.tf').write_text(terraform_code)
            (tf_dir / 'variables.tf').write_text(self._generate_variables())
            (tf_dir / 'terraform.tfvars').write_text(self._generate_tfvars())

            # 4. Setze Credentials als Env Vars
            env = os.environ.copy()
            env['AWS_ACCESS_KEY_ID'] = credentials['access_key']
            env['AWS_SECRET_ACCESS_KEY'] = credentials['secret_key']
            env['AWS_REGION'] = architecture_json['metadata']['region']

            # 5. Terraform Init
            result_init = subprocess.run(
                ['terraform', 'init'],
                cwd=tmpdir,
                env=env,
                capture_output=True,
                text=True
            )

            if result_init.returncode != 0:
                raise Exception(f"Terraform init failed: {result_init.stderr}")

            # 6. Terraform Plan
            result_plan = subprocess.run(
                ['terraform', 'plan', '-out=tfplan'],
                cwd=tmpdir,
                env=env,
                capture_output=True,
                text=True
            )

            if result_plan.returncode != 0:
                raise Exception(f"Terraform plan failed: {result_plan.stderr}")

            # 7. Terraform Apply (nur wenn nicht dry_run)
            if not dry_run:
                result_apply = subprocess.run(
                    ['terraform', 'apply', '-auto-approve', 'tfplan'],
                    cwd=tmpdir,
                    env=env,
                    capture_output=True,
                    text=True
                )

                if result_apply.returncode != 0:
                    raise Exception(f"Terraform apply failed: {result_apply.stderr}")

                # 8. Hole Outputs
                result_output = subprocess.run(
                    ['terraform', 'output', '-json'],
                    cwd=tmpdir,
                    env=env,
                    capture_output=True,
                    text=True
                )

                outputs = json.loads(result_output.stdout) if result_output.returncode == 0 else {}
            else:
                outputs = {}

            return {
                'success': True,
                'plan_output': result_plan.stdout,
                'apply_output': result_apply.stdout if not dry_run else None,
                'outputs': outputs
            }
```

---

### WebSocket für Live-Output

```python
# backend/app/api/deployments.py

from fastapi import WebSocket

@router.websocket("/deployments/{deployment_id}/stream")
async def deployment_stream(websocket: WebSocket, deployment_id: UUID):
    """Stream Terraform Output live"""
    await websocket.accept()

    try:
        # Run Deployment in Background Task
        # Send Output Lines via WebSocket

        process = subprocess.Popen(
            ['terraform', 'apply', '-auto-approve'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            await websocket.send_text(line)

        process.wait()

        await websocket.send_json({
            'type': 'complete',
            'success': process.returncode == 0
        })
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': str(e)
        })
    finally:
        await websocket.close()
```

---

## 📋 Roadmap & Phasen

### Phase 1: MVP (4-6 Wochen)

**Ziel:** Grundlegende Terraform-Generation + Deployment

✅ **Credentials Management**
- DB-Schema
- Encryption (Fernet)
- API-Endpoints
- Frontend: Credentials-Seite

✅ **Statische AWS-Daten**
- Hardcoded Instance-Types (Top 20)
- Hardcoded AMIs
- Regions-Liste

✅ **Detaillierte Service-Forms**
- VPC Wizard (+ Auto-Create)
- EC2 Instance Wizard (4 Steps)
- S3 Bucket Form
- RDS Form

✅ **JSON-Schema v2**
- Network-Struktur (VPC, Subnets, SG, IGW, NAT, Routes)
- Compute (EC2)
- Storage (S3)
- Database (RDS)

✅ **Terraform Generator**
- Jinja2 Templates
- VPC + Networking
- EC2 Instances
- S3 Buckets
- RDS Instances

✅ **Deployment (Basic)**
- Terraform Runner (subprocess)
- Plan + Apply
- Error Handling

---

### Phase 2: Production-Ready (6-8 Wochen)

✅ **Aktuelle AWS-Daten**
- Sync-Job (Celery/Cron)
- CloudFormation Specs
- SSM Parameter Store (AMIs)
- DB-Tabellen

✅ **Erweiterte Services**
- Lambda Functions
- Auto Scaling Groups
- Application Load Balancer
- CloudFront
- Route53

✅ **Deployment-Verbesserungen**
- WebSocket Live-Output
- Rollback-Funktion
- State-Management (S3 Backend)
- Multi-Environment (dev, staging, prod)

✅ **Validierung**
- Pre-Deployment Checks (Kosten-Schätzung, Security-Scan)
- Terraform Validate
- Dry-Run Enforced

---

### Phase 3: Advanced (8-12 Wochen)

✅ **Multi-Cloud**
- Azure Support
- GCP Support

✅ **Visual Builder**
- Drag & Drop Canvas
- Component Library
- Auto-Layout

✅ **AI-Powered**
- Architektur-Vorschläge
- Kosten-Optimierung
- Security Best Practices

---

## 🎯 Nächste Schritte

### Sofort (Diese Woche):

1. **Credentials-Schema erstellen** (DB Migration)
2. **Encryption-Modul implementieren** (Fernet)
3. **Credentials-API implementieren**
4. **Credentials-Frontend** (Seite + Form)

### Diese Sprint (2 Wochen):

1. **JSON-Schema v2** (Network-Struktur)
2. **VPC-Form** (mit Auto-Create)
3. **EC2-Form** (Multi-Step Wizard)
4. **Terraform Generator v1** (VPC + EC2)

### Nächster Sprint (2 Wochen):

1. **Terraform Deployer** (subprocess)
2. **Deployment-API**
3. **Deployment-Frontend** (Button + Status)

---

**Bereit loszulegen?** 🚀

Soll ich mit dem Credentials-Schema anfangen oder hast du Fragen zu einem der Punkte?
