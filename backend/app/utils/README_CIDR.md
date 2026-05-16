# VPC/CIDR Calculator

Interaktiver Calculator zur Planung von AWS VPCs und Subnets mit visueller Validierung und Overlap-Erkennung.

## Features

### Backend (Python/FastAPI)

- **CIDR Validierung**: Prüfung von VPC CIDR Blocks nach AWS-Regeln
- **Subnet Validierung**: Überprüfung ob Subnets innerhalb der VPC liegen
- **VPC Planning**: Berechnung von IP-Allocations mit Overlap-Erkennung
- **Subnet Suggestions**: Automatische Vorschläge für sinnvolle Subnet-Aufteilung
- **AWS-kompatibel**: Berücksichtigt die 5 reservierten IPs pro Subnet

### Frontend (Vanilla JS)

- **Interaktive UI**: Visueller Calculator mit Tailwind CSS
- **Real-time Validation**: Live-Feedback beim Eingeben
- **Visual Plan**: Grafische Darstellung der IP-Allocation
- **Overlap Detection**: Farbige Kennzeichnung von Konflikten
- **Responsive**: Mobile-friendly Design

## API Endpoints

### POST `/api/v1/cidr/validate`

Validiert einen VPC CIDR Block.

**Request:**
```json
{
  "cidr": "10.0.0.0/16"
}
```

**Response:**
```json
{
  "valid": true,
  "cidr": "10.0.0.0/16",
  "total_ips": 65536,
  "usable_ips": 65531,
  "error": null,
  "warning": null
}
```

### POST `/api/v1/cidr/validate-subnet`

Validiert ob ein Subnet innerhalb eines VPC liegt.

**Request:**
```json
{
  "subnet_cidr": "10.0.1.0/24",
  "vpc_cidr": "10.0.0.0/16"
}
```

**Response:**
```json
{
  "valid": true,
  "subnet_cidr": "10.0.1.0/24",
  "vpc_cidr": "10.0.0.0/16",
  "total_ips": 256,
  "usable_ips": 251
}
```

### POST `/api/v1/cidr/plan`

Plant VPC mit Subnets und prüft auf Overlaps.

**Request:**
```json
{
  "vpc_cidr": "10.0.0.0/16",
  "subnets": [
    {
      "name": "public-1a",
      "cidr": "10.0.1.0/24",
      "type": "public",
      "az": "us-east-1a"
    },
    {
      "name": "private-1a",
      "cidr": "10.0.2.0/24",
      "type": "private",
      "az": "us-east-1a"
    }
  ]
}
```

**Response:**
```json
{
  "vpc_cidr": "10.0.0.0/16",
  "total_ips": 65536,
  "usable_ips": 65531,
  "subnets": [
    {
      "cidr": "10.0.1.0/24",
      "name": "public-1a",
      "availability_zone": "us-east-1a",
      "subnet_type": "public",
      "total_ips": 256,
      "usable_ips": 251,
      "first_ip": "10.0.1.0",
      "last_ip": "10.0.1.255",
      "reserved_ips": [
        "10.0.1.0",   // Network
        "10.0.1.1",   // VPC Router
        "10.0.1.2",   // DNS
        "10.0.1.3",   // Reserved
        "10.0.1.255"  // Broadcast
      ]
    }
  ],
  "unallocated_ips": 65024,
  "has_overlaps": false,
  "overlap_details": []
}
```

### POST `/api/v1/cidr/suggest`

Generiert Subnet-Vorschläge basierend auf VPC CIDR.

**Request:**
```json
{
  "vpc_cidr": "10.0.0.0/16",
  "num_azs": 3,
  "subnet_types": ["public", "private", "database"]
}
```

**Response:**
```json
{
  "vpc_cidr": "10.0.0.0/16",
  "num_azs": 3,
  "suggested_subnets": [
    {
      "name": "public-a",
      "cidr": "10.0.0.0/20",
      "type": "public",
      "az": "region-a"
    },
    ...
  ]
}
```

## Verwendung

### Backend starten

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

API Dokumentation: http://localhost:8000/api/docs

### Frontend öffnen

```bash
cd frontend
# Mit Vite Dev Server
npm run dev

# Oder statisch
open src/cidr-calculator.html
```

Calculator UI: http://localhost:5173/cidr-calculator.html

## AWS CIDR Regeln

### VPC CIDR Requirements

