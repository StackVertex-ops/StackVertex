# Live Cost Calculation System

**Status:** ✅ Implementiert  
**Version:** 1.0.0  
**Datum:** 2026-05-16

## Übersicht

Das Live Cost Calculation System ermöglicht Real-Time Kostenberechnung für Blueprint-Formulare. Nutzer sehen sofort, wie sich ihre Konfigurationsänderungen auf die monatlichen AWS-Kosten auswirken.

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend                               │
│                                                              │
│  ┌────────────────┐         ┌─────────────────────┐        │
│  │  FormBuilder   │────────>│  LiveCostPanel      │        │
│  │                │  onChange│                     │        │
│  │  - Fields      │         │  - Debouncing       │        │
│  │  - Validation  │         │  - API Calls        │        │
│  │  - Events      │         │  - Rendering        │        │
│  └────────────────┘         └─────────────────────┘        │
│                                      │                       │
│                                      │ POST /costs/         │
│                                      │   calculate-live     │
└──────────────────────────────────────┼───────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       Backend                                │
│                                                              │
│  ┌────────────────┐         ┌─────────────────────┐        │
│  │  costs.py      │────────>│  cost_calculator.py │        │
│  │  (API Endpoint)│         │                     │        │
│  │                │         │  - EC2              │        │
│  │                │         │  - RDS              │        │
│  │                │         │  - S3               │        │
│  │                │         │  - Lambda           │        │
│  │                │         │  - ALB/NAT/Route53  │        │
│  └────────────────┘         └─────────────────────┘        │
│                                      │                       │
│                                      │                       │
│                                      ▼                       │
│                          ┌─────────────────────┐            │
│                          │  aws_constraints.py │            │
│                          │                     │            │
│                          │  - Pricing Data     │            │
│                          │  - Instance Types   │            │
│                          │  - Storage Types    │            │
│                          └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Komponenten

### 1. Backend: `cost_calculator.py`

**Pfad:** `/backend/app/services/cost_calculator.py`

Berechnet Kosten für AWS Resources basierend auf Konfiguration.

**Funktionen:**

- `calculate_ec2_cost()` - EC2 Instance Kosten
- `calculate_rds_cost()` - RDS Database Kosten (Instance + Storage + Backups)
- `calculate_s3_cost()` - S3 Storage Kosten (Storage + Requests + Transfer)
- `calculate_cloudfront_cost()` - CloudFront CDN Kosten
- `calculate_lambda_cost()` - Lambda Serverless Kosten
- `calculate_alb_cost()` - Application Load Balancer
- `calculate_nat_gateway_cost()` - NAT Gateway
- `calculate_route53_cost()` - Route53 DNS
- `calculate_blueprint_cost()` - Gesamt-Blueprint Kosten

**Modelle:**

- `CostItem` - Einzelner Kostenposten
- `CostBreakdown` - Kompletter Kosten-Breakdown

**Beispiel:**

```python
from app.services.cost_calculator import calculate_blueprint_cost

breakdown = calculate_blueprint_cost(
    blueprint_id="three-tier-web",
    configuration={
        "ec2_instance_type": "t3.small",
        "min_instances": 2,
        "rds_instance_class": "db.t3.micro",
        "rds_engine": "postgres",
        "rds_allocated_storage": 20
    }
)

print(f"Total: ${breakdown.total}/month")
```

### 2. Backend: API Endpoint

**Pfad:** `/backend/app/api/costs.py`

**Endpoint:** `POST /api/v1/costs/calculate-live`

**Request:**

```json
{
  "blueprint_id": "static-website",
  "configuration": {
    "storage_gb": 50,
    "traffic_gb": 1000,
    "monthly_requests": 1000000,
    "domain_name": "example.com"
  }
}
```

**Response:**

```json
{
  "items": [
    {
      "service": "S3",
      "resource": "Storage (STANDARD)",
      "amount": 0.023,
      "unit": "GB/month",
      "quantity": 50,
      "total": 1.15
    },
    {
      "service": "CloudFront",
      "resource": "Data Transfer",
      "amount": 0.085,
      "unit": "GB",
      "quantity": 1000,
      "total": 85.0
    },
    {
      "service": "Route53",
      "resource": "Hosted Zone",
      "amount": 0.5,
      "unit": "zone/month",
      "quantity": 1,
      "total": 0.5
    }
  ],
  "subtotal": 86.65,
  "tax": 0.0,
  "total": 86.65,
  "currency": "USD",
  "period": "monthly",
  "assumptions": [
    "~50GB stored files",
    "~1000GB traffic per month",
    "~1,000,000 requests per month"
  ]
}
```

