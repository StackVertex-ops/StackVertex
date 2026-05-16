# Infrastructure Designer - Testing Guide

**Projekt:** OverCloud Infrastructure Designer  
**Version:** 1.0.0 MVP

---

## Übersicht

Dieser Guide beschreibt, wie man Tests für den Infrastructure Designer ausführt.

**Test-Typen:**
1. **Backend Tests** - API Endpoints (pytest)
2. **Frontend Tests** - UI Komponenten (Vitest + manuelle Tests)
3. **E2E Tests** - User Flows (Playwright)
4. **Integration Tests** - Backend ↔ Frontend

---

## Voraussetzungen

### Backend
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend

# Virtual Environment aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install -e ".[test]"

# Oder mit Poetry
poetry install --with test
```

### Frontend
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend

# Dependencies installieren
npm install

# Playwright installieren (für E2E Tests)
npx playwright install
```

---

## 1. Backend Tests

### Test-Script ausführen
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend

# Einfacher Test
./test_designer_api.sh

# Oder manuell mit pytest
pytest tests/test_terraform_api.py -v
pytest tests/test_cidr_api.py -v
```

### Test-Coverage
```bash
# Mit Coverage Report
pytest --cov=app --cov-report=html --cov-report=term

# Coverage anzeigen
open htmlcov/index.html
```

### Einzelne Tests ausführen
```bash
# Nur Terraform-Generierung testen
pytest tests/test_terraform_api.py::test_generate_terraform -v

# Nur CIDR-Validierung testen
pytest tests/test_cidr_api.py::test_validate_cidr -v
```

### API Tests mit curl
```bash
# Backend starten
uvicorn app.main:app --reload

# In neuem Terminal:
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend
./test_designer_api.sh
```

**Getestete Endpoints:**
- `POST /api/v1/terraform/generate-from-json`
- `POST /api/v1/terraform/validate`
- `POST /api/v1/cidr/validate`
- `POST /api/v1/cidr/plan`
- `POST /api/v1/terraform/estimate-cost`

---

## 2. Frontend Tests

### Test-Script ausführen
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend

# Dependency- & File-Checks
./test_infrastructure_designer.sh
```

