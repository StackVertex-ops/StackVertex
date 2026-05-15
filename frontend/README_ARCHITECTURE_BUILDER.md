# OverCloud Architecture Builder - Setup & Quick Start

## Installation & Setup

### 1. Dependencies installieren

```bash
cd frontend
npm install
```

### 2. Dev Server starten

```bash
npm run dev
```

Der Dev Server läuft auf: `http://localhost:5173`

## Verwendung

### Option 1: Dedizierte Builder-Page (NEU - Empfohlen)

Öffne im Browser:
```
http://localhost:5173/architecture-builder.html
```

**Features:**
- Visual Drag & Drop Canvas
- Component Palette mit AWS Services
- Properties Panel für Konfiguration
- Templates (Web App, Serverless API)
- JSON Export/Import
- Zoom & Pan Navigation

### Option 2: Klassischer Form-based Builder (Alt)

Öffne im Browser:
```
http://localhost:5173/#/architectures/new
```

**Features:**
- Requirements-Formular
- JSON Editor
- Templates laden

## Tests ausführen

### E2E Tests (Playwright)

```bash
# Alle Tests
npm run test:e2e

# Mit UI (interaktiv)
npm run test:e2e:ui

# Nur eine Test-Datei
npx playwright test tests/e2e/architecture-builder.spec.js

# Debugging
npx playwright test --debug
```

### Unit Tests

```bash
npm run test:unit
```

## Verzeichnisstruktur

```
frontend/
├── src/
│   ├── architecture-builder.html          # NEU: Dedizierte Builder Page
│   ├── js/
│   │   ├── architecture-builder-entry.js  # NEU: Entry Point
│   │   ├── components/
│   │   │   ├── component-palette.js       # NEU: Component Sidebar
│   │   │   ├── architecture-canvas.js     # NEU: Drag & Drop Canvas
│   │   │   ├── properties-panel.js        # NEU: Properties Editor
│   │   │   ├── architecture-form.js       # Alt: Requirements Form
│   │   │   └── architecture-list.js
│   │   ├── pages/
│   │   │   ├── architecture-builder-canvas.js  # NEU: Main Controller
│   │   │   ├── architecture-builder.js    # Alt: Form-based Builder
│   │   │   ├── architectures.js
│   │   │   └── architecture-detail.js
│   │   ├── lib/
│   │   │   ├── architecture-validator.js  # NEU: Client-side Validation
│   │   │   ├── aws-components.js
│   │   │   ├── example-architectures.js
│   │   │   └── api-client.js
│   │   └── api/
│   │       └── architectures.js
│   └── css/
│       └── main.css
├── tests/
│   ├── e2e/
│   │   └── architecture-builder.spec.js   # NEU: E2E Tests
│   └── unit/
│       └── architecture-validator.test.js # NEU: Unit Tests
├── docs/
│   └── ARCHITECTURE_BUILDER.md            # NEU: Ausführliche Dokumentation
├── package.json
├── playwright.config.js                   # NEU: Playwright Config
└── vite.config.js
```

## Was ist neu?

### Phase 1 (DONE ✅)

1. **Visual Canvas** - Drag & Drop Interface für Components
2. **Component Palette** - Alle AWS Services durchsuchbar
3. **Properties Panel** - Service-spezifische Konfiguration
4. **Templates** - Quick Start mit vorgefertigten Architekturen
5. **Validation** - Client-side JSON Schema Validierung
6. **Zoom & Pan** - Navigation für große Architekturen
7. **E2E Tests** - Vollständige Playwright Test-Suite
8. **Unit Tests** - Validator Tests
9. **Documentation** - Umfassende User & Dev Docs

### Phase 2 (TODO 🚧)

- Visual Relationship Editor (Click & Connect)
- Auto-Layout Algorithmus
- Undo/Redo Stack
- Multi-Select & Bulk Operations
- Copy/Paste Components
- Keyboard Shortcuts (vollständig)
- Cost Estimation Integration
- Deployment Preview

## Backend Requirements

Der Architecture Builder benötigt ein laufendes Backend:

```bash
# Backend starten (in separatem Terminal)
cd backend
poetry run uvicorn app.main:app --reload
```

Backend läuft auf: `http://localhost:8000`

### API Endpoints

- `GET /api/v1/architectures` - Liste aller Architekturen
- `GET /api/v1/architectures/{id}` - Einzelne Architektur
- `POST /api/v1/architectures` - Neue Architektur erstellen
- `PUT /api/v1/architectures/{id}` - Architektur aktualisieren
- `DELETE /api/v1/architectures/{id}` - Architektur löschen

## Browser Support

- **Chrome/Edge:** ✅ Vollständig getestet
- **Firefox:** ✅ Funktioniert
- **Safari:** ⚠️ Basic Support (Drag & Drop kann Issues haben)
- **Mobile:** ❌ Nicht optimiert (Desktop only)

## Troubleshooting

### "Module not found" Fehler

```bash
# Dependencies neu installieren
rm -rf node_modules package-lock.json
npm install
```

### Backend nicht erreichbar

1. Prüfe ob Backend läuft: `curl http://localhost:8000/health`
2. Prüfe CORS-Einstellungen im Backend
3. Prüfe Browser Console für Fehler

### Tests schlagen fehl

```bash
# Playwright Browsers installieren
npx playwright install

# Tests einzeln ausführen
npx playwright test tests/e2e/architecture-builder.spec.js --headed
```

### Canvas zeigt nichts an

1. Öffne Browser DevTools Console
2. Prüfe auf JavaScript-Fehler
3. Stelle sicher dass Vite korrekt lädt (keine 404s im Network Tab)

## Nützliche Befehle

```bash
# Dev Server mit Custom Port
npm run dev -- --port 3000

# Build für Production
npm run build

# Preview Production Build
npm run preview

# Playwright Code Generator (für Tests)
npx playwright codegen http://localhost:5173/architecture-builder.html

# Playwright Report anzeigen
npx playwright show-report
```

## Links

- **User Guide:** [docs/ARCHITECTURE_BUILDER.md](./docs/ARCHITECTURE_BUILDER.md)
- **API Docs:** [Backend README](../backend/README.md)
- **Component Library:** [src/js/lib/aws-components.js](./src/js/lib/aws-components.js)
- **Example Architectures:** [src/js/lib/example-architectures.js](./src/js/lib/example-architectures.js)

## Support

Bei Fragen oder Problemen:
1. Prüfe die [Dokumentation](./docs/ARCHITECTURE_BUILDER.md)
2. Schaue in die [Test-Files](./tests/e2e/) für Usage-Beispiele
3. Öffne ein Issue im Repository

---

**Happy Building! 🏗️**