### 3. Frontend: `LiveCostPanel.js`

**Pfad:** `/frontend/src/js/components/LiveCostPanel.js`

Zeigt Kostenübersicht und updated automatisch bei Form-Änderungen.

**Features:**

- **Debouncing:** 500ms Verzögerung zwischen API-Calls
- **Loading State:** Spinner während Berechnung
- **Error Handling:** User-friendly Error Messages
- **Animated Transitions:** Smooth number changes
- **Responsive Design:** Mobile-optimiert

**Verwendung:**

```javascript
import { LiveCostPanel } from './components/LiveCostPanel.js';

const costPanel = new LiveCostPanel('static-website');
costPanel.render(); // Initial render

// Update on form change
costPanel.updateCost({
  storage_gb: 100,
  traffic_gb: 2000
});
```

### 4. Frontend: FormBuilder Integration

**Pfad:** `/frontend/src/js/components/forms/FormBuilder.js`

FormBuilder integriert LiveCostPanel automatisch.

**Automatische Updates:**

- Bei jedem `change` Event
- Bei jedem `input` Event (debounced)
- Nach Field Dependencies

**Beispiel:**

```javascript
import { FormBuilder } from './components/forms/FormBuilder.js';

const blueprint = {
  metadata: { id: 'three-tier-web' },
  form_schema: [ /* fields */ ]
};

const formBuilder = new FormBuilder(blueprint);
formBuilder.render();
formBuilder.renderCostPanel(); // Renders cost panel + initial calculation
```

## Blueprint-Unterstützung

### 1. Static Website

**Blueprint ID:** `static-website`

**Services:**

- S3 (Storage)
- CloudFront (CDN)
- Route53 (DNS)

**Configuration:**

```json
{
  "storage_gb": 50,
  "traffic_gb": 1000,
  "monthly_requests": 1000000,
  "domain_name": "example.com"
}
```

### 2. Three-Tier Web App

**Blueprint ID:** `three-tier-web`

**Services:**

- EC2 (Compute)
- RDS (Database)
- ALB (Load Balancer)
- NAT Gateway (VPC)

**Configuration:**

```json
{
  "ec2_instance_type": "t3.small",
  "min_instances": 2,
  "rds_instance_class": "db.t3.micro",
  "rds_engine": "postgres",
  "rds_allocated_storage": 20,
  "rds_multi_az": false
}
```

### 3. Serverless API

**Blueprint ID:** `serverless-api`

**Services:**

- Lambda (Functions)
- API Gateway (REST API)
- DynamoDB (Database)

**Configuration:**

```json
{
  "lambda_invocations_per_month": 1000000,
  "lambda_memory_mb": 512,
  "lambda_avg_duration_ms": 200,
  "api_requests_per_month": 1000000
}
```

## CSS Styling

**Pfad:** `/frontend/src/css/components/live-cost-panel.css`

**Klassen:**

- `.cost-estimation-panel` - Haupt-Container
- `.cost-breakdown-item` - Einzelner Cost Item
- `.cost-total` - Total Cost Bereich
- `.cost-value-updated` - Animation bei Änderung
- `.cost-assumptions` - Annahmen-Liste

**Animationen:**

```css
.cost-value-updated {
  @apply scale-110 text-blue-600;
  transition: transform 0.3s ease, color 0.3s ease;
}
```

## Testing

### Backend Unit Tests

**Pfad:** `/backend/tests/test_cost_calculator.py`

**Ausführen:**

```bash
cd backend
pytest tests/test_cost_calculator.py -v
```

**Test Coverage:**

- ✅ EC2 Cost Calculation
- ✅ RDS Cost Calculation (Single-AZ, Multi-AZ, Backups)
- ✅ S3 Cost Calculation
- ✅ CloudFront Tiered Pricing
- ✅ Lambda Free Tier
- ✅ Blueprint Calculations (alle 3 Blueprints)
- ✅ Error Handling (invalid instance types, etc.)

### Backend API Tests

**Pfad:** `/backend/test_live_cost_api.sh`

**Ausführen:**

```bash
cd backend
./test_live_cost_api.sh
```

**Tests:**

1. Static Website Blueprint
2. Three-Tier Web App Blueprint
3. Serverless API Blueprint
4. Invalid Blueprint (Error Handling)
5. Invalid Instance Type (Error Handling)

### Frontend Testing

**Pfad:** `/frontend/src/test-live-cost.html`

**Starten:**

