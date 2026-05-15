# Architecture Builder - User Guide & Developer Documentation

## Übersicht

Der **Architecture Builder** ist ein moderner, visueller Editor für Cloud-Infrastruktur-Architekturen. Er kombiniert die Einfachheit von Templates mit der Flexibilität eines vollständigen Visual Builders.

## Features

### ✅ Implementiert (Phase 1)

#### 1. **Component Palette** (Linke Sidebar)
- **Quick Start Templates:** Vorgefertigte Architekturen (Web App, Serverless API, Static Site)
- **Component Browser:** Alle AWS-Components gruppiert nach Kategorien
- **Suche:** Echtzeit-Suche über alle Components
- **Drag & Drop:** Ziehe Components direkt auf die Canvas

#### 2. **Visual Canvas** (Hauptbereich)
- **Drag & Drop:** Füge Components per Drag & Drop hinzu
- **Zoom & Pan:** Navigiere große Architekturen (Mausrad oder Zoom-Buttons)
- **Component Nodes:** Visuelle Darstellung aller Components mit Icon und Name
- **Grid Background:** Orientierungshilfe für Platzierung
- **Empty State:** Hilfreiche Anleitung beim Start

#### 3. **Properties Panel** (Rechte Sidebar)
- **Component Details:** Name, ID, Typ, Provider Service
- **Service-spezifische Properties:** Unterschiedliche Felder je nach Component-Typ
  - **VPC:** CIDR Block, DNS Settings
  - **EC2:** Instance Type, AMI
  - **RDS:** Engine, Instance Class, Storage, Multi-AZ
  - **S3:** Versioning, Encryption, Public Access
  - **Lambda:** Runtime, Memory, Timeout
  - **DynamoDB:** Billing Mode, Hash Key
  - **ALB:** Internal/External
- **Live Updates:** Änderungen werden sofort auf der Canvas angezeigt

#### 4. **Validierung**
- **Client-side Validation:** JSON Schema Validierung
- **Error Detection:** Fehlende Felder, Duplicate IDs, Broken References
- **Warnings:** Empfehlungen für Best Practices
- **Realtime Feedback:** Validation Status in der Statusbar

#### 5. **JSON Export/Import**
- **JSON View Modal:** Zeige komplettes Architecture JSON
- **Copy to Clipboard:** JSON mit einem Klick kopieren
- **Download JSON:** Als Datei herunterladen
- **Format:** Kompatibel mit Backend API

#### 6. **Save/Load**
- **Backend Integration:** Speichert direkt in der Datenbank
- **Edit Mode:** Lade bestehende Architekturen zum Bearbeiten
- **Auto-Update:** Timestamps werden automatisch gesetzt

## Benutzerhandbuch

### Neue Architektur erstellen

1. **Öffne den Builder:** Navigiere zu `/architecture-builder.html`
2. **Wähle einen Ansatz:**
   - **Option A:** Quick Start Template laden (empfohlen für Anfänger)
   - **Option B:** Von Grund auf neu erstellen

#### Option A: Template verwenden

1. Klicke in der **Component Palette** auf eines der Templates:
   - **Web Application:** VPC + ALB + EC2 + RDS + S3 (3-Tier Architektur)
   - **Serverless API:** API Gateway + Lambda + DynamoDB
   - **Static Website:** S3 + CloudFront + Route53 (coming soon)

2. Das Template wird automatisch auf die Canvas geladen

3. **Anpassen:**
   - Klicke auf eine Component, um sie auszuwählen
   - Bearbeite Properties im rechten Panel
   - Verschiebe Components per Drag & Drop
   - Füge weitere Components hinzu

#### Option B: Von Grund auf erstellen

1. **Component hinzufügen:**
   - Suche nach der gewünschten Component (z.B. "VPC")
   - Ziehe die Component auf die Canvas
   - Oder: Klicke auf die Component und folge dem Hinweis

2. **Component konfigurieren:**
   - Klicke auf die Component auf der Canvas
   - Bearbeite Properties im rechten Panel
   - Klicke "Änderungen übernehmen"

