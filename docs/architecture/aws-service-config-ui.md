# AWS Service Configuration UI - Design Specification

> **Status:** Draft (In Planning)
> **Author:** Claude Code
> **Date:** 2026-03-25
> **Version:** 0.1.0

---

## 1. Übersicht

### Vision
Statt nur einem JSON-Editor bieten wir **visuelle, formularbasierte Konfiguration** für AWS Services mit:
- ✅ **Guided Input** - Multi-Step Wizards für komplexe Services
- ✅ **Smart Validation** - AWS-Limits und Best Practices automatisch prüfen
- ✅ **Tooltips & Hilfe** - Erklärungen zu jedem Feld
- ✅ **Cost Preview** - Geschätzte Kosten pro Service anzeigen
- ✅ **Security Warnings** - Warnung bei unsicheren Konfigurationen

### Zielgruppe
- **Einsteiger:** Müssen nicht alle AWS-Parameter kennen
- **Fortgeschrittene:** Können ins JSON wechseln für Fine-Tuning
- **Teams:** Visuelle Config ist besser teilbar/verständlich

---

## 2. MVP Scope - Welche Services?

### Phase 1 (MVP) - 6 Core Services

| Service | Priority | Complexity | Reason |
|---------|----------|------------|--------|
| **EC2** | HIGH | Medium | Häufigster Compute Service |
| **RDS** | HIGH | Medium | Häufigste Datenbank |
| **S3** | HIGH | Low | Einfachster Storage Service |
| **Security Groups** | HIGH | Medium | Kritisch für Sicherheit |
| **VPC** | MEDIUM | High | Netzwerk-Basis (später auto-generiert) |
| **ALB/ELB** | MEDIUM | Medium | Load Balancing für Web Apps |

### Phase 2 - Serverless & Advanced
- Lambda
- API Gateway
- DynamoDB
- CloudFront (CDN)
- Route 53 (DNS)
- IAM Roles

### Phase 3 - Enterprise
- ECS/EKS (Container)
- ElastiCache (Redis/Memcached)
- SQS/SNS (Messaging)
- CloudWatch (Monitoring)

---

## 3. UI/UX Konzept

### 3.1 Layout - 3-Column Design

```
┌────────────────────────────────────────────────────────┐
│  Component Library  │  Canvas/Preview  │  Properties  │
│      (Sidebar)      │     (Main)       │   (Sidebar)  │
├─────────────────────┼──────────────────┼──────────────┤
│                     │                  │              │
│ 🔍 Search           │                  │ ✏️ Edit EC2   │
│                     │    ┌─────────┐   │              │
│ Compute             │    │   EC2   │   │ Name:        │
│  ▸ EC2              │    │ t3.med  │   │ web-server   │
│  ▸ Lambda           │    └────┬────┘   │              │
│  ▸ ECS              │         │        │ Type:        │
│                     │         ▼        │ t3.medium ▼  │
│ Database            │    ┌─────────┐   │              │
│  ▸ RDS              │    │   RDS   │   │ Storage:     │
│  ▸ DynamoDB         │    │Postgres │   │ [20] GB      │
│                     │    └─────────┘   │              │
│ Storage             │                  │ [Validate]   │
│  ▸ S3               │  [JSON View ▼]   │ [Save]       │
│  ▸ EBS              │                  │              │
└─────────────────────┴──────────────────┴──────────────┘
```

### 3.2 Interaction Flow

**Option A: Click to Add**
1. User klickt "EC2" in Component Library
2. Modal öffnet sich mit Multi-Step Wizard
3. User füllt Form aus (Name, Instance Type, AMI, etc.)
4. "Add Component" → erscheint in Canvas
5. Component ist selektiert → Properties Panel zeigt Details

**Option B: Drag & Drop (später)**
1. User zieht "EC2" aus Library auf Canvas
2. Properties Panel öffnet sich automatisch
3. User konfiguriert inline
4. "Save" → Component ist fertig

**MVP: Option A** (einfacher zu implementieren)

---

## 4. Service-spezifische Forms

### 4.1 EC2 Instance Configuration

#### Step 1: Basics
```
┌─────────────────────────────────────────┐
│ EC2 Instance - Grundlagen               │
├─────────────────────────────────────────┤
│                                         │
│ Name *                                  │
│ ┌─────────────────────────────────────┐ │
│ │ web-server-1                        │ │
│ └─────────────────────────────────────┘ │
│ ℹ️ Eindeutiger Name für diese Instanz   │
│                                         │
│ Purpose                                 │
│ ┌─────────────────────────────────────┐ │
│ │ Web application server              │ │
│ └─────────────────────────────────────┘ │
│                                         │
│              [Zurück]  [Weiter →]      │
└─────────────────────────────────────────┘
```

