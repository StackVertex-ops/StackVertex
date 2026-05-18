"""
Three-Tier Web Application Blueprint

Production-ready VPC + ALB + EC2 Auto Scaling + RDS
Perfekt für: Traditionelle Web Apps, CMS, E-Commerce, SaaS Backends
"""

from .base import (
    Blueprint,
    BlueprintCategory,
    BlueprintDifficulty,
    BlueprintFormField,
    BlueprintMetadata,
    CostEstimate,
    FieldType,
    FieldValidation,
    SelectOption,
)

THREE_TIER_WEB = Blueprint(
    metadata=BlueprintMetadata(
        id="three-tier-web",
        name="Three-Tier Web Application",
        description="Production-ready Web App mit VPC, Load Balancer, Auto Scaling und RDS Database",
        category=BlueprintCategory.WEBAPP,
        difficulty=BlueprintDifficulty.INTERMEDIATE,
        estimated_cost=CostEstimate(
            min_usd=80.0,
            typical_usd=150.0,
            max_usd=400.0,
            breakdown={
                "EC2 (2x t3.small, 24/7)": 30.30,
                "Application Load Balancer": 22.27,
                "RDS PostgreSQL (db.t3.micro, Multi-AZ)": 27.74,
                "NAT Gateway": 32.85,
                "EBS Storage (2x 20GB gp3)": 3.20,
                "RDS Storage (20GB gp3)": 2.30,
                "Data Transfer": 10.00,
                "CloudWatch Logs": 5.00,
            },
            assumptions=[
                "2x EC2 t3.small instances (24/7 running)",
                "RDS db.t3.micro Multi-AZ für High Availability",
                "Single NAT Gateway (HA würde 2x kosten)",
                "~100GB Data Transfer out pro Monat",
                "us-east-1 Region Pricing",
            ],
        ),
        setup_time_minutes=30,
        use_cases=[
            "Traditionelle Web Applications (Django, Rails, Laravel, ASP.NET)",
            "Content Management Systeme (WordPress, Drupal)",
            "E-Commerce Plattformen",
            "SaaS Backend Services",
            "Intranet Applications",
        ],
        features=[
            "High Availability (Multi-AZ)",
            "Auto Scaling (automatische Server-Anpassung)",
            "Load Balancing (ALB mit Health Checks)",
            "Private Subnets für Database Security",
            "NAT Gateway für outbound Internet",
            "RDS Automated Backups (7 Tage)",
            "SSL/TLS Termination am Load Balancer",
        ],
        limitations=[
            "Kosten ~$80-150/Monat MINIMUM (nicht für kleine Hobby-Projekte)",
            "NAT Gateway kostet auch ohne Traffic ~$33/Monat",
            "Erfordert Code-Deployment (nicht managed wie Heroku)",
            "Keine Auto-Scaling für RDS (manuelle Skalierung nötig)",
        ],
        icon="layers",
    ),
    form_schema=[
        BlueprintFormField(
            name="app_name",
            type=FieldType.TEXT,
            label="Application Name",
            description="Name deiner Application (z.B. 'my-web-app')",
            required=True,
            validation=FieldValidation(
                pattern=r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$",
            ),
        ),
        BlueprintFormField(
            name="vpc_cidr",
            type=FieldType.CIDR,
            label="VPC CIDR Block",
            description="IP-Bereich für deine VPC (Standard: 10.0.0.0/16)",
            required=True,
            default="10.0.0.0/16",
            validation=FieldValidation(
                pattern=r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$",
            ),
            constraints="aws.vpc.cidr",
        ),
        BlueprintFormField(
            name="ec2_instance_type",
            type=FieldType.SELECT,
            label="EC2 Instance Type",
            description="Instance-Größe für deine Web Server",
            required=True,
            default="t3.small",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="t3.micro",
                        label="t3.micro (1 vCPU, 1GB RAM) - $7.30/Monat",
                        description="Nur für Dev/Test, nicht Production!",
                        price_factor=0.5,
                    ),
                    SelectOption(
                        value="t3.small",
                        label="t3.small (2 vCPU, 2GB RAM) - $15.18/Monat",
                        description="Minimum für kleine Production Apps",
                        price_factor=1.0,
                    ),
                    SelectOption(
                        value="t3.medium",
                        label="t3.medium (2 vCPU, 4GB RAM) - $30.37/Monat",
                        description="Gut für mittelgroße Apps",
                        price_factor=2.0,
                    ),
                    SelectOption(
                        value="t3.large",
                        label="t3.large (2 vCPU, 8GB RAM) - $60.74/Monat",
                        description="Größere Apps mit mehr Traffic",
                        price_factor=4.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="min_instances",
            type=FieldType.NUMBER,
            label="Minimum Instances",
            description="Minimale Anzahl EC2 Instances (min 2 für HA)",
            required=True,
            default=2,
            validation=FieldValidation(min=1, max=10),
        ),
        BlueprintFormField(
            name="max_instances",
            type=FieldType.NUMBER,
            label="Maximum Instances",
            description="Maximale Anzahl EC2 Instances (Auto Scaling Limit)",
            required=True,
            default=4,
            validation=FieldValidation(min=1, max=20),
        ),
        BlueprintFormField(
            name="rds_engine",
            type=FieldType.SELECT,
            label="Database Engine",
            description="Welche Datenbank möchtest du nutzen?",
            required=True,
            default="postgres",
            validation=FieldValidation(
                options=[
                    SelectOption(value="postgres", label="PostgreSQL 16"),
                    SelectOption(value="mysql", label="MySQL 8.0"),
                    SelectOption(value="mariadb", label="MariaDB 10.11"),
                ],
            ),
        ),
        BlueprintFormField(
            name="rds_instance_class",
            type=FieldType.SELECT,
            label="Database Instance Class",
            description="RDS Instance-Größe",
            required=True,
            default="db.t3.micro",
            validation=FieldValidation(
                options=[
                    SelectOption(
                        value="db.t3.micro",
                        label="db.t3.micro (2 vCPU, 1GB RAM) - $13.87/Monat",
                        description="Minimum für Dev/Test",
                        price_factor=0.5,
                    ),
                    SelectOption(
                        value="db.t3.small",
                        label="db.t3.small (2 vCPU, 2GB RAM) - $27.74/Monat",
                        description="Klein aber production-tauglich",
                        price_factor=1.0,
                    ),
                    SelectOption(
                        value="db.t3.medium",
                        label="db.t3.medium (2 vCPU, 4GB RAM) - $55.48/Monat",
                        description="Gute Balance für mittelgroße DBs",
                        price_factor=2.0,
                    ),
                    SelectOption(
                        value="db.t3.large",
                        label="db.t3.large (2 vCPU, 8GB RAM) - $110.96/Monat",
                        description="Größere Datenbanken",
                        price_factor=4.0,
                    ),
                ],
            ),
        ),
        BlueprintFormField(
            name="rds_storage_gb",
            type=FieldType.NUMBER,
            label="Database Storage (GB)",
            description="RDS Storage Size (20-65536 GB)",
            required=True,
            default=20,
            validation=FieldValidation(min=20, max=65536),
            constraints="aws.rds.storage",
        ),
        BlueprintFormField(
            name="rds_multi_az",
            type=FieldType.TOGGLE,
            label="Multi-AZ Deployment",
            description="Hochverfügbarkeit (kostet 2x, aber wichtig für Production!)",
            required=False,
            default=True,
        ),
        BlueprintFormField(
            name="enable_elasticache",
            type=FieldType.TOGGLE,
            label="ElastiCache Redis aktivieren",
            description="In-Memory Caching für bessere Performance (+$15/Monat)",
            required=False,
            default=False,
        ),
        BlueprintFormField(
            name="enable_bastion_host",
            type=FieldType.TOGGLE,
            label="Bastion Host aktivieren",
            description="SSH-Zugriff zu privaten Instances (+$7.30/Monat)",
            required=False,
            default=False,
        ),
        BlueprintFormField(
            name="ssl_certificate_arn",
            type=FieldType.TEXT,
            label="SSL Certificate ARN (optional)",
            description="ACM Certificate ARN für HTTPS (z.B. arn:aws:acm:...)",
            required=False,
            default=None,
        ),
    ],
    aws_resources=[
        "VPC",
        "Internet Gateway",
        "NAT Gateway",
        "Subnets (Public + Private)",
        "Route Tables",
        "Security Groups",
        "Application Load Balancer",
        "EC2 Auto Scaling Group",
        "Launch Template",
        "RDS",
        "ElastiCache (optional)",
        "CloudWatch",
        "IAM Roles",
    ],
    terraform_templates=[
        "blueprints/three_tier_web/vpc.tf.j2",
        "blueprints/three_tier_web/security_groups.tf.j2",
        "blueprints/three_tier_web/alb.tf.j2",
        "blueprints/three_tier_web/asg.tf.j2",
        "blueprints/three_tier_web/rds.tf.j2",
        "blueprints/three_tier_web/elasticache.tf.j2",
        "blueprints/three_tier_web/bastion.tf.j2",
        "blueprints/three_tier_web/iam.tf.j2",
    ],
    deployment_guide="""
## Deployment Guide: Three-Tier Web Application

### 1. VPC & Networking Setup
Nach dem Terraform Apply hast du:
- VPC mit Public + Private Subnets (Multi-AZ)
- Internet Gateway für Public Subnets
- NAT Gateway für Private Subnets (outbound Internet)
- Security Groups (ALB, EC2, RDS, Bastion)

### 2. Application Code deployen

#### Option A: Mit User Data (schnell für Tests)
Terraform erstellt Launch Template mit User Data:
```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
docker run -d -p 80:8000 your-dockerhub/your-app:latest
```

#### Option B: Mit CI/CD (Production)
```bash
# AWS CodeDeploy oder GitHub Actions
# Beispiel: Code via S3 deployen
aws s3 cp app.zip s3://your-deployment-bucket/
aws deploy create-deployment \\
  --application-name your-app \\
  --deployment-group your-group \\
  --s3-location bucket=your-deployment-bucket,key=app.zip,bundleType=zip
```

### 3. Database Migration
```bash
# SSH via Bastion Host zu EC2 Instance
ssh -i key.pem ec2-user@bastion-ip
ssh ec2-user@private-instance-ip

# Run migrations (Beispiel Django)
python manage.py migrate

# Oder via psql direkt
psql -h YOUR_RDS_ENDPOINT -U postgres -d mydb < schema.sql
```

### 4. Health Checks konfigurieren
ALB Target Group prüft automatisch:
- `/health` Endpoint (konfigurierbar)
- Interval: 30s
- Timeout: 5s
- Healthy Threshold: 2
- Unhealthy Threshold: 3

Stelle sicher, dass deine App einen `/health` Endpoint hat!

### 5. Auto Scaling testen
```bash
# Manueller Test: CPU-Last erzeugen
ssh ec2-user@instance-ip
stress-ng --cpu 2 --timeout 300s

# CloudWatch Alarm sollte triggern → neue Instance starten
```

### 6. SSL/TLS (HTTPS)
#### Certificate via ACM erstellen:
```bash
aws acm request-certificate \\
  --domain-name www.example.com \\
  --validation-method DNS

# ARN in Terraform Variable eintragen und erneut apply
```

### 7. Monitoring
CloudWatch Dashboards:
- ALB Request Count, Target Response Time
- EC2 CPU, Memory (via CloudWatch Agent)
- RDS Connections, CPU, Storage
- Auto Scaling Activities

### Best Practices:
- **Backups:** RDS Automated Backups aktiviert (7 Tage default)
- **Snapshots:** Regelmäßige manuelle Snapshots vor großen Änderungen
- **Secrets:** RDS Passwort in AWS Secrets Manager (nicht Terraform State!)
- **Updates:** AMI regelmäßig aktualisieren (Security Patches)
- **Monitoring:** CloudWatch Alarms für CPU > 80%, Disk > 80%
- **Cost Optimization:** Reserved Instances für konstante Workloads (-40% Kosten)

### Troubleshooting:
- **Instances nicht healthy:** Prüfe Security Groups, Health Check Endpoint
- **Database nicht erreichbar:** Security Group muss EC2 Security Group erlauben
- **NAT Gateway teuer:** Überlege VPC Endpoints für AWS Services (S3, DynamoDB)
- **Auto Scaling triggert zu oft:** CloudWatch Alarm Thresholds anpassen
""",
)
