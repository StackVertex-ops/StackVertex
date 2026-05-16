# Infrastructure Designer - Frontend Developer Guide

Entwickler-Dokumentation für den Infrastructure Designer.

---

## Übersicht

Der Infrastructure Designer ist eine Single-Page-Application (SPA) gebaut mit:
- **Vanilla JavaScript** (ES6+ Modules)
- **Vite** (Build Tool + Dev Server)
- **Cytoscape.js** (Graph Visualisierung)
- **Tailwind CSS** (Styling)

**Kein Framework:** Bewusste Entscheidung für maximale Performance und minimale Bundle-Size.

---

## File-Struktur

```
frontend/
├── src/
│   ├── js/
│   │   ├── components/
│   │   │   ├── InfrastructureCanvas.js      # Cytoscape Canvas
│   │   │   ├── ComponentPalette.js          # Draggable Palette
│   │   │   ├── ConfigurationTabs.js         # Tab-basierte Config (4 Tabs)
│   │   │   ├── TabSystem.js                 # Tab Management (alt, deprecated)
│   │   │   └── forms/
│   │   │       └── FormBuilder.js           # Dynamic Form Generator
│   │   ├── lib/
│   │   │   ├── ArchitectureState.js         # State Management
│   │   │   ├── SyncCoordinator.js           # Canvas ↔ Tabs Sync
│   │   │   └── utils.js                     # Helper Functions
│   │   ├── pages/
│   │   │   └── infrastructure-designer.js   # Page Controller
│   │   ├── demo/
│   │   │   └── sample-architecture.js       # Demo Data
│   │   └── main.js                          # Entry Point
│   ├── css/
│   │   ├── main.css                         # Tailwind Imports + Custom
│   │   └── components/
│   │       └── infrastructure-designer.css  # Designer-spezifisches CSS
│   └── infrastructure-designer.html         # HTML Template
├── public/
│   └── assets/                              # Static Assets
├── vite.config.js                           # Vite Configuration
├── tailwind.config.js                       # Tailwind Configuration
└── package.json                             # Dependencies
```

---

## Installation & Setup

### 1. Dependencies installieren

```bash
cd frontend
npm install
```

**Hauptabhängigkeiten:**
```json
{
  "dependencies": {
    "cytoscape": "^3.28.1"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

### 2. Dev Server starten

```bash
npm run dev
```

Server läuft auf: **http://localhost:5174**

### 3. Production Build

```bash
npm run build
```

Output: `dist/` Verzeichnis

---

## Component Architecture

### InfrastructureCanvas

**Datei:** `src/js/components/InfrastructureCanvas.js`

**Zweck:** Cytoscape.js Wrapper für Graph-Darstellung

**Initialisierung:**
```javascript
import { InfrastructureCanvas } from './components/InfrastructureCanvas.js';

const canvas = new InfrastructureCanvas(
  'canvas-container',  // DOM container ID
  onNodeClick,         // Callback: (componentId, type) => {...}
  onEdgeClick          // Callback: (edgeId, data) => {...}
);
```

**API:**
```javascript
// Add Component
canvas.addComponent({
  id: 'vpc-123',
  type: 'vpc',
  name: 'Main VPC',
  config: { cidr: '10.0.0.0/16' },
  position: { x: 400, y: 200 }
});

// Update Component
canvas.updateComponent('vpc-123', { cidr: '10.1.0.0/16' });

// Remove Component
canvas.removeComponent('vpc-123');

// Add Connection
canvas.addConnection('ec2-456', 'rds-789', {
  port: 5432,
  protocol: 'tcp'
});

// Layout
canvas.autoLayout();  // Breadthfirst layout
canvas.fit();         // Fit to viewport

