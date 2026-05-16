# Terraform Component Templates

Dieses Verzeichnis enthält Jinja2-Templates zur Generierung von Terraform HCL Code aus OverCloud Architecture JSON.

## Template-Struktur

Jedes Template folgt diesem Muster:

```jinja2
# ============================================================================
# Resource Type Description
# ============================================================================

{% for comp in components %}
# {{ comp.name }}
resource "aws_resource_type" "{{ comp.id }}" {
  # Resource-spezifische Attribute
  attribute = "{{ comp.config.attribute }}"
  
  tags = {
    Name = "{{ comp.name }}"
  }
  
  {% if comp.depends_on %}
  depends_on = [
    {% for dep in comp.depends_on %}
    {{ dep }},
    {% endfor %}
  ]
  {% endif %}
}
{% endfor %}
```

## Verfügbare Templates

### Core Infrastructure

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `main.tf.j2` | Provider Config | Terraform & AWS Provider Konfiguration |
| `variables.tf.j2` | Variables | Terraform Input Variables |
| `outputs.tf.j2` | Outputs | Terraform Output Values |

### Networking

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `vpc.tf.j2` | `aws_vpc` | Virtual Private Cloud + Internet Gateway |
| `subnet.tf.j2` | `aws_subnet` | Subnets (public/private) + Route Tables |
| `internet_gateway.tf.j2` | `aws_internet_gateway` | Internet Gateway + Public Route Table |
| `nat_gateway.tf.j2` | `aws_nat_gateway` | NAT Gateway + Elastic IP + Private Route Table |
| `route_table.tf.j2` | `aws_route_table` | Standalone Route Tables + Associations |
| `security_group.tf.j2` | `aws_security_group` | Security Groups mit Ingress/Egress Rules |

### Compute

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `ec2.tf.j2` | `aws_instance` | EC2 Instances + AMI Data Source |
| `lambda.tf.j2` | `aws_lambda_function` | Lambda Functions + Layer + Permissions |

### Load Balancing

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `alb.tf.j2` | `aws_lb` | Application Load Balancer + Listener + Target Group |
| `target_group.tf.j2` | `aws_lb_target_group` | Standalone Target Groups |

### Database

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `rds.tf.j2` | `aws_db_instance` | RDS Database Instances + Subnet Groups |
| `dynamodb.tf.j2` | `aws_dynamodb_table` | DynamoDB Tables + GSI + LSI + Auto-Scaling |

### Storage

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `s3.tf.j2` | `aws_s3_bucket` | S3 Buckets + Versioning + Encryption + Public Access Block |

### IAM & Security

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `iam.tf.j2` | `aws_iam_role` | IAM Roles + Policies + Instance Profiles |

### Fallback

| Template | Resource Type | Beschreibung |
|----------|--------------|--------------|
| `generic.tf.j2` | `*` | Generisches Template für unbekannte Resource Types |

## Jinja2 Variables

### Global Context (alle Templates)

```python
{
  "project_name": str,        # Projektname
  "region": str,              # AWS Region
  "provider": str,            # Cloud Provider (aws, azure, gcp)
  "created_at": str,          # ISO Timestamp
  "environment": str          # dev, staging, prod
}
```

### Component Context

Jedes Template erhält eine `components` Liste mit folgendem Format:

```python
{
  "id": str,                  # Eindeutige Component ID (z.B. "vpc-1", "ec2-main")
  "name": str,                # Human-readable Name
  "config": dict,             # Component-spezifische Konfiguration
  "dependencies": list[str],  # Liste von abhängigen Component IDs
  "depends_on": list[str]     # Terraform depends_on Statements
}
```

## Component Types & Config-Felder

### VPC (`vpc.tf.j2`)

```yaml
config:
  cidr: string              # CIDR Block (z.B. "10.0.0.0/16")
  enableDns: bool           # DNS Resolution aktivieren (default: true)
  needsIGW: bool           # Internet Gateway erstellen (default: true)
```

### Subnet (`subnet.tf.j2`)

