# OverCloud Frontend Test Setup

## Übersicht

Das Frontend verwendet zwei Test-Frameworks:

1. **Vitest** - Unit Tests für isolierte Komponenten
2. **Playwright** - E2E Tests für Integration und User Flows

## Installation

### Vitest Dependencies installieren

```bash
npm install -D vitest@latest jsdom@latest @vitest/ui@latest happy-dom@latest
```

### Bereits installiert

- `@playwright/test` - E2E Testing
- `playwright` - Browser Automation

## Test-Struktur

```
tests/
├── e2e/                              # Playwright E2E Tests
│   ├── infrastructure-designer.spec.js   # Designer Integration Tests
│   ├── architecture-builder.spec.js      # Bestehende Tests
│   └── architecture-builder-advanced.spec.js
├── unit/                             # Vitest Unit Tests
│   ├── setup.js                      # Test Setup
│   ├── infrastructure-canvas.test.js # Canvas Component Tests
│   ├── tab-system.test.js           # Tab System Tests
│   ├── designer-api.test.js         # API Client Tests
│   └── architecture-validator.test.js # Bestehende Tests
└── TEST_SETUP.md                     # Diese Datei
```

## Test-Scripts (package.json)

Füge folgende Scripts hinzu:

```json
{
  "scripts": {
    "test": "vitest",
    "test:unit": "vitest run",
    "test:unit:watch": "vitest",
    "test:unit:ui": "vitest --ui",
    "test:unit:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "npm run test:unit && npm run test:e2e"
  }
}
```

## Test-Ausführung

### Unit Tests

```bash
# Alle Unit-Tests ausführen
npm run test:unit

# Unit-Tests im Watch-Mode
npm run test:unit:watch

# Unit-Tests mit UI
npm run test:unit:ui

# Coverage Report
npm run test:unit:coverage
```

### E2E Tests

```bash
# Alle E2E-Tests ausführen
npm run test:e2e

# E2E-Tests mit UI
npm run test:e2e:ui

# Spezifischen Test ausführen
npx playwright test infrastructure-designer
```

### Alle Tests

```bash
npm run test:all
```

## Test Coverage Ziele

Basierend auf den CLAUDE.md Regeln:

- **Core Business Logic:** 90%+ Coverage
- **API Endpoints/Clients:** 80%+ Coverage
- **UI Components:** 60%+ Coverage (kritische Pfade)
- **Utilities:** 100% Coverage

## Erstellte Tests

### ✅ Unit Tests

1. **infrastructure-canvas.test.js**
   - Initialization
   - Component Management (add, update, remove, get)
   - Connections (add, remove)
   - Layout (auto-layout, fit, center, zoom)
   - Export/Import JSON

2. **tab-system.test.js**
   - Initialization
   - Tab Management (open, close, activate)
   - Tab Content Rendering
   - Visual State
   - Multiple Tabs

3. **designer-api.test.js**
   - Save Architecture
   - Load Architecture
   - Generate Terraform
   - Validate Architecture
   - Download Terraform ZIP

4. **architecture-validator.test.js** (bereits vorhanden)
   - Basic Validation
   - Component Validation
   - Relationship Validation
   - JSON Syntax Validation
   - Isolated Components Detection
   - Circular Dependencies Detection

### ✅ E2E Tests

1. **infrastructure-designer.spec.js**
   - Full Flow Tests
     - Load page with components
     - Display component palette
     - Add components to canvas
     - Open tabs on component add
     - Display configuration forms
     - Update component configuration
     - Add multiple components
     - Switch between tabs
     - Close tabs
     - Click canvas node to open tab
     - Create connections
     - Save architecture
     - Validate architecture
     - Generate Terraform
     - Export Terraform ZIP
     - Load existing architecture
     - Error handling
   - Advanced Features
     - Auto-layout
     - Zoom and pan
     - Search/filter components
     - Component tooltips
     - Undo/redo

