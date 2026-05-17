# Sentry Error Tracking - Setup Guide

**Datum:** 2026-05-17  
**Status:** Code integriert ✅, Config ausstehend ⏳  
**Zeit:** ~10 Minuten

---

## 🎯 Ziel

Sentry Error Tracking für Production aktivieren, um automatisch über Backend-Fehler benachrichtigt zu werden.

---

## ✅ Was bereits implementiert ist

Der Code ist **vollständig integriert**:
- ✅ Sentry SDK in `app/core/logging.py`
- ✅ Config-Variablen in `app/config.py`
- ✅ Initialisierung in `app/main.py`
- ✅ Error Handler konfiguriert

**Es fehlt nur noch die Sentry-Konfiguration!**

---

## 📋 Quick Start (10 Minuten)

### 1. Sentry Account erstellen
- Gehe zu: [sentry.io](https://sentry.io)
- Sign Up (Free Tier: 5.000 Events/Monat)

### 2. Projekt erstellen
- Platform: **Python / FastAPI**
- Name: `overcloud-backend`

### 3. DSN kopieren
- Format: `https://<key>@o0.ingest.sentry.io/<project-id>`

### 4. .env aktualisieren
```bash
# backend/.env
ENABLE_SENTRY=true
SENTRY_DSN=https://DEINE-DSN-HIER
```

### 5. Backend neu starten
```bash
cd backend
poetry run uvicorn app.main:app --reload
```

### 6. Test-Error triggern
```bash
curl http://localhost:8000/api/v1/test/sentry
```

### 7. Sentry Dashboard checken
- Error sollte erscheinen + Email-Alert

**✅ Fertig!**

---

## 📚 Detaillierte Anleitung

Siehe vollständige Dokumentation oben für:
- Konfiguration
- Security Best Practices
- Production Setup
- Troubleshooting

---

**Benefit:** Sofortige Benachrichtigung bei Production Errors  
**Kosten:** Free Tier ausreichend (5K Events/Monat)  
**Status:** ✅ Code ready, nur Config nötig
