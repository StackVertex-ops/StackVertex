# FAQ System - Manual Testing Guide

## Setup

### 1. Backend starten

```bash
cd backend
source venv/bin/activate  # oder venv\Scripts\activate auf Windows
uvicorn app.main:app --reload
```

Backend läuft auf: http://localhost:8000

### 2. Frontend starten

```bash
cd frontend
npm run dev
```

Frontend läuft auf: http://localhost:5173

### 3. Kategorien seeden

```bash
cd backend
python scripts/seed_faq_categories.py
```

Erwartete Ausgabe:
```
🌱 Seeding default FAQ categories...
✅ Created category: Allgemein (general)
✅ Created category: Preise (pricing)
✅ Created category: Technik (technical)
✅ Created category: Sicherheit (security)
✅ Created category: Support (support)
✨ Seeding complete!
```

### 4. (Optional) Beispiel-FAQs erstellen

```bash
python scripts/seed_example_faqs.py
```

## Test-Szenarien

### Scenario 1: Public FAQ View (Startseite)

**Ziel**: FAQs auf Startseite anzeigen

1. Öffne http://localhost:5173/
2. Scrolle zur "Häufig gestellte Fragen" Sektion
3. Prüfe:
   - [ ] FAQs werden geladen
   - [ ] Kategorien-Filter sind sichtbar (📌 Allgemein, 💰 Preise, etc.)
   - [ ] Such-Feld ist vorhanden
   - [ ] FAQs sind gruppiert nach Kategorie

4. Klicke auf ein FAQ
   - [ ] Accordion öffnet sich smooth
   - [ ] Antwort ist lesbar
   - [ ] Markdown ist korrekt gerendert (falls vorhanden)

5. Klicke nochmal auf dasselbe FAQ
   - [ ] Accordion schließt sich

6. Teste Suche
   - [ ] Eingabe "preis" → Nur Preis-FAQs angezeigt
   - [ ] Leere Suche → Alle FAQs wieder sichtbar

7. Teste Kategorie-Filter
   - [ ] Klick auf "💰 Preise" → Nur Preis-FAQs
   - [ ] Klick auf "Alle" → Alle FAQs wieder sichtbar

**Erwartetes Resultat**: ✅ Alle FAQs korrekt dargestellt

---

### Scenario 2: Admin - Login & Analytics

**Ziel**: Zugriff auf Admin-Dashboard

1. Erstelle SuperAdmin (falls noch nicht vorhanden)
   ```bash
   # Im Backend
   python scripts/create_superadmin.py
   ```

2. Login unter http://localhost:5173/login.html
   - Email: admin@overcloud.io
   - Password: (dein Passwort)

3. Öffne http://localhost:5173/admin-faq.html
   - [ ] Redirect zu Login FALLS nicht eingeloggt
   - [ ] Dashboard lädt FALLS eingeloggt

4. Prüfe Stats-Cards:
   - [ ] "Gesamt FAQs" zeigt korrekte Anzahl
   - [ ] "Veröffentlicht" zeigt published count
   - [ ] "Entwürfe" zeigt draft count
   - [ ] "Gesamt Views" zeigt 0 (noch keine Views)

5. Prüfe FAQ-Liste:
   - [ ] FAQs werden angezeigt
   - [ ] Kategorie-Filter funktioniert
   - [ ] "Bearbeiten" & "Löschen" Buttons sichtbar

**Erwartetes Resultat**: ✅ Dashboard zeigt korrekte Daten

---

### Scenario 3: Admin - FAQ erstellen

**Ziel**: Neues FAQ erstellen

1. Im Admin-Dashboard, klicke "+ Neues FAQ"
2. Modal öffnet sich

3. Fülle Formular aus:
   - **Kategorie**: "general"
   - **Frage**: "Was ist ein Test-FAQ?"
   - **Antwort**: 
     ```markdown
     Dies ist ein **Test-FAQ** mit Markdown:
     
     - Punkt 1
     - Punkt 2
     
     Code: `test`
     ```
   - **Status**: "published"

4. Klicke "Speichern"
   - [ ] Success-Nachricht erscheint
   - [ ] Modal schließt sich
   - [ ] FAQ erscheint in Liste

