# Infrastructure Designer - User Guide

Vollständige Dokumentation des visuellen Infrastructure Designers.

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Component Types](#component-types)
3. [Configuration Fields](#configuration-fields)
4. [IP Calculator](#ip-calculator)
5. [Connection Types](#connection-types)
6. [Terraform Output](#terraform-output)
7. [Best Practices](#best-practices)

---

## Übersicht

Der Infrastructure Designer besteht aus drei Hauptkomponenten:

1. **Component Palette (links)** - Draggable AWS-Komponenten
2. **Canvas (oben)** - Visuelle Darstellung mit Cytoscape.js
3. **Configuration Tabs (unten)** - 4 Tabs für detaillierte Konfiguration

### Workflow

```
Drag & Drop → Configure → Save → Generate Terraform → Deploy
```

---

## Component Types

### Network Components

#### VPC (Virtual Private Cloud)
**Zweck:** Isoliertes virtuelles Netzwerk in AWS  
**Icon:** 🌐  
**Default CIDR:** `10.0.0.0/16`

**Konfiguration:**
- **Name:** Eindeutiger VPC-Name (z.B. `production-vpc`)
- **CIDR Block:** IP-Adressbereich (z.B. `10.0.0.0/16`)
  - Minimum: `/28` (16 IPs)
  - Maximum: `/16` (65,536 IPs)
  - Empfohlen: `/16` oder `/20`
- **Region:** AWS-Region (us-east-1, eu-central-1, etc.)
- **DNS Hostnames:** Enable/Disable
- **DNS Support:** Enable/Disable (empfohlen: beide aktiviert)

**IP Calculator Anzeige:**
```
Total IPs: 65,536
Nutzbar: 65,531 (AWS reserviert 5 IPs)
Range: 10.0.0.0 - 10.0.255.255
```

#### Subnet
**Zweck:** Unterteilung einer VPC in kleinere Netzwerke  
**Icon:** 📦  
**Default CIDR:** `10.0.1.0/24`

**Konfiguration:**
- **Name:** Beschreibender Name (z.B. `public-subnet-1a`)
- **VPC:** Parent VPC auswählen (Dropdown)
- **CIDR Block:** Muss innerhalb VPC CIDR liegen
  - Beispiel VPC: `10.0.0.0/16`
  - Subnet Public: `10.0.1.0/24` (251 usable IPs)
  - Subnet Private: `10.0.2.0/24` (251 usable IPs)
  - Subnet DB: `10.0.3.0/24` (251 usable IPs)
- **Subnet Type:**
  - **Public:** Hat Internet Gateway Route (Web-Server)
  - **Private:** Nur interne Kommunikation (App-Server)
  - **Database:** Isoliert für Datenbanken (RDS, ElastiCache)
- **Availability Zone:** us-east-1a, us-east-1b, etc.

**IP Calculator Anzeige:**
```
Total IPs: 256
Nutzbar: 251
IP Range: 10.0.1.0 - 10.0.1.255
AWS Reserved:
  10.0.1.0   - Network address
  10.0.1.1   - VPC router
  10.0.1.2   - DNS server
  10.0.1.3   - Future use
  10.0.1.255 - Broadcast
```

**Best Practice:**
- Public Subnets: `/24` (251 IPs)
- Private Subnets: `/20` (4,091 IPs) für Autoscaling
- Database Subnets: `/24` (ausreichend für RDS Multi-AZ)

#### Internet Gateway (IGW)
**Zweck:** Ermöglicht Internet-Zugriff für Public Subnets  
**Icon:** 🌍  
**Konfiguration:** Nur Name, wird automatisch an VPC attached

#### NAT Gateway
**Zweck:** Ermöglicht Private Subnets Internet-Zugriff (ausgehend)  
**Icon:** 🔀  
**Konfiguration:**
- **Subnet:** Public Subnet (benötigt Elastic IP)
- **Allocation ID:** Auto-generiert

---

### Security Components

#### Security Group
**Zweck:** Virtuelle Firewall für EC2, RDS, ALB  
**Icon:** 🛡️  
**Default:** Allow all outbound, deny all inbound

**Konfiguration:**
- **Name:** z.B. `web-server-sg`
- **Description:** Beschreibung (wird in AWS angezeigt)
- **Inbound Rules:**
  - Port 80 (HTTP) from 0.0.0.0/0
  - Port 443 (HTTPS) from 0.0.0.0/0
  - Port 22 (SSH) from MY_IP
- **Outbound Rules:**
  - All traffic to 0.0.0.0/0 (default)

**Beispiel Web-Server:**
```
Inbound:
  HTTP  (80)   ← 0.0.0.0/0
  HTTPS (443)  ← 0.0.0.0/0
  SSH   (22)   ← 203.0.113.25/32
Outbound:
  All traffic  → 0.0.0.0/0
```

**Beispiel Database:**
```
Inbound:
  PostgreSQL (5432)  ← web-server-sg
Outbound:
  All traffic        → 0.0.0.0/0
```

#### Network ACL (NACL)
**Zweck:** Subnet-Level Firewall (stateless)  
**Icon:** 🔒  
**Konfiguration:** Inbound/Outbound Rules mit Rule Numbers

**Unterschied zu Security Groups:**
- NACL = Subnet-Level (stateless)
- Security Group = Instance-Level (stateful)
- Empfohlung: Security Groups bevorzugen

#### IAM Role
**Zweck:** Berechtigungen für AWS-Services  
**Icon:** 👤  
**Konfiguration:**
- **Name:** z.B. `ec2-s3-read-role`
- **Policies:** Managed oder Custom Policies

---

### Data Components

#### RDS (Relational Database Service)
**Zweck:** Managed SQL-Datenbank  
**Icon:** 💾  
**Engines:** PostgreSQL, MySQL, MariaDB, Aurora

**Konfiguration:**
- **Name:** DB Instance Identifier (z.B. `production-db`)
- **Engine:** PostgreSQL, MySQL, MariaDB, Aurora
- **Engine Version:** z.B. `14.7` für PostgreSQL
- **Instance Class:**
  - `db.t3.micro` - 1 vCPU, 1GB RAM ($0.017/hr)
  - `db.t3.small` - 2 vCPU, 2GB RAM ($0.034/hr)
  - `db.t3.medium` - 2 vCPU, 4GB RAM ($0.068/hr)
  - `db.r6g.large` - 2 vCPU, 16GB RAM ($0.24/hr) - Production
- **Storage:**
  - Type: GP3 (empfohlen), GP2, io1
  - Size: 20GB - 64TB
  - IOPS: 3,000 - 256,000 (nur io1/io2)
- **Multi-AZ:** Failover (empfohlen für Production)
- **Subnet Group:** Min. 2 Subnets in verschiedenen AZs
- **Backup Retention:** 7 Tage (empfohlen)
- **Encryption:** KMS Key (empfohlen)

**Private IP:** Auto-assigned aus Subnet CIDR

#### DynamoDB
**Zweck:** NoSQL Key-Value Store  
**Icon:** ⚡  
**Konfiguration:**
- **Name:** Table Name
- **Billing Mode:**
  - **On-Demand:** Pay per request (keine Kapazitätsplanung)
  - **Provisioned:** Feste RCUs/WCUs
- **Partition Key:** Primary Key (z.B. `id`)
- **Sort Key:** Optional (z.B. `timestamp`)
- **GSI/LSI:** Global/Local Secondary Indexes

#### S3 (Simple Storage Service)
**Zweck:** Object Storage  
**Icon:** 📁  
**Konfiguration:**
- **Bucket Name:** Global eindeutig (z.B. `my-app-assets-prod`)
- **Versioning:** Enable/Disable
- **Encryption:** SSE-S3 (empfohlen)
- **Public Access:** Block (empfohlen) oder Allow
- **Lifecycle Rules:** Transition to Glacier after X days
- **CORS:** Falls Frontend darauf zugreift

**Keine IP-Adresse** (Service Endpoint)

#### ElastiCache
**Zweck:** Managed Redis/Memcached  
**Icon:** 🔄  
**Konfiguration:**
- **Engine:** Redis (empfohlen) oder Memcached
- **Node Type:** `cache.t3.micro`, `cache.r6g.large`, etc.
- **Number of Nodes:** 1-20
- **Cluster Mode:** Enabled/Disabled (Redis)
- **Subnet Group:** Private Subnets

**Private IP:** Auto-assigned

---

### Computing Components

#### EC2 (Elastic Compute Cloud)
**Zweck:** Virtuelle Server  
**Icon:** 🖥️  
**Instance Types:** t3, m5, c5, r5, etc.

**Konfiguration:**
- **Name:** Instance Name Tag (z.B. `web-server-1`)
- **Instance Type:**
  - `t3.micro` - 1 vCPU, 1GB RAM ($0.0104/hr) - Testing
  - `t3.small` - 2 vCPU, 2GB RAM ($0.0208/hr) - Dev
  - `t3.medium` - 2 vCPU, 4GB RAM ($0.0416/hr) - Staging
  - `t3.large` - 2 vCPU, 8GB RAM ($0.0832/hr) - Production
  - `m5.xlarge` - 4 vCPU, 16GB RAM ($0.192/hr) - High Traffic
- **AMI:** Amazon Machine Image (z.B. `ami-0c55b159cbfafe1f0`)
  - Amazon Linux 2023
  - Ubuntu 22.04 LTS
  - Custom AMI
- **Subnet:** Wähle Public oder Private Subnet
- **Private IP Assignment:**
  - **Auto:** AWS wählt nächste freie IP aus Subnet
  - **Manual:** Feste IP (z.B. `10.0.1.15`) für Load Balancer Target
- **Public IP:**
  - ☐ Keine Public IP (nur private Kommunikation)
  - ☑ Auto-assign Public IP (für Internet-Zugriff)
  - Alternativ: Elastic IP (statisch, $0.005/hr wenn nicht attached)
- **Security Groups:** 1-5 Security Groups attachable
- **Key Pair:** SSH-Key für Login
- **User Data:** Startup-Script (z.B. `#!/bin/bash\napt update`)

**IP-Anzeige im Canvas:**
```
web-server-1
10.0.1.15          (Private IP)
54.123.45.67       (Public IP, falls aktiviert)
```

#### Lambda
**Zweck:** Serverless Functions  
**Icon:** λ  
**Konfiguration:**
- **Name:** Function Name (z.B. `image-processor`)
- **Runtime:** python3.11, nodejs20.x, go1.x, etc.
- **Memory:** 128MB - 10,240MB (mehr Memory = mehr CPU)
- **Timeout:** 3s - 900s (15 min max)
- **Environment Variables:** KEY=VALUE
- **VPC:** Optional (für RDS-Zugriff)
- **Trigger:** API Gateway, S3, DynamoDB, etc.

**Keine IP-Adresse** (serverless)

#### ECS (Elastic Container Service)
**Zweck:** Container Orchestration  
**Icon:** 🐳  
**Launch Types:** Fargate (serverless) oder EC2

**Konfiguration:**
- **Service Name:** z.B. `api-service`
- **Launch Type:**
  - **Fargate:** Serverless, kein EC2-Management
  - **EC2:** Self-managed Cluster
- **Task Definition:**
  - CPU: 256 (.25 vCPU) - 16384 (16 vCPU)
  - Memory: 512MB - 120GB
  - Container Image: ECR/DockerHub URL
  - Port Mappings: 80, 443, 8080, etc.
- **Desired Count:** Anzahl Tasks (z.B. 2 für HA)
- **Subnets:** Private Subnets (empfohlen)
- **Load Balancer:** ALB Target Group

**Private IP:** Auto-assigned pro Task (Fargate: ENI pro Task)

#### ALB (Application Load Balancer)
**Zweck:** Layer 7 Load Balancer (HTTP/HTTPS)  
**Icon:** ⚖️  
**Konfiguration:**
- **Name:** z.B. `web-alb`
- **Scheme:**
  - **Internet-facing:** Public IP, Route 53 DNS
  - **Internal:** Nur VPC-intern
- **IP Address Type:** IPv4 oder Dualstack (IPv4 + IPv6)
- **Subnets:** Min. 2 Public Subnets in verschiedenen AZs
- **Security Groups:** Allow Port 80/443 from Internet
- **Target Groups:**
  - Target Type: Instance, IP, Lambda
  - Protocol: HTTP, HTTPS
  - Port: 80, 8080, etc.
  - Health Check: Path `/health`, Interval 30s
- **Listeners:**
  - HTTP (80) → Redirect to HTTPS
  - HTTPS (443) → Forward to Target Group
- **SSL Certificate:** ACM Certificate

**Public IP:** Auto-assigned (DNS Name)

---

## Configuration Fields

### Gemeinsame Felder (alle Komponenten)

- **ID:** Auto-generiert (z.B. `vpc-1647892345678`)
- **Name:** User-defined (editierbar)
- **Type:** Component Type (vpc, ec2, rds, etc.)
- **Position:** Canvas-Koordinaten `{x, y}`

### VPC-spezifisch

```json
{
  "id": "vpc-123",
  "type": "vpc",
  "name": "production-vpc",
  "config": {
    "cidr": "10.0.0.0/16",
    "region": "us-east-1",
    "enableDnsHostnames": true,
    "enableDnsSupport": true
  },
  "position": { "x": 400, "y": 200 }
}
```

### Subnet-spezifisch

```json
{
  "id": "subnet-456",
  "type": "subnet",
  "name": "public-subnet-1a",
  "config": {
    "vpcId": "vpc-123",
    "cidr": "10.0.1.0/24",
    "subnetType": "public",
    "az": "us-east-1a",
    "mapPublicIpOnLaunch": true
  },
  "position": { "x": 350, "y": 350 }
}
```

### EC2-spezifisch

```json
{
  "id": "ec2-789",
  "type": "ec2",
  "name": "web-server-1",
  "config": {
    "instanceType": "t3.small",
    "ami": "ami-0c55b159cbfafe1f0",
    "subnetId": "subnet-456",
    "ipMode": "manual",
    "privateIP": "10.0.1.15",
    "assignPublicIP": true,
    "publicIP": null,
    "securityGroupIds": ["sg-123"],
    "keyName": "my-key-pair",
    "userData": "#!/bin/bash\napt update"
  },
  "position": { "x": 350, "y": 500 }
}
```

### RDS-spezifisch

```json
{
  "id": "rds-101",
  "type": "rds",
  "name": "production-db",
  "config": {
    "engine": "postgres",
    "engineVersion": "14.7",
    "instanceClass": "db.t3.micro",
    "allocatedStorage": 20,
    "storageType": "gp3",
    "multiAZ": true,
    "subnetGroupName": "db-subnet-group",
    "securityGroupIds": ["sg-456"],
    "backupRetentionPeriod": 7,
    "encrypted": true,
    "kmsKeyId": "arn:aws:kms:..."
  },
  "position": { "x": 550, "y": 500 }
}
```

---

## IP Calculator

### Funktionsweise

Der IP Calculator berechnet automatisch IP-Informationen basierend auf CIDR-Block.

**Input:** `10.0.0.0/16`

**Output:**
```
Total IPs: 65,536
Usable IPs: 65,531 (AWS reserviert 5)
First IP: 10.0.0.0
Last IP: 10.0.255.255
Reserved IPs:
  10.0.0.0   - Network address
  10.0.0.1   - VPC router
  10.0.0.2   - DNS server
  10.0.0.3   - Future use
  10.0.255.255 - Broadcast
```

### CIDR-Tabelle

| CIDR | Total IPs | Usable IPs | Anwendungsfall |
|------|-----------|------------|----------------|
| /28 | 16 | 11 | Sehr klein (NAT Gateway) |
| /27 | 32 | 27 | Klein (ALB) |
| /26 | 64 | 59 | Klein |
| /25 | 128 | 123 | Mittel |
| /24 | 256 | 251 | Standard Subnet |
| /23 | 512 | 507 | Groß |
| /22 | 1,024 | 1,019 | Sehr groß |
| /21 | 2,048 | 2,043 | EKS Nodes |
| /20 | 4,096 | 4,091 | Private Subnet (Autoscaling) |
| /19 | 8,192 | 8,187 | Sehr groß |
| /18 | 16,384 | 16,379 | Mega |
| /17 | 32,768 | 32,763 | Mega |
| /16 | 65,536 | 65,531 | Standard VPC |

### Best Practices

**VPC:**
- Standard: `/16` (65,536 IPs)
- Groß: `/12` (1,048,576 IPs)
- Klein: `/20` (4,096 IPs)

**Subnets:**
- Public (Web): `/24` (251 IPs)
- Private (App): `/20` (4,091 IPs)
- Database: `/24` (251 IPs)
- NAT/ALB: `/28` (11 IPs)

### Inline vs. Separate Page

**Inline (aktuell):**
- Zeigt IP-Info direkt im Form
- Kein Context-Switch
- Live-Updates bei CIDR-Änderung

**Separate Page (deprecated):**
- Alte separate CIDR Calculator Seite
- Nicht mehr verwendet

---

## Connection Types

Verbindungen zwischen Komponenten werden im JSON als `connections` Array gespeichert.

```json
{
  "connections": [
    {
      "id": "conn-1",
      "from": "ec2-789",
      "to": "rds-101",
      "data": {
        "port": 5432,
        "protocol": "tcp",
        "description": "EC2 → RDS"
      }
    }
  ]
}
```

**Canvas-Darstellung:**
- Pfeil von EC2 zu RDS
- Label: `:5432 (tcp)`

**Unterstützte Verbindungen:**
- EC2 → RDS (Database Connection)
- EC2 → S3 (IAM Role)
- ALB → EC2 (Target Group)
- Lambda → DynamoDB (Event Source)

---

## Terraform Output

### Generierte Dateien

1. **main.tf** - Provider & Terraform Config
2. **variables.tf** - Input Variables
3. **vpc.tf** - VPC & Subnets
4. **ec2.tf** - EC2 Instances
5. **rds.tf** - RDS Databases
6. **s3.tf** - S3 Buckets
7. **outputs.tf** - Output Values

### Beispiel: main.tf

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "production"
      Environment = var.environment
      ManagedBy   = "OverCloud"
    }
  }
}
```

### Beispiel: vpc.tf

```hcl
resource "aws_vpc" "vpc_123" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "production-vpc"
  }
}

resource "aws_subnet" "subnet_456" {
  vpc_id                  = aws_vpc.vpc_123.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-1a"
    Type = "public"
  }
}
```

### Beispiel: ec2.tf

```hcl
resource "aws_instance" "ec2_789" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.small"
  subnet_id     = aws_subnet.subnet_456.id
  private_ip    = "10.0.1.15"

  vpc_security_group_ids = [aws_security_group.sg_123.id]
  key_name               = "my-key-pair"

  user_data = <<-EOF
    #!/bin/bash
    apt update
  EOF

  tags = {
    Name = "web-server-1"
  }
}
```

---

## Best Practices

### Netzwerk-Design

1. **Verwende /16 für VPC**
   - Genügend Platz für Wachstum
   - Standard AWS-Empfehlung

2. **Subnets nach Funktion trennen**
   - Public Subnets: Web, ALB
   - Private Subnets: App-Server
   - Database Subnets: RDS, ElastiCache

3. **Multi-AZ für HA**
   - Min. 2 Subnets in verschiedenen AZs
   - ALB/RDS nutzen beide AZs automatisch

4. **Private IP-Bereiche nutzen**
   - `10.0.0.0/8` (empfohlen für große Deployments)
   - `172.16.0.0/12` (alternative)
   - `192.168.0.0/16` (klein, Home-Netzwerke)

### Security

1. **Least Privilege Security Groups**
   - Nur notwendige Ports öffnen
   - Source-IP einschränken wo möglich

2. **Keine Public IPs für Databases**
   - RDS immer in Private Subnet
   - Zugriff nur via EC2 Bastion oder VPN

3. **Encryption aktivieren**
   - RDS: Encryption at Rest (KMS)
   - S3: SSE-S3 oder SSE-KMS
   - EBS: Encrypted Volumes

4. **Regelmäßige Backups**
   - RDS: Automated Backups (7+ Tage)
   - DynamoDB: Point-in-Time Recovery
   - S3: Versioning

### Cost Optimization

1. **Instance Sizing**
   - Start small (t3.micro für Testing)
   - Scale up basierend auf Metrics
   - Reserved Instances für Production (-75%)

2. **Spot Instances**
   - Batch Jobs, CI/CD
   - Bis zu -90% Ersparnis

3. **S3 Lifecycle Policies**
   - Infrequent Access nach 30 Tagen
   - Glacier nach 90 Tagen
   - Delete nach 365 Tagen

4. **CloudWatch Alarms**
   - Ungenutzte Ressourcen identifizieren
   - Auto-Scaling für Traffic-Spikes

### Performance

1. **Use Content Delivery**
   - CloudFront für statische Assets
   - ElastiCache für DB Caching

2. **Auto Scaling**
   - EC2 Auto Scaling Groups
   - ECS Service Auto Scaling
   - RDS Read Replicas

3. **Load Balancing**
   - ALB für Multi-AZ Distribution
   - Health Checks aktivieren

---

## Weitere Ressourcen

- [Quick Start Guide](./infrastructure-designer-quickstart.md)
- [Architecture Overview](./infrastructure-designer-architecture.md)
- [API Reference](./api/terraform-api.md)
- [Terraform Generator Docs](./guides/terraform-generation.md)

---

**Happy Designing!**
