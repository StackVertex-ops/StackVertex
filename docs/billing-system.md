# StackVertex Billing System

> **Hybrid Pricing Model:** Flat Fee + % AWS Infrastructure Costs

---

## Überblick

Das StackVertex Billing System implementiert ein hybrides Pricing-Modell, das Transparenz und faire Preise gewährleistet:

- **Base Fee:** Feste monatliche/jährliche Gebühr je nach Tier
- **AWS Cost Markup:** Prozentuale Aufschlag auf tatsächliche AWS-Infrastrukturkosten
- **Pay-as-you-go:** Optional für variable Nutzung ohne monatliche Verpflichtung

---

## Pricing Tiers

### 1. STARTER
**Für Einzelpersonen & kleine Projekte**

- **Base Fee:** €10/Monat (€100/Jahr)
- **AWS Markup:** 15%
- **Limits:**
  - Max 3 Deployments
  - Max 10 AWS Resources pro Deployment
  - 1 Organisation
  - Community Support

**Beispiel-Rechnung:**
```
AWS Costs:        €30/Monat (kleine EC2 Instance)
StackVertex Base:   €10/Monat
StackVertex Markup: €4.50 (15% von €30)
─────────────────────────────────────
Subtotal:         €44.50
VAT (19%):        €8.46
Total:            €52.96/Monat
```

---

### 2. PRO (Recommended)
**Für Teams & Production Apps**

- **Base Fee:** €50/Monat (€500/Jahr)
- **AWS Markup:** 10%
- **Limits:**
  - Max 20 Deployments
  - Unlimited AWS Resources
  - 3 Organisationen
  - Email Support (24h Response)
  - Advanced Monitoring

**Beispiel-Rechnung:**
```
AWS Costs:        €200/Monat (EC2, RDS, S3, etc.)
StackVertex Base:   €50/Monat
StackVertex Markup: €20 (10% von €200)
─────────────────────────────────────
Subtotal:         €70
VAT (19%):        €13.30
Total:            €83.30/Monat
```

---

### 3. ENTERPRISE
**Für große Teams & kritische Infrastruktur**

- **Base Fee:** €250/Monat (€2500/Jahr)
- **AWS Markup:** 5%
- **Limits:**
  - Unlimited Deployments
  - Unlimited Organisations
  - Priority Support (4h Response)
  - SLA 99.9%
  - Dedicated Account Manager
  - Custom Integrations

**Beispiel-Rechnung:**
```
AWS Costs:        €2000/Monat (große Production-Infrastruktur)
StackVertex Base:   €250/Monat
StackVertex Markup: €100 (5% von €2000)
─────────────────────────────────────
Subtotal:         €350
VAT (19%):        €66.50
Total:            €416.50/Monat
```

---

### 4. PAY-AS-YOU-GO
**Für variable Nutzung ohne Commitment**

- **Base Fee:** €0/Monat
- **AWS Markup:** 20%
- **Per-Deployment Fee:** €5 pro Deployment
- **Limits:**
  - Unbegrenzte Deployments (pay per use)
  - 1 Organisation
  - Community Support

**Beispiel-Rechnung:**
```
AWS Costs:        €50/Monat
StackVertex Base:   €0
Deployments:      3 × €5 = €15
StackVertex Markup: €10 (20% von €50)
─────────────────────────────────────
Subtotal:         €25
VAT (19%):        €4.75
Total:            €29.75/Monat
```

---

## Architektur

### Database Schema (DynamoDB)

#### Subscription Table
```json
{
  "PK": "ORG#<org_id>",
  "SK": "SUBSCRIPTION",
  "id": "subscription-uuid",
  "org_id": "org-uuid",
  "tier": "pro",
  "billing_period": "monthly",
  "status": "active",
  "base_price": 50.00,
  "aws_cost_percentage": 10,
  "limits": {
    "max_deployments": 20,
    "max_organisations": 3
  },
  "current_period_start": "2026-05-01T00:00:00Z",
  "current_period_end": "2026-06-01T00:00:00Z",
  "stripe_subscription_id": "sub_xyz",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-05-01T00:00:00Z"
}
```