#### Step 2: Instance Type
```
┌─────────────────────────────────────────┐
│ EC2 Instance - Instance Type            │
├─────────────────────────────────────────┤
│                                         │
│ Instance Type Family *                  │
│ ○ General Purpose (t3, m5, m6i)        │
│ ● Compute Optimized (c5, c6i)          │
│ ○ Memory Optimized (r5, x1, z1d)       │
│ ○ Storage Optimized (i3, d2, h1)       │
│                                         │
│ Instance Size *                         │
│ ┌─────────────────────────────────────┐ │
│ │ t3.medium ▼                         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ℹ️ t3.medium                            │
│    • 2 vCPU                             │
│    • 4 GB RAM                           │
│    • ~$30/month                         │
│                                         │
│ ⚠️ Best Practice:                       │
│ Start with t3.medium for web apps      │
│                                         │
│          [← Zurück]  [Weiter →]        │
└─────────────────────────────────────────┘
```

#### Step 3: AMI & Storage
```
┌─────────────────────────────────────────┐
│ EC2 Instance - AMI & Storage            │
├─────────────────────────────────────────┤
│                                         │
│ AMI (Amazon Machine Image) *            │
│ ○ Amazon Linux 2023                    │
│ ● Ubuntu 22.04 LTS                     │
│ ○ Custom AMI                           │
│                                         │
│ Root Volume Size (GB) *                 │
│ ┌────┐                                  │
│ │ 20 │ GB (min. 8 GB)                  │
│ └────┘                                  │
│ ℹ️ Empfohlung: 20 GB für Web Server     │
│                                         │
│ Volume Type                             │
│ ● gp3 (General Purpose SSD)            │
│ ○ io2 (Provisioned IOPS)               │
│ ○ st1 (Throughput Optimized HDD)       │
│                                         │
│          [← Zurück]  [Weiter →]        │
└─────────────────────────────────────────┘
```

#### Step 4: Network & Security
```
┌─────────────────────────────────────────┐
│ EC2 Instance - Network & Security       │
├─────────────────────────────────────────┤
│                                         │
│ VPC *                                   │
│ ┌─────────────────────────────────────┐ │
│ │ main-vpc (10.0.0.0/16) ▼            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Subnet *                                │
│ ┌─────────────────────────────────────┐ │
│ │ public-subnet-1 (eu-central-1a) ▼   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Public IP                               │
│ ☑ Auto-assign Public IP                │
│ ℹ️ Benötigt für direkten Internet-Zugriff │
│                                         │
│ Security Group *                        │
│ ┌─────────────────────────────────────┐ │
│ │ web-sg ▼                            │ │
│ └─────────────────────────────────────┘ │
│ [+ Create New Security Group]           │
│                                         │
│ Key Pair *                              │
│ ┌─────────────────────────────────────┐ │
│ │ web-server-key ▼                    │ │
│ └─────────────────────────────────────┘ │
│ [+ Generate New Key Pair]               │
│                                         │
│          [← Zurück]  [Fertig ✓]        │
└─────────────────────────────────────────┘
```

---

### 4.2 Security Group Configuration

```
┌─────────────────────────────────────────────────────┐
│ Security Group - Inbound Rules                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Name *                                              │
│ ┌─────────────────────────────────────────────────┐ │
│ │ web-sg                                          │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Description                                         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Security group for web servers (HTTP/HTTPS)     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Inbound Rules                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Type       │ Port  │ Source        │ Action    │ │
│ ├────────────┼───────┼───────────────┼───────────┤ │
│ │ HTTP       │ 80    │ 0.0.0.0/0     │ [Remove] │ │
│ │ HTTPS      │ 443   │ 0.0.0.0/0     │ [Remove] │ │
│ │ SSH        │ 22    │ 192.168.1.0/24│ [Remove] │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ [+ Add Rule]                                        │
│                                                     │
│ ⚠️ Security Warning:                                │
│ SSH (Port 22) sollte NICHT öffentlich sein!        │
│ Empfehlung: Nur von deiner IP (89.123.45.67/32)    │
│                                                     │
│                          [Cancel]  [Save ✓]        │
└─────────────────────────────────────────────────────┘
```