```yaml
config:
  vpc: string               # VPC Component ID
  cidr: string              # Subnet CIDR (z.B. "10.0.1.0/24")
  az: string                # Availability Zone (z.B. "us-east-1a")
  subnetType: string        # "public" oder "private"
```

### EC2 (`ec2.tf.j2`)

```yaml
config:
  subnet: string            # Subnet Component ID
  instanceType: string      # Instance Type (z.B. "t3.small")
  privateIp: string         # Private IP (optional)
  hasPublicIp: bool        # Public IP zuweisen (default: false)
  securityGroups: list      # Liste von Security Group IDs
  keyPair: string           # Key Pair Name (optional)
  userData: string          # User Data Script (optional)
  amiFilter: string         # AMI Filter (default: "amzn2-ami-hvm-*-x86_64-gp2")
```

### RDS (`rds.tf.j2`)

```yaml
config:
  engine: string            # "postgres", "mysql", "mariadb"
  engineVersion: string     # Engine Version (z.B. "15.4")
  instanceClass: string     # Instance Class (z.B. "db.t3.micro")
  allocatedStorage: int     # Storage in GB (default: 20)
  storageType: string       # "gp3", "gp2", "io1" (default: "gp3")
  dbName: string            # Database Name
  username: string          # Master Username
  subnets: list             # Liste von Subnet IDs
  securityGroups: list      # Liste von Security Group IDs
  multiAZ: bool            # Multi-AZ Deployment (default: false)
  backupRetention: int      # Backup Retention in Tagen (default: 7)
  skipFinalSnapshot: bool   # Skip Final Snapshot (default: true)
```

### S3 (`s3.tf.j2`)

```yaml
config:
  versioning: bool          # Versioning aktivieren (default: false)
```

### Lambda (`lambda.tf.j2`)

```yaml
config:
  runtime: string           # Runtime (z.B. "python3.11", "nodejs20.x")
  handler: string           # Handler (z.B. "index.handler")
  timeout: int              # Timeout in Sekunden (default: 30)
  memory: int               # Memory in MB (default: 128)
  sourceFile: string        # Source Code File Path
  environment: dict         # Environment Variables
  role: string              # IAM Role Component ID
  layers: list              # Lambda Layer ARNs
  vpc: dict                 # VPC Config (subnets, securityGroups)
```

### Application Load Balancer (`alb.tf.j2`)

```yaml
config:
  internal: bool            # Internal ALB (default: false)
  subnets: list             # Liste von Subnet IDs (min. 2)
  securityGroups: list      # Liste von Security Group IDs
  vpc: string               # VPC Component ID
  targetPort: int           # Target Port (default: 80)
  protocol: string          # Protocol (default: "HTTP")
  listenerPort: int         # Listener Port (default: 80)
  listenerProtocol: string  # Listener Protocol (default: "HTTP")
  healthCheck:
    path: string            # Health Check Path (default: "/")
    port: string            # Health Check Port (default: "traffic-port")
    protocol: string        # Health Check Protocol (default: "HTTP")
    interval: int           # Interval in Sekunden (default: 30)
    timeout: int            # Timeout in Sekunden (default: 5)
    healthyThreshold: int   # Healthy Threshold (default: 2)
    unhealthyThreshold: int # Unhealthy Threshold (default: 2)
    matcher: string         # Success Codes (default: "200")
  enableHttps: bool         # HTTPS Listener aktivieren
  certificateArn: string    # ACM Certificate ARN (für HTTPS)
  redirectToHttps: bool     # HTTP zu HTTPS Redirect (default: false)
  sslPolicy: string         # SSL Policy (default: "ELBSecurityPolicy-TLS13-1-2-2021-06")
  targets: list             # Target Attachments (optional)
    - instance: string      # EC2 Instance ID
      port: int             # Port Override (optional)
```

### DynamoDB (`dynamodb.tf.j2`)