3. **Weitere Components hinzufügen:**
   - Wiederhole Schritt 1-2 für alle benötigten Components

4. **Relationships definieren:**
   - (In Phase 2: Visual Connections)
   - Aktuell: Über JSON Editor

### Navigation & Bedienung

#### Canvas Controls

- **Zoom In/Out:** Buttons oben links oder Mausrad
- **Pan:** Canvas mit Maus ziehen (Linksklick + Ziehen)
- **Reset Zoom:** Button "Reset" oben links
- **Component verschieben:** Component anklicken und ziehen

#### Keyboard Shortcuts

- `Ctrl/Cmd + Plus`: Zoom In
- `Ctrl/Cmd + Minus`: Zoom Out
- `Ctrl/Cmd + 0`: Reset Zoom
- `Delete`: Ausgewählte Component löschen (geplant)
- `Ctrl/Cmd + S`: Speichern (geplant)

### Validierung

1. Klicke auf **"Validieren"** Button in der Header-Bar
2. Ergebnisse werden in der **Statusbar** angezeigt:
   - ✓ **Grün:** Alles OK
   - ⚠ **Gelb:** Warnungen (funktioniert, aber nicht optimal)
   - ✗ **Rot:** Fehler (muss behoben werden)

3. Bei Fehlern: Pop-up mit Details öffnet sich
4. Behebe Fehler und validiere erneut

### Speichern

1. Klicke auf **"Speichern"** Button (oben rechts)
2. Architecture wird im Backend gespeichert
3. Du wirst automatisch zur Architecture-Liste weitergeleitet

### JSON Export

1. Klicke auf **"JSON anzeigen"** Button (Statusbar unten rechts)
2. JSON Modal öffnet sich
3. Optionen:
   - **Kopieren:** In Zwischenablage kopieren
   - **Download:** Als `.json` Datei herunterladen

### Bestehende Architektur bearbeiten

1. Öffne den Builder mit `?id=<architecture-id>` Parameter
2. Beispiel: `/architecture-builder.html?id=abc123`
3. Architektur wird automatisch geladen
4. Bearbeite wie gewohnt
5. Klicke "Speichern" zum Aktualisieren

## Developer Documentation

### Architektur

#### Komponenten-Übersicht

```
frontend/src/
├── architecture-builder.html           # Dedizierte HTML-Page
├── js/
│   ├── architecture-builder-entry.js  # Entry Point
│   ├── components/
│   │   ├── component-palette.js       # Linke Sidebar mit Components
│   │   ├── architecture-canvas.js     # Canvas (Drag & Drop, Zoom, Pan)
│   │   ├── properties-panel.js        # Rechte Sidebar mit Properties
│   ├── pages/
│   │   ├── architecture-builder-canvas.js  # Main Controller
│   ├── lib/
│   │   ├── architecture-validator.js  # Validation Logic
│   │   ├── aws-components.js          # AWS Component Definitions
│   │   ├── example-architectures.js   # Templates
│   └── api/
│       ├── architectures.js           # Backend API Integration
└── tests/
    ├── e2e/
    │   └── architecture-builder.spec.js  # E2E Tests (Playwright)
    └── unit/
        └── architecture-validator.test.js  # Unit Tests
```

#### State Management

Der Architecture Builder verwendet **lokalen State** in der `ArchitectureCanvas` Klasse:

```javascript
class ArchitectureCanvas {
  constructor() {
    this.components = new Map();      // id -> component data
    this.relationships = [];           // array of {from, to, type}
    this.selectedComponentId = null;
    this.scale = 1;
    this.panX = 0;
    this.panY = 0;
  }
}
```

#### Event Flow

1. **User Action** → Event Handler
2. **Event Handler** → Update State
3. **State Update** → Re-render affected parts
4. **Re-render** → Update DOM

Beispiel: Component hinzufügen

```
Drag & Drop → canvas.addComponent()
            → components.set(id, data)
            → renderComponents()
            → onComponentAdd callback
            → updateStatus()
```