**Add Rule Modal:**
```
┌─────────────────────────────────────────┐
│ Add Inbound Rule                        │
├─────────────────────────────────────────┤
│                                         │
│ Type *                                  │
│ ┌─────────────────────────────────────┐ │
│ │ HTTP ▼                              │ │
│ └─────────────────────────────────────┘ │
│ Common: HTTP, HTTPS, SSH, MySQL, RDP    │
│ Custom: Port Range eingeben             │
│                                         │
│ Protocol                                │
│ ● TCP  ○ UDP  ○ ICMP  ○ All            │
│                                         │
│ Port Range *                            │
│ ┌────┐                                  │
│ │ 80 │ (auto-filled for HTTP)          │
│ └────┘                                  │
│                                         │
│ Source *                                │
│ ○ Anywhere (0.0.0.0/0, ::/0)          │
│ ○ My IP (89.123.45.67/32)             │
│ ● Custom                               │
│ ┌─────────────────────────────────────┐ │
│ │ 10.0.0.0/16                         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Description                             │
│ ┌─────────────────────────────────────┐ │
│ │ Allow HTTP from VPC                 │ │
│ └─────────────────────────────────────┘ │
│                                         │
│              [Cancel]  [Add Rule]      │
└─────────────────────────────────────────┘
```

---

### 4.3 RDS Database Configuration

```
┌─────────────────────────────────────────┐
│ RDS Database - Engine                   │
├─────────────────────────────────────────┤
│                                         │
│ Database Engine *                       │
│ ┌─────────────────────────────────────┐ │
│ │ ● PostgreSQL                        │ │
│ │ ○ MySQL                             │ │
│ │ ○ MariaDB                           │ │
│ │ ○ Aurora (PostgreSQL)               │ │
│ │ ○ Aurora (MySQL)                    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Engine Version *                        │
│ ┌─────────────────────────────────────┐ │
│ │ 15.5 (Latest) ▼                     │ │
│ └─────────────────────────────────────┘ │
│ ℹ️ Empfohlung: Immer neueste Stable Version │
│                                         │
│ Use Case Template                       │
│ ○ Development (db.t3.micro, 20GB)      │
│ ● Production Web App (db.t3.medium, Multi-AZ) │
│ ○ Data Warehouse (db.r5.xlarge, 100GB)│
│                                         │
│              [Cancel]  [Weiter →]      │
└─────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────┐
│ RDS Database - Instance & Storage       │
├─────────────────────────────────────────┤
│                                         │
│ DB Instance Class *                     │
│ ┌─────────────────────────────────────┐ │
│ │ db.t3.medium ▼                      │ │
│ └─────────────────────────────────────┘ │
│ ℹ️ db.t3.medium                         │
│    • 2 vCPU, 4 GB RAM                   │
│    • ~$60/month                         │
│                                         │
│ Storage Type                            │
│ ● gp3 (General Purpose SSD)            │
│ ○ io1 (Provisioned IOPS)               │
│                                         │
│ Allocated Storage (GB) *                │
│ ┌────┐                                  │
│ │ 50 │ GB (min. 20 GB)                 │
│ └────┘                                  │
│ ⚠️ Min 20 GB für PostgreSQL 15!         │
│                                         │
│ Storage Autoscaling                     │
│ ☑ Enable autoscaling                   │
│ Max: [100] GB                           │
│                                         │
│ Multi-AZ Deployment                     │
│ ☑ Enable Multi-AZ (Recommended)        │
│ ℹ️ +100% Cost, aber 99.95% SLA          │
│                                         │
│          [← Zurück]  [Weiter →]        │
└─────────────────────────────────────────┘
```

---

### 4.4 S3 Bucket Configuration

```
┌─────────────────────────────────────────┐
│ S3 Bucket Configuration                 │
├─────────────────────────────────────────┤
│                                         │
│ Bucket Name *                           │
│ ┌─────────────────────────────────────┐ │
│ │ my-app-static-assets-2026           │ │
│ └─────────────────────────────────────┘ │
│ ⚠️ Muss global eindeutig sein!          │
│ ℹ️ Format: <app>-<purpose>-<year>       │
│                                         │
│ Region                                  │
│ ┌─────────────────────────────────────┐ │
│ │ eu-central-1 (Frankfurt) ▼          │ │
│ └─────────────────────────────────────┘ │
│ ℹ️ Wähle Region nahe deiner User        │
│                                         │
│ Versioning                              │
│ ☑ Enable Versioning                    │
│ ℹ️ Empfohlen: Schutz vor versehentlichem Löschen │
│                                         │
│ Encryption                              │
│ ● SSE-S3 (Server-Side Encryption)      │
│ ○ SSE-KMS (mit eigenem Key)            │
│ ○ None (Not recommended)               │
│                                         │
│ Public Access                           │
│ ☐ Block all public access (Recommended)│
│ ⚠️ Warnung: Öffentlicher Zugriff kann   │
│    Sicherheitsrisiko sein!              │
│                                         │
│ Use Case                                │
│ ● Static Website Hosting               │
│ ○ File Storage (Private)               │
│ ○ Backup & Archive                     │
│ ○ Data Lake                             │
│                                         │
│              [Cancel]  [Create ✓]      │
└─────────────────────────────────────────┘
```

