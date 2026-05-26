# Terraform API Reference

API-Dokumentation für Terraform-Generierung aus Infrastructure Designer.

---

## Base URL

```
http://localhost:8000/api/v1
```

Production:
```
https://api.stackvertex.io/api/v1
```

---

## Authentication

**Header:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Beispiel:**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     http://localhost:8000/api/v1/terraform/generate-from-json
```

---

## Endpoints

### 1. Generate Terraform from JSON

**POST** `/terraform/generate-from-json`

Generiert Terraform HCL-Dateien aus Architecture JSON.

#### Request

**Body:**
```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "production-infrastructure",
    "description": "Production AWS Infrastructure",
    "provider": "aws",
    "region": "us-east-1"
  },
  "components": {
    "vpc-abc123": {
      "id": "vpc-abc123",
      "type": "vpc",
      "name": "main-vpc",
      "config": {
        "cidr": "10.0.0.0/16",
        "region": "us-east-1",
        "enableDnsHostnames": true,
        "enableDnsSupport": true
      },
      "position": { "x": 400, "y": 200 }
    },
    "subnet-def456": {
      "id": "subnet-def456",
      "type": "subnet",
      "name": "public-subnet-1a",
      "config": {
        "vpcId": "vpc-abc123",
        "cidr": "10.0.1.0/24",
        "subnetType": "public",
        "az": "us-east-1a",
        "mapPublicIpOnLaunch": true
      },
      "position": { "x": 350, "y": 350 }
    },
    "ec2-ghi789": {
      "id": "ec2-ghi789",
      "type": "ec2",
      "name": "web-server-1",
      "config": {
        "instanceType": "t3.small",
        "ami": "ami-0c55b159cbfafe1f0",
        "subnetId": "subnet-def456",
        "ipMode": "manual",
        "privateIP": "10.0.1.15",
        "assignPublicIP": true,
        "securityGroupIds": ["sg-123"],
        "keyName": "my-key-pair"
      },
      "position": { "x": 350, "y": 500 }
    }
  },
  "connections": [
    {
      "id": "conn-1",
      "from": "ec2-ghi789",
      "to": "rds-jkl012",
      "data": {
        "port": 5432,
        "protocol": "tcp",
        "description": "EC2 → RDS"
      }
    }
  ]
}
```

#### Response (Success)

**Status:** `200 OK`

```json
{
  "success": true,
  "files": {
    "main.tf": "terraform {\n  required_version = \">= 1.0\"\n  ...",
    "variables.tf": "variable \"aws_region\" {\n  type = string\n  ...",
    "vpc.tf": "resource \"aws_vpc\" \"vpc_abc123\" {\n  cidr_block = \"10.0.0.0/16\"\n  ...",
    "ec2.tf": "resource \"aws_instance\" \"ec2_ghi789\" {\n  ami = \"ami-0c55b159cbfafe1f0\"\n  ...",
    "outputs.tf": "output \"vpc_id\" {\n  value = aws_vpc.vpc_abc123.id\n  ..."
  },
  "metadata": {
    "component_count": 3,
    "connection_count": 1,
    "provider": "aws",
    "generated_at": "2026-05-16T12:30:00Z",
    "generation_time_ms": 87
  }
}
```

#### Response (Error)

**Status:** `400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CIDR",
    "message": "CIDR block '10.0.0.0/33' is invalid. Prefix must be between 0 and 32.",
    "component_id": "vpc-abc123",
    "field": "cidr"
  }
}
```

**Error Codes:**
- `INVALID_CIDR` - CIDR-Block ungültig
- `MISSING_COMPONENT` - Referenzierte Komponente fehlt (z.B. VPC in Subnet)
- `INVALID_COMPONENT_TYPE` - Unbekannter Component Type
- `DEPENDENCY_CYCLE` - Zirkuläre Abhängigkeiten
- `TEMPLATE_ERROR` - Jinja2 Template-Fehler

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/terraform/generate-from-json \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @architecture.json \
  -o terraform-files.json
```

#### JavaScript Example

```javascript
async function generateTerraform(architectureJSON) {
  const response = await fetch('/api/v1/terraform/generate-from-json', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify(architectureJSON)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }
  
  const result = await response.json();
  return result.files;
}
```

---

### 2. Validate Architecture JSON

**POST** `/terraform/validate`

Validiert Architecture JSON ohne Terraform zu generieren.

#### Request

**Body:** Gleich wie `/generate-from-json`

#### Response (Success)

**Status:** `200 OK`