2. **architecture-builder.spec.js** (bereits vorhanden)
3. **architecture-builder-advanced.spec.js** (bereits vorhanden)

## Bekannte Issues

### Unit Tests

Die Unit-Tests verwenden Mocks für Cytoscape.js und können nicht die echte Canvas-Interaktion testen. Diese werden in E2E-Tests abgedeckt.

### E2E Tests

Die E2E-Tests in `infrastructure-designer.spec.js` setzen voraus, dass:

1. Die Infrastructure Designer Seite unter `/infrastructure-designer.html` erreichbar ist
2. Alle HTML-Attribute (`data-component-type`, `data-tab-id`, etc.) korrekt gesetzt sind
3. Das Backend unter `http://localhost:8000` läuft (für Save/Load/Generate Tests)

## Fehlende Tests

Folgende Bereiche benötigen noch Tests:

1. **ComponentPalette.js** - Drag & Drop Logic
2. **ConfigurationTabs.js** - Dynamic Form Rendering
3. **infrastructure-designer.js** - State Management
4. **Error Boundary Tests** - Error Handling
5. **Performance Tests** - Large Architectures (100+ Components)

## Nächste Schritte

1. **Vitest installieren:**
   ```bash
   npm install -D vitest jsdom @vitest/ui happy-dom
   ```

2. **package.json Scripts updaten** (siehe oben)

3. **Tests ausführen:**
   ```bash
   npm run test:unit
   npm run test:e2e
   ```

4. **Fehlende Implementierungen ergänzen:**
   - Manche Tests setzen Funktionen voraus, die noch implementiert werden müssen (z.B. `addComponent`, `updateComponent` in InfrastructureCanvas)
   - Prüfe Test-Ergebnisse und implementiere fehlende Methoden

5. **Coverage prüfen:**
   ```bash
   npm run test:unit:coverage
   ```

6. **CI/CD Integration:**
   - Tests in GitHub Actions Workflow einbinden
   - Coverage Reporting zu SonarQube/Codecov

## Troubleshooting

### Vitest findet Tests nicht

Prüfe `vitest.config.js`:
```js
test: {
  include: ['tests/unit/**/*.test.js']
}
```

### Cytoscape Mock funktioniert nicht

In der Test-Datei Cytoscape korrekt mocken:
```js
vi.mock('cytoscape', () => ({
  default: mockCytoscape
}));
```

### Playwright kann Elemente nicht finden

Prüfe:
1. Dev-Server läuft: `npm run dev`
2. Selektoren sind korrekt (z.B. `[data-component-type="vpc"]`)
3. Warte-Zeiten ausreichend: `await page.waitForTimeout(500)`

### Tests schlagen fehl wegen fehlender Implementierung

Das ist normal! Die Tests sind "Test-First" geschrieben. Implementiere die fehlenden Methoden basierend auf den Test-Erwartungen.

## Beispiel Test-Ausgabe

```
✓ tests/unit/infrastructure-canvas.test.js (25)
  ✓ InfrastructureCanvas - Initialization (4)
  ✓ InfrastructureCanvas - Component Management (6)
  ✓ InfrastructureCanvas - Connections (2)
  ✓ InfrastructureCanvas - Layout (4)
  ✓ InfrastructureCanvas - Export/Import (3)

✓ tests/unit/tab-system.test.js (18)
  ✓ TabSystem - Initialization (3)
  ✓ TabSystem - Tab Management (7)
  ✓ TabSystem - Tab Content Rendering (3)
  ✓ TabSystem - Visual State (4)
  ✓ TabSystem - Multiple Tabs (3)

✓ tests/unit/designer-api.test.js (15)
  ✓ Designer API - Save Architecture (3)
  ✓ Designer API - Load Architecture (2)
  ✓ Designer API - Generate Terraform (3)
  ✓ Designer API - Validate Architecture (4)
  ✓ Designer API - Download Terraform (3)

Test Files  3 passed (3)
     Tests  58 passed (58)
  Start at  12:34:56
  Duration  2.45s
```
