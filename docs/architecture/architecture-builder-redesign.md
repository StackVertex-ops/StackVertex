# Architecture Builder - Redesign Specification

> **Status:** Draft (In Planning)
> **Author:** Claude Code
> **Date:** 2026-03-25
> **Version:** 0.2.0
> **Depends on:** aws-service-config-ui.md

---

## 1. Vision & Ziele

### Was ändern wir?

**ALT (Current):**
- Rein JSON-basierter Editor
- Keine visuelle Darstellung
- Nur für JSON-Experten nutzbar
- Keine Guidance

**NEU (Target):**
- **Visual-First:** Canvas mit Komponenten-Boxen
- **Wizard-Driven:** Multi-Step Forms für Services
- **Guided Experience:** Best Practices, Warnings, Cost Preview
- **JSON-Second:** JSON bleibt editierbar, aber optional

### Zielgruppe

1. **Beginner:** Erstellen ihre erste Cloud-Architektur ohne AWS-Kenntnisse
2. **Intermediate:** Nutzen Wizards + gelegentlich JSON für Fine-Tuning
3. **Expert:** Nutzen hauptsächlich JSON, aber Canvas als Visualisierung

---

## 2. Layout - 3-Column Design

### 2.1 Desktop (> 1280px)

```
┌──────────────────────────────────────────────────────────────────┐
│  Header: OverCloud | [Architecture Name] | [Save] [Export] [?]   │
├──────────────┬─────────────────────────────┬─────────────────────┤
│              │                             │                     │
│  Component   │        Canvas               │  Properties Panel   │
│  Library     │        (Main)               │      (Sidebar)      │
│  (240px)     │        (flex-1)             │      (360px)        │
│              │                             │                     │
│ 🔍 Search    │   ┌─────────────────────┐  │ ✏️ Edit: EC2        │
│              │   │                     │  │                     │
│ ┏━━━━━━━━┓  │   │   ┌───────────┐     │  │ Name:               │
│ ┃Compute ┃  │   │   │    EC2    │     │  │ ┌─────────────────┐ │
│ ┗━━━━━━━━┛  │   │   │ t3.medium │     │  │ │ web-server-1    │ │
│  □ EC2      │   │   │  Running  │     │  │ └─────────────────┘ │
│  □ Lambda   │   │   └─────┬─────┘     │  │                     │
│  □ ECS      │   │         │           │  │ Instance Type:      │
│             │   │         ▼           │  │ ┌─────────────────┐ │
│ Database    │   │   ┌───────────┐     │  │ │ t3.medium    ▼ │ │
│  □ RDS      │   │   │    RDS    │     │  │ └─────────────────┘ │
│  □ DynamoDB │   │   │ PostgreSQL│     │  │                     │
│             │   │   │  20GB     │     │  │ Storage:            │
│ Storage     │   │   └───────────┘     │  │ ┌───┐               │
│  □ S3       │   │                     │  │ │20 │ GB            │
│  □ EBS      │   │   ┌───────────┐     │  │ └───┘               │
│             │   │   │     S3    │     │  │                     │
│ Network     │   │   │  Bucket   │     │  │ [Validate]          │
│  □ VPC      │   │   │ Encrypted │     │  │ [Delete Component]  │
│  □ ALB      │   │   └───────────┘     │  │ [Save Changes]      │
│  □ Sec.Grp  │   │                     │  │                     │
│             │   └─────────────────────┘  │                     │
│             │                             │                     │
│ [+ Add      │   [View: ● Boxes  ○ JSON] │                     │
│  Custom]    │   [Zoom: - 100% +]         │                     │
│             │                             │                     │
└──────────────┴─────────────────────────────┴─────────────────────┘
```

### 2.2 Tablet (768px - 1280px)

- **Component Library:** Collapsible (Hamburger Menu)
- **Canvas:** Full Width
- **Properties Panel:** Slide-in Drawer (von rechts)

### 2.3 Mobile (< 768px)

- **Stacked Layout:** Component Library → Canvas → Properties
- **Full-Screen Modals:** Wizards nehmen ganzen Screen ein
- **Bottom Sheet:** Properties als Bottom Sheet (swipe up)

---

## 3. Component Library (Sidebar Links)

### 3.1 Struktur

