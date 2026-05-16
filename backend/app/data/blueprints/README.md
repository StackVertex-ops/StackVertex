# OverCloud Blueprint Library

Zentrale Blueprint-Bibliothek mit realistischen, production-ready Architektur-Templates.

## Verfügbare Blueprints

### 1. Static Website (`static-website`)
**Kosten:** $1-20/Monat | **Schwierigkeit:** Beginner

S3 + CloudFront + Route53 für statische Websites.

**Use Cases:**
- Landing Pages
- Dokumentation (MkDocs, Docusaurus)
- Portfolio Websites
- Marketing Sites

**AWS Services:** S3, CloudFront, Route53, ACM

---

### 2. Single Page Application (`spa`)
**Kosten:** $2-150/Monat | **Schwierigkeit:** Beginner

S3 Frontend + CloudFront + API Gateway + Lambda Backend + DynamoDB.

**Use Cases:**
- React/Vue/Angular Apps
- Progressive Web Apps (PWA)
- Dashboards & Admin Panels
- SaaS Frontends

**AWS Services:** S3, CloudFront, API Gateway, Lambda, DynamoDB, Route53, ACM, Cognito (optional)

---

### 3. Simple REST API (`simple-api`)
**Kosten:** $0-100/Monat | **Schwierigkeit:** Beginner

API Gateway + Lambda + DynamoDB für serverlose REST APIs.

**Use Cases:**
- REST APIs für Web/Mobile Apps
- Serverlose Microservices
- Webhook Endpoints
- CRUD APIs

**AWS Services:** API Gateway, Lambda, DynamoDB, CloudWatch

---

### 4. Three-Tier Web Application (`three-tier-web`)
**Kosten:** $80-400/Monat | **Schwierigkeit:** Intermediate

VPC + ALB + EC2 Auto Scaling + RDS für traditionelle Web Apps.

**Use Cases:**
- Django, Rails, Laravel, ASP.NET Apps
- Content Management Systeme
- E-Commerce Plattformen
- SaaS Backend Services

**AWS Services:** VPC, ALB, EC2 Auto Scaling, RDS, NAT Gateway, CloudWatch, ElastiCache (optional)

---

### 5. WordPress (`wordpress`)
**Kosten:** $40-200/Monat | **Schwierigkeit:** Intermediate

EC2 + RDS MySQL + EFS + CloudFront für managed WordPress.

**Use Cases:**
- WordPress Blogs & Corporate Websites
- E-Commerce mit WooCommerce
- Membership Sites
- News & Magazine Websites

**AWS Services:** EC2, RDS MySQL, EFS, CloudFront, Route53, ACM

---

## Verwendung

### Python API

```python
from app.data.blueprints import (
    get_blueprint,
    list_blueprints,
    search_blueprints,
    BlueprintCategory,
    BlueprintDifficulty,
)

# Einzelnen Blueprint holen
blueprint = get_blueprint("static-website")
print(blueprint.metadata.name)
print(blueprint.metadata.estimated_cost.typical_usd)

# Alle Blueprints listen
all_blueprints = list_blueprints()

# Filtern nach Kategorie
api_blueprints = list_blueprints(category=BlueprintCategory.API)

# Filtern nach Schwierigkeit
beginner_blueprints = list_blueprints(difficulty=BlueprintDifficulty.BEGINNER)

# Filtern nach max. Kosten
cheap_blueprints = list_blueprints(max_cost_usd=50)

# Suche
wordpress_blueprints = search_blueprints("wordpress")
```

### Form Schema für Frontend

Jeder Blueprint enthält ein `form_schema`, das alle Konfigurationsfelder definiert:

```python
blueprint = get_blueprint("simple-api")

for field in blueprint.form_schema:
    print(f"{field.label} ({field.type})")
    print(f"  Default: {field.default}")
    print(f"  Required: {field.required}")
    if field.validation:
        print(f"  Validation: {field.validation}")
```

### Terraform Template Generierung