```yaml
config:
  billingMode: string       # "PAY_PER_REQUEST" oder "PROVISIONED"
  readCapacity: int         # Read Capacity Units (bei PROVISIONED)
  writeCapacity: int        # Write Capacity Units (bei PROVISIONED)
  hashKey: string           # Partition Key
  hashKeyType: string       # "S" (String), "N" (Number), "B" (Binary)
  rangeKey: string          # Sort Key (optional)
  rangeKeyType: string      # Key Type
  attributes: list          # Zusätzliche Attribute (für GSI/LSI)
    - name: string
      type: string
  globalSecondaryIndexes: list  # GSI Definitions
    - name: string
      hashKey: string
      rangeKey: string
      projectionType: string    # "ALL", "KEYS_ONLY", "INCLUDE"
      nonKeyAttributes: list    # Bei INCLUDE
  localSecondaryIndexes: list   # LSI Definitions
  ttlEnabled: bool              # TTL aktivieren
  ttlAttribute: string          # TTL Attribute Name
  pointInTimeRecovery: bool     # PITR aktivieren (default: true)
  encryption: string            # "AWS_OWNED", "AWS_MANAGED", "CUSTOMER_MANAGED"
  kmsKeyArn: string             # KMS Key ARN (bei CUSTOMER_MANAGED)
  streamEnabled: bool           # DynamoDB Streams aktivieren
  streamViewType: string        # "NEW_IMAGE", "OLD_IMAGE", "NEW_AND_OLD_IMAGES", "KEYS_ONLY"
  autoScaling: dict             # Auto-Scaling Config (bei PROVISIONED)
    read:
      min: int
      max: int
      target: float
    write:
      min: int
      max: int
      target: float
```

### Security Group (`security_group.tf.j2`)

```yaml
config:
  vpc: string               # VPC Component ID
  description: string       # Beschreibung
  ingressRules: list        # Ingress Rules
    - description: string
      fromPort: int
      toPort: int
      protocol: string      # "tcp", "udp", "icmp", "-1"
      cidrBlocks: list
  egressRules: list         # Egress Rules (optional, default: allow all)
    - description: string
      fromPort: int
      toPort: int
      protocol: string
      cidrBlocks: list
```

### NAT Gateway (`nat_gateway.tf.j2`)

```yaml
config:
  subnet: string            # Public Subnet Component ID
  vpc: string               # VPC Component ID
  createRouteTable: bool    # Route Table erstellen (default: true)
  privateSubnets: list      # Private Subnets für Route Table Association
```

### Internet Gateway (`internet_gateway.tf.j2`)

```yaml
config:
  vpc: string               # VPC Component ID
  createRouteTable: bool    # Public Route Table erstellen (default: true)
  associateWithMain: bool   # Als Main Route Table setzen (default: false)
```

### IAM Role (`iam.tf.j2`)

```yaml
config:
  principalType: string     # "Service", "AWS", "Federated"
  principal: string         # Service/ARN/Identity Provider ARN
  description: string       # Role Beschreibung
  maxSessionDuration: int   # Max Session Duration in Sekunden (default: 3600)
  permissionsBoundary: string  # Permissions Boundary ARN
  conditions: dict          # Assume Role Conditions
  inlinePolicies: list      # Inline Policies
    - name: string
      document: dict        # Policy Document (JSON)
  managedPolicyArns: list   # AWS Managed Policy ARNs
  customPolicies: list      # Custom Managed Policies
    - name: string
      description: string
      document: dict
  createInstanceProfile: bool  # Instance Profile erstellen (für EC2)
```

## Beispiel: JSON → Terraform Transformation

### Input Architecture JSON