```
┌──────────────────┐
│  Component Lib.  │
├──────────────────┤
│                  │
│ 🔍 [Search...]  │
│                  │
│ ▾ Compute        │ ← Collapsible Section
│   □ EC2          │
│   □ Lambda       │
│   □ ECS/Fargate  │
│   □ Lightsail    │
│                  │
│ ▾ Database       │
│   □ RDS          │
│   □ DynamoDB     │
│   □ Aurora       │
│   □ ElastiCache  │
│                  │
│ ▾ Storage        │
│   □ S3           │
│   □ EBS          │
│   □ EFS          │
│                  │
│ ▾ Network        │
│   □ VPC          │
│   □ ALB/NLB      │
│   □ Sec. Group   │
│   □ CloudFront   │
│                  │
│ ▾ Integration    │
│   □ SQS          │
│   □ SNS          │
│   □ EventBridge  │
│                  │
│ ▾ IAM & Security │
│   □ IAM Role     │
│   □ Secrets Mgr  │
│   □ KMS          │
│                  │
│ [+ Custom]       │ ← Add custom resource
│                  │
└──────────────────┘
```

### 3.2 Interaction

**Click on Service:**
1. Service Modal/Wizard öffnet sich
2. User füllt Form aus
3. "Add Component" → erscheint im Canvas
4. Properties Panel zeigt neue Component

**Search:**
- Filtert Services in Echtzeit
- Suche nach: Name, Type, Keywords

**Drag & Drop (Phase 3):**
- User zieht Service aus Library auf Canvas
- Component erscheint an Drop-Position

---

## 4. Canvas (Hauptbereich)

### Phase 1 (MVP): Static Boxes

**Features:**
- Components als **Boxen** dargestellt
- **Keine Drag & Drop** (Position automatisch)
- **Kein Visual Connection** (nur implizit durch JSON)
- **Click to Select** → Properties Panel öffnet