```bash
cd frontend
npm run dev
# Open http://localhost:5173/src/test-live-cost.html
```

**Interaktive Tests:**

- Blueprint Selection
- Form Field Changes
- Live Cost Updates
- Error States
- Loading States

## Performance

### Optimierungen

1. **Debouncing:** 500ms Verzögerung reduziert API-Calls
2. **Caching:** AWS Pricing Data ist statisch gecached
3. **Lazy Loading:** Cost Panel nur bei Bedarf gerendert
4. **Incremental Updates:** Nur geänderte Werte neu berechnet

### Metriken

- **API Response Time:** < 50ms (p95)
- **Frontend Update:** < 100ms nach Debounce
- **Total Latency:** < 600ms (incl. debounce)

## Pricing Data

**Quelle:** `/backend/app/data/aws_constraints.py`

**Stand:** Mai 2026 (us-east-1)

**Update Strategie:**

1. Manuelle Updates bei AWS Preisänderungen
2. TODO: Automatischer Sync via AWS Pricing API

**Abweichungen:**

- Free Tier berücksichtigt
- Tiered Pricing implementiert
- Multi-AZ Duplikation korrekt
- Backup Storage separat

## Erweiterungen

### Neue Blueprints hinzufügen

1. **Backend:** `cost_calculator.py`

```python
elif blueprint_id == "new-blueprint":
    # Calculate costs
    items.append(calculate_ec2_cost(...))
    items.append(calculate_rds_cost(...))
    assumptions.append("...")
```

2. **Frontend:** Test-Formular in `test-live-cost.html`

```javascript
'new-blueprint': {
    fields: [
        { name: 'field1', label: 'Field 1', type: 'number', default: 100 }
    ]
}
```

### Neue AWS Services

1. **Constraints:** `aws_constraints.py`

```python
# Add pricing data
NEW_SERVICE_PRICING = {
    'service_option': Decimal('0.10')
}
```

2. **Calculator:** `cost_calculator.py`

```python
def calculate_new_service_cost(...) -> CostItem:
    """Berechnet Kosten für neuen Service"""
    ...
```

## Troubleshooting

### Problem: Kosten werden nicht updated

**Lösung:**

1. Browser Console checken (Netzwerk-Errors?)
2. Backend Logs checken (API Errors?)
3. FormBuilder onChange Events prüfen

### Problem: Falsche Kosten

**Lösung:**

1. AWS Constraints prüfen (Pricing korrekt?)
2. Blueprint Configuration validieren
3. Unit Tests ausführen

### Problem: Performance-Issues

**Lösung:**

1. Debounce-Delay erhöhen (aktuell 500ms)
2. API Response cachen (client-side)
3. Weniger Form Fields verwenden

## Best Practices

### Backend

1. **Decimal verwenden:** Alle Kosten als `Decimal` (nicht `float`)
2. **Free Tier berücksichtigen:** Lambda, S3, etc.
3. **Multi-AZ korrekt:** Storage verdoppeln
4. **Tiered Pricing:** CloudFront, Data Transfer

### Frontend

1. **Debouncing:** Immer bei User Input
2. **Loading States:** User Feedback während Berechnung
3. **Error Handling:** User-friendly Messages
4. **Accessibility:** WCAG 2.1 AA compliant

### Testing

1. **Edge Cases:** Free Tier, Multi-AZ, Tiered Pricing
2. **Invalid Input:** Unknown instance types, etc.
3. **Integration Tests:** Full flow (Form → API → Render)

## Roadmap

### Phase 1 (✅ Done)

- [x] Backend Cost Calculator
- [x] API Endpoint
- [x] Frontend LiveCostPanel
- [x] FormBuilder Integration
- [x] 3 Blueprint-Unterstützungen
- [x] Unit Tests
- [x] Documentation

### Phase 2 (Geplant)

- [ ] Cost History & Comparison
- [ ] Cost Alerts (über Budget)
- [ ] Export als PDF/CSV
- [ ] Multi-Region Support
- [ ] Azure/GCP Pricing
- [ ] Automatische AWS Pricing Updates

### Phase 3 (Später)

- [ ] Cost Optimization Suggestions
- [ ] Reserved Instance Recommendations
- [ ] Savings Plans Simulation
- [ ] Budget Tracking
- [ ] Forecast (ML-basiert)

## Kontakt & Support

**Entwickler:** Andy Schwarz  
**Email:** schwarz23andy@gmail.com  
**Projekt:** StackVertex  
**Version:** 1.0.0  

---

**Letzte Aktualisierung:** 2026-05-16