5. Refresh Startseite (http://localhost:5173/)
   - [ ] Neues FAQ erscheint unter "Allgemein"
   - [ ] Markdown ist korrekt gerendert

**Erwartetes Resultat**: ✅ FAQ erfolgreich erstellt und öffentlich sichtbar

---

### Scenario 4: Admin - FAQ bearbeiten

**Ziel**: Bestehendes FAQ ändern

1. Im Admin-Dashboard, klicke "Bearbeiten" bei einem FAQ
2. Modal öffnet sich mit vorausgefüllten Daten

3. Ändere:
   - **Frage**: "EDITIERT: {alte Frage}"
   - **Status**: "draft" (falls vorher published)

4. Klicke "Speichern"
   - [ ] Success-Nachricht
   - [ ] Änderungen in Liste sichtbar

5. Refresh Startseite
   - [ ] FAQ ist NICHT mehr sichtbar (weil draft)

6. Setze Status zurück auf "published"
   - [ ] FAQ wieder öffentlich sichtbar

**Erwartetes Resultat**: ✅ Änderungen werden korrekt gespeichert

---

### Scenario 5: Admin - FAQ löschen

**Ziel**: FAQ entfernen

1. Im Admin-Dashboard, klicke "Löschen" bei einem FAQ
2. Confirm-Dialog erscheint
3. Bestätige Löschung
   - [ ] Success-Nachricht
   - [ ] FAQ verschwindet aus Liste
   - [ ] Stats aktualisieren sich

4. Refresh Startseite
   - [ ] FAQ ist nicht mehr sichtbar

**Erwartetes Resultat**: ✅ FAQ erfolgreich gelöscht

---

### Scenario 6: Admin - Drag & Drop Sortierung

**Ziel**: FAQs neu sortieren

1. Im Admin-Dashboard, filtere nach einer Kategorie (z.B. "Allgemein")
2. Ziehe ein FAQ nach oben/unten
3. Lasse los
   - [ ] FAQ bleibt an neuer Position
   - [ ] (Optional) Success-Nachricht

4. Refresh Seite
   - [ ] Neue Sortierung bleibt erhalten

5. Öffne Startseite
   - [ ] FAQs in neuer Reihenfolge angezeigt

**Erwartetes Resultat**: ✅ Sortierung funktioniert und bleibt persistent

---

### Scenario 7: Admin - Kategorie erstellen

**Ziel**: Neue FAQ-Kategorie anlegen

1. Im Admin-Dashboard, rechte Spalte "Kategorien"
2. Klicke "+ Neue Kategorie"
3. Modal öffnet sich

4. Fülle aus:
   - **Name**: "Test Kategorie"
   - **Slug**: Auto-generiert zu "test-kategorie"
   - **Icon**: "🧪"

5. Klicke "Speichern"
   - [ ] Success-Nachricht
   - [ ] Kategorie erscheint in Liste
   - [ ] Kategorie erscheint in FAQ-Formular Dropdown
   - [ ] Kategorie erscheint in Filter-Buttons

**Erwartetes Resultat**: ✅ Kategorie erstellt und überall verfügbar

---

### Scenario 8: View Count Tracking

**Ziel**: Prüfen ob Views getrackt werden

1. Öffne Startseite (http://localhost:5173/)
2. Öffne ein FAQ (klicke darauf)
3. Öffne Admin-Dashboard
4. Prüfe FAQ in Liste:
   - [ ] "X Views" sollte sich erhöht haben (kann 1-2 Sekunden dauern)

5. Refresh Admin → Stats
   - [ ] "Gesamt Views" hat sich erhöht

6. Öffne dasselbe FAQ nochmal auf Startseite
   - [ ] View Count erhöht sich NOCHMAL (jedes Öffnen zählt)

**Erwartetes Resultat**: ✅ Views werden korrekt getrackt

---

### Scenario 9: Mobile Responsive

**Ziel**: Prüfen ob FAQs auf Mobile funktionieren

1. Öffne Startseite
2. Öffne DevTools (F12)
3. Schalte auf Mobile-Ansicht (z.B. iPhone 12)

4. Prüfe:
   - [ ] FAQs sind lesbar
   - [ ] Accordion funktioniert
   - [ ] Suche funktioniert
   - [ ] Kategorien-Filter sind scrollbar (falls zu viele)

5. Öffne Admin-Dashboard auf Mobile
   - [ ] Layout passt sich an
   - [ ] Buttons sind klickbar
   - [ ] Formulare sind nutzbar

**Erwartetes Resultat**: ✅ Mobile-optimiert

---

### Scenario 10: API Testing (cURL)

**Ziel**: Direkte API-Tests

1. Public Endpoints (keine Auth)

```bash
# Alle FAQs
curl http://localhost:8000/api/v1/faq

# Suche
curl "http://localhost:8000/api/v1/faq/search?q=preis"

# Kategorien
curl http://localhost:8000/api/v1/faq/categories

# Einzelnes FAQ (tracked view)
curl http://localhost:8000/api/v1/faq/{faq_id}
```

2. Admin Endpoints (mit Token)

```bash
# Login holen
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@overcloud.io","password":"dein-passwort"}' \
  | jq -r '.access_token')

# Alle FAQs (inkl. Drafts)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/faq

# Analytics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/faq/analytics

# Neues FAQ erstellen
curl -X POST http://localhost:8000/api/v1/admin/faq \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "general",
    "question": "API Test FAQ?",
    "answer": "Via cURL erstellt!",
    "status": "published",
    "sort_order": 0
  }'
```

**Erwartetes Resultat**: ✅ Alle Endpunkte antworten korrekt

---

## Fehlerbehandlung

### Test: Invalid Input

1. Versuche FAQ zu erstellen mit:
   - Leerer Frage → ❌ Fehler
   - Zu kurzer Antwort (<10 Zeichen) → ❌ Fehler
   - Ungültigem Status → ❌ Fehler

2. Versuche Kategorie mit:
   - Ungültigem Slug (Leerzeichen) → ❌ Fehler
   - Leerem Namen → ❌ Fehler

**Erwartetes Resultat**: ✅ Validation funktioniert

### Test: Unauthorized Access

1. Logout
2. Versuche http://localhost:5173/admin-faq.html zu öffnen
   - [ ] Redirect zu Login

3. Versuche Admin API direkt (ohne Token)
   ```bash
   curl http://localhost:8000/api/v1/admin/faq
   ```
   - [ ] 401 Unauthorized

**Erwartetes Resultat**: ✅ Auth-Schutz funktioniert

---

## Cleanup

Nach Tests (optional):

```bash
# Alle Test-FAQs löschen via Admin UI
# ODER DynamoDB direkt (wenn Testdaten)
# Vorsicht: Löscht ALLE FAQs!
```

---

## Success Criteria

✅ **Alle Scenarios erfolgreich**
✅ **Keine Console-Errors**
✅ **Performance OK** (<2s Ladezeit)
✅ **Mobile Responsive**
✅ **Auth funktioniert**

---

**Test durchgeführt von**: _____________

**Datum**: _____________

**Ergebnis**: ✅ Pass / ❌ Fail

**Notizen**:
```
(Hier Probleme notieren)
```
