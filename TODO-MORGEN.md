# TODO für Morgen - Frontend Fixes

## 🎯 Gefundene Probleme (30.05.2026 - 23:40)

### ❌ 1. Dashboard & Blueprints - Falsche Error States
**Problem:** "Fehler beim Laden" wird angezeigt wenn keine Daten vorhanden sind
**Fix:**
- API-Fehler → "Fehler beim Laden" + "Erneut versuchen" Button
- Keine Daten (leeres Array) → "Aktuell keine Architekturen/Blueprints vorhanden" + CTA "Erste Architektur erstellen"
- Loading → Spinner/Skeleton

**Dateien:**
- `frontend/src/dashboard.html`
- `frontend/src/blueprints.html`
- `frontend/src/js/pages/dashboard.js`
- `frontend/src/js/pages/blueprints.js`

---

### ❌ 2. Pricing - Kostenrechner falsch
**Problem:** User kann AWS-Kosten selbst eintragen (€500 Input-Feld)
**Fix:**
- **NUR** fester StackVertex-Betrag (Tier: Free, Pro, Enterprise)
- **Deutlicher Hinweis:** "Zusätzlich: 10% der tatsächlichen AWS-Kosten"
- **Info-Boxen:**
  - "AWS-Kosten werden beim Deployment angezeigt (vor Bestätigung)"
  - "Test-Deployments (<4h) = KEINE AWS-Kostenabrechnung"
  - "Produktiv-Deployments (>4h) = monatliche AWS-Rechnung"

**Dateien:**
- `frontend/src/pricing.html`
- `frontend/src/js/pages/pricing.js`

---

### ❌ 3. Navigation - Inkonsistent & falsche Links
**Problem:**
- Menü ändert sich auf verschiedenen Seiten
- "Preise" führt zu "Billing"
- Logo führt nicht zur Startseite

**Fix:**
- **EINE** zentrale Navigation für alle Seiten
- Konsistente Links:
  - `Home` → `/index.html`
  - `Dashboard` → `/dashboard.html`
  - `Blueprints` → `/blueprints.html`
  - `Builder` → `/architecture-builder.html`
  - `Preise` → `/pricing.html`
  - `Login` → `/login.html`
- Logo immer → `/index.html`

**Dateien:**
- Alle HTML-Seiten (konsistente `<nav>` Section)

---

### ❌ 4. Architecture Builder - Kein Exit
**Problem:**
- X-Button oben rechts funktioniert nicht
- Logo führt nicht zur Startseite
- User kommt nicht raus aus dem Builder

**Fix:**
- X-Button → zurück zu `/dashboard.html`
- Logo → `/index.html`
- Breadcrumbs: Home > Dashboard > Architecture Builder

**Dateien:**
- `frontend/src/architecture-builder.html`
- `frontend/src/js/pages/architecture-builder.js`

---

## 📋 Deployment-Plan für Morgen

### 1. Fixes implementieren
```bash
# Alle 4 Probleme fixen (siehe oben)
```

### 2. Frontend Build
```bash
cd frontend
npm run build
```

### 3. Deployment
```bash
./infrastructure/scripts/deploy-dev.sh
# Option 3: Nur Frontend Deployment
```

### 4. Testing
- ✅ Dashboard: Empty State korrekt
- ✅ Blueprints: Empty State korrekt
- ✅ Pricing: Keine AWS-Kosten-Eingabe
- ✅ Navigation: Konsistent auf allen Seiten
- ✅ Builder: Exit funktioniert

### 5. Commit & Push
```bash
git add frontend/
git commit -m "[frontend] Fix UX Issues: Empty States, Pricing, Navigation, Builder Exit"
git push
```

---

## 🚀 Deployment-Scripts (Neu erstellt)

### Deploy
```bash
./infrastructure/scripts/deploy-dev.sh
```
- Option 1: Komplett (Bootstrap + Infra)
- Option 2: Nur Infrastructure
- Option 3: Nur Frontend

### Destroy
```bash
./infrastructure/scripts/destroy-dev.sh
```
- Option 1: GitHub Actions (empfohlen)
- Option 2: Cleanup Script (schnell)
- Option 3: Terraform Destroy

---

## ✅ Was heute funktioniert hat

1. ✅ Deployment erfolgreich - ALLE 9 Seiten deployed
2. ✅ Multi-Page Vite Build funktioniert
3. ✅ Navigation grundsätzlich funktioniert
4. ✅ Landing Page mit Mock-Daten (FAQ, Reviews)
5. ✅ Infrastructure Deploy (Lambda, API Gateway, DynamoDB, S3)
6. ✅ Neue Deployment-Scripts erstellt

---

## 🔧 Nächste Session

1. Tasks abarbeiten (siehe oben)
2. Deployment testen
3. Weitere Features testen (Architecture Builder, Blueprints)
4. Backend-Integration (wenn nötig)

---

**Status:** Bereit für Destroy heute Abend  
**Morgen:** Neu deployen mit allen Fixes
