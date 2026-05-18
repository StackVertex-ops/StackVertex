# Voucher/Gutscheinsystem für OverCloud

## Übersicht

Das Voucher-System ermöglicht es SuperAdmins, Gutscheincodes zu erstellen, die Rabatte auf Subscriptions gewähren.

### Features

- **Flexible Rabatte**: Percentage (10%, 25%, 50%, 75%, 100%) oder Fixed Amount (EUR)
- **Granulare Anwendung**: Rabatt auf Base Fee, AWS Markup, oder Beide
- **Verwendungslimits**: Einmalig, n-mal, oder unbegrenzt
- **Zeitsteuerung**: Optional valid_from und valid_until
- **User-Limitierung**: Jeder User kann jeden Voucher nur einmal verwenden
- **Audit Trail**: Alle Voucher-Aktionen werden geloggt
- **Admin UI**: SuperAdmin-Dashboard für Voucher-Verwaltung

---

## Architektur

### Backend

#### Repository: `backend/app/repositories/voucher.py`
- **DynamoDB Single-Table Design**
- **PK**: `VOUCHER#{code}`, **SK**: `METADATA`
- **GSI1**: `VOUCHERS` → Ermöglicht schnelles Listing aller Vouchers

**Methoden:**
- `create()` - Erstellt neuen Voucher
- `get_by_code()` - Case-insensitive Lookup
- `validate()` - Prüft ob Voucher verwendbar
- `redeem()` - Markiert Voucher als verwendet
- `list_all()` - Admin-Übersicht
- `deactivate()` / `reactivate()` - Soft enable/disable
- `get_usage_stats()` - Nutzungsstatistiken

#### Service: `backend/app/services/voucher_service.py`
- **Business Logic** für Discount-Berechnung
- `validate_voucher()` - Validiert Code für User
- `apply_discount()` - Berechnet finale Kosten mit Rabatt
- `redeem_voucher()` - Wendet Voucher auf Subscription an
- `remove_voucher_from_subscription()` - Entfernt Voucher

#### API: `backend/app/api/voucher.py`
**Public Endpoints (Authenticated Users):**
- `POST /api/v1/voucher/validate` - Validiere Code
- `POST /api/v1/voucher/redeem` - Löse Voucher ein
- `DELETE /api/v1/voucher/remove/{org_id}` - Entferne Voucher

**Admin Endpoints (SuperAdmin only):**
- `GET /api/v1/admin/vouchers` - Liste alle Vouchers
- `GET /api/v1/admin/vouchers/{code}` - Voucher-Details
- `GET /api/v1/admin/vouchers/{code}/stats` - Usage Stats
- `POST /api/v1/admin/vouchers` - Erstelle Voucher
- `DELETE /api/v1/admin/vouchers/{code}` - Deaktiviere Voucher
- `POST /api/v1/admin/vouchers/{code}/reactivate` - Reaktiviere Voucher

#### Invoice Generator Update
- `backend/app/services/invoice_generator.py` erweitert
- Voucher-Rabatte werden als Line Item in Invoices eingetragen
- Format: `"Discount (FRIEND2026): -€50.00"`

---

### Frontend

#### Billing Page: `frontend/src/billing.html`
- **Voucher Input Field** mit Live-Validierung
- **Active Voucher Display** zeigt angewendeten Gutschein
- **Remove Voucher Button** zum Entfernen

#### Billing Controller: `frontend/src/js/pages/billing.js`
- `handleValidateVoucher()` - Validiert Code
- `handleRedeemVoucher()` - Löst Code ein
- `handleRemoveVoucher()` - Entfernt Code
- `renderVoucherStatus()` - Zeigt aktiven Voucher

#### Admin Voucher Management: `frontend/src/admin-vouchers.html`
- **Voucher Table** mit allen Gutscheinen
- **Create Voucher Modal** mit vollständigem Form
- **Actions**: Stats, Deactivate, Reactivate