```json
{
  "metadata": {
    "name": "my-web-app",
    "provider": "aws"
  },
  "components": {
    "vpc-1": {
      "name": "main-vpc",
      "type": "vpc",
      "config": {
        "cidr": "10.0.0.0/16",
        "enableDns": true,
        "needsIGW": true
      }
    },
    "subnet-1": {
      "name": "public-subnet-a",
      "type": "subnet",
      "config": {
        "vpc": "vpc-1",
        "cidr": "10.0.1.0/24",
        "az": "us-east-1a",
        "subnetType": "public"
      }
    },
    "sg-1": {
      "name": "web-sg",
      "type": "security_group",
      "config": {
        "vpc": "vpc-1",
        "description": "Security group for web servers",
        "ingressRules": [
          {
            "description": "Allow HTTP",
            "fromPort": 80,
            "toPort": 80,
            "protocol": "tcp",
            "cidrBlocks": ["0.0.0.0/0"]
          },
          {
            "description": "Allow HTTPS",
            "fromPort": 443,
            "toPort": 443,
            "protocol": "tcp",
            "cidrBlocks": ["0.0.0.0/0"]
          }
        ]
      }
    },
    "ec2-1": {
      "name": "web-server",
      "type": "ec2",
      "config": {
        "subnet": "subnet-1",
        "instanceType": "t3.small",
        "hasPublicIp": true,
        "securityGroups": ["sg-1"],
        "userData": "#!/bin/bash\nyum update -y\nyum install -y httpd\nsystemctl start httpd"
      }
    }
  },
  "connections": [
    {"from": "vpc-1", "to": "subnet-1"},
    {"from": "subnet-1", "to": "ec2-1"},
    {"from": "sg-1", "to": "ec2-1"}
  ]
}
```

### Output Terraform Files

**main.tf**
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
      Project     = "my-web-app"
      Environment = var.environment
      ManagedBy   = "OverCloud"
    }
  }
}
```

**vpc.tf**
```hcl
resource "aws_vpc" "vpc-1" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "main-vpc" }
}

resource "aws_internet_gateway" "vpc-1_igw" {
  vpc_id = aws_vpc.vpc-1.id
  tags = { Name = "main-vpc-igw" }
}
```

**subnet.tf**
```hcl
resource "aws_subnet" "subnet-1" {
  vpc_id            = aws_vpc.vpc-1.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true
  tags = { Name = "public-subnet-a", Type = "public" }
  depends_on = [aws_vpc.vpc-1]
}

resource "aws_route_table" "subnet-1_rt" {
  vpc_id = aws_vpc.vpc-1.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.vpc-1_igw.id
  }
  tags = { Name = "public-subnet-a-rt" }
}

