# Stripe Payment Integration - Setup Guide

**Status:** ✅ Implementiert | ⏳ Setup erforderlich

---

## Übersicht

OverCloud verwendet **Stripe** für Subscription-Management:

| Plan | Monatlich | Jährlich | Rabatt |
|------|-----------|----------|--------|
| 🆓 **FREE** | €0 | €0 | - |
| 💼 **PRO** | €29/Monat | €290/Jahr | 17% (= 10 Monate) |
| 🚀 **ENTERPRISE** | €149/Monat | €1,491/Jahr | 17% |

**Features:**
- ✅ Monatlich jederzeit kündbar
- ✅ Jährlich nach Ablauf kündbar
- ✅ KEINE automatische Verlängerung per Default (Opt-In!)
- ✅ Benachrichtigungen: 30 Tage + 7 Tage vor Ablauf
- ✅ Grace Period: 30 Tage nach Ablauf (Deployments pausiert, Daten gespeichert)
- ✅ Transparente Preise, kein Dark Pattern

---

## Schritt 1: Stripe Account erstellen

1. Gehe zu [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)
2. Registriere dich mit deiner E-Mail
3. Verifiziere deine E-Mail-Adresse
4. Fülle Business-Details aus (für Auszahlungen später nötig)

---

## Schritt 2: Test Mode aktivieren

**WICHTIG:** Für Development immer **Test Mode** verwenden!

1. Im Stripe Dashboard oben rechts: **Test Mode** Toggle aktivieren
2. Du siehst jetzt: "Viewing test data"

---

## Schritt 3: API Keys kopieren

### 3.1 Secret Key holen

