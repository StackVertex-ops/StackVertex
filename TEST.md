# OverCloud - Test Guide

> Teste Backend und Frontend

---

## 🐍 Backend Testen

### Terminal 1: Start Backend Server

```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend

# Start FastAPI dev server (empfohlene Methode)
poetry run python -m app.main

# ODER: Venv aktivieren und dann Python Modul ausführen
source .venv/bin/activate
python -m app.main

# ODER: Mit Uvicorn direkt (mit auto-reload)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Erwartetes Output:**
```
INFO:     Will watch for changes in these directories: ['/Users/andyschwarz/Documents/Privat/OverCloud/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Teste im Browser:**
- http://localhost:8000 → Sollte JSON zeigen: `{"message": "OverCloud API", ...}`
- http://localhost:8000/health → Sollte zeigen: `{"status": "healthy", ...}`
- http://localhost:8000/api/docs → Interactive API Documentation (Swagger UI)

---

## 🌐 Frontend Testen

### Terminal 2: Start Frontend Dev Server

```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend

# Start Vite dev server
npm run dev
```

**Erwartetes Output:**
```
  VITE v8.0.1  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Browser öffnet automatisch:**
- http://localhost:5173

**Du solltest sehen:**
- ✅ "Welcome to OverCloud" Überschrift
- ✅ 3 Feature Cards (Requirements-Driven, JSON-First, Transparent)
- ✅ Status Card mit **grünem Punkt** und "✓ API Connected (v0.1.0)"
  - Falls Backend **nicht** läuft: Roter Text "✗ API Offline"

---

## ✅ Success Kriterien

### Backend ✅
- [ ] Server startet ohne Fehler
- [ ] http://localhost:8000 erreichbar
- [ ] `/health` endpoint antwortet mit `{"status": "healthy"}`
- [ ] `/api/docs` zeigt Swagger UI

### Frontend ✅
- [ ] Vite startet ohne Fehler
- [ ] http://localhost:5173 erreichbar
- [ ] Tailwind CSS Styles funktionieren (schöne UI)
- [ ] API Status zeigt "✓ API Connected" (falls Backend läuft)
- [ ] Browser Console zeigt: "OverCloud Frontend initialized"

---

## 🔧 Troubleshooting

### Backend: "ModuleNotFoundError: No module named 'app'"

```bash
# Stelle sicher dass du im backend/ Ordner bist
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend

# WICHTIG: Nutze Python Modul-Syntax (-m) statt direkten Pfad
poetry run python -m app.main

# ODER: Venv aktivieren
source .venv/bin/activate
python -m app.main

# FALSCH: python app/main.py  ❌ (findet 'app' Modul nicht)
```

### Backend: "connection refused" zur Datenbank

Das ist OK! Wir haben noch keine PostgreSQL Datenbank.
Der Server läuft trotzdem. Wir fügen DB später hinzu.

### Frontend: "Failed to fetch" API Error

Das ist OK! Backend muss laufen für API Connection.
Starte Backend zuerst, dann Frontend.

### Frontend: Styles sehen falsch aus

```bash
# Check dass Tailwind richtig installiert ist
cd frontend
npm install

# Restart dev server
npm run dev
```

---

## 📸 Screenshots (erwartetes Ergebnis)

### Backend (http://localhost:8000)
```json
{
  "message": "OverCloud API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/api/docs"
}
```

### Frontend (http://localhost:5173)
![OverCloud Landing Page]
- Weißer/Dunkler Hintergrund (je nach OS Theme)
- "OverCloud" Header
- "Welcome to OverCloud" Hero Section
- Grüner Status Indicator wenn Backend läuft

---

## 🚀 Nächste Schritte

Wenn beide Tests erfolgreich:

1. ✅ Backend läuft
2. ✅ Frontend läuft
3. ✅ API Verbindung funktioniert

Dann sag Claude: **"Tests erfolgreich! Was kommt als nächstes?"**

Wir bauen dann:
- JSON Schema Validation
- Architecture CRUD API
- Architecture Builder UI

---

**Viel Erfolg beim Testen!** 🎉
