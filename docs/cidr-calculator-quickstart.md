# VPC/CIDR Calculator - Quick Start Guide

## Übersicht

Der VPC/CIDR Calculator ist ein interaktives Tool zur Planung von AWS Virtual Private Clouds (VPCs) und Subnets. Er hilft bei der Berechnung von IP-Adressen, erkennt Overlaps und schlägt optimale Subnet-Aufteilungen vor.

## Features im Überblick

- ✅ **VPC CIDR Validierung** - Prüfung nach AWS-Regeln (/16 bis /28)
- ✅ **Subnet Planung** - Visuelle IP-Allocation mit Overlap-Erkennung
- ✅ **Automatische Vorschläge** - Sinnvolle Subnet-Aufteilung für 3 AZs
- ✅ **AWS-kompatibel** - Berücksichtigt 5 reservierte IPs pro Subnet
- ✅ **Interaktive UI** - Real-time Validation & visuelles Feedback
- ✅ **Production-ready** - Umfassend getestet (47 Tests)

## Schnellstart

### 1. Backend & Frontend starten

```bash
# Automatisches Setup mit Test-Script
cd frontend
./test_cidr_calculator.sh
```

**Manuell:**

```bash
# Terminal 1: Backend
cd backend
poetry run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 2. Browser öffnen

- **Calculator UI:** http://localhost:5173/cidr-calculator.html
- **API Docs:** http://localhost:8000/api/docs

### 3. VPC planen

1. Gib VPC CIDR ein (z.B. `10.0.0.0/16`)
2. Klicke "Validieren"
3. Nutze "Vorschläge" oder füge manuell Subnets hinzu
4. Klicke "VPC Plan berechnen"
5. Prüfe visuelle Darstellung auf Overlaps

## Beispiel-Workflow

### Szenario: 3-Tier Web Application in 3 AZs

**1. VPC CIDR eingeben**
```
10.0.0.0/16
```
→ 65.536 IPs total, 65.531 usable

**2. Vorschläge generieren**
- Anzahl AZs: `3`
- Subnet-Typen: `public`, `private`, `database`

**3. Generierter Plan**
```
VPC: 10.0.0.0/16

Public Subnets (Load Balancer, NAT Gateway)
├─ 10.0.0.0/20   (4.091 usable) - region-a
├─ 10.0.16.0/20  (4.091 usable) - region-b
└─ 10.0.32.0/20  (4.091 usable) - region-c

Private Subnets (Application Server)
├─ 10.0.48.0/20  (4.091 usable) - region-a
├─ 10.0.64.0/20  (4.091 usable) - region-b
└─ 10.0.80.0/20  (4.091 usable) - region-c

Database Subnets (RDS, ElastiCache)
├─ 10.0.96.0/20  (4.091 usable) - region-a
├─ 10.0.112.0/20 (4.091 usable) - region-b
└─ 10.0.128.0/20 (4.091 usable) - region-c

Unallocated: 28.672 IPs
Status: ✓ Keine Overlaps
```

## API Endpoints

### POST `/api/v1/cidr/validate`
Validiert VPC CIDR Block

```bash
curl -X POST http://localhost:8000/api/v1/cidr/validate \
  -H "Content-Type: application/json" \
  -d '{"cidr": "10.0.0.0/16"}'
```

### POST `/api/v1/cidr/plan`
Berechnet VPC Plan mit Subnets

```bash
curl -X POST http://localhost:8000/api/v1/cidr/plan \
  -H "Content-Type: application/json" \
  -d '{
    "vpc_cidr": "10.0.0.0/16",
    "subnets": [
      {"name": "public-1a", "cidr": "10.0.1.0/24", "type": "public"}
    ]
  }'
```

### POST `/api/v1/cidr/suggest`
Generiert Subnet-Vorschläge

```bash
curl -X POST http://localhost:8000/api/v1/cidr/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "vpc_cidr": "10.0.0.0/16",
    "num_azs": 3,
    "subnet_types": ["public", "private", "database"]
  }'