**Layout:** CSS Grid (Auto-Placement)

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────┐   ┌─────────────┐     │
│  │    VPC      │   │   Subnet    │     │
│  │ 10.0.0.0/16 │   │ 10.0.1.0/24 │     │
│  └─────────────┘   └─────────────┘     │
│                                         │
│  ┌─────────────┐   ┌─────────────┐     │
│  │    EC2      │   │    RDS      │     │
│  │ t3.medium   │   │ PostgreSQL  │     │
│  │ ~$30/mo     │   │   ~$60/mo   │     │
│  └─────────────┘   └─────────────┘     │
│                                         │
│  ┌─────────────┐                        │
│  │     S3      │                        │
│  │   Bucket    │                        │
│  │  Encrypted  │                        │
│  └─────────────┘                        │
│                                         │
└─────────────────────────────────────────┘
```

**Component Box Design:**
```
┌───────────────────────────┐
│ [Icon] EC2                │ ← Service Type
│ web-server-1              │ ← Name
├───────────────────────────┤
│ t3.medium                 │ ← Key Config
│ Ubuntu 22.04              │
│ 20 GB gp3                 │
├───────────────────────────┤
│ 💰 ~$30.50/month          │ ← Cost
│ ✅ Healthy                 │ ← Status (optional)
└───────────────────────────┘
```

**States:**
- **Normal:** White/Dark Gray Background
- **Selected:** Blue Border + Blue Shadow
- **Error:** Red Border + Warning Icon
- **Hover:** Slight Elevation + Cursor Pointer

---

### Phase 2: Visual Connections

**Features:**
- **Boxes with Arrows** (SVG Lines)
- **Connection Types:** `network`, `accesses`, `triggers`, `depends_on`
- **Color-coded:** Network (Blue), Data (Green), Trigger (Orange)

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────┐                        │
│  │     VPC     │                        │
│  └──────┬──────┘                        │
│         │ (network)                     │
│         ↓                               │
│  ┌─────────────┐     ┌─────────────┐   │
│  │   Subnet    │────→│    EC2      │   │
│  │  Public     │     │ t3.medium   │   │
│  └─────────────┘     └──────┬──────┘   │
│                              │ (accesses)│
│                              ↓          │
│                       ┌─────────────┐   │
│                       │    RDS      │   │
│                       │ PostgreSQL  │   │
│                       └─────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Connection Rendering:**
- SVG Overlay Layer über Canvas
- Berechnung: Start Box (x,y) → End Box (x,y)
- Bezier Curves für schöne Bögen

---

### Phase 3: Drag & Drop + Auto-Layout

**Features:**
- **Drag & Drop:** User kann Boxen verschieben
- **Auto-Layout:** "Organize" Button → Automatisches Layout
- **Snap to Grid:** Boxen rasten ein (optional)
- **Zoom & Pan:** Canvas zoomen und verschieben

**Libraries:**
- **dagre.js** - Graph Layout Algorithmus
- **d3.js** - SVG Manipulation (optional)
- **Vanilla JS** - Custom Implementation (leichter)

---

## 5. Properties Panel (Rechte Sidebar)

### 5.1 Zustände

#### State 1: Nichts selektiert
```
┌─────────────────────────┐
│  Properties             │
├─────────────────────────┤
│                         │
│  [Icon]                 │
│                         │
│  Select a component     │
│  to view details        │
│                         │
│  Or add a new           │
│  component from the     │
│  library →              │
│                         │
└─────────────────────────┘
```

#### State 2: Component selektiert (Read-Only)
```
┌─────────────────────────┐
│  Properties             │
├─────────────────────────┤
│ [Icon] EC2 Instance     │
│                         │
│ Name:                   │
│ web-server-1            │
│                         │
│ Instance Type:          │
│ t3.medium (2 vCPU, 4GB) │
│                         │
│ AMI:                    │
│ Ubuntu 22.04 LTS        │
│                         │
│ Storage:                │
│ 20 GB gp3               │
│                         │
│ Network:                │
│ VPC: main-vpc           │
│ Subnet: public-subnet-1 │
│                         │
│ Cost Estimate:          │
│ 💰 $30.50/month         │
│                         │
│ [Edit] [Delete]         │
└─────────────────────────┘
```

#### State 3: Component in Edit Mode
```
┌─────────────────────────┐
│  Edit: EC2 Instance     │
├─────────────────────────┤
│                         │
│ Name: *                 │
│ ┌─────────────────────┐ │
│ │ web-server-1        │ │
│ └─────────────────────┘ │
│                         │
│ Instance Type: *        │
│ ┌─────────────────────┐ │
│ │ t3.medium        ▼ │ │
│ └─────────────────────┘ │
│ • 2 vCPU, 4 GB RAM      │
│ • ~$30/month            │
│                         │
│ AMI: *                  │
│ ┌─────────────────────┐ │
│ │ Ubuntu 22.04 LTS ▼ │ │
│ └─────────────────────┘ │
│                         │
│ Root Volume:            │
│ Size: [20] GB           │
│ Type: [gp3 ▼]           │
│                         │
│ [Advanced Settings ▼]   │
│                         │
│ ⚠️ Validation Errors:   │
│ • Key Pair missing      │
│                         │
│ [Cancel] [Save Changes] │
└─────────────────────────┘
```

### 5.2 Actions

**Edit Button:**
- Öffnet Inline Form im Properties Panel
- Oder: Öffnet Modal Wizard (je nach Komplexität)

**Delete Button:**
- Confirmation Dialog: "Delete web-server-1?"
- Prüft Dependencies: "This component is used by X other components"

**Duplicate Button (später):**
- Klont Component mit neuem Namen

**View JSON Button:**
- Zeigt Raw JSON für diesen Component
- Editierbar für Experten

---

## 6. Toolbar (Über Canvas)

```
┌──────────────────────────────────────────────────────────────┐
│ [View: ● Boxes  ○ Diagram  ○ JSON]  [Zoom: - 100% +]        │
│ [Organize Layout] [Validate All] [Cost: $120/mo] [Export ▼] │
└──────────────────────────────────────────────────────────────┘
```

### Actions

**View Modes:**
- **Boxes (Default):** Boxen ohne Connections
- **Diagram:** Boxen mit Visual Connections
- **JSON:** Raw JSON Editor (existing)

**Organize Layout:**
- Automatisches Layout mit dagre.js
- "Reset to Auto Layout"

**Validate All:**
- Validiert alle Components
- Zeigt Errors/Warnings in Overlay

**Cost Preview:**
- Summe aller Component Costs
- Click → öffnet Cost Breakdown Modal

**Export:**
- Download JSON
- Download Terraform (später)
- Download Diagram (PNG/SVG)

---

## 7. Workflows

### 7.1 Neue Architektur erstellen

1. User klickt "New Architecture"
2. Form: Name, Description, Provider, Region
3. Canvas ist leer → "Add your first component"
4. User klickt "EC2" in Component Library
5. EC2 Wizard öffnet sich (Modal)
6. User füllt 4 Steps aus
7. "Add Component" → EC2 erscheint im Canvas
8. Properties Panel zeigt EC2 Details
9. User wiederholt für weitere Components
10. "Save Architecture" → POST /api/architectures

### 7.2 Architektur bearbeiten

1. User wählt Architektur aus Liste
2. Builder lädt mit existierenden Components
3. User klickt auf EC2 Box
4. Properties Panel zeigt EC2 Details
5. User klickt "Edit"
6. Form wird editierbar
7. User ändert Instance Type
8. "Save Changes" → Component updated im JSON
9. "Save Architecture" → PUT /api/architectures/:id

### 7.3 Component löschen

1. User selektiert Component
2. User klickt "Delete" in Properties Panel
3. Confirmation Dialog:
   ```
   Delete "web-server-1"?

   ⚠️ Warning: This component is referenced by:
   • Security Group "web-sg"
   • Load Balancer "web-alb"

   [Cancel] [Delete Anyway]
   ```
4. User bestätigt
5. Component wird aus Canvas entfernt
6. JSON wird aktualisiert

### 7.4 Validation Workflow

1. User klickt "Validate All" in Toolbar
2. System validiert alle Components
3. Errors werden in Canvas angezeigt:
   - Red Border auf fehlerhaften Components
   - Error Icon mit Tooltip
4. Properties Panel zeigt Details:
   ```
   ⚠️ Validation Errors (3):

   • web-server-1:
     "Key Pair missing - you won't be able to SSH"

   • db-instance:
     "Storage must be at least 20 GB (current: 10 GB)"

   • web-sg:
     "SSH port 22 open to 0.0.0.0/0 (security risk!)"
   ```
5. User kann direkt zu Component springen und fixen

---

## 8. JSON View Integration

### 8.1 JSON View (Existing)

- Bleibt als separate View bestehen
- Toggle: "View: Boxes / JSON"
- JSON Editor mit Line Numbers (neu implementiert)

### 8.2 Sync zwischen Canvas und JSON

**Canvas → JSON:**
- User fügt EC2 hinzu → JSON wird generiert
- User editiert EC2 → JSON wird aktualisiert
- **Real-time Sync** (kein Save Button nötig für JSON Update)

**JSON → Canvas:**
- User editiert JSON direkt
- "Apply Changes" Button
- Canvas wird neu gerendert mit neuen Components

**Conflict Resolution:**
- Wenn JSON ungültig → Error anzeigen, Canvas nicht updaten
- Wenn JSON gültig aber nicht standard → Warning, aber erlaubt

---

## 9. Responsive Design

### Desktop (> 1280px)
- 3-Column Layout
- Component Library: 240px fixed
- Properties Panel: 360px fixed
- Canvas: flex-1

### Laptop (1024px - 1280px)
- Component Library: 200px
- Properties Panel: 300px
- Canvas: kleiner, aber nutzbar

### Tablet (768px - 1024px)
- Component Library: Collapsible (Hamburger)
- Canvas: Full Width
- Properties Panel: Slide-in Drawer

### Mobile (< 768px)
- Single Column Stacked
- Component Library: Bottom Sheet
- Canvas: Scrollable
- Properties: Full-Screen Modal

---

## 10. Technische Architektur

### 10.1 Component Structure

```
/frontend/src/js/
├── components/
│   ├── builder/
│   │   ├── component-library.js    # Sidebar mit Services
│   │   ├── canvas.js                # Canvas Rendering
│   │   ├── canvas-box.js            # Einzelne Component Box
│   │   ├── canvas-connections.js    # SVG Connections (Phase 2)
│   │   ├── properties-panel.js      # Properties Sidebar
│   │   ├── toolbar.js               # Canvas Toolbar
│   │   └── builder-layout.js        # Overall Layout Manager
│   ├── service-wizard/              # From aws-service-config-ui.md
│   │   ├── wizard-modal.js
│   │   ├── ec2-wizard.js
│   │   └── ...
│   └── ...
├── lib/
│   ├── canvas-layout.js             # Layout Engine (dagre.js wrapper)
│   ├── json-to-canvas.js            # JSON → Canvas Components
│   ├── canvas-to-json.js            # Canvas → JSON (validation)
│   └── ...
└── pages/
    └── architecture-builder.js      # Main Builder Page