#### JSON Schema

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "My Architecture",
    "description": "...",
    "provider": "aws",
    "region": "eu-central-1"
  },
  "requirements": { ... },
  "architecture": {
    "components": [
      {
        "id": "vpc-1",
        "type": "network",
        "name": "Main VPC",
        "provider_service": "vpc",
        "position": { "x": 100, "y": 100 },
        "configuration": {
          "cidr_block": "10.0.0.0/16",
          "enable_dns_hostnames": true
        }
      }
    ],
    "relationships": [
      {
        "from": "ec2-1",
        "to": "vpc-1",
        "type": "network"
      }
    ]
  }
}
```

### Extending the Builder

#### Neue AWS Components hinzufügen

1. **Definiere Component in `aws-components.js`:**

```javascript
export const AWS_COMPONENTS = {
  compute: {
    fargate: {
      name: 'Fargate',
      icon: '🐳',
      category: 'compute',
      description: 'Serverless container service',
      provider_service: 'fargate'
    }
  }
};
```

2. **Füge Properties-Form in `properties-panel.js` hinzu:**

```javascript
function renderFargateFields(config) {
  return `
    <div>
      <label>Task CPU</label>
      <select id="prop-task-cpu">
        <option value="256">256 (.25 vCPU)</option>
        <option value="512">512 (.5 vCPU)</option>
      </select>
    </div>
  `;
}
```

3. **Update `extractProperties()` in `properties-panel.js`:**

```javascript
case 'fargate':
  properties.configuration.task_cpu = container.querySelector('#prop-task-cpu')?.value;
  break;
```

#### Neue Template hinzufügen

1. **Erstelle Template in `example-architectures.js`:**

```javascript
export const EXAMPLE_MICROSERVICES = {
  version: "1.0.0",
  metadata: {
    name: "Microservices Architecture",
    provider: "aws"
  },
  architecture: {
    components: [ ... ],
    relationships: [ ... ]
  }
};
```

2. **Registriere in `EXAMPLE_ARCHITECTURES` Array:**

```javascript
export const EXAMPLE_ARCHITECTURES = [
  {
    id: 'microservices',
    name: 'Microservices',
    description: 'ECS + RDS + ElastiCache',
    provider: 'aws',
    complexity: 'high',
    data: EXAMPLE_MICROSERVICES
  }
];
```

3. **Update `loadTemplate()` in `architecture-builder-canvas.js`:**

```javascript
case 'microservices':
  template = EXAMPLE_MICROSERVICES;
  break;
```

### Testing

#### E2E Tests ausführen

```bash
# Alle Tests
npm run test:e2e

# Mit UI
npm run test:e2e:ui

# Nur Chrome
npx playwright test --project=chromium

# Debugging
npx playwright test --debug
```

#### Unit Tests ausführen

```bash
npm run test:unit
```

#### Neuen Test hinzufügen

```javascript
test.describe('New Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/architecture-builder.html');
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await expect(page.locator('#element')).toBeVisible();
  });
});
```

### Performance Optimization

#### Rendering Performance

- **Canvas:** Verwendet SVG für Skalierbarkeit
- **Components:** Lazy Rendering (nur sichtbare Components)
- **Re-renders:** Minimiert durch gezieltes Update nur betroffener Bereiche

#### Empfehlungen

- **Max. 50 Components** pro Canvas für optimale Performance
- **Relationships:** Bei >100 Relationships visual grouping erwägen
- **Zoom:** Scale Factor zwischen 0.1 und 3 begrenzt

### Known Issues & Limitations

#### Phase 1 (Current)

- ❌ **Visual Relationship Drawing:** Relationships werden gerendert, aber nicht interaktiv erstellt
- ❌ **Auto-Layout:** Components müssen manuell positioniert werden
- ❌ **Undo/Redo:** Noch nicht implementiert
- ❌ **Multi-Select:** Nur eine Component gleichzeitig selektierbar
- ❌ **Copy/Paste:** Noch nicht implementiert
- ❌ **Keyboard Shortcuts:** Nur basic Zoom

#### Planned (Phase 2)

- ✅ Visual Relationship Editor (Click & Connect)
- ✅ Auto-Layout Algorithmus
- ✅ Undo/Redo Stack
- ✅ Multi-Select & Bulk Operations
- ✅ Copy/Paste Components
- ✅ Full Keyboard Navigation
- ✅ Cost Estimation Integration
- ✅ Security Validation
- ✅ Deployment Preview

## API Integration

### Backend Endpoints

```javascript
// List all architectures
GET /api/v1/architectures