#### Admin Controller: `frontend/src/js/pages/admin-vouchers.js`
- `loadVouchers()` - Lädt alle Vouchers
- `renderVouchersTable()` - Rendert Tabelle
- `handleCreateVoucher()` - Erstellt neuen Voucher
- `viewVoucherStats()` - Zeigt Stats
- `deactivateVoucher()` / `reactivateVoucher()` - Toggle Status

#### API Client: `frontend/src/js/api/voucher.js`
- Wrapper für alle Voucher API Calls

---

## Integration mit Subscription System

### Subscription Schema

**Subscription-Objekt in DynamoDB:**

```python
{
    "PK": "ORG#{org_id}",
    "SK": "SUBSCRIPTION",
    "id": "sub-uuid",
    "org_id": "org-uuid",
    "tier": "pro",                     # payg, starter, pro, enterprise
    "billing_interval": "monthly",     # monthly, annual
    "status": "active",                # active, canceled, suspended
    "base_price": 50.0,                # EUR
    "aws_markup_percentage": 0.10,     # 10%
    
    # Voucher-Felder (Optional)
    "voucher_code": "FRIEND2026",      # Aktueller Voucher (null wenn keiner)
    "voucher_discount_type": "percentage",
    "voucher_discount_value": 50,
    "voucher_applies_to": "both",
    "voucher_redeemed_at": "2026-05-17T10:30:00Z",
    
    "stripe_subscription_id": "sub_xyz",
    "stripe_customer_id": "cus_abc",
    "current_period_start": "2026-05-01T00:00:00Z",
    "current_period_end": "2026-06-01T00:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-05-17T10:30:00Z"
}
```

### Integration Flow

**1. User löst Voucher ein:**

```
┌─────────────┐      validate        ┌────────────────┐
│   Frontend  │─────────────────────>│ VoucherService │
│ (billing.js)│                       └────────┬───────┘
└─────────────┘                                │
                                               │ 1. validate_voucher()
                                               │    - Check is_active
                                               │    - Check valid_until
                                               │    - Check max_uses
                                               │    - Check used_by
                                               │
                                               v
                                       ┌────────────────┐
                                       │ VoucherRepo    │
                                       └────────┬───────┘
                                                │
                                                │ 2. redeem()
                                                │    - Increment current_uses
                                                │    - Append user_id to used_by
                                                │
                                                v
                                       ┌────────────────┐
                                       │SubscriptionRepo│
                                       └────────┬───────┘
                                                │
                                                │ 3. update()
                                                │    - Set voucher_code
                                                │    - Set voucher_*
                                                │
                                                v
                                       ┌────────────────┐
                                       │   AuditLog     │
                                       └────────────────┘
```

**2. Invoice wird generiert (monatlich):**

```
┌──────────────┐      ┌────────────────┐      ┌────────────────┐
│Cron Job      │─────>│InvoiceGenerator│─────>│ VoucherService │
│(monthly)     │      └────────┬───────┘      └────────┬───────┘
└──────────────┘               │                       │
                               │                       │
                               │ 1. get_subscription() │
                               │    - Load voucher_*   │
                               │                       │
                               │ 2. calculate_discount()
                               │<──────────────────────┘
                               │
                               │ 3. generate_invoice()
                               │    - Line Item: Base Fee
                               │    - Line Item: AWS Markup
                               │    - Line Item: Discount (negative)
                               │    - Total
                               │
                               v
                       ┌────────────────┐
                       │   DynamoDB     │
                       │ (INVOICE Item) │
                       └────────────────┘
```

**3. Stripe Subscription Update (optional):**