```

### 10.2 State Management

**Approach: Event-Driven State (Vanilla JS)**

```javascript
// state.js - Simple Reactive State
class BuilderState {
  constructor() {
    this.architecture = null;
    this.selectedComponent = null;
    this.viewMode = 'boxes'; // boxes, diagram, json
    this.listeners = [];
  }

  setArchitecture(arch) {
    this.architecture = arch;
    this.notify('architecture', arch);
  }

  selectComponent(componentId) {
    this.selectedComponent = componentId;
    this.notify('selected', componentId);
  }

  addComponent(component) {
    this.architecture.architecture.components.push(component);
    this.notify('component-added', component);
  }

  updateComponent(componentId, updates) {
    const comp = this.architecture.architecture.components.find(c => c.id === componentId);
    Object.assign(comp, updates);
    this.notify('component-updated', comp);
  }

  deleteComponent(componentId) {
    const index = this.architecture.architecture.components.findIndex(c => c.id === componentId);
    this.architecture.architecture.components.splice(index, 1);
    this.notify('component-deleted', componentId);
  }

  subscribe(event, callback) {
    this.listeners.push({ event, callback });
  }

  notify(event, data) {
    this.listeners
      .filter(l => l.event === event)
      .forEach(l => l.callback(data));
  }
}

export const builderState = new BuilderState();
```

**Usage:**
```javascript
// component-library.js
import { builderState } from '../lib/state.js';