**Das Script prüft:**
- ✅ Backend läuft (http://localhost:8000)
- ✅ Frontend läuft (http://localhost:5173)
- ✅ Cytoscape.js installiert
- ✅ Alle Dateien vorhanden
- ✅ CSS Imports korrekt

### Manuelle UI Tests
```bash
# Frontend starten
npm run dev

# Browser öffnen
open http://localhost:5173/infrastructure-designer.html
```

**Test-Checklist:**
1. ✅ Drag VPC from palette onto canvas
2. ✅ Click VPC node → Tab should open
3. ✅ Change CIDR → IP info should update
4. ✅ Delete component → Should remove from canvas
5. ✅ Load demo architecture (add ?id=demo to URL)
6. ✅ Export JSON (Cmd/Ctrl+S or Save button)
7. ✅ Export PNG (Screenshot button)
8. ✅ Auto-Save in localStorage

### Unit Tests (Vitest)
```bash
# Wenn Vitest konfiguriert ist
npm run test

# Mit Coverage
npm run test:coverage
```

---

## 3. End-to-End Tests (Playwright)

### E2E Tests ausführen
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend

# Playwright Tests
npx playwright test

# Headed Mode (mit Browser-Fenster)
npx playwright test --headed

# Nur Chrome
npx playwright test --project=chromium

# Debug Mode
npx playwright test --debug
```

### E2E Test-Szenarien

#### Szenario 1: Simple Web App erstellen
```javascript
test('Create simple web app architecture', async ({ page }) => {
  await page.goto('http://localhost:5173/infrastructure-designer.html');
  
  // Drag VPC
  await page.dragAndDrop('[data-component="vpc"]', '#cy');
  
  // Configure VPC
  await page.click('.cy-node[data-type="vpc"]');
  await page.fill('[name="cidr"]', '10.0.0.0/16');
  
  // Add Subnets
  await page.dragAndDrop('[data-component="subnet"]', '#cy');
  // ...
  
  // Generate Terraform
  await page.click('[data-action="generate-terraform"]');
  
  // Verify output
  await expect(page.locator('[data-output="terraform"]')).toContainText('resource "aws_vpc"');
});
```

#### Szenario 2: Demo-Architektur laden
```javascript
test('Load demo architecture', async ({ page }) => {
  await page.goto('http://localhost:5173/infrastructure-designer.html?id=demo');
  
  // Wait for canvas to load
  await page.waitForSelector('.cy-node[data-type="vpc"]');
  
  // Verify components
  const vpcNodes = await page.locator('.cy-node[data-type="vpc"]').count();
  expect(vpcNodes).toBe(1);
  
  const subnetNodes = await page.locator('.cy-node[data-type="subnet"]').count();
  expect(subnetNodes).toBeGreaterThan(0);
});
```

---

## 4. Integration Tests

### Backend + Frontend Integration
```bash
# Terminal 1: Backend starten
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend
uvicorn app.main:app --reload

# Terminal 2: Frontend starten
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend
npm run dev

# Terminal 3: Integration Tests
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend
npx playwright test tests/integration/
```

---

## Test-Coverage Ziele

### Backend Coverage
- **Core Business Logic:** 90%+ ✅
- **API Endpoints:** 80%+ ✅
- **Utilities:** 100% ✅

### Frontend Coverage
- **State Management:** 80%+
- **UI Components:** 60%+ (critical paths)
- **Utilities:** 100%

---

## CI/CD Integration

### GitHub Actions (geplant)
```yaml
name: Infrastructure Designer Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[test]"
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test
      - uses: codecov/codecov-action@v3

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run dev &
      - run: npx playwright test
```

---

## Troubleshooting

### Backend Tests schlagen fehl
```bash
# Logs prüfen
tail -f backend/logs/app.log

# Dependencies neu installieren
pip install --force-reinstall -e ".[test]"

# Datenbank zurücksetzen (falls nötig)
alembic downgrade base
alembic upgrade head
```

### Frontend Tests schlagen fehl
```bash
# Node Modules neu installieren
rm -rf node_modules package-lock.json
npm install

# Build-Cache löschen
rm -rf dist .vite

# Browser-Cache löschen (bei manuellen Tests)
Cmd+Shift+R (Chrome/Firefox)
```

### E2E Tests schlagen fehl
```bash
# Playwright neu installieren
npx playwright install --with-deps

# Headed Mode für Debugging
npx playwright test --headed --debug

# Screenshots bei Failure
npx playwright test --screenshot=on
```

---

## Performance Tests

### Backend Performance
```bash
# Load Testing mit Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/terraform/generate-from-json

# Oder mit hey
hey -n 1000 -c 10 -m POST -H "Content-Type: application/json" -d @test_payload.json http://localhost:8000/api/v1/terraform/generate-from-json
```

### Frontend Performance
```bash
# Lighthouse Audit
npm run build
npx lighthouse http://localhost:5173/infrastructure-designer.html --view

# Bundle Size Analysis
npm run build -- --analyze
```

---

## Test-Reports

### Automatische Reports
- **Backend:** `htmlcov/index.html` (pytest-cov)
- **Frontend:** `coverage/index.html` (Vitest)
- **E2E:** `playwright-report/index.html` (Playwright)

### Manuelle Reports
Siehe:
- `/Users/andyschwarz/Documents/Privat/OverCloud/TEST_REPORT_INFRASTRUCTURE_DESIGNER.md`
- `/Users/andyschwarz/Documents/Privat/OverCloud/INFRASTRUCTURE_DESIGNER_BUGS.md`

---

## Best Practices

### Testen
1. **Test-First:** Kritische Features mit TDD entwickeln
2. **Mock External Services:** AWS SDK, Terraform CLI
3. **Isolierte Tests:** Keine Abhängigkeiten zwischen Tests
4. **Fast Tests:** Unit Tests < 500ms
5. **Descriptive Names:** `test_vpc_creation_with_invalid_cidr_should_fail`

### Debugging
1. **Print Statements:** Temporär für schnelles Debugging
2. **Debugger:** `breakpoint()` (Python) oder `debugger` (JS)
3. **Logging:** Strukturiertes Logging mit Context
4. **Screenshots:** Bei UI-Tests immer Screenshots bei Failure

---

## Nächste Schritte

### Kurzfristig (nach Testing)
1. ✅ Backend Tests ausführen
2. ✅ Frontend Tests ausführen
3. ✅ E2E Tests ausführen
4. ✅ Test-Report erstellen
5. ✅ Bugs fixen

### Mittelfristig (nach MVP)
1. ⏳ CI/CD Pipeline aufsetzen
2. ⏳ Automated Regression Tests
3. ⏳ Performance Monitoring
4. ⏳ Test-Coverage erhöhen (90%+)

---

**Viel Erfolg beim Testen!** 🧪

_Letztes Update: 2026-05-16_
