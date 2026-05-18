# Billing System Setup Guide

Quick Start Guide für die Integration des Hybrid Billing Systems.

---

## Backend Setup

### 1. Install Dependencies

Keine neuen Dependencies erforderlich! Das System nutzt bestehende Packages:
- `boto3` - AWS SDK (bereits vorhanden)
- `stripe` - Stripe Integration (bereits vorhanden)
- `fastapi` - API Framework (bereits vorhanden)

### 2. Environment Variables

Füge folgende Variablen zu `.env` hinzu:

```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ENABLED=true

# AWS Cost Explorer
AWS_COST_EXPLORER_ENABLED=true

# Billing Settings
BILLING_CURRENCY=EUR
BILLING_VAT_RATE=0.19
```

### 3. DynamoDB Tables

Keine neuen Tables erforderlich! Das System nutzt die bestehende DynamoDB-Tabelle mit folgenden Access Patterns:

**Subscription:**
- PK: `ORG#<org_id>`
- SK: `SUBSCRIPTION`
- GSI1PK: `SUBSCRIPTION#<subscription_id>`
- GSI1SK: `METADATA`

**AWS Costs:**
- PK: `ORG#<org_id>`
- SK: `AWS_COST#<month>`
- GSI1PK: `MONTH#<month>`
- GSI1SK: `ORG#<org_id>`

**Invoices:**
- PK: `ORG#<org_id>`
- SK: `INVOICE#<invoice_number>`
- GSI1PK: `INVOICE#<invoice_id>`
- GSI1SK: `METADATA`

### 4. Register API Routes

In `backend/app/main.py`:

```python
from app.api import billing

# Register billing routes
app.include_router(
    billing.router,
    prefix="/billing",
    tags=["billing"]
)
```

### 5. AWS IAM Permissions

Der OverCloud Service Account benötigt:

```json
{
  "Version": "2012-17-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
```

### 6. Customer AWS Credentials

Kunden müssen OverCloud Zugriff auf ihre AWS Cost Explorer API gewähren:

**Option 1: IAM Role (Recommended)**
```json
{
  "Version": "2012-17-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

**Option 2: IAM User mit Read-Only Cost Explorer Access**

---

## Frontend Setup

### 1. Update Navigation

Füge Pricing & Billing Links zur Navigation hinzu:

```html
<!-- In allen HTML-Files -->
<nav>
  <a href="/pricing-hybrid.html">Pricing</a>
  <a href="/billing.html">Billing</a>
</nav>
```

### 2. API Config

In `frontend/src/js/api/config.js`:

```javascript
export const API_BASE_URL = process.env.API_URL || 'http://localhost:8000/api';
```

### 3. Build & Deploy

```bash
cd frontend
npm install
npm run build
```

---

## Stripe Setup

### 1. Create Stripe Account
- Sign up at https://stripe.com
- Complete KYC verification
- Activate account

### 2. Create Products & Prices

**Via Stripe Dashboard:**

1. Products → Add Product
2. Create für jeden Tier:
   - STARTER (€10/month, €100/year)
   - PRO (€50/month, €500/year)
   - ENTERPRISE (€250/month, €2500/year)

3. Copy Price IDs zu `.env`

**Via Stripe API (Automated):**

```bash
# Run setup script
python backend/scripts/setup_stripe_products.py
```

### 3. Configure Webhooks

**Dashboard:**
1. Developers → Webhooks → Add endpoint
2. URL: `https://your-domain.com/api/webhooks/stripe`
3. Events to listen:
   - `checkout.session.completed`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

4. Copy Webhook Secret zu `.env`

### 4. Test Webhooks

```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger invoice.paid
```

---

## AWS Cost Explorer Setup

### 1. Enable Cost Explorer

In AWS Console:
1. Billing → Cost Explorer
2. Enable Cost Explorer
3. Wait 24h for initial data

### 2. Create Cost Allocation Tags

1. Billing → Cost Allocation Tags
2. Activate User-Defined Tags:
   - `overcloud:deployment_id`
   - `overcloud:org_id`
   - `overcloud:tier`
   - `overcloud:managed_by`

3. Wait 24h for activation

### 3. Test Cost Explorer API

```python
import boto3

ce = boto3.client('ce')

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': '2026-05-01',
        'End': '2026-05-31'
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost']
)

print(response)
```