#### AWS Cost Record
```json
{
  "PK": "ORG#<org_id>",
  "SK": "AWS_COST#2026-05",
  "id": "cost-record-uuid",
  "org_id": "org-uuid",
  "month": "2026-05",
  "deployment_costs": {
    "deployment-uuid-1": {
      "ec2": 50.00,
      "rds": 80.00,
      "s3": 5.00,
      "total": 135.00
    }
  },
  "total_aws_costs": 185.00,
  "stackvertex_percentage_fee": 18.50,
  "created_at": "2026-05-01T00:00:00Z"
}
```

#### Invoice
```json
{
  "PK": "ORG#<org_id>",
  "SK": "INVOICE#INV-2026-05-001",
  "id": "invoice-uuid",
  "invoice_number": "INV-2026-05-001",
  "org_id": "org-uuid",
  "period_start": "2026-05-01T00:00:00Z",
  "period_end": "2026-06-01T00:00:00Z",
  "line_items": [
    {
      "description": "StackVertex Pro - Base Fee",
      "amount": 50.00,
      "currency": "EUR"
    },
    {
      "description": "AWS Infrastructure Costs (10% markup)",
      "breakdown": {
        "aws_costs": 185.00,
        "percentage": 10,
        "fee": 18.50
      },
      "amount": 18.50,
      "currency": "EUR"
    }
  ],
  "subtotal": 68.50,
  "tax": 13.02,
  "total": 81.52,
  "status": "paid",
  "stripe_invoice_id": "in_xyz",
  "paid_at": "2026-06-05T14:20:00Z",
  "created_at": "2026-06-01T00:00:00Z"
}
```

---

## Backend Services

### 1. SubscriptionRepository
**Location:** `backend/app/repositories/subscription.py`

**Funktionen:**
- `create()` - Erstellt neue Subscription
- `get_by_org()` - Holt Subscription einer Organisation
- `update_tier()` - Ändert Tier (Upgrade/Downgrade)
- `update_status()` - Ändert Status (active, cancelled, etc.)
- `renew_period()` - Verlängert Billing-Period nach Zahlung
- `check_limit()` - Prüft ob Limit erreicht ist

### 2. AWSCostRepository
**Location:** `backend/app/repositories/aws_cost.py`

**Funktionen:**
- `store_monthly_costs()` - Speichert monatliche AWS-Kosten
- `get_monthly_costs()` - Holt Kosten für einen Monat
- `list_costs_by_org()` - Listet Cost-History
- `get_deployment_costs()` - Holt Kosten eines Deployments
- `get_cost_trend()` - Berechnet Cost-Trend über Zeit

### 3. InvoiceRepository
**Location:** `backend/app/repositories/invoice.py`

**Funktionen:**
- `create()` - Erstellt neue Invoice
- `get_by_number()` - Holt Invoice per Nummer
- `list_by_org()` - Listet alle Invoices einer Org
- `mark_as_paid()` - Markiert Invoice als bezahlt
- `get_overdue_invoices()` - Findet überfällige Invoices

### 4. AWSCostTracker
**Location:** `backend/app/services/aws_cost_tracker.py`

**Funktionen:**
- `fetch_and_store_monthly_costs()` - Holt AWS Costs via Cost Explorer API
- `get_cost_projection()` - Projiziert End-of-Month Costs

**AWS Cost Explorer Integration:**
```python
# Fetches costs grouped by Service AND Deployment Tag
response = ce_client.get_cost_and_usage(
    TimePeriod={'Start': '2026-05-01', 'End': '2026-06-01'},
    Granularity='MONTHLY',
    Metrics=['UnblendedCost'],
    GroupBy=[
        {'Type': 'DIMENSION', 'Key': 'SERVICE'},
        {'Type': 'TAG', 'Key': 'stackvertex:deployment_id'}
    ]
)
```

### 5. InvoiceGenerator
**Location:** `backend/app/services/invoice_generator.py`

