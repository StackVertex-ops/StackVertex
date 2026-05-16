# Uptime Monitoring - Setup Guide

> **Zeit:** 30 Minuten  
> **Tool:** UptimeRobot (kostenlos)  
> **Zweck:** Benachrichtigung wenn API down ist

---

## Was ist Uptime Monitoring?

Uptime Monitoring prüft regelmäßig ob deine API erreichbar ist und benachrichtigt dich sofort bei Ausfällen.

**Ohne Uptime Monitoring:**
- Du merkst erst von Ausfällen wenn Kunden sich beschweren
- Keine Transparenz über Verfügbarkeit
- Kein Nachweis für SLA (99.9% Uptime)

**Mit Uptime Monitoring:**
- Benachrichtigung innerhalb 1-5 Minuten bei Ausfall
- Uptime-Statistiken (99.95%, 99.99%, etc.)
- Public Status Page für Kunden
- Incident History

---

## Tool-Vergleich

| Tool | Kosten (Free) | Kosten (Paid) | Empfehlung |
|------|--------------|---------------|------------|
| **UptimeRobot** | 50 Monitore, 5min Interval | $7/Monat (1min Interval) | ⭐ MVP |
| **Better Uptime** | 10 Monitore, 3min Interval | $20/Monat | Später |
| **Pingdom** | 1 Monitor | $10/Monat | Zu teuer |
| **AWS CloudWatch** | Pay-per-use | ~$1-5/Monat | Komplex |

**Empfehlung:** Start mit **UptimeRobot Free**, später upgrade zu Better Uptime.

---

## Setup: UptimeRobot (30 Minuten)

### 1. Account erstellen

1. Gehe zu: https://uptimerobot.com/signUp
2. Registriere dich (Email + Passwort)
3. Email bestätigen
4. Login: https://uptimerobot.com/dashboard

### 2. API Health Check Monitor erstellen

**Monitor Settings:**
```
Monitor Type:     HTTPS
Friendly Name:    OverCloud API Production
URL:              https://api.overcloud.io/health
Monitoring Interval: 5 minutes (Free) oder 1 minute (Paid)
Monitor Timeout:  30 seconds

Alert Contacts:   deine@email.de
Alert When:       Down
```

**Klick auf "Create Monitor"**

### 3. Weitere Monitore erstellen (optional)

#### Staging Environment
```
Friendly Name:    OverCloud API Staging
URL:              https://api-staging.overcloud.io/health
Monitoring Interval: 5 minutes
```

#### Frontend
```
Friendly Name:    OverCloud Frontend
URL:              https://overcloud.io
Monitoring Interval: 5 minutes
```

#### Specific Endpoints (kritische Features)
```
Friendly Name:    OverCloud API - Auth
URL:              https://api.overcloud.io/api/v1/auth/health
Monitoring Interval: 5 minutes
```

### 4. Alert Channels konfigurieren

**Email Alerts (Standard):**
- Automatisch aktiviert bei Account-Erstellung
- Bekommt Alerts bei Down/Up Events

**Slack Integration (empfohlen):**
1. UptimeRobot → My Settings → Alert Contacts
2. Add Alert Contact → Slack
3. Autorisiere Slack Workspace
4. Wähle Channel: `#overcloud-alerts`
5. Speichern

**SMS Alerts (optional, $9/Monat):**
- Nur für kritische Production Alerts
- Wenn Email nicht schnell genug

**Webhook (für Custom Integration):**
```
Webhook URL: https://api.overcloud.io/webhooks/uptime
Method: POST
Custom HTTP Headers:
  Authorization: Bearer YOUR_WEBHOOK_SECRET
```

### 5. Public Status Page erstellen

**Warum?**
- Kunden können selbst sehen ob alles läuft
- Transparenz bei Incidents
- Reduces Support-Anfragen ("Ist die API down?")

**Setup:**
1. UptimeRobot → Status Pages
2. Create Status Page
3. Settings:
   ```
   Status Page Name: OverCloud Status
   Monitors: Wähle alle Production Monitors
   Custom Domain: status.overcloud.io (optional)
   Show Response Times: Yes
   Show Uptime: Yes (Last 30 days)
   ```
