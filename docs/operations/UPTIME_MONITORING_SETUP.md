# Uptime Monitoring Setup - UptimeRobot

**Zweck:** 24/7 Verfügbarkeitsüberwachung für Production  
**Tool:** UptimeRobot (Free Tier ausreichend)  
**Zeit:** ~30 Minuten  
**Kosten:** Kostenlos (bis 50 Monitors)

---

## 🎯 Ziel

Automatische Benachrichtigung bei Production Downtime innerhalb von 5 Minuten.

---

## 📋 Quick Start (30 Minuten)

### 1. UptimeRobot Account erstellen (5 Min)

1. Gehe zu: **[uptimerobot.com](https://uptimerobot.com)**
2. Klicke **"Sign Up Free"**
3. Registriere dich mit:
   - Email: `schwarz23andy@gmail.com`
   - Oder: Login via Google
4. Email bestätigen

**Free Tier beinhaltet:**
- ✅ 50 Monitors
- ✅ 5-Minuten Check-Intervall
- ✅ Email + SMS Alerts
- ✅ Public Status Page
- ✅ Unbegrenzte Alert-Kontakte

---

### 2. Ersten Monitor erstellen (10 Min)

#### Health Endpoint Monitor

1. **Dashboard → Add New Monitor**

2. **Monitor Type:** HTTP(s)

3. **Friendly Name:** `StackVertex API - Health`

4. **URL:** `https://api.stackvertex.io/health`
   - Development: `http://localhost:8000/health` (nur für lokale Tests)
   - Staging: `https://api-staging.stackvertex.io/health`
   - Production: `https://api.stackvertex.io/health`

5. **Monitoring Interval:** 5 minutes (Free Tier)
   - Upgrade: 1 minute (Pro Plan)

6. **Monitor Timeout:** 30 seconds

7. **HTTP Method:** GET

8. **Expected Status Code:** 200

9. **Keyword Monitoring (optional):**
   - Keyword: `"status":"healthy"`
   - Alert if keyword not found

**Klicke "Create Monitor"**

---

### 3. Alert-Kontakte hinzufügen (5 Min)

1. **My Settings → Alert Contacts**

2. **Add Alert Contact:**
   - Type: **Email**
   - Email: `schwarz23andy@gmail.com`
   - Name: `Andy Schwarz - Primary`

3. **Optional: Weitere Kontakte:**
   - Type: **SMS** (Telefonnummer)
   - Type: **Slack** (Webhook URL)
   - Type: **Webhook** (für eigene Integration)

4. **Threshold einstellen:**
   - Alert wenn: Monitor ist down (Default)
   - Alert nach: 1 fehlgeschlagenem Check (sofort)
   - Recovery Alert: Ja (wenn wieder online)

---

### 4. Weitere Monitors erstellen (10 Min)

#### Monitor #2: Root Endpoint
```
Name:     StackVertex API - Root
URL:      https://api.stackvertex.io/
Expected: 200
Keyword:  "StackVertex API"
```

#### Monitor #3: Frontend
```
Name:     StackVertex Frontend
URL:      https://stackvertex.io/
Expected: 200
Keyword:  "StackVertex"
```

#### Monitor #4: Auth API
```
Name:     StackVertex API - Auth Health
URL:      https://api.stackvertex.io/api/v1/auth/health
Expected: 200 (oder 404 wenn Endpoint nicht existiert)
```

#### Monitor #5: Database Connection (indirect)
```
Name:     StackVertex API - Architectures List
URL:      https://api.stackvertex.io/api/v1/architectures
Expected: 401 (Unauthorized - bedeutet API läuft, nur Auth fehlt)
```

**Tipp:** Bei Endpoints die Auth brauchen:
- Expected Status: 401 ist OK (API läuft)
- 500/502/503 = ALERT (Backend Problem)

---

### 5. Public Status Page erstellen (Optional, 5 Min)

1. **Dashboard → Add New Status Page**

2. **Type:** Public Status Page (kostenlos)

3. **Custom Domain:** `status.stackvertex.io` (DNS konfigurieren)
   - Oder: Standard `stackvertex.betteruptime.com`

4. **Select Monitors:**
   - [x] StackVertex API - Health
   - [x] StackVertex Frontend
   - [x] StackVertex API - Root

5. **Customization:**
   - Logo: StackVertex Logo
   - Color: #a18072 (Primary Color)
   - Custom Message: "Real-time status of StackVertex services"

6. **Klicke "Create Status Page"**

**Share URL mit Team:** `https://status.stackvertex.io`

---

## 🔔 Alert-Konfiguration

### Email Alert Template

UptimeRobot sendet automatisch Emails bei Downtime:

**Subject:**
```
[DOWN] StackVertex API - Health is down
```

**Body:**
```
Monitor Name: StackVertex API - Health
URL: https://api.stackvertex.io/health
Status: Down
Started: 2026-05-17 23:45 UTC
Duration: 5 minutes

Reason: Connection timeout

View Details: [Link to Dashboard]
```

### Alert-Frequenz

**Default:**
- Sofort bei erstem Failed Check (nach 5 Min)
- Re-Alert alle 30 Minuten (solange down)
- Recovery Alert wenn wieder online

**Empfehlung:**
- Production: Re-Alert alle 15 Min
- Staging: Re-Alert alle 60 Min

---

## 📊 Dashboard Overview

### Uptime Percentage

UptimeRobot zeigt:
- **Last 24 hours:** 99.8% Uptime
- **Last 7 days:** 99.5% Uptime
- **Last 30 days:** 99.9% Uptime

**SLA Target:** 99.9% (< 43 Min Downtime/Monat)

### Response Time Graph

- Average: <500ms
- Peak: <2000ms
- Baseline: ~200ms

**Alerts bei:**
- Response Time > 3000ms (3s)
- Häufige Timeouts

---

## 🔧 Advanced Configuration

### Custom HTTP Headers

Für Endpoints mit spezifischen Requirements:

```
Monitor Settings → Advanced
→ Custom HTTP Headers
→ Add Header:
   Key:   Authorization
   Value: Bearer test-token-für-monitoring
```

**Sicherheit:**
- Niemals echte User-Credentials verwenden
- Separater "Monitoring API Key" erstellen
- Read-Only Permissions

### POST Requests Monitoring

Für API Health Checks die POST brauchen:

```
Monitor Type: HTTP(s)
Method:       POST
Post Type:    JSON
Post Value:   {"action": "health_check"}
Expected:     200
```

### SSL Certificate Monitoring

UptimeRobot prüft automatisch:
- ✅ SSL Certificate Validity
- ✅ Expiration Date
- ✅ Certificate Chain

**Alert:** 30 Tage vor Ablauf

---

## 📱 Mobile App (Optional)

**UptimeRobot App:**
- iOS: App Store
- Android: Play Store

**Features:**
- Push Notifications (schneller als Email)
- Dashboard on-the-go
- Acknowledge Incidents
- View History

---

## 🚨 Integration mit anderen Tools

### Slack Integration

1. **Slack → Apps → Incoming Webhooks**
2. **Create Webhook für #stackvertex-alerts**
3. **UptimeRobot → Alert Contacts → Add Webhook**
   ```
   Webhook URL: https://hooks.slack.com/services/XXX/YYY/ZZZ
   POST Value:  {"text": "*MONITOR_NAME* is *MONITOR_STATUS*"}
   ```

### PagerDuty Integration (für On-Call)

1. **PagerDuty → Services → Create Service**
2. **Integration:** UptimeRobot
3. **Copy Integration Key**
4. **UptimeRobot → Alert Contacts → Add PagerDuty**

### Custom Webhook (für eigene Automation)

```bash
# Webhook Endpoint erstellen (optional)
POST https://api.stackvertex.io/webhooks/uptime-alert

Body:
{
  "monitor_id": "123456",
  "monitor_name": "StackVertex API - Health",
  "monitor_url": "https://api.stackvertex.io/health",
  "status": "down",
  "alert_datetime": "2026-05-17 23:45:00",
  "alert_type": "down"
}
```

---

## 📈 Reporting

### Uptime Reports (monatlich)

UptimeRobot generiert automatisch:
- PDF Report (Email)
- Uptime % pro Monitor
- Downtime Incidents
- Average Response Time

**Konfiguration:**
```
My Settings → Reports
→ Enable Monthly Report
→ Email: schwarz23andy@gmail.com
→ Send on: 1st of each month
```

### SLA Reporting

Für Kunden/Stakeholder:

```
Dashboard → Monitor → Stats
→ Export CSV (30/90 days)
→ Share via Public Status Page
```

---

## 🔒 Sicherheit

### Was UptimeRobot sieht:
- ✅ Response Status Codes (200, 500, etc.)
- ✅ Response Times
- ✅ Response Body (nur Keywords)
- ✅ SSL Certificate Info

### Was UptimeRobot NICHT sehen sollte:
- ❌ Sensitive User Data
- ❌ API Keys in Response
- ❌ Database Credentials

**Best Practice:**
- Separate `/health` Endpoint ohne sensitive Data
- Kein PII (Personal Identifiable Information)
- Rate Limiting für Health Endpoint ausschalten (Monitoring-Traffic)

---

## 💰 Kosten

### Free Plan (aktuell)
- **50 Monitors:** Kostenlos
- **5 Min Interval:** Kostenlos
- **Public Status Page:** Kostenlos
- **Email Alerts:** Unbegrenzt
- **SMS Alerts:** 50/Monat kostenlos

**Ausreichend für:** MVP, kleine Teams

### Pro Plan ($7/Monat)
- **1 Min Interval** (schnellere Detection)
- Advanced Status Pages
- Custom Domains
- API Access
- Priority Support

**Upgrade wenn:**
- Kritische Production App
- SLA < 5 Min Detection nötig
- Custom Branding wichtig

---

## ✅ Verification Checklist

Nach Setup:

- [ ] UptimeRobot Account erstellt
- [ ] Monitor für `/health` Endpoint angelegt
- [ ] Alert-Kontakt (Email) hinzugefügt
- [ ] Test-Alert getriggert (Stop Backend kurz)
- [ ] Email-Benachrichtigung erhalten
- [ ] Optional: Public Status Page erstellt
- [ ] Optional: Weitere Monitors angelegt
- [ ] Optional: Slack Integration konfiguriert

**Status:** 🟢 Uptime Monitoring aktiv!

---

## 🧪 Testing

### Test-Alert triggern

**Option 1: Backend stoppen**
```bash
# Stoppe Backend für 2 Minuten
cd backend
# Strg+C (Uvicorn beenden)
# Warte 5-10 Min
# → UptimeRobot sendet Alert

# Starte Backend wieder
poetry run uvicorn app.main:app --reload
# Warte 5 Min
# → UptimeRobot sendet Recovery Alert
```

**Option 2: Falsche URL**
```bash
# Temporär Monitor auf nicht-existierende URL ändern
Dashboard → Monitor → Edit
URL: https://api.stackvertex.io/does-not-exist
→ Save
→ Warte 5 Min → Alert
→ URL wieder auf /health ändern
```

---

## 🐛 Troubleshooting

### "Monitor is UP but I can't access the URL"

**Mögliche Ursachen:**
1. Firewall blockiert deinen Client, nicht UptimeRobot
2. VPN/Proxy Problem
3. DNS Cache (flush: `sudo dscacheutil -flushcache`)

### "Too many false alerts"

**Lösungen:**
1. Timeout erhöhen (30s → 60s)
2. Retry: 2-3 mal bevor Alert
3. Keyword Monitoring deaktivieren (falls Response variiert)

### "Alert kommt zu spät"

**Limits:**
- Free Tier: 5 Min Check-Intervall
- Lösung: Upgrade auf Pro ($7/Monat) für 1 Min Checks

---

## 📚 Ressourcen

- **UptimeRobot Docs:** [uptimerobot.com/help](https://uptimerobot.com/help/)
- **API Docs:** [uptimerobot.com/api](https://uptimerobot.com/api/)
- **Status:** [status.uptimerobot.com](https://status.uptimerobot.com/)

---

## 📋 Monitor-Übersicht (Empfohlen)

| Monitor | URL | Interval | Alert Threshold |
|---------|-----|----------|-----------------|
| API Health | /health | 5 Min | 1 failed check |
| API Root | / | 5 Min | 1 failed check |
| Frontend | stackvertex.io | 5 Min | 1 failed check |
| Auth | /api/v1/auth/... | 5 Min | 2 failed checks |

**Total:** 4 Monitors (von 50 verfügbar)

---

**Geschätzte Setup-Zeit:** 30 Minuten  
**Benefit:** 24/7 Monitoring + Sofortige Downtime-Alerts  
**Kosten:** Kostenlos (Free Tier)  
**Status:** ✅ Setup-Anleitung komplett

**Erstellt:** 2026-05-17  
**Autor:** Claude Sonnet 4.5