// Export
const json = canvas.exportToJSON();
const png = canvas.exportImage();
```

**Node Styles:**
Definiert in Constructor (`init()` Methode):
```javascript
{
  selector: 'node[type="vpc"]',
  style: {
    'background-color': '#667eea',
    'label': 'data(label)',
    'width': 200,
    'height': 150,
    'shape': 'roundrectangle'
  }
}
```

**Neuen Component Type hinzufügen:**
1. Style in `init()` hinzufügen
2. Default Config in `generateDefaultConfig()` hinzufügen
3. Default Name in `generateDefaultName()` hinzufügen

---

### ComponentPalette

**Datei:** `src/js/components/ComponentPalette.js`

**Zweck:** Draggable Component Library

**Initialisierung:**
```javascript
const palette = new ComponentPalette('component-palette');
```

**Neuen Component Type hinzufügen:**

```javascript
// In render() Methode
<div class="palette-section mb-4">
  <h4 class="text-sm font-medium text-gray-700 mb-2">Network</h4>
  <div class="grid grid-cols-2 gap-2">
    ${this.renderComponent('vpc', 'VPC', '🌐')}
    ${this.renderComponent('subnet', 'Subnet', '📦')}
    
    <!-- NEUER TYPE -->
    ${this.renderComponent('route_table', 'Route Table', '🗺️')}
  </div>
</div>
```

**Drag & Drop:**
- `dragstart` setzt `dataTransfer.setData('componentType', type)`
- Canvas empfängt mit `drop` Event

---

### ConfigurationTabs

**Datei:** `src/js/components/ConfigurationTabs.js`

**Zweck:** 4 fixe Tabs (Network, Security, Data, Computing) mit Forms

**Initialisierung:**
```javascript
const tabs = new ConfigurationTabs(
  'tabs-container',
  (id, field, value) => { /* onComponentUpdate */ },
  (id) => { /* onComponentDelete */ }
);

tabs.setComponents([
  { id: 'vpc-1', type: 'vpc', name: 'Main VPC', config: {...} },
  { id: 'ec2-1', type: 'ec2', name: 'Web Server', config: {...} }
]);
```

**Neue Component Form hinzufügen:**

```javascript
// In renderComponentForm(component)
switch (component.type) {
  case 'vpc':
    return this.renderVPCForm(component);
  case 'subnet':
    return this.renderSubnetForm(component);
    
  // NEUER TYPE
  case 'route_table':
    return this.renderRouteTableForm(component);
    
  default:
    return this.renderGenericForm(component);
}

// Neue Methode
renderRouteTableForm(component) {
  return `
    <div class="component-form bg-white border border-gray-200 rounded-lg p-6">
      <h3>${component.name}</h3>
      
      <!-- VPC Auswahl -->
      <div>
        <label>VPC</label>
        <select onchange="updateComponent('${component.id}', 'vpcId', this.value)">
          ${this.components.network
            .filter(c => c.type === 'vpc')
            .map(vpc => `<option value="${vpc.id}">${vpc.name}</option>`)
            .join('')}
        </select>
      </div>
      
      <!-- Routes -->
      <div>
        <label>Routes</label>
        <!-- Route Table hier -->
      </div>
    </div>
  `;
}
```

**IP Calculator (Inline):**
```javascript
calculateIPInfo(cidr) {
  const [ip, prefix] = cidr.split('/');
  const prefixNum = parseInt(prefix);
  const total = Math.pow(2, 32 - prefixNum);
  const usable = Math.max(0, total - 5); // AWS reserves 5
  
  // ... berechne firstIP, lastIP, reserved
  
  return { total, usable, firstIP, lastIP, reserved };
}
```

**Live-Update:**
```html
<input
  type="text"
  value="${cidr}"
  oninput="updateVPCCIDR('${component.id}', this.value)"
/>
<div class="inline-ip-info">
  Total IPs: ${ipInfo.total}
  Usable: ${ipInfo.usable}
</div>
```

---

### ArchitectureState

**Datei:** `src/js/lib/ArchitectureState.js`

**Zweck:** JSON State Management + Undo/Redo

**Struktur:**
```javascript
{
  version: "1.0.0",
  metadata: { name, description, provider, region },
  components: { "vpc-123": {...}, "ec2-456": {...} },
  connections: [ {from, to, data} ],
  ipAllocations: { "ec2-456": {ip, subnetId} }
}
```

**API:**
```javascript
// Add
state.addComponent(component);
state.addConnection(from, to, data);

// Update
state.updateComponent(id, updates);

// Remove
state.removeComponent(id);
state.removeConnection(id);

// Export/Import
const json = state.exportJSON();
state.loadJSON(json);

// Undo/Redo
state.undo();
state.redo();
```

**Undo/Redo Implementation:**
```javascript
class ArchitectureState {
  constructor() {
    this.state = { components: {}, connections: [] };
    this.history = [];
    this.historyIndex = -1;
    this.maxHistory = 50;
  }
  