```

## AWS Best Practices

### VPC Sizing

| Use Case | VPC CIDR | Total IPs | Empfehlung |
|----------|----------|-----------|------------|
| Dev/Test | /24 | 256 | Klein, schnell aufgesetzt |
| Standard | /16 | 65.536 | **Empfohlen für Production** |
| Enterprise | /12 | 1.048.576 | Multi-Account Organisationen |

### Subnet Types

**Public Subnets**
- Internet Gateway attached
- Route: `0.0.0.0/0` → IGW
- Für: Load Balancer, NAT Gateway, Bastion Hosts

**Private Subnets**
- NAT Gateway für ausgehenden Traffic
- Route: `0.0.0.0/0` → NAT
- Für: Application Server, Container Instances

**Database Subnets**
- Kein Internet-Zugang
- Nur interne Routes
- Für: RDS, ElastiCache, DynamoDB Endpoints

### High Availability

- **Mindestens 3 AZs** für kritische Workloads
- **Gleiche Subnet-Größe** pro AZ (einfacheres Management)
- **Separate Subnets pro Layer** (Public/Private/Database)

## Tests ausführen

```bash
cd backend

# Alle CIDR Tests
poetry run pytest tests/test_cidr_calculator.py tests/test_cidr_api.py -v

# Mit Coverage
poetry run pytest --cov=app/utils/cidr_calculator --cov-report=html

# Nur Unit Tests
poetry run pytest tests/test_cidr_calculator.py -v

# Nur API Tests
poetry run pytest tests/test_cidr_api.py -v
```

**Ergebnis:** 47 Tests, alle bestanden ✓

## Troubleshooting

### Backend startet nicht

**Problem:** `ModuleNotFoundError: No module named 'ipaddress'`

**Lösung:**
```bash
cd backend
poetry install
```

### Frontend zeigt keine Daten

**Problem:** CORS-Fehler in Browser Console

**Lösung:**
- Backend läuft auf Port 8000?
- CORS in `backend/app/config.py` korrekt konfiguriert?
- Frontend nutzt `http://localhost:8000` (nicht `127.0.0.1`)

### Tests schlagen fehl

**Problem:** `ImportError: cannot import name 'CIDRCalculator'`

**Lösung:**
```bash
cd backend
poetry run pytest --collect-only  # Zeigt gefundene Tests
export PYTHONPATH=/Users/andyschwarz/Documents/Privat/OverCloud/backend
poetry run pytest
```

## Integration in OverCloud

Der CIDR Calculator ist für die spätere Integration in den Architecture Builder vorbereitet:

```javascript
// In Architecture Builder
import { CIDRCalculator } from '/js/components/CIDRCalculator.js';

// Calculator als Modal
const calc = new CIDRCalculator('modal-container');
calc.render();

// Event Handler für Plan-Übernahme
calc.onPlanCalculated = (plan) => {
  architectureBuilder.setNetworkConfig({
    vpc_cidr: plan.vpc_cidr,
    subnets: plan.subnets.map(s => ({
      id: generateId(),
      name: s.name,
      cidr: s.cidr,
      type: s.subnet_type,
      az: s.availability_zone
    }))
  });
};
```

## Weitere Informationen

- **Detaillierte Dokumentation:** `backend/app/utils/README_CIDR.md`
- **API Dokumentation:** http://localhost:8000/api/docs
- **AWS VPC Docs:** https://docs.aws.amazon.com/vpc/
- **CIDR Calculator (extern):** https://cidr.xyz

## Roadmap

- [ ] Export als Terraform Code (`vpc.tf`, `subnets.tf`)
- [ ] Import von bestehenden VPCs (AWS API)
- [ ] Visual Drag & Drop für Subnet-Größen
- [ ] Cost Estimation (NAT Gateway, VPC Endpoints)
- [ ] Multi-Cloud Support (Azure VNet, GCP VPC)
- [ ] VPC Peering Validator

## Support

Bei Fragen oder Problemen:
1. Prüfe API Dokumentation: http://localhost:8000/api/docs
2. Schaue in die Tests: `tests/test_cidr_*.py`
3. Lies README: `backend/app/utils/README_CIDR.md`

---

**Entwickelt für OverCloud** - Requirements-driven Cloud Infrastructure Management