```python
# backend/app/services/stripe_service.py

def update_stripe_subscription_with_voucher(
    subscription: dict,
    voucher: dict
):
    """Aktualisiert Stripe Subscription mit Voucher-Rabatt.
    
    Optionen:
    1. Coupon erstellen (einmalig oder mehrfach)
    2. Invoice Item hinzufügen (manuell)
    3. Promotion Code verwenden
    """
    
    # Option 1: Coupon erstellen
    if voucher["discount_type"] == "percentage":
        coupon = stripe.Coupon.create(
            percent_off=voucher["discount_value"],
            duration="repeating",
            duration_in_months=12,  # Bis Voucher abläuft
            name=voucher["code"]
        )
        
        stripe.Subscription.modify(
            subscription["stripe_subscription_id"],
            coupon=coupon.id
        )
    
    # Option 2: Fixed Amount → Invoice Item
    elif voucher["discount_type"] == "fixed":
        stripe.InvoiceItem.create(
            customer=subscription["stripe_customer_id"],
            amount=-int(voucher["discount_value"] * 100),  # Cents, negativ
            currency="eur",
            description=f"Discount ({voucher['code']})"
        )
```

---

## Beispiel-Flows

### Flow 1: SuperAdmin erstellt Gutschein

**Schritte:**

1. SuperAdmin öffnet Admin-Dashboard (`/admin-vouchers.html`)
2. Klickt auf "Create Voucher"
3. Füllt Formular aus:
   - Code: `BETA100`
   - Discount Type: `percentage`
   - Discount Value: `100`
   - Applies To: `both`
   - Max Uses: `50`
   - Valid Until: `2026-06-30`
4. Klickt "Create"
5. Backend erstellt Voucher in DynamoDB
6. Audit Log: `admin.create_voucher`
7. Success-Message: "Voucher BETA100 created"

**Code:**

```javascript
// frontend/src/js/pages/admin-vouchers.js

async createVoucher(formData) {
    const payload = {
        code: formData.code.toUpperCase(),
        discount_type: formData.discountType,
        discount_value: parseFloat(formData.discountValue),
        applies_to: formData.appliesTo,
        max_uses: parseInt(formData.maxUses),
        valid_until: formData.validUntil
    };
    
    const result = await this.voucherAPI.createVoucher(payload);
    
    showSuccess(`Voucher ${result.code} created successfully!`);
    this.loadVouchers();  // Refresh table
}
```

### Flow 2: User validiert und löst Gutschein ein

**Schritte:**

1. User öffnet Billing-Page (`/billing.html`)
2. Gibt Gutscheincode ein: `BETA100`
3. Klickt "Validate"
4. Backend prüft Voucher:
   - ✅ Existiert
   - ✅ is_active = true
   - ✅ valid_until > now
   - ✅ current_uses < max_uses
   - ✅ User hat noch nicht verwendet
5. Success: "Voucher valid: 100% off"
6. User klickt "Redeem"
7. Backend:
   - Increment `current_uses`
   - Append `user_id` zu `used_by`
   - Update Subscription mit `voucher_code`
8. Audit Log: `voucher.redeem`
9. Success: "Voucher BETA100 applied! Next invoice will be €0."

**Code:**

```javascript
// frontend/src/js/pages/billing.js

async handleRedeemVoucher() {
    const code = document.getElementById('voucher-code-input').value.trim();
    const orgId = this.currentOrgId;
    
    try {
        const result = await this.voucherAPI.redeemVoucher(code, orgId);
        
        if (result.success) {
            showSuccess(`🎉 Voucher ${code} applied! Your subscription is now FREE.`);
            this.renderVoucherStatus(result.subscription);
            this.loadInvoices();  // Refresh to show discount
        }
    } catch (error) {
        showError(error.detail || 'Failed to redeem voucher');
    }
}
```

### Flow 3: Invoice mit Rabatt wird generiert

**Schritte:**

1. Cron Job läuft monatlich (z.B. 1. des Monats)
2. Lädt alle aktiven Subscriptions
3. Für jede Subscription:
   - Lädt AWS Costs (aus CloudWatch oder manuell eingegeben)
   - Berechnet Base Price + AWS Markup
   - Prüft ob `voucher_code` gesetzt
   - Wenn ja: Berechnet Rabatt
   - Erstellt Invoice mit Line Items
4. Speichert Invoice in DynamoDB
5. Sendet Email an User: "Your invoice is ready"
6. User sieht in Billing-Page:

```
Invoice #INV-2026-06-001
Period: 2026-05-01 - 2026-05-31

Base Fee (PRO):                €50.00
AWS Markup (€200 × 10%):       €20.00
Discount (BETA100): 100% off:  -€70.00
──────────────────────────────────────
Subtotal:                      €0.00
VAT (19%):                     €0.00
──────────────────────────────────────
Total:                         €0.00  🎉
```

**Code:**

```python
# backend/app/services/invoice_generator.py

def generate_monthly_invoices():
    """Generiert monatliche Invoices für alle Subscriptions."""
    subscriptions = subscription_repo.get_all_active()
    
    for sub in subscriptions:
        # AWS Costs abrufen
        aws_costs = get_aws_costs(
            org_id=sub["org_id"],
            start=sub["current_period_start"],
            end=sub["current_period_end"]
        )
        
        # Invoice generieren
        invoice = invoice_generator.generate_invoice(
            subscription=sub,
            aws_costs=aws_costs,
            period_start=sub["current_period_start"],
            period_end=sub["current_period_end"]
        )
        
        # Speichern
        invoice_repo.create(invoice)
        
        # Email senden
        send_invoice_email(
            user_email=sub["owner_email"],
            invoice=invoice
        )
        
        logger.info(f"Invoice {invoice['invoice_id']} created for subscription {sub['id']}")
```

---

## Security Considerations

### 1. Voucher Code Brute-Force Prevention

**Problem:** Attacker könnte zufällige Codes ausprobieren.

**Lösung:**

```python
# Rate Limiting auf /voucher/validate
@router.post("/voucher/validate")
@limiter.limit("10/minute")  # Max 10 Validierungen pro Minute
async def validate_voucher(...):
    ...
```

### 2. Voucher Sharing Prevention

**Problem:** User könnten Voucher-Codes öffentlich teilen.

**Lösung:**

```python
# Jeder User kann jeden Voucher nur 1x verwenden
# used_by Array speichert alle User IDs

# Beispiel:
voucher = {
    "code": "FRIEND2026",
    "max_uses": 100,
    "current_uses": 42,
    "used_by": ["user-1", "user-2", ..., "user-42"]
}

# Validation:
if user_id in voucher["used_by"]:
    raise HTTPException(400, "You have already used this voucher")
```

### 3. Voucher Manipulation Prevention

**Problem:** User könnte Voucher-Daten manipulieren (z.B. discount_value erhöhen).

**Lösung:**

```python
# ✅ Backend speichert Voucher-Details in Subscription
# → User kann nur Code eingeben, nicht Details

# ❌ FALSCH:
# User sendet: {"code": "FRIEND2026", "discount_value": 100}  # Manipulation!

# ✅ RICHTIG:
# User sendet: {"code": "FRIEND2026"}
# Backend lädt Voucher aus DB und verwendet Original-Werte
```

### 4. Expired Voucher Cleanup

**Problem:** Abgelaufene Vouchers bleiben aktiv.

**Lösung:**

```python
# Cron Job: Daily Voucher Cleanup
def deactivate_expired_vouchers():
    """Deaktiviert abgelaufene Vouchers (täglich)."""
    now = datetime.utcnow()
    vouchers = voucher_repo.list_all(include_inactive=False)
    
    for v in vouchers:
        if v.get("valid_until"):
            valid_until = datetime.fromisoformat(v["valid_until"])
            if valid_until < now:
                voucher_repo.deactivate(v["code"])
                logger.info(f"Deactivated expired voucher {v['code']}")
```

---

## Monitoring & Analytics

### CloudWatch Alarms

```python
# Alarm: High Voucher Usage
cloudwatch.put_metric_alarm(
    AlarmName="OverCloud-HighVoucherUsage",
    ComparisonOperator="GreaterThanThreshold",
    EvaluationPeriods=1,
    MetricName="VoucherRedemptions",
    Namespace="OverCloud/Vouchers",
    Period=3600,  # 1 hour
    Statistic="Sum",
    Threshold=50,  # Alert wenn >50 Redemptions pro Stunde
    AlarmActions=[sns_topic_arn]
)
```