- Größe: Zwischen `/16` (65.536 IPs) und `/28` (16 IPs)
- Empfohlen: Private IP Ranges
  - `10.0.0.0/8`
  - `172.16.0.0/12`
  - `192.168.0.0/16`

### Subnet CIDR Requirements

- Muss innerhalb des VPC CIDR liegen
- Maximal `/28` (16 IPs)
- Keine Overlaps mit anderen Subnets

### Reserved IPs pro Subnet

AWS reserviert automatisch 5 IP-Adressen pro Subnet:

1. **Network Address** (z.B. `10.0.1.0`)
2. **VPC Router** (z.B. `10.0.1.1`)
3. **DNS Server** (z.B. `10.0.1.2`)
4. **Reserved for future use** (z.B. `10.0.1.3`)
5. **Broadcast Address** (z.B. `10.0.1.255`)

Beispiel: Ein `/24` Subnet hat 256 IPs total, aber nur **251 usable IPs**.

## Best Practices

### VPC Design

- Nutze `/16` für Produktionsumgebungen (Flexibilität)
- Plane genug Platz für zukünftiges Wachstum
- Vermeide Overlaps mit anderen VPCs (VPC Peering!)
- Nutze private IP-Ranges

### Subnet Strategie

- **Mindestens 3 AZs** für High Availability
- **Public Subnets**: Load Balancer, NAT Gateway, Bastion Hosts
- **Private Subnets**: Application Server, Container Instances
- **Database Subnets**: Separate Isolation für Datenbanken

### Standard-Layout (3 AZs)

```
VPC: 10.0.0.0/16 (65.536 IPs)

├─ Public Subnets (Internet-facing)
│  ├─ 10.0.0.0/20  (4.096 IPs) - us-east-1a
│  ├─ 10.0.16.0/20 (4.096 IPs) - us-east-1b
│  └─ 10.0.32.0/20 (4.096 IPs) - us-east-1c
│
├─ Private Subnets (Application Layer)
│  ├─ 10.0.48.0/20  (4.096 IPs) - us-east-1a
│  ├─ 10.0.64.0/20  (4.096 IPs) - us-east-1b
│  └─ 10.0.80.0/20  (4.096 IPs) - us-east-1c
│
└─ Database Subnets (Data Layer)
   ├─ 10.0.96.0/20  (4.096 IPs) - us-east-1a
   ├─ 10.0.112.0/20 (4.096 IPs) - us-east-1b
   └─ 10.0.128.0/20 (4.096 IPs) - us-east-1c
```

## Tests

```bash
# Unit Tests
poetry run pytest tests/test_cidr_calculator.py -v

# API Tests
poetry run pytest tests/test_cidr_api.py -v

# Alle Tests
poetry run pytest -v

# Mit Coverage
poetry run pytest --cov=app/utils/cidr_calculator --cov-report=html
```

## Technische Details

### Python Dependencies

- `ipaddress`: CIDR Berechnungen (Standard Library)
- `pydantic`: Request/Response Validation
- `fastapi`: API Framework

### JavaScript Components

- **CIDRCalculator**: Hauptkomponente
- **Vanilla JS**: Keine Framework-Dependencies
- **Tailwind CSS**: Styling

## Integration in OverCloud

Der CIDR Calculator ist Teil des OverCloud Architecture Builders und kann:

1. **Standalone genutzt werden**: Direkt über `/cidr-calculator.html`
2. **In Architecture Builder integriert werden**: Als Component
3. **API als Service**: Andere Module können die API nutzen

### Verwendung im Architecture Builder

```javascript
import { CIDRCalculator } from '/js/components/CIDRCalculator.js';

// Calculator in Modal einbinden
const modal = document.getElementById('cidr-modal');
const calc = new CIDRCalculator('cidr-container');
calc.render();

// VPC Plan übernehmen
calc.onPlanCalculated = (plan) => {
  // Plan in Architecture JSON übernehmen
  architectureBuilder.setNetworkConfig(plan);
};
```

## Roadmap

- [ ] Export als Terraform Code
- [ ] Import von bestehenden VPCs (AWS API)
- [ ] Visual Drag & Drop für Subnet-Größen
- [ ] Cost Estimation für IP-basierte Services
- [ ] Multi-Cloud Support (Azure VNet, GCP VPC)
- [ ] VPC Peering Validator

## Lizenz

Teil des OverCloud Projekts - Proprietär