4. Customize Design:
   - Logo hochladen
   - Farben anpassen (Purple Gradient wie Landing Page)
   - Custom CSS (optional)

**Fertig!** Status Page URL: `https://stats.uptimerobot.com/abc123`

**Einbinden auf Website:**
```html
<!-- In frontend/src/index.html Footer -->
<a href="https://stats.uptimerobot.com/abc123" target="_blank">
  System Status
</a>
```

### 6. Maintenance Windows konfigurieren

**Warum?**
- Geplante Wartungen sollen keine Alerts triggern
- Verhindert False-Positives

**Setup:**
1. UptimeRobot → Maintenance Windows
2. Create Maintenance Window
3. Settings:
   ```
   Type: One-Time (für geplantes Deployment)
   Start: 2026-05-20 02:00 UTC
   Duration: 1 hour
   Affected Monitors: All Production Monitors
   Reason: "Planned deployment of v1.2.0"
   ```

---

## Alert-Strategie

### Production (Critical)
```
Monitor Interval: 1 minute (Paid)
Alert After: 1 failed check (sofort)
Alert Channels: Email + Slack + SMS (Critical)
```

### Staging (Important)
```
Monitor Interval: 5 minutes
Alert After: 2 failed checks (10 Min)
Alert Channels: Email + Slack
```

### Development (Informational)
```
Monitor Interval: 15 minutes
Alert After: 3 failed checks (45 Min)
Alert Channels: Email only
```

---

## Health Check Endpoint verbessern

**Aktuell (`backend/app/main.py`):**
```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
```

**Besser (detailliert):**
```python
@app.get("/health")
async def health_check():
    """Detailed health check with dependencies."""
    try:
        # Check DynamoDB connection
        from app.repositories.base import BaseRepository
        # Quick ping test (doesn't count against throughput)
        
        # Check S3 connection (optional)
        # Check Redis connection (wenn implementiert)
        
        return {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "api": "ok",
                "database": "ok",
                "storage": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Service temporarily unavailable"
            }
        )
```

**Vorteil:**
- UptimeRobot erkennt `503 Service Unavailable` als Down
- Detaillierte Logs warum Health Check fehlgeschlagen ist

---

## Monitoring Best Practices

### ✅ Do:
- Monitor kritische Endpoints (`/health`, `/api/v1/auth/login`)
- Public Status Page für Transparenz
- Alert Fatigue vermeiden (nicht jede Warnung = Critical)
- Maintenance Windows nutzen für geplante Deployments
- Response Times tracken (SLA-relevant)

### ❌ Don't:
- Zu viele Monitore (nur kritische Pfade)
- Zu kurze Intervalle (1min reicht für die meisten Cases)
- Alle Alerts als Critical markieren
- Status Page ignorieren (Kunden nutzen das!)

---

## SLA-Reporting

### Uptime berechnen

**UptimeRobot zeigt automatisch:**
- **Last 24h:** 100.00%
- **Last 7 days:** 99.95%
- **Last 30 days:** 99.98%
- **Last 90 days:** 99.96%

**Für Kunden-SLA:**
```
Uptime Guarantee: 99.9% (monatlich)

Downtime Budget pro Monat:
- 99.9%  = 43 Minuten
- 99.95% = 22 Minuten
- 99.99% = 4.3 Minuten

Incident Report:
- Datum: 2026-05-15
- Dauer: 12 Minuten
- Ursache: Database Connection Issue
- Lösung: Connection Pool erhöht
- Prevention: Connection Pool Monitoring aktiviert
```

### Monatlicher Report

**Automatisch generieren lassen:**
1. UptimeRobot → Reports
2. Create Report
3. Schedule: Monthly (1st of month)
4. Recipients: team@overcloud.io
5. Include: Uptime, Response Times, Incidents

---

## Incident Response Workflow

### 1. Alert empfangen (Email/Slack/SMS)

```
🚨 OverCloud API Production is DOWN
URL: https://api.overcloud.io/health
Status Code: 503
Time: 2026-05-15 14:32 UTC
```

### 2. Sofort checken

```bash
# Manual Check
curl -I https://api.overcloud.io/health

# Check Backend Logs (CloudWatch)
aws logs tail /aws/ecs/overcloud-backend --follow

# Check ECS Tasks
aws ecs describe-services --cluster overcloud-prod --services backend
```