  saveToHistory() {
    // Remove future states if we're not at the end
    this.history = this.history.slice(0, this.historyIndex + 1);
    
    // Add current state
    this.history.push(JSON.parse(JSON.stringify(this.state)));
    
    // Limit history size
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    } else {
      this.historyIndex++;
    }
  }
  
  undo() {
    if (this.historyIndex > 0) {
      this.historyIndex--;
      this.state = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
      this.notifyListeners();
    }
  }
  
  redo() {
    if (this.historyIndex < this.history.length - 1) {
      this.historyIndex++;
      this.state = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
      this.notifyListeners();
    }
  }
}
```

---

### SyncCoordinator

**Datei:** `src/js/lib/SyncCoordinator.js`

**Zweck:** Event-Router für Canvas ↔ Tabs ↔ State Sync

**Event Flow:**
```
User Action (Drag, Click, Edit)
    ↓
Component Event ('component-added', 'component-updated', etc.)
    ↓
SyncCoordinator routes event
    ↓
Update State + notify other components
    ↓
Canvas + Tabs re-render
```

**Events:**
```javascript
// Component added via Drag & Drop
window.dispatchEvent(new CustomEvent('component-added', {
  detail: { component }
}));

// Component updated via Tab Form
window.dispatchEvent(new CustomEvent('component-updated', {
  detail: { componentId, updates }
}));

// Component position changed (Canvas Drag)
window.dispatchEvent(new CustomEvent('component-position-changed', {
  detail: { componentId, position }
}));

// Component deleted
window.dispatchEvent(new CustomEvent('component-deleted', {
  detail: { componentId }
}));
```

**Global Listeners:**
```javascript
// In InfrastructureDesignerPage
attachGlobalListeners() {
  window.addEventListener('component-added', (e) => {
    const { component } = e.detail;
    this.architectureState.components[component.id] = component;
    this.tabs.openTab(component);
  });
  
  window.addEventListener('component-updated', (e) => {
    const { componentId, updates } = e.detail;
    this.canvas.updateComponent(componentId, updates);
    Object.assign(
      this.architectureState.components[componentId].config,
      updates
    );
  });
}
```

---

## Neuen Component Type hinzufügen

**Schritt-für-Schritt:**

### 1. Canvas Style definieren

In `InfrastructureCanvas.js` → `init()` Methode:

```javascript
// Route Table Node Style
{
  selector: 'node[type="route_table"]',
  style: {
    'background-color': '#10B981',
    'label': 'data(label)',
    'color': '#fff',
    'width': 120,
    'height': 70,
    'shape': 'roundrectangle',
    'border-width': 2,
    'border-color': '#059669',
    'font-size': '11px'
  }
}
```

### 2. Default Config hinzufügen

In `InfrastructureCanvas.js` → `generateDefaultConfig()`:

```javascript
generateDefaultConfig(type) {
  const configs = {
    vpc: { cidr: '10.0.0.0/16', ... },
    subnet: { cidr: '10.0.1.0/24', ... },
    
    // NEU
    route_table: {
      vpcId: null,
      routes: [
        { destination: '0.0.0.0/0', target: 'igw-id' }
      ]
    }
  };
  return configs[type] || {};
}
```

### 3. Default Name hinzufügen

In `InfrastructureCanvas.js` → `generateDefaultName()`:

```javascript
generateDefaultName(type) {
  const names = {
    vpc: 'VPC',
    subnet: 'Subnet',
    route_table: 'Route Table'  // NEU
  };
  return `${names[type] || type} ${count}`;
}
```

### 4. Palette Entry hinzufügen

In `ComponentPalette.js` → `render()`:

```javascript
<div class="palette-section mb-4">
  <h4 class="text-sm font-medium text-gray-700 mb-2">Network</h4>
  <div class="grid grid-cols-2 gap-2">
    ${this.renderComponent('vpc', 'VPC', '🌐')}
    ${this.renderComponent('subnet', 'Subnet', '📦')}
    ${this.renderComponent('route_table', 'Route Table', '🗺️')}  <!-- NEU -->
  </div>