function addEC2Component(config) {
  const component = {
    id: generateId(),
    type: 'compute',
    provider_service: 'ec2',
    configuration: config
  };

  builderState.addComponent(component);
}

// canvas.js
import { builderState } from '../lib/state.js';

builderState.subscribe('component-added', (component) => {
  renderNewComponentBox(component);
});

builderState.subscribe('component-updated', (component) => {
  updateComponentBox(component);
});
```

### 10.3 Canvas Rendering

**Option A: Pure DOM (Vanilla JS)**
- Pro: Einfach, kein Framework
- Pro: Gut für statische Boxen (Phase 1)
- Con: Performance bei vielen Components

**Option B: Canvas API (HTML5 Canvas)**
- Pro: Bessere Performance bei vielen Elements
- Con: Komplexer, schwerer zu stylen
- Con: Accessibility schwieriger

**Option C: SVG**
- Pro: Vektorbasiert, skalierbar
- Pro: Gut für Connections
- Con: Performance bei sehr vielen Elements

**MVP Entscheidung: Option A (Pure DOM)**
- Einfacher für Phase 1
- Später: Hybrid (DOM Boxes + SVG Connections)

---

## 11. Animation & Transitions

### Component Hinzufügen
```css
@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.component-box.new {
  animation: fadeInScale 0.3s ease-out;
}
```

### Component Löschen
```css
@keyframes fadeOutScale {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.9);
  }
}

.component-box.deleting {
  animation: fadeOutScale 0.2s ease-in;
}
```

### Selection
```css
.component-box.selected {
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
  transition: all 0.15s ease;
}
```

---

## 12. Accessibility (WCAG 2.1 AA)

### Keyboard Navigation
- **Tab:** Navigate zwischen Components
- **Enter:** Select Component
- **Delete:** Delete Selected Component
- **Escape:** Deselect / Close Modal
- **Arrow Keys:** Navigate Canvas (wenn zoomed)

### Screen Reader Support
```html
<div
  class="component-box"
  role="button"
  tabindex="0"
  aria-label="EC2 Instance: web-server-1, t3.medium, $30 per month"
  aria-selected="false"
>
  <!-- Component Content -->