### Revenue Impact Dashboard

**CloudWatch Dashboard:**

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Voucher Discount (Total EUR)",
        "metrics": [
          ["OverCloud/Billing", "VoucherDiscount", {"stat": "Sum"}]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Voucher Redemptions",
        "metrics": [
          ["OverCloud/Vouchers", "VoucherRedemptions", {"stat": "Sum"}]
        ]
      }
    }
  ]
}
```

### Analytics Queries

**PostgreSQL (falls verwendet):**

```sql
-- Top 10 Most Profitable Vouchers (höchste Conversion)
SELECT 
    v.code,
    COUNT(s.id) as subscription_count,
    SUM(i.total) as total_revenue
FROM vouchers v
LEFT JOIN subscriptions s ON s.voucher_code = v.code
LEFT JOIN invoices i ON i.subscription_id = s.id
WHERE v.is_active = true
GROUP BY v.code
ORDER BY subscription_count DESC
LIMIT 10;

-- Average Discount per Invoice
SELECT 
    AVG(discount_amount) as avg_discount,
    COUNT(*) as invoice_count
FROM invoices
WHERE voucher_code IS NOT NULL;
```

---

## Beispiel-Usage

### 1. SuperAdmin erstellt Voucher

```bash
# API Call
POST /api/v1/admin/vouchers
Authorization: Bearer {superadmin_token}

{
  "code": "FRIEND2026",
  "discount_type": "percentage",
  "discount_value": 50,
  "applies_to": "both",
  "max_uses": 100,
  "valid_until": "2026-12-31T23:59:59Z"
}

# Response
{
  "code": "FRIEND2026",
  "discount_type": "percentage",
  "discount_value": 50,
  "applies_to": "both",
  "max_uses": 100,
  "current_uses": 0,
  "is_active": true,
  "valid_until": "2026-12-31T23:59:59",
  "created_at": "2026-05-17T12:00:00",
  "created_by": "uuid-of-superadmin"
}
```

### 2. User validiert Voucher

```bash
# API Call
POST /api/v1/voucher/validate
Authorization: Bearer {user_token}

{
  "code": "FRIEND2026"
}

# Response (Success)
{
  "valid": true,
  "code": "FRIEND2026",
  "discount_type": "percentage",
  "discount_value": 50,
  "applies_to": "both",
  "remaining_uses": 100,
  "message": "Voucher is valid and can be used"
}

# Response (Error - Expired)
{
  "detail": "Voucher expired on 2026-01-01"
}
```

### 3. User löst Voucher ein

```bash
# API Call
POST /api/v1/voucher/redeem
Authorization: Bearer {user_token}

{
  "code": "FRIEND2026",
  "org_id": "uuid-of-org"
}

# Response
{
  "success": true,
  "message": "Voucher FRIEND2026 successfully applied to subscription",
  "voucher_code": "FRIEND2026",
  "org_id": "uuid-of-org",
  "subscription": {
    "id": "sub123",
    "tier": "pro",
    "base_price": 50.0,
    "voucher_code": "FRIEND2026",
    "voucher_discount_type": "percentage",
    "voucher_discount_value": 50,
    "voucher_applies_to": "both"
  }
}
```

### 4. Discount-Berechnung

**Beispiel: PRO Plan mit 50% Voucher auf "both"**

```
Base Price:        €50.00
AWS Costs:         €100.00
AWS Markup (10%):  €10.00
----------------------------
Subtotal:          €60.00

Voucher (FRIEND2026): 50% auf both
Discount:          -€30.00  (50% von €60)
----------------------------
Final Subtotal:    €30.00
Tax (19%):         €5.70
----------------------------
Total:             €35.70
```

**Beispiel: ENTERPRISE Plan mit 100% Voucher (kostenfrei)**

```
Base Price:        €250.00
AWS Costs:         €500.00
AWS Markup (5%):   €25.00
----------------------------
Subtotal:          €275.00