```json
{
  "valid": true,
  "components": 3,
  "connections": 1,
  "warnings": [
    {
      "type": "MISSING_PUBLIC_IP",
      "message": "EC2 instance 'web-server-1' in public subnet has no public IP assigned",
      "component_id": "ec2-ghi789"
    }
  ]
}
```

#### Response (Error)

**Status:** `400 Bad Request`

```json
{
  "valid": false,
  "errors": [
    {
      "code": "INVALID_CIDR",
      "message": "VPC CIDR '10.0.0.0/33' is invalid",
      "component_id": "vpc-abc123"
    },
    {
      "code": "SUBNET_OUTSIDE_VPC",
      "message": "Subnet CIDR '10.1.0.0/24' is outside VPC CIDR '10.0.0.0/16'",
      "component_id": "subnet-def456"
    }
  ]
}
```

---

### 3. Validate CIDR Block

**POST** `/cidr/validate`

Validiert einzelnen CIDR-Block und berechnet IP-Informationen.

#### Request

```json
{
  "cidr": "10.0.0.0/16"
}
```

#### Response

**Status:** `200 OK`

```json
{
  "valid": true,
  "cidr": "10.0.0.0/16",
  "network": "10.0.0.0",
  "prefix": 16,
  "total_ips": 65536,
  "usable_ips": 65531,
  "first_ip": "10.0.0.0",
  "last_ip": "10.0.255.255",
  "reserved_ips": [
    "10.0.0.0",
    "10.0.0.1",
    "10.0.0.2",
    "10.0.0.3",
    "10.0.255.255"
  ],
  "reserved_descriptions": {
    "10.0.0.0": "Network address",
    "10.0.0.1": "VPC router",
    "10.0.0.2": "DNS server",
    "10.0.0.3": "Reserved for future use",
    "10.0.255.255": "Broadcast address"
  }
}
```

#### Response (Invalid)

**Status:** `400 Bad Request`

```json
{
  "valid": false,
  "error": "Invalid CIDR format. Expected format: X.X.X.X/Y (e.g., 10.0.0.0/16)"
}
```

---

### 4. Plan CIDR Allocation

**POST** `/cidr/plan`

Plant Subnet-Aufteilung für VPC.

#### Request

```json
{
  "vpc_cidr": "10.0.0.0/16",
  "subnets": [
    { "name": "public-1a", "type": "public", "size": "/24" },
    { "name": "public-1b", "type": "public", "size": "/24" },
    { "name": "private-1a", "type": "private", "size": "/20" },
    { "name": "private-1b", "type": "private", "size": "/20" },
    { "name": "db-1a", "type": "database", "size": "/24" },
    { "name": "db-1b", "type": "database", "size": "/24" }
  ]
}
```

#### Response

**Status:** `200 OK`

```json
{
  "vpc_cidr": "10.0.0.0/16",
  "vpc_total_ips": 65536,
  "subnets": [
    {
      "name": "public-1a",
      "type": "public",
      "cidr": "10.0.0.0/24",
      "total_ips": 256,
      "usable_ips": 251,
      "first_ip": "10.0.0.0",
      "last_ip": "10.0.0.255"
    },
    {
      "name": "public-1b",
      "type": "public",
      "cidr": "10.0.1.0/24",
      "total_ips": 256,
      "usable_ips": 251,
      "first_ip": "10.0.1.0",
      "last_ip": "10.0.1.255"
    },
    {
      "name": "private-1a",
      "type": "private",
      "cidr": "10.0.16.0/20",
      "total_ips": 4096,
      "usable_ips": 4091,
      "first_ip": "10.0.16.0",
      "last_ip": "10.0.31.255"
    },
    {
      "name": "private-1b",
      "type": "private",
      "cidr": "10.0.32.0/20",
      "total_ips": 4096,
      "usable_ips": 4091,
      "first_ip": "10.0.32.0",
      "last_ip": "10.0.47.255"
    },
    {
      "name": "db-1a",
      "type": "database",
      "cidr": "10.0.48.0/24",
      "total_ips": 256,
      "usable_ips": 251,
      "first_ip": "10.0.48.0",
      "last_ip": "10.0.48.255"
    },
    {
      "name": "db-1b",
      "type": "database",
      "cidr": "10.0.49.0/24",
      "total_ips": 256,
      "usable_ips": 251,
      "first_ip": "10.0.49.0",
      "last_ip": "10.0.49.255"
    }
  ],
  "total_allocated_ips": 8960,
  "remaining_ips": 56576,
  "utilization_percent": 13.7
}
```

---

### 5. Estimate Cost

**POST** `/terraform/estimate-cost`