---

## 5. Validierungsregeln

### 5.1 AWS-spezifische Validierung

| Service | Field | Validation Rule | Error Message |
|---------|-------|----------------|---------------|
| **RDS** | Allocated Storage | `>= 20 GB` (für PostgreSQL/MySQL) | "PostgreSQL benötigt mindestens 20 GB Storage" |
| **S3** | Bucket Name | `/^[a-z0-9][a-z0-9-]*[a-z0-9]$/` | "Bucket Name muss lowercase sein, keine Underscores" |
| **S3** | Bucket Name | `length: 3-63` | "Bucket Name: 3-63 Zeichen" |
| **EC2** | Instance Type | Muss zu AMI passen (z.B. ARM vs x86) | "t4g.* Instanzen benötigen ARM AMI" |
| **Security Group** | Port 22 Source | `!= 0.0.0.0/0` (Warning) | "⚠️ SSH sollte nicht öffentlich sein!" |
| **VPC** | CIDR Block | RFC 1918 Private Range | "Verwende private IP-Bereiche (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)" |

### 5.2 Best Practice Warnings

| Condition | Warning | Severity |
|-----------|---------|----------|
| RDS ohne Multi-AZ | "Für Production: Multi-AZ aktivieren!" | WARNING |
| S3 ohne Versioning | "Versioning schützt vor Datenverlust" | INFO |
| Security Group mit 0.0.0.0/0 auf Port 22 | "SSH nicht öffentlich zugänglich machen!" | ERROR |
| EC2 ohne Key Pair | "Ohne Key Pair kannst du nicht auf die Instanz zugreifen" | ERROR |
| S3 Public Access enabled | "Bucket ist öffentlich! Sensitive Daten?" | WARNING |

---

## 6. JSON Schema Erweiterung

### 6.1 Component Configuration Schema

```json
{
  "architecture": {
    "components": [
      {
        "id": "web-server-1",
        "type": "compute",
        "name": "Web Server 1",
        "provider_service": "ec2",
        "configuration": {
          "instance_type": "t3.medium",
          "ami": "ami-0c55b159cbfafe1f0",
          "ami_name": "Ubuntu 22.04 LTS",
          "root_volume": {
            "size_gb": 20,
            "type": "gp3",
            "iops": 3000,
            "throughput_mb": 125
          },
          "network": {
            "vpc_id": "main-vpc",
            "subnet_id": "public-subnet-1",
            "assign_public_ip": true,
            "security_group_ids": ["web-sg"]
          },
          "key_pair": "web-server-key",
          "user_data": null,
          "tags": {
            "Environment": "production",
            "ManagedBy": "StackVertex"
          }
        },
        "metadata": {
          "created_via": "ui_wizard",
          "wizard_version": "1.0.0",
          "estimated_monthly_cost_usd": 30.50
        }
      }
    ]
  }
}
```

### 6.2 Security Group Schema

```json
{
  "id": "web-sg",
  "type": "security_group",
  "name": "Web Server Security Group",
  "provider_service": "security_group",
  "configuration": {
    "description": "Security group for web servers (HTTP/HTTPS)",
    "vpc_id": "main-vpc",
    "ingress": [
      {
        "type": "http",
        "protocol": "tcp",
        "port": 80,
        "source": "0.0.0.0/0",
        "description": "Allow HTTP from anywhere"
      },
      {
        "type": "https",
        "protocol": "tcp",
        "port": 443,
        "source": "0.0.0.0/0",
        "description": "Allow HTTPS from anywhere"
      },
      {
        "type": "custom",
        "protocol": "tcp",
        "port": 22,
        "source": "192.168.1.0/24",
        "description": "SSH from office network only"
      }
    ],
    "egress": [
      {
        "protocol": "-1",
        "port": 0,
        "destination": "0.0.0.0/0",
        "description": "Allow all outbound"
      }
    ]
  },
  "metadata": {
    "security_warnings": [
      {
        "severity": "info",
        "message": "SSH restricted to private network - good practice!"
      }
    ]
  }
}
```