Voucher (BETA100): 100% auf both
Discount:          -€275.00
----------------------------
Final Subtotal:    €0.00
Tax (19%):         €0.00
----------------------------
Total:             €0.00  🎉
```

---

## Voucher-Typen Übersicht

### Nach Discount-Typ

| Type       | Beispiel | Beschreibung |
|------------|----------|--------------|
| percentage | 50       | 50% Rabatt   |
| fixed      | 25.00    | €25 Rabatt   |

### Nach Anwendung

| applies_to     | Beschreibung |
|----------------|--------------|
| base_fee       | Rabatt nur auf Base Subscription Fee |
| aws_percentage | Rabatt nur auf AWS Markup Fee |
| both           | Rabatt auf Gesamt (Base + AWS) |

### Nach Verwendungslimit

| max_uses | Beschreibung |
|----------|--------------|
| 1        | Einmalig     |
| 100      | 100x verwendbar |
| -1       | Unbegrenzt   |

---

## Validierungsregeln

### Code
- Min 4 Zeichen, Max 32 Zeichen
- Nur A-Z und 0-9 (alphanumerisch)
- Case-insensitive (intern uppercase)
- Muss unique sein

### Discount Value
- Muss > 0 sein
- Bei Percentage: Max 100%
- Bei Fixed: Beliebiger EUR-Betrag

### Zeitfenster
- `valid_from`: Optional, muss in Zukunft oder Gegenwart liegen
- `valid_until`: Optional, muss in Zukunft liegen

### User-Limits
- Jeder User kann jeden Voucher nur einmal verwenden
- Auch wenn `max_uses` = 100, User kann nicht zweimal einlösen
- `used_by` Array speichert alle User IDs

---

## Audit Logging

Alle Voucher-Aktionen werden geloggt:

- `voucher.validate` - User validiert Voucher
- `voucher.redeem` - User löst Voucher ein
- `voucher.remove` - User entfernt Voucher
- `admin.create_voucher` - Admin erstellt Voucher
- `admin.deactivate_voucher` - Admin deaktiviert Voucher
- `admin.reactivate_voucher` - Admin reaktiviert Voucher

Details enthalten:
- User Email
- Voucher Code
- Organisation ID
- Timestamp
- Success/Failure

---

## Testing

### Unit Tests

**Repository Tests:** `backend/tests/test_voucher_repository.py`
- ✅ Create voucher
- ✅ Duplicate code rejection
- ✅ Code validation (length, chars)
- ✅ Discount value validation
- ✅ Case-insensitive lookup
- ✅ Validate voucher (active, expired, usage limit)
- ✅ Redeem voucher
- ✅ List vouchers
- ✅ Deactivate/Reactivate
- ✅ Usage stats

**Service Tests:** `backend/tests/test_voucher_service.py`
- ✅ Validate voucher
- ✅ Apply discount (percentage, fixed, applies_to)
- ✅ 100% discount (kostenfrei)
- ✅ Fixed discount exceeds target
- ✅ Redeem voucher
- ✅ Remove voucher
- ✅ Calculate subscription price with voucher

### Integration Tests (TODO)

- E2E Test: Create → Validate → Redeem → Invoice
- Test: Voucher in Stripe Subscription
- Test: Voucher removal doesn't "un-redeem"

---

## Deployment

### Database Migration

**Kein Schema-Update nötig** - DynamoDB ist schemaless.

Vouchers werden als neue Items gespeichert:
```
PK: VOUCHER#{code}
SK: METADATA
GSI1PK: VOUCHERS
GSI1SK: {code}
```

### Environment Variables

Keine neuen Env Vars erforderlich.

### API Router

Router ist bereits in `backend/app/main.py` eingebunden:
```python
from app.api import voucher
app.include_router(voucher.router, tags=["vouchers"])
```

---

## Sicherheit

### SuperAdmin-Only Creation
- Nur SuperAdmins können Vouchers erstellen
- `get_current_superadmin` Dependency in Admin-Endpoints

### User Verification
- User muss Mitglied der Organisation sein
- `org_repo.is_member()` Check vor Redeem

### Code Injection Prevention
- Alle Inputs validiert (Pydantic Models)
- Code nur A-Z0-9 (Regex Pattern)
- SQL Injection nicht möglich (DynamoDB)

### Rate Limiting
- Global Rate Limits via SlowAPI
- Voucher-Endpoints unterliegen Standard-Limits

---

## Monitoring & Analytics

### Metriken

1. **Usage Rate**
   - Wie viele Vouchers werden verwendet?
   - Welcher Discount-Typ ist beliebt?

2. **Conversion Rate**
   - Wie viele Validations führen zu Redemptions?

3. **Revenue Impact**
   - Durchschnittlicher Rabatt pro Voucher
   - Gesamter Rabatt-Betrag pro Monat

### CloudWatch Logs

```bash
# Voucher creation
[INFO] SuperAdmin admin@overcloud.com created voucher FRIEND2026