**Funktionen:**
- `generate_monthly_invoice()` - Generiert monatliche Invoice
- `preview_next_invoice()` - Preview ohne zu erstellen
- `_build_line_items()` - Baut Invoice Line Items

---

## API Endpoints

### GET /billing/pricing/hybrid
**Public Endpoint** - Hybrid Pricing Information

**Response:**
```json
[
  {
    "tier": "pro",
    "base_price_monthly": 50.00,
    "base_price_annual": 500.00,
    "aws_cost_percentage": 10,
    "limits": {...},
    "features": [...]
  }
]
```

---

### POST /billing/pricing/estimate
**Public Endpoint** - Cost Estimation

**Request:**
```json
{
  "tier": "pro",
  "estimated_aws_costs": 200.00,
  "num_deployments": 0
}
```

**Response:**
```json
{
  "tier": "pro",
  "base_price": 50.00,
  "aws_costs": 200.00,
  "markup_percentage": 10,
  "markup_fee": 20.00,
  "deployment_fees": 0.00,
  "subtotal": 70.00,
  "tax": 13.30,
  "total": 83.30,
  "currency": "EUR"
}
```

---

### GET /billing/{org_id}/costs/current
**Auth Required** - Current Month Costs

**Response:**
```json
{
  "month": "2026-05",
  "total_aws_costs": 185.00,
  "stackvertex_percentage_fee": 18.50,
  "deployment_costs": {
    "deployment-1": {
      "ec2": 50.00,
      "rds": 80.00
    }
  }
}
```

---

### GET /billing/{org_id}/costs/projection
**Auth Required** - Cost Projection

**Response:**
```json
{
  "current_aws_costs": 120.00,
  "projected_aws_costs": 200.00,
  "projected_stackvertex_fee": 20.00,
  "projected_total": 220.00,
  "days_elapsed": 18,
  "days_in_month": 30
}
```

---

### GET /billing/{org_id}/invoices
**Auth Required** - Invoice History

**Response:**
```json
[
  {
    "id": "invoice-uuid",
    "invoice_number": "INV-2026-05-001",
    "period_start": "2026-05-01T00:00:00Z",
    "period_end": "2026-06-01T00:00:00Z",
    "total": 83.30,
    "status": "paid",
    "created_at": "2026-06-01T00:00:00Z",
    "paid_at": "2026-06-05T14:20:00Z"
  }
]
```

---

## Frontend

### 1. Pricing Page
**File:** `frontend/src/pricing-hybrid.html`

**Features:**
- Pricing Tiers Display
- Interactive Cost Calculator
- Real-time Cost Estimation
- Responsive Design

### 2. Billing Dashboard
**File:** `frontend/src/js/pages/billing-dashboard.js`

**Features:**
- Current Subscription Status
- Current Month Costs
- Cost Projection
- Invoice History
- Stripe Billing Portal Integration

---

## Stripe Integration

### Checkout Flow
1. User wählt Plan auf Pricing-Page
2. Backend erstellt Stripe Checkout Session via `StripeService`
3. User wird zu Stripe Checkout weitergeleitet
4. Nach erfolgreicher Zahlung: Webhook aktualisiert Subscription

### Billing Portal
- User kann Subscription verwalten
- Payment Methods ändern
- Invoices herunterladen
- Subscription kündigen

**Code:**
```python
stripe_service.create_billing_portal_session(
    customer_id=customer_id,
    return_url=return_url
)
```

---

## AWS Cost Tracking

### Tagging Strategy
Alle von StackVertex deployte Resources werden automatisch getaggt:

```hcl
tags = {
  "stackvertex:deployment_id" = "deployment-uuid"
  "stackvertex:org_id"         = "org-uuid"
  "stackvertex:tier"           = "pro"
  "stackvertex:managed_by"     = "stackvertex"
}
```

### Cost Explorer Query
Monatliche Kosten werden via AWS Cost Explorer API abgerufen:

```python
ce_client.get_cost_and_usage(
    TimePeriod={'Start': start_date, 'End': end_date},
    Granularity='MONTHLY',
    Metrics=['UnblendedCost'],
    GroupBy=[
        {'Type': 'DIMENSION', 'Key': 'SERVICE'},
        {'Type': 'TAG', 'Key': 'stackvertex:deployment_id'}
    ]
)
```

**Hinweis:** Cost Explorer API erfordert, dass der Customer AWS Account Zugriff gewährt hat.

---

## Automated Invoicing

### Monthly Cron Job
**Scheduled:** 1. Tag des Monats, 02:00 UTC

**Flow:**
1. Für alle aktiven Subscriptions:
   - Fetch AWS Costs für vergangenen Monat
   - Generate Invoice
   - Send via Stripe (automatische Email)
2. Update Subscription Period
3. Alert bei Fehlern

**Implementation:**
```python
# backend/app/services/background_tasks.py
@scheduler.scheduled_job('cron', day=1, hour=2)
async def generate_monthly_invoices():
    """Generate invoices for all active subscriptions."""
    generator = InvoiceGenerator(...)
    generator.generate_invoices_for_all_orgs(current_month)
```

---

## Testing

### Unit Tests
**File:** `backend/tests/test_billing.py`

**Coverage:**
- Billing Models
- Subscription Repository
- AWS Cost Repository
- Invoice Repository
- Invoice Generator
- Cost Calculations

**Run Tests:**
```bash
cd backend
pytest tests/test_billing.py -v
```

### Integration Tests
- Full Billing Cycle
- Stripe Webhook Handling
- AWS Cost Explorer Integration

---

## Security

### Customer AWS Credentials
- Gespeichert verschlüsselt in AWS Secrets Manager
- Nur temporärer Zugriff via AssumeRole
- Niemals in Logs oder Responses

### Payment Data
- Alle Payment Data bei Stripe gespeichert
- StackVertex speichert nur Stripe IDs
- PCI-DSS Compliance durch Stripe

### Invoice Access
- Nur Organisation Members können Invoices sehen
- RBAC: MEMBER role required
- Audit Logs für alle Billing-Zugriffe

---

## Monitoring & Alerts

### Cost Alerts
- 80% of projected monthly cost reached
- Unusual cost spike (>50% increase)
- Deployment without proper tagging

### Billing Alerts
- Payment failed
- Subscription expiring in 7 days
- Invoice overdue

### Admin Alerts
- Monthly revenue report
- Failed invoice generations
- Cost Explorer API errors

---

## Roadmap

### Phase 1 (MVP) ✅
- [x] Hybrid Pricing Model
- [x] Subscription Management
- [x] AWS Cost Tracking
- [x] Invoice Generation
- [x] Stripe Integration

### Phase 2
- [ ] Multi-Currency Support (USD, GBP)
- [ ] Usage-Based Discounts (Volume Pricing)
- [ ] Referral Program
- [ ] Annual Billing Discounts

### Phase 3
- [ ] Azure Cost Tracking
- [ ] GCP Cost Tracking
- [ ] Cost Optimization Recommendations
- [ ] Budget Alerts & Limits

---

## FAQ

### Wie werden AWS Costs getrackt?
Wir nutzen die AWS Cost Explorer API, um deine tatsächlichen Infrastrukturkosten abzurufen. Alle von StackVertex deployte Resources werden automatisch getaggt.

### Was passiert wenn ich mein Limit erreiche?
Du bekommst eine Warnung wenn du 80% deines Deployment-Limits erreichst. Bei 100% werden neue Deployments blockiert (bestehende laufen weiter).

### Kann ich jederzeit kündigen?
Ja! Monatliche Subscriptions sind jederzeit kündbar. Du hast Zugriff bis zum Ende der bezahlten Periode.

### Sind die AWS Costs genau?
Die Costs werden täglich aktualisiert via AWS Cost Explorer. Es kann eine Verzögerung von 24-48h geben, bis AWS die finalen Costs berechnet hat.

---

**Last Updated:** 2026-05-17  
**Version:** 1.0.0
