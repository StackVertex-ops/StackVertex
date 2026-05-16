# Infrastructure Designer - Quick Start Guide

**Ziel:** Den Infrastructure Designer End-to-End testen

---

## 1. Setup

### Backend starten
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend
uvicorn app.main:app --reload
```

**Erwartung:** Backend läuft auf http://localhost:8000

### Frontend starten
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend
npm run dev
```

**Erwartung:** Frontend läuft auf http://localhost:5173

---

## 2. Designer öffnen

**URL:** http://localhost:5173/infrastructure-designer.html

**Erwartetes Ergebnis:**
- Header mit "Infrastructure Designer" Titel
- Linke Sidebar: Component Palette (VPC, EC2, RDS, etc.)
- Rechts: Canvas (grauer Bereich)
- Unten: Tabs-Bereich (leer mit "Keine Komponente ausgewählt")
- Toolbar oben rechts: Auto Layout, Fit to View, Export Image, Delete, Save

---

## 3. Basic Workflow Test

### Test 1: VPC hinzufügen
1. Ziehe "VPC" aus der Palette auf den Canvas
2. **Erwartung:**
   - Node erscheint auf Canvas (lila Rechteck)
   - Tab öffnet sich automatisch unten
   - Tab zeigt VPC Configuration Form

### Test 2: VPC konfigurieren
1. Im Tab: Ändere "Name" zu "My Main VPC"
2. Ändere CIDR zu "172.16.0.0/16"
3. Klick "Save Changes"
4. **Erwartung:**
   - Grüner Toast "Changes saved successfully!" erscheint
   - Tab Header zeigt neuen Namen "My Main VPC"
   - Node Label ändert sich (evtl. erst nach Refresh)

### Test 3: EC2 hinzufügen
1. Ziehe "EC2" aus der Palette auf den Canvas
2. Node erscheint (orange Rechteck)
3. Tab öffnet sich
4. Ändere Instance Type zu "t3.medium"
5. Save Changes
6. **Erwartung:** Änderungen gespeichert

### Test 4: Nodes verschieben
1. Klicke und ziehe VPC Node an neue Position
2. **Erwartung:** Node bewegt sich
3. Klicke und ziehe EC2 Node
4. **Erwartung:** Node bewegt sich

### Test 5: Multiple Tabs
1. Klicke auf VPC Node → VPC Tab wird aktiviert
2. Klicke auf EC2 Node → EC2 Tab wird aktiviert
3. **Erwartung:** Beide Tabs oben sichtbar, aktiver Tab hat andereFarbe

### Test 6: Auto Layout
1. Füge noch 2-3 weitere Komponenten hinzu (RDS, S3)
2. Klicke "Auto Layout" Button oben
3. **Erwartung:** Alle Nodes werden automatisch angeordnet

### Test 7: Delete Component
1. Klicke auf einen Node (z.B. S3)
2. Drücke "Delete" Taste oder klicke "Delete Selected" Button
3. **Erwartung:**
   - Node verschwindet vom Canvas
   - Tab wird geschlossen

### Test 8: Save Architecture
1. Klicke "Save Architecture" Button
2. Gib Name ein: "Test Architecture"
3. **Erwartung:**
   - Alert/Dialog erscheint (oder API Call)
   - "Architektur gespeichert!" Message

---

## 4. Demo Architecture Test

### Test: Demo laden
1. Öffne URL: http://localhost:5173/infrastructure-designer.html?id=demo
2. **Erwartung:**
   - Demo Architecture lädt automatisch
   - Mehrere Komponenten auf Canvas:
     - 1x VPC
     - 2x Subnets (public + private)
     - 1x Internet Gateway
     - 1x NAT Gateway
     - 1x Load Balancer
     - 2x EC2 Instances
     - 1x RDS Database
     - 1x S3 Bucket
   - Connections (Edges) zwischen Komponenten sichtbar

---

## 5. Browser Console Tests

### Test: Debug Helper
1. Öffne Browser DevTools (F12)
2. Gehe zu Console Tab
3. Tippe: `designer`
4. **Erwartung:** Objekt mit Methods wird angezeigt

### Test: VPC via Console hinzufügen
```javascript
designer.addVPC('Console VPC', '192.168.0.0/16')
```
**Erwartung:** VPC erscheint auf Canvas

### Test: Beispiel-Architektur erstellen
```javascript
designer.createExampleArchitecture()
```
**Erwartung:** VPC + EC2 + RDS werden hinzugefügt und verbunden

### Test: JSON exportieren
```javascript
designer.exportJSON()
```
**Erwartung:** JSON Objekt wird in Console ausgegeben

### Test: JSON kopieren
```javascript
await designer.copyJSON()
```
**Erwartung:** "✓ JSON copied to clipboard" Message

### Test: Canvas leeren
```javascript
designer.clear()
```
**Erwartung:** Confirm Dialog → Canvas wird geleert

---

## 6. Edge Cases & Error Handling

### Test: Empty State
1. Lösche alle Komponenten
2. **Erwartung:** Tabs-Bereich zeigt Empty State:
   - Icon
   - "Keine Komponente ausgewählt"
   - "Klicke auf eine Komponente..."

### Test: Tab schließen
1. Füge VPC hinzu → Tab öffnet sich
2. Klicke X auf Tab Header
3. **Erwartung:** Tab verschwindet, Node bleibt auf Canvas