# Voucher redemption
[INFO] User user@example.com redeemed voucher FRIEND2026 for org uuid-123

# Validation failures
[WARNING] Voucher validation failed: Voucher expired
```

---

## Erweiterungen (Future)

### Phase 2
- [ ] Voucher-Kategorien (Beta, Influencer, Partner)
- [ ] Automatische Voucher-Generation (API Key basiert)
- [ ] Voucher-Templates für wiederkehrende Kampagnen
- [ ] Email-Versand von Vouchers

### Phase 3
- [ ] Referral Vouchers (User wirbt User)
- [ ] Tiered Vouchers (Rabatt steigt mit Nutzung)
- [ ] Conditional Vouchers (nur für bestimmte Tiers)
- [ ] Voucher-Stacking (mehrere Vouchers kombinieren)

---

## Troubleshooting

### Voucher wird nicht angezeigt
- **Check**: Ist `is_active = true`?
- **Check**: Ist `valid_from` < now < `valid_until`?
- **Check**: Subscription existiert?

### Voucher kann nicht eingelöst werden
- **Error**: "already used" → User hat Voucher bereits verwendet
- **Error**: "usage limit reached" → `max_uses` erreicht
- **Error**: "already has voucher" → Subscription hat bereits einen Voucher (entfernen zuerst)

### Rabatt wird nicht in Invoice angezeigt
- **Check**: Subscription hat `voucher_code` gesetzt?
- **Check**: `InvoiceGenerator._calculate_voucher_discount()` wird aufgerufen?
- **Check**: Line Item mit negativem Amount vorhanden?

---

## Support & Maintenance

### SuperAdmin Aktionen

**Voucher-Cleanup:**
```bash
# Deaktiviere abgelaufene Vouchers
# (Automatisch via Cron Job - TODO)
GET /api/v1/admin/vouchers?include_inactive=false
→ Filter expired
→ DELETE /api/v1/admin/vouchers/{code}
```

**Voucher-Statistiken:**
```bash
# Top 10 Most Used Vouchers
GET /api/v1/admin/vouchers
→ Sort by current_uses DESC
→ Limit 10
```

---

## Changelog

### Version 1.0.0 (2026-05-17)
- ✅ Initial Implementation
- ✅ Repository + Service + API
- ✅ Frontend Integration (Billing + Admin)
- ✅ Unit Tests (Repository + Service)
- ✅ Invoice Generator Update
- ✅ Audit Logging

---

## Kontakt

Bei Fragen oder Problemen:
- **Docs**: Dieses Dokument
- **Code**: `backend/app/repositories/voucher.py`
- **Tests**: `backend/tests/test_voucher_*.py`
- **Frontend**: `frontend/src/js/pages/billing.js`, `admin-vouchers.js`

**Entwickler**: Claude Sonnet 4.5 via OverCloud Agent Team
**Projekt**: OverCloud - Cloud Infrastructure Management Platform