---

## 7. Technische Implementation

### 7.1 Component Architecture (Frontend)

```
/frontend/src/js/
├── components/
│   ├── service-wizard/
│   │   ├── wizard-modal.js          # Basis Modal für alle Wizards
│   │   ├── ec2-wizard.js            # EC2-spezifischer Wizard
│   │   ├── rds-wizard.js            # RDS-spezifischer Wizard
│   │   ├── s3-wizard.js             # S3-spezifischer Wizard
│   │   ├── security-group-wizard.js # Security Group Wizard
│   │   └── wizard-steps.js          # Shared Step Components
│   ├── service-forms/
│   │   ├── ec2-form.js              # Inline Form für EC2
│   │   ├── rds-form.js              # Inline Form für RDS
│   │   └── form-fields.js           # Reusable Form Components
│   └── component-library/
│       ├── service-list.js          # Sidebar mit AWS Services
│       └── service-card.js          # Einzelner Service-Button
├── lib/
│   ├── aws-validators.js            # AWS-spezifische Validierung
│   ├── aws-pricing.js               # Cost Estimation
│   └── aws-metadata.js              # Service Descriptions, Icons
└── pages/
    └── architecture-builder.js      # Main Builder Page (existing)
```

### 7.2 Wizard System (Vanilla JS)

```javascript
// wizard-modal.js - Basis Modal
export class ServiceWizard {
  constructor(serviceType) {
    this.serviceType = serviceType;
    this.currentStep = 0;
    this.steps = [];
    this.data = {};
  }

  open() {
    this.render();
    this.attachEventHandlers();
  }

  addStep(step) {
    this.steps.push(step);
  }

  nextStep() {
    if (this.validateCurrentStep()) {
      this.currentStep++;
      this.render();
    }
  }

  previousStep() {
    this.currentStep--;
    this.render();
  }

  finish() {
    if (this.validateAllSteps()) {
      this.onComplete(this.data);
      this.close();
    }
  }

  validateCurrentStep() {
    const step = this.steps[this.currentStep];
    return step.validate(this.data);
  }

  render() {
    // Rendert aktuellen Step
  }
}

// ec2-wizard.js - EC2-spezifischer Wizard
export class EC2Wizard extends ServiceWizard {
  constructor() {
    super('ec2');

    this.addStep(new BasicInfoStep());
    this.addStep(new InstanceTypeStep());
    this.addStep(new AMIStep());
    this.addStep(new NetworkStep());
  }
}
```

### 7.3 Validation System

```javascript
// aws-validators.js
export const AWSValidators = {
  rds: {
    minStorage(engine, storage) {
      const minStorageByEngine = {
        'postgres': 20,
        'mysql': 20,
        'mariadb': 20,
        'oracle': 100
      };

      const minRequired = minStorageByEngine[engine] || 20;

      if (storage < minRequired) {
        return {
          valid: false,
          error: `${engine} benötigt mindestens ${minRequired} GB Storage`,
          severity: 'error'
        };
      }

      return { valid: true };
    }
  },

  s3: {
    bucketName(name) {
      const regex = /^[a-z0-9][a-z0-9-]*[a-z0-9]$/;

      if (!regex.test(name)) {
        return {
          valid: false,
          error: 'Bucket Name: lowercase, keine Underscores',
          severity: 'error'
        };
      }

      if (name.length < 3 || name.length > 63) {
        return {
          valid: false,
          error: 'Bucket Name: 3-63 Zeichen',
          severity: 'error'
        };
      }

      return { valid: true };
    }
  },

  securityGroup: {
    checkSSH(rule) {
      if (rule.port === 22 && rule.source === '0.0.0.0/0') {
        return {
          valid: false,
          error: 'SSH sollte nicht öffentlich zugänglich sein!',
          severity: 'error',
          suggestion: 'Verwende deine IP oder VPC CIDR'
        };
      }
      return { valid: true };
    }
  }
};
```

---

## 8. Cost Estimation API

### 8.1 Pricing Data Structure