### 3. Incident Response Plan befolgen

→ Siehe `docs/operations/INCIDENT_RESPONSE_PLAN.md`

### 4. Status Page updaten

**Während Incident:**
1. UptimeRobot → Status Pages → Post Update
2. Message: "Wir untersuchen aktuell API-Probleme. Updates folgen."
3. Status: Investigating

**Nach Fix:**
1. Status Page → Post Update
2. Message: "Problem behoben. API läuft wieder normal."
3. Status: Resolved

### 5. Post-Mortem schreiben

→ Siehe Template in `INCIDENT_RESPONSE_PLAN.md`

---

## Kosten

### UptimeRobot Free
- **50 Monitore:** Mehr als genug für MVP
- **5 Min Interval:** Akzeptabel (max 5min Downtime bis Alert)
- **Email Alerts:** Unbegrenzt
- **Public Status Page:** 1x kostenlos
- **Retention:** 6 Monate

**Kosten:** €0/Monat

### UptimeRobot Pro ($7/Monat)
- **1 Min Interval:** Schnellere Detection
- **SMS Alerts:** Inklusive
- **Advanced Alerts:** Multi-channel
- **Retention:** Unbegrenzt
- **Custom Status Page Domain:** status.overcloud.io

**Upgrade wenn:** Paying Customers vorhanden

### Better Uptime ($20/Monat)
- **Schönere UI**
- **Bessere Incident Management**
- **Phone Call Alerts**
- **Team On-Call Rotation**

**Upgrade wenn:** Team > 3 Personen

---

## Integration mit anderen Tools

### Sentry Integration

**Warum?**
- Uptime Alert → Check Sentry für Error Details

**Wie?**
- Im Alert Runbook: "Check Sentry Dashboard for errors during downtime"

### CloudWatch Integration

**Custom Metric zu CloudWatch senden:**
```python
# In health check endpoint
import boto3
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='OverCloud',
    MetricData=[
        {
            'MetricName': 'HealthCheckStatus',
            'Value': 1,  # 1 = healthy, 0 = unhealthy
            'Unit': 'Count',
        }
    ]
)
```

**CloudWatch Alarm basierend auf Metric:**
→ Redundanz zu UptimeRobot (falls UptimeRobot down ist)

---

## Testing

### Manueller Test

```bash
# 1. Backend stoppen
docker-compose stop backend

# 2. Warten auf Alert (max 5 Min)

# 3. Alert empfangen? ✅

# 4. Backend starten
docker-compose start backend

# 5. Warten auf "Up" Alert (max 5 Min)

# 6. "Up" Alert empfangen? ✅
```

### Status Page testen

1. Öffne Status Page URL
2. Siehst du Uptime-Statistiken? ✅
3. Sind alle Monitore "Up"? ✅
4. Response Times sichtbar? ✅

---

## Checkliste

**Setup (30 Min):**
- [ ] UptimeRobot Account erstellt
- [ ] Monitor: Production API (`/health`)
- [ ] Monitor: Staging API (optional)
- [ ] Monitor: Frontend (optional)
- [ ] Alert Contact: Email konfiguriert
- [ ] Alert Contact: Slack konfiguriert (optional)
- [ ] Public Status Page erstellt
- [ ] Status Page auf Website verlinkt
- [ ] Maintenance Window Template erstellt
- [ ] Test: Backend stoppen → Alert empfangen

**Dokumentation:**
- [ ] Status Page URL in README.md
- [ ] Incident Response Plan verlinkt
- [ ] Team informiert (wo Alerts ankommen)

---

## Summary

**UptimeRobot Free reicht für:**
- MVP mit < 100 Usern
- Downtime-Detection innerhalb 5 Minuten
- Public Status Page

**Upgrade zu Pro wenn:**
- Paying Customers vorhanden
- SLA vertraglich zugesagt (99.9%)
- 1-Minute Detection nötig

**Zeit:** 30 Minuten Setup  
**Kosten:** €0 (Free Tier)  
**Nutzen:** ⭐⭐⭐⭐⭐ (kritisch für Production)

---

**Nächster Schritt:** [Backup Restore Testing](../scripts/test-backup-restore.sh)