Schätzt monatliche AWS-Kosten basierend auf Architektur.

#### Request

**Body:** Gleich wie `/generate-from-json`

#### Response

**Status:** `200 OK`

```json
{
  "total_monthly_cost": 123.45,
  "currency": "USD",
  "breakdown": [
    {
      "component_id": "ec2-ghi789",
      "component_name": "web-server-1",
      "service": "EC2",
      "instance_type": "t3.small",
      "hours_per_month": 730,
      "hourly_cost": 0.0208,
      "monthly_cost": 15.18
    },
    {
      "component_id": "rds-jkl012",
      "component_name": "production-db",
      "service": "RDS",
      "instance_class": "db.t3.micro",
      "multi_az": true,
      "storage_gb": 20,
      "monthly_cost": 34.00
    },
    {
      "component_id": "alb-mno345",
      "component_name": "web-alb",
      "service": "ALB",
      "hours_per_month": 730,
      "lcu_per_hour": 1,
      "monthly_cost": 22.50
    }
  ],
  "notes": [
    "Costs are estimates and may vary based on actual usage",
    "Data transfer costs not included",
    "Free tier not applied"
  ]
}
```

---

## Data Models

### Architecture JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "metadata", "components"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "provider": { "enum": ["aws", "azure", "gcp"] },
        "region": { "type": "string" }
      }
    },
    "components": {
      "type": "object",
      "patternProperties": {
        "^[a-z]+-[a-f0-9]+$": {
          "type": "object",
          "required": ["id", "type", "name", "config"],
          "properties": {
            "id": { "type": "string" },
            "type": { "type": "string" },
            "name": { "type": "string" },
            "config": { "type": "object" },
            "position": {
              "type": "object",
              "properties": {
                "x": { "type": "number" },
                "y": { "type": "number" }
              }
            }
          }
        }
      }
    },
    "connections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["from", "to"],
        "properties": {
          "id": { "type": "string" },
          "from": { "type": "string" },
          "to": { "type": "string" },
          "data": { "type": "object" }
        }
      }
    }
  }
}
```

### Component Config Schemas

#### VPC Config

```json
{
  "cidr": "10.0.0.0/16",
  "region": "us-east-1",
  "enableDnsHostnames": true,
  "enableDnsSupport": true
}
```

#### Subnet Config

```json
{
  "vpcId": "vpc-abc123",
  "cidr": "10.0.1.0/24",
  "subnetType": "public",
  "az": "us-east-1a",
  "mapPublicIpOnLaunch": true
}
```

#### EC2 Config

```json
{
  "instanceType": "t3.small",
  "ami": "ami-0c55b159cbfafe1f0",
  "subnetId": "subnet-def456",
  "ipMode": "manual",
  "privateIP": "10.0.1.15",
  "assignPublicIP": true,
  "securityGroupIds": ["sg-123"],
  "keyName": "my-key-pair",
  "userData": "#!/bin/bash\napt update"
}
```

#### RDS Config

```json
{
  "engine": "postgres",
  "engineVersion": "14.7",
  "instanceClass": "db.t3.micro",
  "allocatedStorage": 20,
  "storageType": "gp3",
  "multiAZ": true,
  "subnetGroupName": "db-subnet-group",
  "securityGroupIds": ["sg-456"],
  "backupRetentionPeriod": 7,
  "encrypted": true
}
```

---

## Rate Limits

- **Authenticated:** 100 requests/minute
- **Unauthenticated:** 10 requests/minute

**Header bei Rate Limit:**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1647892400
```

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "cidr",
      "expected": "X.X.X.X/Y",
      "received": "10.0.0.0/33"
    }
  }
}
```

### HTTP Status Codes

- `200 OK` - Erfolg
- `400 Bad Request` - Ungültige Eingabe
- `401 Unauthorized` - Fehlende/ungültige Authentifizierung
- `403 Forbidden` - Keine Berechtigung
- `404 Not Found` - Ressource nicht gefunden
- `429 Too Many Requests` - Rate Limit überschritten
- `500 Internal Server Error` - Server-Fehler

---

## WebSocket Events (geplant)

Für Real-Time Collaboration in Zukunft:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/terraform/watch');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'component-updated':
      // Sync component from other user
      break;
    case 'terraform-generated':
      // Download ready
      break;
  }
};
```

---

## Related Documentation

- [Quick Start Guide](../infrastructure-designer-quickstart.md)
- [User Guide](../infrastructure-designer-guide.md)
- [Architecture Overview](../infrastructure-designer-architecture.md)

---

**API Version:** v1  
**Letzte Aktualisierung:** 2026-05-16