```javascript
// aws-pricing.js
export const AWSPricing = {
  'eu-central-1': {
    ec2: {
      't3.micro': { hourly: 0.0104, monthly: 7.59 },
      't3.small': { hourly: 0.0208, monthly: 15.18 },
      't3.medium': { hourly: 0.0416, monthly: 30.37 },
      't3.large': { hourly: 0.0832, monthly: 60.74 },
      // ... mehr Instance Types
    },
    rds: {
      'db.t3.micro': { hourly: 0.018, monthly: 13.14 },
      'db.t3.medium': { hourly: 0.07, monthly: 51.10 },
      // ... mehr Instance Classes
    },
    storage: {
      gp3: { per_gb_month: 0.088 },
      gp2: { per_gb_month: 0.11 },
      io1: { per_gb_month: 0.138 }
    }
  }
};

export function estimateCost(component) {
  const region = component.metadata?.region || 'eu-central-1';
  const service = component.provider_service;

  switch (service) {
    case 'ec2':
      return estimateEC2Cost(component, region);
    case 'rds':
      return estimateRDSCost(component, region);
    case 's3':
      return estimateS3Cost(component, region);
    default:
      return { estimated: false };
  }
}

function estimateEC2Cost(component, region) {
  const pricing = AWSPricing[region].ec2;
  const instanceType = component.configuration.instance_type;

  const computeCost = pricing[instanceType]?.monthly || 0;
  const storageCost = (component.configuration.root_volume?.size_gb || 0) *
                      AWSPricing[region].storage.gp3.per_gb_month;

  return {
    compute: computeCost,
    storage: storageCost,
    total: computeCost + storageCost,
    currency: 'USD',
    period: 'monthly'
  };
}
```

---

## 9. Mobile Responsive Design

### Tablet (768px - 1024px)
- Component Library: Collapsible (Hamburger Menu)
- Canvas: Full Width
- Properties: Modal statt Sidebar

### Mobile (< 768px)
- Stacked Layout (kein Multi-Column)
- Wizard: Fullscreen Modal
- Touch-friendly Buttons (min 44x44px)

---

## 10. Accessibility (WCAG 2.1 AA)

- ✅ Keyboard Navigation (Tab, Enter, Escape)
- ✅ Screen Reader Support (ARIA Labels)
- ✅ Focus Indicators (Blue Outline)
- ✅ Color Contrast (4.5:1 für Text)
- ✅ Error Messages (deutlich, nicht nur Farbe)

---

## 11. Implementation Roadmap

### Week 1-2: Foundation
- [ ] Wizard Modal Component (Vanilla JS)
- [ ] Form Field Components (Input, Select, Checkbox, etc.)
- [ ] Validation System
- [ ] Cost Estimation API (Static Pricing Data)

### Week 3-4: Core Services (MVP)
- [ ] EC2 Wizard (4 Steps)
- [ ] Security Group Form
- [ ] RDS Wizard (3 Steps)
- [ ] S3 Form (1 Step)

### Week 5-6: Integration
- [ ] Component Library UI
- [ ] Properties Panel UI
- [ ] JSON Generation from Form Data
- [ ] Form Pre-fill from JSON (Edit Mode)

### Week 7-8: Polish
- [ ] Best Practice Tooltips
- [ ] Security Warnings
- [ ] Cost Preview per Component
- [ ] Mobile Responsive Design
- [ ] Testing & Bug Fixes

---

## 12. Success Metrics

- ✅ **User can create EC2 without knowing AWS parameters**
- ✅ **Security warnings prevent common mistakes (open SSH)**
- ✅ **Cost estimation within 20% accuracy**
- ✅ **Time to create first architecture: < 5 minutes**
- ✅ **Mobile usable (not just responsive)**

---

## 13. Open Questions

1. **API Gateway für Pricing?**
   - Statische JSON-Datei für MVP?
   - Später: AWS Price List API integrieren?

2. **VPC Auto-Creation?**
   - Wenn User EC2 erstellt, aber keine VPC existiert → Auto-create?
   - Oder: VPC ist Pflicht-Voraussetzung?

3. **Drag & Drop Priorität?**
   - MVP: Click to Add
   - Phase 2: Drag & Drop auf Canvas

4. **Multi-Step vs. Single-Page Form?**
   - EC2: Multi-Step (4 Steps)
   - S3: Single-Page (einfacher)
   - User Präferenz?

---

## 14. Next Steps

1. **Review mit Andy** - Feedback zu diesem Spec
2. **Prototyp erstellen** - HTML/CSS Mockup für einen Wizard
3. **JSON Schema finalisieren** - Component Configuration Schema
4. **Implementation starten** - Wizard Modal Component

---

**Status:** Ready for Review ✅
**Feedback:** TBD