</div>
```

### 5. Tab Category zuordnen

In `ConfigurationTabs.js` → `getComponentCategory()`:

```javascript
getComponentCategory(type) {
  const categories = {
    vpc: 'network',
    subnet: 'network',
    route_table: 'network',  // NEU
    ec2: 'computing',
    ...
  };
  return categories[type] || 'network';
}
```

### 6. Form erstellen

In `ConfigurationTabs.js` → `renderComponentForm()`:

```javascript
renderComponentForm(component) {
  switch (component.type) {
    case 'vpc':
      return this.renderVPCForm(component);
    case 'route_table':  // NEU
      return this.renderRouteTableForm(component);
    default:
      return this.renderGenericForm(component);
  }
}
```

Neue Methode hinzufügen:

```javascript
renderRouteTableForm(component) {
  return `
    <div class="component-form bg-white border border-gray-200 rounded-lg p-6">
      <div class="flex justify-between items-start mb-6">
        <div class="flex items-center gap-3">
          <div class="text-3xl">🗺️</div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">
              ${component.name || 'Route Table'}
            </h3>
            <p class="text-xs text-gray-500">VPC Route Table</p>
          </div>
        </div>
        <button
          class="text-red-600 hover:text-red-700"
          onclick="deleteComponent('${component.id}')"
        >
          Löschen
        </button>
      </div>
      
      <div class="space-y-5">
        <!-- Name -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Route Table Name
          </label>
          <input
            type="text"
            value="${component.name || ''}"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg"
            onchange="updateComponent('${component.id}', 'name', this.value)"
          />
        </div>
        
        <!-- VPC -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            VPC
          </label>
          <select
            class="w-full px-4 py-2 border border-gray-300 rounded-lg"
            onchange="updateComponent('${component.id}', 'vpcId', this.value)"
          >
            <option value="">VPC auswählen...</option>
            ${this.components.network
              .filter(c => c.type === 'vpc')
              .map(vpc => `
                <option value="${vpc.id}" ${component.config?.vpcId === vpc.id ? 'selected' : ''}>
                  ${vpc.name}
                </option>
              `).join('')}
          </select>
        </div>
        
        <!-- Routes -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Routes
          </label>
          <div class="space-y-2">
            ${(component.config?.routes || []).map((route, i) => `
              <div class="flex gap-2">
                <input
                  type="text"
                  value="${route.destination}"
                  placeholder="0.0.0.0/0"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg font-mono"
                />
                <input
                  type="text"
                  value="${route.target}"
                  placeholder="igw-xxxxx"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            `).join('')}
          </div>
          <button class="mt-2 text-sm text-purple-600 hover:text-purple-700">
            + Add Route
          </button>
        </div>
      </div>
    </div>
  `;
}
```

### 7. Backend Template erstellen

Erstelle `backend/templates/terraform/components/route_table.tf.j2`:

```jinja2
# ============================================================================
# Route Table Resources
# ============================================================================

{% for component in components %}
resource "aws_route_table" "{{ component.id | replace('-', '_') }}" {
  vpc_id = aws_vpc.{{ component.config.vpcId | replace('-', '_') }}.id

  {% for route in component.config.routes %}
  route {
    cidr_block = "{{ route.destination }}"
    gateway_id = aws_internet_gateway.{{ route.target | replace('-', '_') }}.id
  }
  {% endfor %}

  tags = {
    Name = "{{ component.name }}"
  }
}
{% endfor %}
```

### 8. Generator Support hinzufügen

In `backend/app/services/terraform_generator_v2.py` → `supported_types`:

```python
self.supported_types = {
    'vpc', 'subnet', 'ec2', 'rds', 's3',
    'route_table'  # NEU
}
```

**Fertig!** Der neue Component Type ist jetzt voll integriert.

---

## Testing

### Unit Tests (Vitest)

```bash
npm run test
```

**Beispiel Test:**
```javascript
// tests/InfrastructureCanvas.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { InfrastructureCanvas } from '../src/js/components/InfrastructureCanvas';

describe('InfrastructureCanvas', () => {
  let canvas;
  
  beforeEach(() => {
    document.body.innerHTML = '<div id="test-canvas"></div>';
    canvas = new InfrastructureCanvas('test-canvas');
  });
  
  it('should add component to canvas', () => {
    const component = {
      id: 'vpc-123',
      type: 'vpc',
      name: 'Test VPC',
      config: { cidr: '10.0.0.0/16' },
      position: { x: 100, y: 100 }
    };
    
    canvas.addComponent(component);
    
    expect(canvas.components.size).toBe(1);
    expect(canvas.cy.nodes().length).toBe(1);
  });
  
  it('should update component', () => {
    const component = { id: 'vpc-123', type: 'vpc', ... };
    canvas.addComponent(component);
    
    canvas.updateComponent('vpc-123', { cidr: '10.1.0.0/16' });
    
    const node = canvas.cy.getElementById('vpc-123');
    expect(node.data('cidr')).toBe('10.1.0.0/16');
  });
});
```

### E2E Tests (Playwright)

```bash
npm run test:e2e
```

**Beispiel Test:**
```javascript
// tests/e2e/designer.spec.js
import { test, expect } from '@playwright/test';