1. Gehe zu [Developers → API Keys](https://dashboard.stripe.com/test/apikeys)
2. Unter "Secret key" klicke "Reveal test key"
3. Kopiere `sk_test_...`

### 3.2 Publishable Key holen

1. Unter "Publishable key" kopiere `pk_test_...`

### 3.3 In .env eintragen

```bash
# backend/.env
STRIPE_ENABLED=True
STRIPE_SECRET_KEY=sk_test_51Abc...XYZ
STRIPE_PUBLISHABLE_KEY=pk_test_51Abc...XYZ
```

---

## Schritt 4: Webhook Endpoint registrieren

### 4.1 Lokales Testing mit Stripe CLI

**Installation:**
```bash
# macOS
brew install stripe/stripe-cli/stripe

# Linux
https://stripe.com/docs/stripe-cli#install
```

**Login:**
```bash
stripe login
```

**Webhook forwarding starten:**
```bash
stripe listen --forward-to http://localhost:8001/webhooks/stripe
```

Du bekommst ein **Webhook Signing Secret** (whsec_...):
```bash
STRIPE_WEBHOOK_SECRET=whsec_abc123xyz
```

Trage es in `.env` ein.

**Testen:**
```bash
# Trigger test event
stripe trigger checkout.session.completed
```

### 4.2 Production Webhook (später)

1. Gehe zu [Developers → Webhooks](https://dashboard.stripe.com/test/webhooks)
2. Klicke "Add endpoint"
3. URL: `https://api.overcloud.io/webhooks/stripe`
4. Events auswählen:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.payment_succeeded`
   - ✅ `invoice.payment_failed`
5. Klicke "Add endpoint"
6. Kopiere **Signing secret** (whsec_...) und trage in Production `.env` ein

---

## Schritt 5: Backend starten

```bash
cd backend

# .env checken
cat .env | grep STRIPE

# Backend starten
poetry run uvicorn app.main:app --reload --port 8001
```

**Checken ob Stripe funktioniert:**
```bash
curl http://localhost:8001/api/v1/billing/pricing

# Erwartete Response:
[
  {
    "plan": "free",
    "monthly_price_eur": 0.0,
    "yearly_price_eur": 0.0,
    "yearly_discount_percent": 0.0,
    "currency": "EUR"
  },
  {
    "plan": "pro",
    "monthly_price_eur": 29.0,
    "yearly_price_eur": 290.0,
    "yearly_discount_percent": 17.0,
    "currency": "EUR"
  },
  {
    "plan": "enterprise",
    "monthly_price_eur": 149.0,
    "yearly_price_eur": 1491.0,
    "yearly_discount_percent": 17.0,
    "currency": "EUR"
  }
]
```

---

## Schritt 6: Ersten Test-Checkout machen

### 6.1 User registrieren

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "Test1234!"
  }'

# Response kopieren: access_token
```

### 6.2 Checkout Session erstellen

```bash
curl -X POST http://localhost:8001/api/v1/billing/{org_id}/checkout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "pro",
    "interval": "monthly",
    "auto_renewal": false,
    "success_url": "http://localhost:5173/billing/success",
    "cancel_url": "http://localhost:5173/billing/cancel"
  }'

# Response:
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_abc123",
  "session_id": "cs_test_abc123",
  "expires_at": 1234567890
}
```

### 6.3 Checkout durchführen

1. Öffne `checkout_url` im Browser
2. Verwende Stripe Test Cards:
   - **Success:** `4242 4242 4242 4242`
   - **Decline:** `4000 0000 0000 0002`
   - **Requires Auth:** `4000 0025 0000 3155`
3. Ablaufdatum: Beliebig in Zukunft (z.B. 12/34)
4. CVC: Beliebig (z.B. 123)
5. PLZ: Beliebig (z.B. 12345)

### 6.4 Webhook Event prüfen

Nach erfolgreichem Payment sollte der Webhook gefeuert werden:

```bash
# Stripe CLI Output:
checkout.session.completed [evt_abc123]

# Backend Logs:
INFO: Received Stripe webhook: checkout.session.completed
INFO: Subscription created for org <uuid>: pro (monthly)
```

### 6.5 Organisation prüfen

```bash
curl http://localhost:8001/api/v1/organisations/{org_id} \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response sollte zeigen:
{
  "plan": "pro",  # Upgraded!
  "stripe_subscription_id": "sub_abc123",
  ...
}
```

---

## API Endpoints

### Pricing (Public)

```bash
GET /api/v1/billing/pricing
```

Keine Authentifizierung nötig.

### Checkout Session erstellen

```bash
POST /api/v1/billing/{org_id}/checkout
Authorization: Bearer <token>

{
  "plan": "pro",
  "interval": "monthly",
  "auto_renewal": false,
  "success_url": "https://app.overcloud.io/billing/success",
  "cancel_url": "https://app.overcloud.io/billing/cancel"
}

Response:
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_...",
  "expires_at": 1234567890
}
```

### Billing Portal (Subscription Management)

```bash
POST /api/v1/billing/{org_id}/billing-portal
Authorization: Bearer <token>

{
  "return_url": "https://app.overcloud.io/settings/billing"
}

Response:
{
  "portal_url": "https://billing.stripe.com/..."
}
```

User kann im Portal:
- ✅ Zahlungsmethoden verwalten
- ✅ Rechnungen einsehen
- ✅ Subscription kündigen
- ✅ Plan wechseln
- ✅ Auto-Renewal aktivieren/deaktivieren

### Subscription Status

```bash
GET /api/v1/billing/{org_id}/subscription
Authorization: Bearer <token>

Response:
{
  "has_subscription": true,
  "plan": "pro",
  "interval": "monthly",
  "status": "active",
  "current_period_end": "2026-05-26T12:00:00",
  "cancel_at_period_end": false,
  "auto_renewal_enabled": false
}
```

### Auto-Renewal aktivieren

```bash
POST /api/v1/billing/{org_id}/subscription/enable-auto-renewal
Authorization: Bearer <token>

Response:
{
  "message": "Auto-renewal enabled successfully"
}
```

### Subscription kündigen

```bash
POST /api/v1/billing/{org_id}/subscription/cancel?immediately=false
Authorization: Bearer <token>

Response:
{
  "message": "Subscription canceled at period end"
}
```

- `immediately=false`: Kündigung zum Perioden-Ende (empfohlen)
- `immediately=true`: Sofortige Kündigung

---

## Subscription Lifecycle

### 1. User kauft PRO (Monatlich, ohne Auto-Renewal)

```
checkout.session.completed
→ Organisation upgraded zu PRO
→ subscription_period_end = in 30 Tagen
→ cancel_at_period_end = true (!)
```

### 2. Benachrichtigungen

**30 Tage vor Ablauf:**
> "Dein PRO Plan läuft in 30 Tagen ab. Möchtest du automatisch verlängern?"

**7 Tage vor Ablauf:**
> "Dein PRO Plan läuft in 7 Tagen ab. Verlängern oder zur FREE downgraden?"

### 3. Ablauf ohne Renewal

```
customer.subscription.deleted
→ Organisation downgraded zu FREE
→ Status: SUSPENDED
→ grace_period_end = in 30 Tagen
```

**Grace Period:**
- Deployments werden pausiert (nicht gelöscht!)
- JSON Exports bleiben verfügbar
- User kann jederzeit wieder upgraden

**Nach 30 Tagen Grace Period:**
- Deployments werden gelöscht
- Architectures bleiben (JSON Export)

---

## Test Cards (Stripe Test Mode)

| Zweck | Kartennummer | Resultat |
|-------|-------------|----------|
| Success | `4242 4242 4242 4242` | ✅ Payment erfolgreich |
| Decline | `4000 0000 0000 0002` | ❌ Card declined |
| Requires Auth | `4000 0025 0000 3155` | 🔐 3D Secure erforderlich |
| Insufficient Funds | `4000 0000 0000 9995` | ❌ Insufficient funds |
| Expired Card | `4000 0000 0000 0069` | ❌ Card expired |

**Alle anderen Details:**
- Ablaufdatum: Beliebig in Zukunft
- CVC: Beliebig (3-4 Ziffern)
- PLZ: Beliebig

---

## Monitoring

### Stripe Dashboard

- [Payments](https://dashboard.stripe.com/test/payments)
- [Subscriptions](https://dashboard.stripe.com/test/subscriptions)
- [Customers](https://dashboard.stripe.com/test/customers)
- [Webhooks](https://dashboard.stripe.com/test/webhooks)
- [Logs](https://dashboard.stripe.com/test/logs)

### Backend Logs

```bash
# Webhook Events
grep "Received Stripe webhook" logs/app.log

# Subscription Changes
grep "Subscription" logs/app.log
```

---

## Production Checklist

Bevor du Live Mode aktivierst:

- [ ] Stripe Account verifiziert (Auszahlungen aktiviert)
- [ ] Business-Details ausgefüllt
- [ ] Live Mode Keys in Production `.env`
- [ ] Webhook Endpoint in Live Mode registriert
- [ ] Webhook Signing Secret korrekt
- [ ] Test-Payment in Live Mode durchgeführt
- [ ] Benachrichtigungen getestet (30d + 7d vor Ablauf)
- [ ] Grace Period Flow getestet
- [ ] Billing Portal getestet (Cancel, Change Plan)

---

## Troubleshooting

### "Webhook signature verification failed"

**Ursache:** Falsches `STRIPE_WEBHOOK_SECRET`

**Lösung:**
```bash
# Neues Secret generieren
stripe listen --forward-to http://localhost:8001/webhooks/stripe

# Secret kopieren und in .env eintragen
STRIPE_WEBHOOK_SECRET=whsec_abc123
```

### "Invalid API Key"

**Ursache:** Falsches `STRIPE_SECRET_KEY` oder Live Mode Key im Test Mode verwendet

**Lösung:**
```bash
# Test Mode Key verwenden
STRIPE_SECRET_KEY=sk_test_...

# Im Stripe Dashboard checken: "Viewing test data" sichtbar?
```

### Checkout Session läuft ab

**Ursache:** Session expires after 24 hours

**Lösung:** Neue Session erstellen (POST /checkout)

### Payment succeeded, aber Plan nicht upgraded

**Ursache:** Webhook nicht empfangen oder Fehler im Handler

**Lösung:**
1. Stripe Dashboard → Webhooks → Event prüfen
2. Backend Logs checken
3. Event manuell retrigger:
   ```bash
   stripe trigger checkout.session.completed
   ```

---

## Support

**Stripe Docs:**
- [Checkout Sessions](https://stripe.com/docs/payments/checkout)
- [Subscriptions](https://stripe.com/docs/billing/subscriptions/overview)
- [Webhooks](https://stripe.com/docs/webhooks)
- [Test Mode](https://stripe.com/docs/testing)

**OverCloud Support:**
- Slack: #payment-integration
- Email: support@overcloud.io

---

**Ready to accept payments! 💰**