// Get single architecture
GET /api/v1/architectures/{id}

// Create new architecture
POST /api/v1/architectures
{
  "name": "...",
  "description": "...",
  "version": "1.0.0",
  "architecture_json": { ... },
  "owner": "user"
}

// Update architecture
PUT /api/v1/architectures/{id}
{ ... }

// Delete architecture
DELETE /api/v1/architectures/{id}
```

### API Client Usage

```javascript
import { createArchitecture, getArchitecture } from './api/architectures.js';

// Create
const response = await createArchitecture(payload);

// Get
const architecture = await getArchitecture(id);
```

## Troubleshooting

### Canvas lädt nicht

- **Problem:** Canvas bleibt leer oder zeigt Loading State
- **Lösung:** 
  1. Prüfe Browser Console auf Fehler
  2. Stelle sicher dass Backend läuft (`http://localhost:8000`)
  3. Prüfe CORS-Einstellungen

### Components lassen sich nicht hinzufügen

- **Problem:** Drag & Drop funktioniert nicht
- **Lösung:**
  1. Stelle sicher dass `draggable="true"` auf Component-Items gesetzt ist
  2. Prüfe ob `dragover` und `drop` Events registriert sind
  3. Teste in anderem Browser (Safari hat manchmal Issues)

### Validierung schlägt fehl

- **Problem:** "JSON ist ungültig"
- **Lösung:**
  1. Prüfe ob alle required Fields vorhanden sind
  2. Validiere JSON Syntax (keine trailing commas, etc.)
  3. Nutze "JSON anzeigen" um Struktur zu prüfen

### Performance Issues

- **Problem:** Canvas ist langsam bei vielen Components
- **Lösung:**
  1. Reduziere Anzahl Components (<50)
  2. Deaktiviere Animations (falls custom CSS hinzugefügt)
  3. Nutze Chrome Performance Profiler

## FAQ

**Q: Kann ich eigene Components definieren?**  
A: Ja! Siehe "Extending the Builder" → "Neue AWS Components hinzufügen"

**Q: Unterstützt der Builder Azure/GCP?**  
A: Aktuell nur AWS (Phase 1). Azure/GCP sind für Phase 2+ geplant.

**Q: Kann ich JSON manuell bearbeiten?**  
A: Ja! Nutze "JSON anzeigen" Modal oder den alten JSON Editor (`/architectures/new`)

**Q: Werden Änderungen automatisch gespeichert?**  
A: Nein. Du musst explizit auf "Speichern" klicken.

**Q: Kann ich Architekturen exportieren/importieren?**  
A: Export: Ja (JSON Download). Import: Noch nicht (Phase 2)

**Q: Funktioniert der Builder mobil?**  
A: Nein, aktuell nur Desktop (min. 1280px Breite empfohlen)

## Contributing

### Code Style

- **JavaScript:** ES6+ Modules, async/await
- **Naming:** camelCase für Variablen, PascalCase für Klassen
- **Comments:** JSDoc für alle exports
- **Formatting:** Prettier (automatisch via Vite)

### Pull Request Process

1. Feature Branch erstellen
2. Implementierung + Tests
3. E2E Tests erfolgreich
4. PR erstellen mit Beschreibung
5. Code Review abwarten
6. Merge nach Approval

## License

MIT License - siehe Projekt-Root

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-15  
**Author:** OverCloud Team