```python
from jinja2 import Environment, FileSystemLoader

blueprint = get_blueprint("static-website")

# Jinja2 Environment
env = Environment(loader=FileSystemLoader("templates/terraform"))

# Render Templates
for template_path in blueprint.terraform_templates:
    template = env.get_template(template_path)
    output = template.render(
        blueprint_id=blueprint.metadata.id,
        website_name="my-website",
        domain_name="www.example.com",
        cloudfront_price_class="PriceClass_100",
        enable_versioning=False,
        # ... weitere Variablen
    )
    print(output)
```

---

## Blueprint-Struktur

Jeder Blueprint besteht aus:

### 1. Metadata
- ID, Name, Beschreibung
- Kategorie, Schwierigkeit
- Kostenabschätzung (min/typical/max)
- Setup-Zeit
- Use Cases
- Features & Limitations

### 2. Form Schema
Liste von Formularfeldern:
- Name, Type, Label, Description
- Required, Default Value
- Validierung (min, max, pattern, options)
- AWS Constraints (Referenz zu `aws_constraints.py`)

### 3. AWS Resources
Liste der verwendeten AWS Services

### 4. Terraform Templates
Liste der Terraform Template-Pfade (Jinja2)

### 5. Deployment Guide
Markdown-Anleitung für Deployment & Best Practices

---

## Neue Blueprints hinzufügen

1. **Erstelle neue Blueprint-Datei:**
   ```
   backend/app/data/blueprints/my_blueprint.py
   ```

2. **Definiere Blueprint:**
   ```python
   from .base import Blueprint, BlueprintMetadata, ...

   MY_BLUEPRINT = Blueprint(
       metadata=BlueprintMetadata(...),
       form_schema=[...],
       aws_resources=[...],
       terraform_templates=[...],
       deployment_guide="...",
   )
   ```

3. **Erstelle Terraform Templates:**
   ```
   backend/templates/terraform/blueprints/my_blueprint/
   ├── main.tf.j2
   ├── networking.tf.j2
   └── ...
   ```

4. **Registriere Blueprint:**
   ```python
   # In blueprints/__init__.py
   from .my_blueprint import MY_BLUEPRINT

   BLUEPRINT_REGISTRY = {
       ...
       "my-blueprint": MY_BLUEPRINT,
   }
   ```

---

## Best Practices

### Kostenabschätzungen
- **min_usd:** Absolutes Minimum (z.B. nur AWS Free Tier)
- **typical_usd:** Realistischer Production-Betrieb (1000-10000 Nutzer/Tag)
- **max_usd:** High-Traffic Szenario oder alle Features aktiviert
- **breakdown:** Detaillierte Kostenaufschlüsselung pro Service
- **assumptions:** Klare Annahmen dokumentieren (Traffic, Storage, Region)

### Form Fields
- Sinnvolle Defaults setzen (Production-ready, nicht billigste Option!)
- Validation Rules nutzen (min, max, pattern)
- AWS Constraints referenzieren (`constraints="aws.rds.storage"`)
- Abhängigkeiten definieren (`depends_on="enable_feature"`)

### Terraform Templates
- Jinja2 Syntax nutzen (`{{ variable }}`, `{% if %}`, `{% for %}`)
- Production-ready Defaults (Encryption, Backups, Multi-AZ wo sinnvoll)
- Proper Tagging (Name, Blueprint, Environment, ManagedBy)
- Outputs definieren (wichtige ARNs, URLs, etc.)

### Deployment Guides
- Markdown-Format
- Klare Schritt-für-Schritt Anleitung
- Code-Beispiele (CLI Commands, Config Files)
- Troubleshooting-Sektion
- Best Practices & Security Hardening

---

## Roadmap

### Geplante Blueprints (Phase 2)
- **Container App** (ECS Fargate + ALB + RDS)
- **Serverless App** (Lambda + API Gateway + EventBridge + SQS)
- **Data Lake** (S3 + Glue + Athena + QuickSight)
- **Batch Processing** (Lambda + S3 + Step Functions)
- **Microservices** (ECS + ALB + Service Discovery + RDS/DynamoDB)

### Multi-Cloud Support (Phase 3)
- Azure Blueprints
- GCP Blueprints
- Hybrid Cloud Blueprints

---

Last updated: 2026-05-16