### Test: Keyboard Shortcuts
1. Füge EC2 hinzu
2. Wähle EC2 Node aus
3. Drücke "Delete" Taste
4. **Erwartung:** Node wird gelöscht
5. Füge neue Komponente hinzu
6. Drücke Cmd+S (Mac) oder Ctrl+S (Windows)
7. **Erwartung:** Save Dialog/Funktion wird ausgelöst

### Test: Zoom & Pan
1. Scrolle mit Mausrad
2. **Erwartung:** Canvas zoomt ein/aus
3. Klicke auf leeren Bereich und ziehe
4. **Erwartung:** Canvas pannt

### Test: Box Selection
1. Klicke auf leeren Bereich und ziehe Rechteck über mehrere Nodes
2. **Erwartung:** Alle Nodes im Rechteck werden ausgewählt (rot umrandet)

---

## 7. Kritische Bugs prüfen

### Bug Check 1: Cytoscape nicht geladen
**Symptom:** Canvas bleibt grau, keine Nodes erscheinen  
**Check:** Browser Console → Fehler wie "cytoscape is not defined"?  
**Fix:** `npm install` nochmal ausführen

### Bug Check 2: Tab öffnet sich nicht
**Symptom:** Klick auf Node → kein Tab erscheint  
**Check:** Console Errors?  
**Debug:** `console.log` in `handleNodeClick` einfügen

### Bug Check 3: Drag & Drop funktioniert nicht
**Symptom:** Node lässt sich nicht aus Palette ziehen  
**Check:** Console Errors?  
**Debug:** `e.dataTransfer.getData('componentType')` loggen

### Bug Check 4: Save funktioniert nicht
**Symptom:** Save Button → nichts passiert  
**Check:** Console Errors? Network Tab → API Call?  
**Debug:** `localStorage.getItem('architecture-draft')` prüfen

---

## 8. Performance Tests

### Test: Viele Komponenten
1. Via Console: 20 VPCs hinzufügen
```javascript
for (let i = 0; i < 20; i++) {
    designer.addVPC(`VPC ${i}`, `10.${i}.0.0/16`)
}
```
2. **Erwartung:**
   - Alle 20 Nodes erscheinen
   - Canvas bleibt responsive
   - Auto Layout funktioniert noch

### Test: Viele Tabs
1. Öffne 10 Tabs (jeweils anderen Node klicken)
2. **Erwartung:**
   - Tab Headers scrollen horizontal
   - Tab-Wechsel funktioniert noch
   - Keine Performance-Probleme

---

## 9. Fehlerbehandlung

### Was tun bei Fehlern?

#### Console Errors anschauen
1. Browser DevTools öffnen (F12)
2. Console Tab öffnen
3. Errors lesen und notieren

#### Häufige Fehler:

**"Cannot read property 'cy' of undefined"**
→ Canvas nicht richtig initialisiert
→ Check: `this.canvas` in `infrastructure-designer.js`

**"Module not found: cytoscape"**
→ npm install nicht ausgeführt
→ Fix: `npm install`

**"Failed to fetch architecture"**
→ Backend nicht gestartet oder API Endpoint fehlt
→ Check: Backend läuft? http://localhost:8000/health

**"Cannot find element #canvas-container"**
→ HTML nicht richtig geladen oder ID fehlt
→ Check: `infrastructure-designer.html` korrekt?

---

## 10. Success Criteria

### ✅ Designer funktioniert wenn:

- [ ] Komponenten aus Palette ziehbar
- [ ] Nodes erscheinen auf Canvas mit korrekten Icons/Farben
- [ ] Klick auf Node öffnet Tab
- [ ] Configuration Forms zeigen korrekte Felder
- [ ] Save Changes funktioniert
- [ ] Änderungen werden in Node übernommen
- [ ] Auto Layout ordnet Nodes an
- [ ] Fit to View funktioniert
- [ ] Delete löscht Nodes
- [ ] Tabs können geschlossen werden
- [ ] Save Architecture speichert JSON
- [ ] Demo Architecture (?id=demo) lädt korrekt
- [ ] Console Debug Helper funktioniert
- [ ] Keine Console Errors

---

## 11. Nächste Schritte nach erfolgreichem Test

### Integration Tests
- Backend API Endpoints testen
- Terraform Generator V2 anbinden
- Cost Estimation API testen

### Feature Enhancements
- IP Calculator inline anzeigen
- Edge Creation Mode (manuell Connections erstellen)
- Undo/Redo implementieren
- Validation für CIDR Blocks

### Polish
- Animations & Transitions verfeinern
- Loading States hinzufügen
- Error Messages verbessern
- Accessibility (ARIA Labels)

---

## Hilfreiche Dateien

- **Status Dokumentation:** `INFRASTRUCTURE_DESIGNER_STATUS.md`
- **Test Script:** `test_infrastructure_designer.sh`
- **Debug Helper:** `src/js/utils/designer-debug.js`
- **Demo Architecture:** `src/js/demo/sample-architecture.js`
- **Simple Example:** `src/js/examples/simple-vpc-example.js`

---

## Kontakt bei Problemen

Dokumentiere alle gefundenen Bugs in:
- Console Errors screenshot
- Beschreibung der Schritte zum Reproduzieren
- Erwartetes vs. tatsächliches Verhalten

Bugs in der Status-Dokumentation unter "Bekannte Issues" nachtragen.

---

**Viel Erfolg beim Testen! 🚀**
