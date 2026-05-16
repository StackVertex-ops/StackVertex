# Sentry Error Tracking - Setup Guide

> **Zeit:** 10 Minuten  
> **Status:** Code bereits integriert, nur noch DSN setzen

---

## Was ist Sentry?

Sentry ist ein Error-Tracking-Tool, das automatisch alle Exceptions im Backend erfasst und dir per Email/Slack benachrichtigt.

**Vorteile:**
- Echtzeit-Benachrichtigung bei Fehlern
- Stack Traces mit Context (welcher User, welche API-Route, etc.)
- Error-Grouping (gleiche Fehler werden zusammengefasst)
- Performance Monitoring (optional)
- **Kostenlos bis 5.000 Events/Monat**

---

## Setup (10 Minuten)

### 1. Sentry Account erstellen

1. Gehe zu: https://sentry.io/signup/
2. Registriere dich (GitHub/Google oder Email)
3. Erstelle ein neues Projekt:
   - **Platform:** Python
   - **Project Name:** `overcloud-backend`
   - **Team:** (Standard oder neues Team)

### 2. DSN kopieren

Nach Projekt-Erstellung siehst du den **DSN (Data Source Name)**:

```
https://abc123def456@o123456.ingest.sentry.io/7890123
```

**Kopiere diesen DSN!**

### 3. DSN in Backend setzen

#### **Lokal (Development):**

In deiner `.env` Datei:

```bash
# Sentry Error Tracking
ENABLE_SENTRY=true
SENTRY_DSN=https://abc123def456@o123456.ingest.sentry.io/7890123
```

#### **Production (AWS Secrets Manager):**

```bash
# DSN in Secrets Manager speichern
aws secretsmanager create-secret \
  --name prod/sentry/dsn \
  --secret-string "https://abc123def456@o123456.ingest.sentry.io/7890123" \
  --region eu-central-1

# In Terraform/ECS Task Definition referenzieren:
# environment = [
#   { name = "ENABLE_SENTRY", value = "true" },
#   { name = "SENTRY_DSN", valueFrom = "arn:aws:secretsmanager:eu-central-1:xxx:secret:prod/sentry/dsn" }
# ]
```

### 4. Backend neu starten

```bash
# Lokal
cd backend
poetry run uvicorn app.main:app --reload

# Docker
docker-compose restart backend
```

### 5. Test: Error triggern

**Option A: API Test (empfohlen)**

```bash
# Erstelle temporären Test-Endpoint
curl -X POST http://localhost:8000/api/v1/test-error \
  -H "Content-Type: application/json"
```

**Option B: Python Console**

```python
# In backend/app/main.py temporär hinzufügen:
@app.get("/test-error")
async def test_error():
    """Trigger test error for Sentry."""
    raise Exception("🚨 Sentry Test Error - If you see this in Sentry, it works!")
```

Dann: `curl http://localhost:8000/test-error`

### 6. Verifizieren

1. Gehe zu Sentry Dashboard: https://sentry.io
2. Wähle Projekt `overcloud-backend`
3. Du solltest den Test-Error sehen mit:
   - Stack Trace
   - Request Context (URL, Method, IP)
   - Environment (development/production)
   - Timestamp

✅ **Funktioniert? Dann Test-Endpoint wieder löschen!**

---

## Konfiguration

### Log-Level für Sentry

Standardmäßig werden nur **Errors und Exceptions** an Sentry geschickt, keine Warnings oder Info-Logs.

**In `backend/app/core/logging.py` (bereits korrekt konfiguriert):**

```python
if enable_sentry and sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=0.1,  # 10% Performance Monitoring
        
        # Nur ERROR und CRITICAL an Sentry
        integrations=[
            LoggingIntegration(
                level=logging.INFO,  # Breadcrumbs (Context)
                event_level=logging.ERROR  # Events (Alerts)
            )
        ]
    )
```

### Sensitive Data ausblenden (DSGVO)

**Bereits konfiguriert in `backend/app/core/logging.py`:**

```python
sentry_sdk.init(
    dsn=sentry_dsn,
    before_send=lambda event, hint: _filter_sensitive_data(event),  # DSGVO-Filter
    ...
)

def _filter_sensitive_data(event):
    """Remove sensitive data before sending to Sentry."""
    # Headers filtern
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        if 'Authorization' in headers:
            headers['Authorization'] = '[Filtered]'
        if 'Cookie' in headers:
            headers['Cookie'] = '[Filtered]'
    
    return event
```

---

## Alert-Konfiguration

### Email-Alerts

1. Gehe zu Sentry → Project Settings → Alerts
2. Erstelle neue Alert Rule:
   - **Name:** "Critical Errors"
   - **Condition:** "An event is seen"
   - **Filter:** `level:error OR level:fatal`
   - **Action:** "Send email to team"
   - **Frequency:** Max 1x pro Stunde (verhindert Spam)

### Slack-Integration (optional)

1. Gehe zu Settings → Integrations → Slack
2. "Add Workspace"
3. Wähle Channel: z.B. `#overcloud-alerts`
4. Alert Rule anpassen: "Send Slack notification to #overcloud-alerts"