---

## Automated Invoice Generation

### 1. Setup Cron Job

**Option A: AWS EventBridge (Recommended)**

```yaml
# infrastructure/terraform/modules/billing/eventbridge.tf
resource "aws_cloudwatch_event_rule" "monthly_invoicing" {
  name                = "overcloud-monthly-invoicing"
  schedule_expression = "cron(0 2 1 * ? *)"  # 1st day of month, 02:00 UTC
}

resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.monthly_invoicing.name
  target_id = "InvokeInvoicingLambda"
  arn       = aws_lambda_function.invoicing.arn
}
```

**Option B: Kubernetes CronJob**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: monthly-invoicing
spec:
  schedule: "0 2 1 * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: invoicing
            image: overcloud/backend:latest
            command: ["python", "-m", "app.cli.generate_invoices"]
          restartPolicy: OnFailure
```

**Option C: Python Script (Development)**

```bash
# Add to crontab
0 2 1 * * cd /app && python -m app.cli.generate_invoices
```

### 2. Test Invoice Generation

```bash
# Generate test invoice for specific org
python -m app.cli.generate_invoices --org-id <org_id> --month 2026-05
```

---

## Testing

### 1. Run Unit Tests

```bash
cd backend
pytest tests/test_billing.py -v --cov=app.repositories --cov=app.services
```

### 2. Test Stripe Integration

```bash
# Use Stripe test mode
export STRIPE_SECRET_KEY=sk_test_...

# Run integration tests
pytest tests/test_stripe_integration.py -v
```

### 3. Test AWS Cost Tracking

```bash
# Mock AWS Cost Explorer
pytest tests/test_aws_cost_tracker.py -v --mock-aws
```

### 4. End-to-End Test

```bash
# Full billing cycle test
python -m app.cli.test_billing_cycle
```

---

## Deployment Checklist

### Pre-Launch
- [ ] Stripe Account aktiviert & verifiziert
- [ ] Products & Prices in Stripe erstellt
- [ ] Webhooks konfiguriert & getestet
- [ ] AWS Cost Explorer aktiviert
- [ ] Cost Allocation Tags aktiviert
- [ ] DynamoDB Tables erstellt
- [ ] Environment Variables gesetzt
- [ ] IAM Permissions konfiguriert
- [ ] Unit Tests bestanden
- [ ] Integration Tests bestanden

### Post-Launch
- [ ] Monitoring eingerichtet
- [ ] Alerts konfiguriert
- [ ] Backup Strategy definiert
- [ ] Incident Response Plan erstellt
- [ ] Documentation aktualisiert
- [ ] Customer Support informiert

---

## Troubleshooting

### Problem: Stripe Checkout fails

**Solution:**
1. Check Stripe logs: https://dashboard.stripe.com/logs
2. Verify API Key is correct
3. Check webhook signature validation

### Problem: AWS Cost Explorer returns empty data

**Solution:**
1. Verify Cost Explorer is enabled (wait 24h after activation)
2. Check IAM permissions
3. Verify tags are properly applied to resources

### Problem: Invoices not generating automatically

**Solution:**
1. Check cron job is running
2. Verify background task scheduler is active
3. Check logs for errors: `tail -f logs/billing.log`

### Problem: Cost projection inaccurate

**Solution:**
1. AWS Cost data has 24-48h delay
2. Check if all resources are properly tagged
3. Verify Cost Explorer data is up-to-date

---

## Support

### Documentation
- Full documentation: `/docs/billing-system.md`
- API Reference: `/docs/api/billing.md`

### Logs
- Application logs: `logs/app.log`
- Billing logs: `logs/billing.log`
- Stripe webhooks: `logs/stripe.log`

### Monitoring
- CloudWatch Dashboard: `OverCloud-Billing`
- Stripe Dashboard: https://dashboard.stripe.com

---

## Next Steps

1. ✅ Review dieser Setup-Guide
2. ✅ Test Billing System im Development
3. ⏳ Deploy zu Staging Environment
4. ⏳ Conduct User Acceptance Testing
5. ⏳ Launch to Production
6. ⏳ Monitor metrics for first 30 days

---

**Questions?** Contact: schwarz23andy@gmail.com