resource "aws_route_table_association" "subnet-1_rta" {
  subnet_id      = aws_subnet.subnet-1.id
  route_table_id = aws_route_table.subnet-1_rt.id
}
```

**security_group.tf**
```hcl
resource "aws_security_group" "sg-1" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.vpc-1.id

  ingress {
    description = "Allow HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "web-sg" }
  depends_on = [aws_vpc.vpc-1]
}
```

**ec2.tf**
```hcl
data "aws_ami" "ec2-1_ami" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "ec2-1" {
  ami           = data.aws_ami.ec2-1_ami.id
  instance_type = "t3.small"
  subnet_id     = aws_subnet.subnet-1.id
  
  vpc_security_group_ids = [
    aws_security_group.sg-1.id,
  ]
  
  associate_public_ip_address = true
  
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
  EOF
  
  tags = { Name = "web-server" }
  
  depends_on = [
    aws_subnet.subnet-1,
    aws_security_group.sg-1,
  ]
}
```

## Template Development Guidelines

### 1. Naming Conventions

- **Template Dateinamen:** `<resource_type>.tf.j2`
- **Resource Names:** `{{ comp.id }}` (eindeutig, Terraform-kompatibel)
- **Display Names:** `{{ comp.name }}` (human-readable)

### 2. Required Attributes

Jedes Template sollte enthalten:
- ✅ Header Kommentar mit Resource Type
- ✅ Resource Loop über `components`
- ✅ Kommentar mit Component Name vor jeder Resource
- ✅ `tags` Block mit mindestens `Name` Tag
- ✅ `depends_on` Block (wenn Dependencies existieren)

### 3. Optional Attributes

- Verwende `| default(value)` für optionale Attribute
- Verwende `{% if ... %}` für konditionale Blöcke
- Dokumentiere defaults im Kommentar

### 4. Data Sources

- Platziere Data Sources VOR der Resource Definition
- Verwende aussagekräftige Namen: `{{ comp.id }}_<data_type>`

### 5. Jinja2 Filters

Verfügbare Filters:
- `| default(value)` - Fallback für optionale Werte
- `| lower` - String zu lowercase
- `| upper` - String zu uppercase
- `| tojson` - Python Object zu JSON
- `| indent(spaces)` - Einrückung für multi-line strings
- `| replace(old, new)` - String Replacement

### 6. Best Practices

#### ✅ DO

```jinja2
# Kommentar mit Component Name
resource "aws_instance" "{{ comp.id }}" {
  instance_type = "{{ comp.config.instanceType | default('t3.micro') }}"
  
  {% if comp.config.userData %}
  user_data = <<-EOF
{{ comp.config.userData | indent(4) }}
  EOF
  {% endif %}
  
  tags = {
    Name = "{{ comp.name }}"
  }
}
```

#### ❌ DON'T

```jinja2
# Kein Kommentar
resource "aws_instance" "{{ comp.id }}" {
  instance_type = "{{ comp.config.instanceType }}"  # Kein default!
  
  user_data = "{{ comp.config.userData }}"  # Nicht für multi-line!
  
  # Keine tags!
}
```

## Testing

### Unit Tests

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('backend/templates/terraform/components'))
template = env.get_template('ec2.tf.j2')

components = [{
    'id': 'ec2-test',
    'name': 'test-instance',
    'config': {
        'subnet': 'subnet-1',
        'instanceType': 't3.small',
        'hasPublicIp': True
    },
    'depends_on': ['aws_subnet.subnet-1']
}]

output = template.render(components=components)
print(output)
```

### Integration Tests

Verwende `terraform validate` um generierten Code zu validieren:

```bash
cd generated_terraform/
terraform init
terraform validate
```

## Troubleshooting

### Problem: Template nicht gefunden

```
TemplateNotFound: ec2.tf.j2
```

**Lösung:**
- Prüfe ob Template in `backend/templates/terraform/components/` existiert
- Prüfe Dateiname (muss `.tf.j2` Endung haben)
- Prüfe Jinja2 Environment Loader Pfade

### Problem: Undefined Variable

```
UndefinedError: 'comp' is undefined
```

**Lösung:**
- Prüfe ob Template im `{% for comp in components %}` Loop ist
- Prüfe ob Variable im `comp.config` Dictionary existiert
- Verwende `| default()` Filter für optionale Werte

### Problem: Invalid Terraform Syntax

```
Error: Argument or block definition required
```

**Lösung:**
- Prüfe ob generierter HCL syntaktisch korrekt ist
- Prüfe ob alle `{` und `}` korrekt geschlossen sind
- Prüfe ob Kommas in Listen korrekt sind (trailing comma!)
- Verwende `terraform fmt` zum Auto-Format

## Contributing

### Neues Template hinzufügen

1. Erstelle Template-Datei: `backend/templates/terraform/components/<type>.tf.j2`
2. Folge Template-Struktur (siehe oben)
3. Dokumentiere Config-Felder in dieser README
4. Füge Unit Test hinzu
5. Teste mit echtem Architecture JSON
6. Aktualisiere `TerraformGeneratorV2.supported_types`

### Template verbessern

1. Prüfe bestehende Config-Felder
2. Füge neue Features als optionale Config-Felder hinzu (mit defaults)
3. Dokumentiere Breaking Changes
4. Aktualisiere README mit neuen Feldern

## Weitere Ressourcen

- [Terraform AWS Provider Dokumentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Jinja2 Template Designer Dokumentation](https://jinja.palletsprojects.com/en/3.1.x/templates/)
- [OverCloud Architecture JSON Schema](../../docs/json-schemas/architecture.schema.json)

---

**Last Updated:** 2026-05-16
**Maintainer:** OverCloud DevOps Team