</div>
```

### Focus Indicators
- Klar sichtbarer Blue Outline bei Tab-Navigation
- Nicht durch CSS entfernen!

### Color Contrast
- Text: min. 4.5:1
- Icons: min. 3:1
- Borders: min. 3:1

---

## 13. Performance Optimierung

### Lazy Rendering
- Components außerhalb des Viewports nicht rendern
- Intersection Observer für virtuelles Scrolling

### Debouncing
- JSON Sync: Debounce 300ms
- Search: Debounce 200ms

### Memoization
- Canvas Layout nur neu berechnen wenn Components ändern
- Properties Panel nur re-rendern wenn Selection ändert

---

## 14. Testing Strategy

### Unit Tests (Vitest)
- State Management
- JSON ↔ Canvas Conversion
- Validation Logic

### Component Tests
- Component Box Rendering
- Properties Panel Forms
- Wizard Flows

### Integration Tests
- Add Component → erscheint im Canvas
- Edit Component → JSON aktualisiert
- Delete Component → Dependencies checked

### E2E Tests (Playwright)
- Complete User Flow: Create Architecture
- Complete User Flow: Edit Architecture
- Complete User Flow: Validate & Export

---

## 15. Implementation Roadmap

### Week 1-2: Foundation
- [ ] Builder Layout Component (3-Column)
- [ ] State Management (Event-Driven)
- [ ] Canvas Component (Pure DOM)
- [ ] Component Box Rendering

### Week 3-4: Component Library & Properties
- [ ] Component Library UI (Collapsible Sections)
- [ ] Properties Panel (Read-Only View)
- [ ] Properties Panel (Edit Mode)
- [ ] JSON ↔ Canvas Sync

### Week 5-6: Integration mit Service Wizards
- [ ] EC2 Wizard → Canvas Integration
- [ ] RDS Wizard → Canvas Integration
- [ ] S3 Form → Canvas Integration
- [ ] Security Group → Canvas Integration

### Week 7-8: Canvas Features
- [ ] Component Selection
- [ ] Component Deletion (mit Dependency Check)
- [ ] Validation UI (Red Borders, Tooltips)
- [ ] Cost Preview Toolbar

### Week 9-10: Polish & Testing
- [ ] Responsive Design (Tablet, Mobile)
- [ ] Keyboard Navigation
- [ ] Animations & Transitions
- [ ] E2E Tests
- [ ] Performance Optimierung

### Phase 2 (Later)
- [ ] Visual Connections (SVG Arrows)
- [ ] Drag & Drop (Components verschieben)
- [ ] Auto-Layout (dagre.js Integration)
- [ ] Zoom & Pan

---

## 16. Success Metrics

- ✅ **User can create architecture without touching JSON**
- ✅ **Visual representation of all components**
- ✅ **Edit components inline (no modal required for simple edits)**
- ✅ **Responsive on Tablet (usable, not perfect)**
- ✅ **Performance: < 100ms to add component**
- ✅ **Accessibility: WCAG 2.1 AA compliant**

---

## 17. Open Questions

1. **Canvas Initial State:**
   - Leerer Canvas mit "Add your first component" CTA?
   - Oder: VPC wird automatisch erstellt als Basis?

2. **Component Auto-Positioning (Phase 1):**
   - CSS Grid Auto-Flow?
   - Oder: Feste Reihenfolge (Compute → Database → Storage)?

3. **Connection Visualization (Phase 2):**
   - Nur explizite Relationships zeigen?
   - Oder: Auch implizite (z.B. EC2 in Subnet)?

4. **Mobile Strategy:**
   - Voll funktionsfähig auf Mobile?
   - Oder: "Best viewed on Desktop" Hinweis?

5. **Undo/Redo:**
   - Command Pattern für Undo/Redo?
   - Oder: Simple "Revert" Button?

---

## 18. Migration Plan (Alt → Neu)

### Phasenweiser Rollout

**Phase 0 (Current):**
- Nur JSON Editor

**Phase 1 (MVP):**
- Boxes + Properties Panel + Wizards
- JSON Editor bleibt als Fallback

**Phase 2:**
- Visual Connections hinzufügen
- JSON Editor wird sekundär

**Phase 3:**
- Drag & Drop aktivieren
- JSON Editor nur für Experten

**Keine Breaking Changes:**
- Alte Architekturen bleiben kompatibel
- JSON bleibt editierbar
- User können zwischen Views wechseln

---

## 19. Dependencies

### Required Libraries

**Zero Dependencies (MVP):**
- Alles Vanilla JS + Tailwind CSS
- Keine zusätzlichen Libraries

**Optional (Phase 2+):**
- **dagre.js** (7 KB) - Graph Layout
- **d3-zoom** (11 KB) - Zoom & Pan (optional)

### Warum Vanilla JS?

1. **Leichtgewichtig:** Keine React/Vue Overhead
2. **Performance:** Direkter DOM Access
3. **Lernkurve:** Einfacher für Onboarding
4. **Flexibilität:** Keine Framework Constraints
5. **OverCloud CLAUDE.md:** "Vanilla JS + Modern Tooling" ist definiert

---

## 20. Next Steps

1. **Review mit Andy** - Feedback zu diesem Design
2. **Wireframe/Prototype** - Figma oder HTML/CSS Mockup
3. **Technical Spike** - State Management testen
4. **Implementation Start** - Week 1-2 Tasks

---

**Status:** Ready for Review ✅
**Feedback:** TBD
**Estimated Effort:** 10 Wochen (2 Entwickler) oder 20 Wochen (1 Entwickler)