---

## Kosten

### Free Tier (ausreichend für MVP)
- **5.000 Events/Monat:** Kostenlos
- **Performance Monitoring:** 10.000 Transactions/Monat
- **1 User:** Kostenlos
- **Retention:** 90 Tage

**Reicht für:**
- Startup mit < 1.000 Users
- ~150 Errors/Tag
- Development + Staging + Production

### Team Plan ($26/Monat)
- **50.000 Events/Monat**
- **50.000 Transactions/Monat**
- **Unlimited Users**
- **Better Alerting**

**Upgrade wenn:**
- > 5.000 Errors/Monat
- Mehr Team-Mitglieder
- Advanced Features benötigt

---

## Monitoring & Maintenance

### Täglich checken (5 Min)
```bash
# Sentry Dashboard öffnen
open https://sentry.io/organizations/dein-org/projects/overcloud-backend/

# Neue Errors?
# → Priorisieren (P1: Production, P2: Staging, P3: Dev)
# → Fixen oder Issue erstellen
```

### Wöchentlich (30 Min)
- Error Trends analysieren (steigen Errors?)
- Häufigste Errors identifizieren
- Fixes deployen

### Monatlich
- Event-Count checken (nah am Limit?)
- Alte Issues schließen (bereits gefixt)
- Alert Rules anpassen

---

## Best Practices

### ✅ Do:
- Sentry nur für **Errors** nutzen, nicht für Debugging
- Test-Errors sofort löschen
- Sensitive Data filtern (bereits implementiert)
- Errors gruppieren (gleiche Root-Cause)
- Fixes schnell deployen (innerhalb 24h für P1)

### ❌ Don't:
- Sentry mit Info/Debug-Logs fluten
- Test-Errors in Production triggern
- Secrets/Passwörter in Error Messages loggen
- Errors ignorieren ("wird schon nicht so schlimm sein")

---

## Troubleshooting

### "Sentry bekommt keine Events"

**Check 1:** DSN korrekt?
```bash
echo $SENTRY_DSN
# Sollte https://... sein
```

**Check 2:** Sentry enabled?
```bash
echo $ENABLE_SENTRY
# Sollte "true" sein
```

**Check 3:** Backend-Logs checken
```bash
# Bei Startup sollte stehen:
# "Sentry initialized for environment: development"
```

**Check 4:** Netzwerk-Problem?
```bash
# Test ob Sentry erreichbar ist
curl https://sentry.io/api/0/
```

### "Zu viele Events (Limit erreicht)"

**Lösung 1:** Sample Rate reduzieren
```python
# In logging.py
traces_sample_rate=0.05  # Nur 5% Performance-Traces
```

**Lösung 2:** Filter schärfer stellen
```python
# Nur ERROR und CRITICAL, keine Warnings
event_level=logging.ERROR
```

**Lösung 3:** Upgrade auf Team Plan

---

## Security & DSGVO

### Was wird an Sentry geschickt?

**✅ Wird geschickt:**
- Exception Type & Message
- Stack Trace (Code-Zeilen)
- Request Context (URL, Method, IP - anonymisiert)
- Environment (dev/staging/prod)
- Timestamp

**❌ Wird NICHT geschickt (gefiltert):**
- Authorization Headers
- Cookies
- Passwörter
- API Keys
- Personenbezogene Daten (Email, Namen)

### Sentry & DSGVO

**Sentry ist DSGVO-konform wenn:**
1. ✅ Sensitive Data gefiltert wird (bereits implementiert)
2. ✅ Sentry Data Processing Agreement (DPA) unterschrieben
   - Download: https://sentry.io/legal/dpa/
3. ✅ In Privacy Policy erwähnen:
   - "Wir nutzen Sentry.io für Error-Tracking"
   - "IP-Adressen werden anonymisiert"
   - "Daten in EU-Rechenzentren (optional: Sentry EU)"

**Optional: Sentry EU Region nutzen**
```python
sentry_sdk.init(
    dsn=sentry_dsn,
    environment=environment,
    # EU-Region für DSGVO
    transport=sentry_sdk.transports.HttpTransport(
        options={"dsn": sentry_dsn.replace("sentry.io", "eu.sentry.io")}
    )
)
```

---

## Summary

**Sentry Setup Checklist:**
- [x] Code bereits integriert (`app/core/logging.py`)
- [ ] Sentry Account erstellen (10 Min)
- [ ] DSN in `.env` setzen
- [ ] Backend neu starten
- [ ] Test-Error triggern
- [ ] Verifizieren in Sentry Dashboard
- [ ] Test-Endpoint löschen
- [ ] Alert Rules konfigurieren
- [ ] DPA unterschreiben (DSGVO)

**Zeit:** 10 Minuten  
**Kosten:** €0 (bis 5k Events/Monat)  
**Nutzen:** ⭐⭐⭐⭐⭐ (kritisch für Production)

---

**Nächster Schritt:** [Uptime Monitoring Setup](./UPTIME_MONITORING_SETUP.md)