test('should design VPC with EC2', async ({ page }) => {
  await page.goto('/infrastructure-designer.html');
  
  // Drag VPC from palette
  await page.dragAndDrop(
    '[data-component-type="vpc"]',
    '#canvas-container',
    { targetPosition: { x: 400, y: 200 } }
  );
  
  // Verify node was added
  await expect(page.locator('.cy-node[type="vpc"]')).toBeVisible();
  
  // Open Network tab
  await page.click('button[data-tab="network"]');
  
  // Configure VPC
  await page.fill('input[name="cidr"]', '10.0.0.0/16');
  
  // Verify IP Calculator
  await expect(page.locator('.inline-ip-info')).toContainText('65,536');
});
```

---

## Styling

### Tailwind Utility Classes

**Layout:**
```html
<div class="flex items-center justify-between gap-4">
  <div class="flex-1">Content</div>
  <button class="px-4 py-2">Button</button>
</div>
```

**Forms:**
```html
<input class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500" />
```

**Cards:**
```html
<div class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
  Card Content
</div>
```

### Custom CSS

In `src/css/components/infrastructure-designer.css`:

```css
/* Canvas Container */
#canvas-container {
  width: 100%;
  height: 600px;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #f9fafb;
}

/* Palette Component */
.palette-component {
  @apply flex flex-col items-center gap-2 p-3 border border-gray-300 rounded-lg cursor-move hover:bg-gray-50 transition;
}

/* Component Form Highlight (bei Click) */
.component-form.highlight {
  @apply ring-2 ring-purple-500 transition-all duration-500;
}
```

---

## Performance Tips

### 1. Debounce Input Events

```javascript
let debounceTimer;
input.addEventListener('input', (e) => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    updateComponent(id, field, e.target.value);
  }, 300);
});
```

### 2. Batch Canvas Updates

```javascript
// Schlecht: 100 einzelne Updates
components.forEach(comp => canvas.addComponent(comp));

// Gut: Batch-Update
canvas.cy.batch(() => {
  components.forEach(comp => canvas.addComponent(comp));
});
```

### 3. Virtualize Large Lists

Für >100 Components:
```javascript
// Use Virtual Scrolling Library (z.B. react-window für Tabs)
// Oder Pagination: Zeige nur sichtbare Components
```

---

## Debugging

### Browser Console

```javascript
// Global verfügbar machen für Debugging
window.debugCanvas = canvas;
window.debugState = architectureState;

// In Console:
debugCanvas.cy.nodes().length  // Anzahl Nodes
debugState.exportJSON()         // Current State
```

### Cytoscape Debugging

```javascript
// Alle Nodes loggen
canvas.cy.nodes().forEach(node => {
  console.log(node.id(), node.data());
});

// Alle Edges loggen
canvas.cy.edges().forEach(edge => {
  console.log(edge.id(), edge.data());
});

// Layout-Probleme debuggen
canvas.cy.layout({ name: 'breadthfirst' }).run();
```

---

## Build & Deployment

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

Output: `dist/` Verzeichnis

### Preview Production Build

```bash
npm run preview
```

### Vite Config

`vite.config.js`:
```javascript
import { defineConfig } from 'vite';

export default defineConfig({
  root: 'src',
  build: {
    outDir: '../dist',
    rollupOptions: {
      input: {
        main: 'src/infrastructure-designer.html'
      }
    }
  },
  server: {
    port: 5174,
    proxy: {
      '/api': 'http://localhost:8000'  // Backend Proxy
    }
  }
});
```

---

## Weitere Ressourcen

- [Cytoscape.js Dokumentation](https://js.cytoscape.org/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vite Guide](https://vitejs.dev/guide/)
- [Architecture Overview](../docs/infrastructure-designer-architecture.md)
- [User Guide](../docs/infrastructure-designer-guide.md)

---

**Happy Coding!**
