# Infrastructure Designer - Architecture

Technische Dokumentation der Systemarchitektur des Infrastructure Designers.

---

## System Overview

```
┌─────────────────────────────────────────────────────┐
│         Frontend (Vite + Vanilla JS)                │
│                                                      │
│  ┌──────────────────┐  ┌───────────────────────┐   │
│  │  Canvas          │  │  Configuration Tabs   │   │
│  │  (Cytoscape.js)  │  │  (4 Tabs: N/S/D/C)   │   │
│  │                  │  │  - Forms              │   │
│  │  - Drag & Drop   │  │  - IP Calculator      │   │
│  │  - Node Rendering│  │  - Validation         │   │
│  │  - Edges         │  │                       │   │
│  └────────┬─────────┘  └───────────┬───────────┘   │
│           │                        │               │
│           └────────────┬───────────┘               │
│                        │                           │
│           ┌────────────▼──────────────┐            │
│           │  SyncCoordinator          │            │
│           │  (Event Router)           │            │
│           └────────────┬──────────────┘            │
│                        │                           │
│           ┌────────────▼──────────────┐            │
│           │  ArchitectureState        │            │
│           │  (JSON Source of Truth)   │            │
│           │  - Components             │            │
│           │  - Connections            │            │
│           │  - Undo/Redo History      │            │
│           └────────────┬──────────────┘            │
│                        │                           │
└────────────────────────┼───────────────────────────┘
                         │ HTTP POST /api/v1/terraform/generate-from-json
┌────────────────────────▼───────────────────────────┐
│         Backend (FastAPI)                          │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  TerraformGeneratorV2                    │     │
│  │  (Jinja2 Template Engine)                │     │
│  │  - Component-based Generation            │     │
│  │  - Dependency Resolution                 │     │
│  │  - Validation                            │     │
│  └──────────────┬───────────────────────────┘     │
│                 │                                  │
│                 ▼                                  │
│         ┌───────────────┐                          │
│         │  .tf Files    │                          │
│         │  (main.tf,    │                          │
│         │   vpc.tf,     │                          │
│         │   ec2.tf,     │                          │
│         │   outputs.tf) │                          │
│         └───────────────┘                          │
└─────────────────────────────────────────────────────┘
```

---

## Frontend Components

### 1. InfrastructureCanvas

**Datei:** `frontend/src/js/components/InfrastructureCanvas.js`

**Zweck:** Visuelle Graph-Darstellung mit Cytoscape.js

**Features:**
- Cytoscape.js Integration
- Node Rendering (VPC, EC2, RDS, S3, Lambda, etc.)
- Edge Rendering (Connections)
- Drag & Drop Target
- Click Events → Tab öffnen
- Export als PNG
- Auto-Layout (Breadthfirst)
- Fit to Viewport

**Node Styles:**
```javascript
{
  selector: 'node[type="vpc"]',
  style: {
    'background-color': '#667eea',
    'width': 200,
    'height': 150,
    'shape': 'roundrectangle',
    'label': 'data(label)'
  }
}
```

**API:**
```javascript
canvas.addComponent(component)          // Add node
canvas.updateComponent(id, updates)     // Update node
canvas.removeComponent(id)              // Remove node
canvas.addConnection(from, to, data)    // Add edge
canvas.loadFromJSON(json)               // Load architecture
canvas.exportToJSON()                   // Export architecture
canvas.exportImage()                    // PNG export
canvas.autoLayout()                     // Auto-arrange nodes
canvas.fit()                            // Fit to viewport
```

**Events:**
- `tap node` → `onNodeClick(componentId, type)`
- `tap edge` → `onEdgeClick(edgeId, data)`
- `dragfree node` → Update position in state

---

### 2. ComponentPalette

**Datei:** `frontend/src/js/components/ComponentPalette.js`

**Zweck:** Draggable AWS-Komponenten

**Kategorien:**
1. **Network:** VPC, Subnet, IGW, NAT
2. **Compute:** EC2, Lambda, ECS, ALB
3. **Data:** RDS, DynamoDB, S3, ElastiCache
4. **Security:** Security Group, NACL, IAM

**Drag & Drop:**
```javascript
comp.addEventListener('dragstart', (e) => {
  e.dataTransfer.setData('componentType', type);
  e.dataTransfer.effectAllowed = 'copy';
});
```

**Canvas empfängt:**
```javascript
canvas.addEventListener('drop', (e) => {
  const type = e.dataTransfer.getData('componentType');
  const component = createComponent(type, position);
  addToCanvas(component);
});
```

---

### 3. ConfigurationTabs

**Datei:** `frontend/src/js/components/ConfigurationTabs.js`

**Zweck:** Tab-basierte Konfiguration mit Inline IP Calculator

**4 Tabs:**
1. **Network** - VPC, Subnet, IGW, NAT, Route Tables
2. **Security** - Security Groups, NACLs, IAM Roles
3. **Data** - RDS, DynamoDB, S3, ElastiCache
4. **Computing** - EC2, Lambda, ECS, ALB

**Forms:**
- VPC Form: CIDR + Inline IP Calculator
- Subnet Form: CIDR + Inline IP Calculator + Type
- EC2 Form: Instance Type + IP Assignment (Auto/Manual)
- RDS Form: Engine + Instance Class + Multi-AZ

**IP Calculator (Inline):**
```javascript
calculateIPInfo(cidr) {
  const [ip, prefix] = cidr.split('/');
  const total = Math.pow(2, 32 - prefix);
  const usable = total - 5; // AWS reserves 5
  
  return {
    total,
    usable,
    firstIP,
    lastIP,
    reserved: [ip, ip+1, ip+2, ip+3, lastIP]
  };
}
```

**Anzeige:**
```html
<div class="inline-ip-info">
  Total IPs: 65,536
  Usable: 65,531
  Range: 10.0.0.0 - 10.0.255.255
  Reserved: .0, .1, .2, .3, .255
</div>
```

**API:**
```javascript
tabs.setComponents(components)          // Update all tabs
tabs.openComponent(id, type)            // Open specific tab
tabs.updateComponent(id, field, value)  // Update component
tabs.deleteComponent(id)                // Delete component
```

---

### 4. TabSystem

**Datei:** `frontend/src/js/components/TabSystem.js`

**Zweck:** Tab-Verwaltung für einzelne Komponenten (alte Version, wird von ConfigurationTabs abgelöst)

**Features:**
- Tab Header Management
- Tab Content Rendering
- Tab Closing
- Active Tab Highlighting

**Hinweis:** In aktueller Version wird `ConfigurationTabs` bevorzugt (4 fixe Tabs nach Kategorie).

---

### 5. ArchitectureState

**Datei:** `frontend/src/js/lib/ArchitectureState.js`

**Zweck:** Zentrale State-Verwaltung (JSON as Source of Truth)

**State Schema:**
```json
{
  "version": "1.0.0",
  "metadata": {
    "id": "arch-123",
    "name": "production-architecture",
    "description": "Production Infrastructure",
    "provider": "aws",
    "createdAt": "2026-05-16T10:00:00Z",
    "updatedAt": "2026-05-16T11:30:00Z"
  },
  "components": {
    "vpc-abc123": {
      "id": "vpc-abc123",
      "type": "vpc",
      "name": "main-vpc",
      "config": {
        "cidr": "10.0.0.0/16",
        "region": "us-east-1",
        "enableDnsHostnames": true,
        "enableDnsSupport": true
      },
      "position": { "x": 400, "y": 200 }
    },
    "subnet-def456": {
      "id": "subnet-def456",
      "type": "subnet",
      "name": "public-subnet-1a",
      "config": {
        "vpcId": "vpc-abc123",
        "cidr": "10.0.1.0/24",
        "subnetType": "public",
        "az": "us-east-1a",
        "mapPublicIpOnLaunch": true
      },
      "position": { "x": 350, "y": 350 }
    },
    "ec2-ghi789": {
      "id": "ec2-ghi789",
      "type": "ec2",
      "name": "web-server-1",
      "config": {
        "instanceType": "t3.small",
        "ami": "ami-0c55b159cbfafe1f0",
        "subnetId": "subnet-def456",
        "ipMode": "manual",
        "privateIP": "10.0.1.15",
        "assignPublicIP": true,
        "publicIP": null,
        "securityGroupIds": ["sg-123"]
      },
      "position": { "x": 350, "y": 500 }
    }
  },
  "connections": [
    {
      "id": "conn-1",
      "from": "ec2-ghi789",
      "to": "rds-jkl012",
      "data": {
        "port": 5432,
        "protocol": "tcp",
        "description": "EC2 → RDS"
      }
    }
  ],
  "ipAllocations": {
    "ec2-ghi789": {
      "ip": "10.0.1.15",
      "subnetId": "subnet-def456",
      "allocatedAt": "2026-05-16T10:15:00Z"
    }
  }
}
```

**API:**
```javascript
state.addComponent(component)           // Add component
state.updateComponent(id, updates)      // Update component
state.removeComponent(id)               // Remove component
state.addConnection(from, to, data)     // Add connection
state.exportJSON()                      // Export state
state.loadJSON(json)                    // Load state
state.undo()                            // Undo last change
state.redo()                            // Redo last change
```

**Undo/Redo:**
```javascript
class ArchitectureState {
  constructor() {
    this.history = [];
    this.historyIndex = -1;
  }
  
  undo() {
    if (this.historyIndex > 0) {
      this.historyIndex--;
      this.restoreFromHistory();
    }
  }
  
  redo() {
    if (this.historyIndex < this.history.length - 1) {
      this.historyIndex++;
      this.restoreFromHistory();
    }
  }
}
```

---

### 6. SyncCoordinator

**Datei:** `frontend/src/js/lib/SyncCoordinator.js`

**Zweck:** Bidirektionale Synchronisation (Canvas ↔ Tabs ↔ State)

**Event Flow:**

```
User drags VPC from Palette
    ↓
Canvas.drop event
    ↓
SyncCoordinator.handleComponentDrop()
    ↓
ArchitectureState.addComponent()
    ↓
State.dispatchEvent('component-added')
    ↓
Canvas.addComponent() + Tabs.openTab()
```

**Update Flow:**

```
User changes CIDR in Tab
    ↓
ConfigurationTabs.updateComponent()
    ↓
ArchitectureState.updateComponent()
    ↓
State.dispatchEvent('component-updated')
    ↓
Canvas.updateComponent() (Label + Node data)
```

**Events:**
- `component-added` - Komponente hinzugefügt
- `component-updated` - Komponente geändert
- `component-deleted` - Komponente gelöscht
- `component-position-changed` - Position geändert (Drag)
- `connection-added` - Verbindung hinzugefügt
- `connection-deleted` - Verbindung gelöscht

**API:**
```javascript
coordinator.init(canvas, tabs, state)   // Initialize
coordinator.handleComponentDrop(e)      // Handle drop
coordinator.handleNodeClick(id)         // Handle click
coordinator.syncCanvasToState()         // Sync canvas → state
coordinator.syncStateToCanvas()         // Sync state → canvas
```

---

### 7. InfrastructureDesignerPage

**Datei:** `frontend/src/js/pages/infrastructure-designer.js`

**Zweck:** Page Controller (koordiniert alle Komponenten)

**Initialisierung:**
```javascript
class InfrastructureDesignerPage {
  constructor() {
    this.canvas = new InfrastructureCanvas(...);
    this.palette = new ComponentPalette(...);
    this.tabs = new TabSystem(...);
    
    this.attachToolbarListeners();
    this.attachGlobalListeners();
    this.loadArchitecture();
  }
}
```

**Toolbar:**
- Auto Layout Button
- Fit to View Button
- Export Image Button
- Delete Button
- Save Button

**Global Event Listeners:**
- `component-added` - Update state
- `component-updated` - Update canvas + state
- `component-position-changed` - Update state
- Keyboard Shortcuts:
  - `Delete` / `Backspace` - Delete selected
  - `Ctrl/Cmd + S` - Save
  - `Ctrl/Cmd + Z` - Undo

**Save Flow:**
```javascript
saveArchitecture() {
  const json = this.canvas.exportToJSON();
  this.architectureState = json;
  
  // Save to localStorage (draft)
  localStorage.setItem('architecture-draft', JSON.stringify(json));
  
  // Save to API (if has ID)
  if (this.architectureState.id) {
    await this.saveToAPI();
  }
}
```

---

## Backend Components

### 1. TerraformGeneratorV2

**Datei:** `backend/app/services/terraform_generator_v2.py`

**Zweck:** Terraform HCL-Generierung aus Architecture JSON

**Features:**
- Component-based Generation
- Jinja2 Templates
- Dependency Resolution
- Validation

**Flow:**
```python
def generate(architecture_json: Dict) -> Dict[str, str]:
    """
    Input: Architecture JSON
    Output: {
        'main.tf': '...',
        'variables.tf': '...',
        'vpc.tf': '...',
        'ec2.tf': '...',
        'outputs.tf': '...'
    }
    """
    files = {}
    
    # 1. Generate main.tf
    files['main.tf'] = self._generate_main_tf(architecture_json)
    
    # 2. Generate variables.tf
    files['variables.tf'] = self._generate_variables_tf(architecture_json)
    
    # 3. Group components by type
    components_by_type = self._group_components_by_type(
        architecture_json['components']
    )
    
    # 4. Generate component-specific .tf files
    for comp_type, comps in components_by_type.items():
        files[f'{comp_type}.tf'] = self._generate_component_file(
            comp_type, comps, architecture_json
        )
    
    # 5. Generate outputs.tf
    files['outputs.tf'] = self._generate_outputs_tf(
        architecture_json['components']
    )
    
    return files
```

**Template System:**
```
backend/templates/terraform/
├── components/
│   ├── main.tf.j2
│   ├── variables.tf.j2
│   ├── outputs.tf.j2
│   ├── vpc.tf.j2
│   ├── subnet.tf.j2
│   ├── ec2.tf.j2
│   ├── rds.tf.j2
│   ├── s3.tf.j2
│   └── ...
```

**Jinja2 Template Beispiel (vpc.tf.j2):**
```jinja2
# ============================================================================
# VPC Resources
# ============================================================================

{% for component in components %}
resource "aws_vpc" "{{ component.id | replace('-', '_') }}" {
  cidr_block           = "{{ component.config.cidr }}"
  enable_dns_hostnames = {{ component.config.enableDnsHostnames | lower }}
  enable_dns_support   = {{ component.config.enableDnsSupport | lower }}

  tags = {
    Name = "{{ component.name }}"
  }
}
{% endfor %}
```

**Dependency Resolution:**
```python
def _resolve_dependencies(components: Dict) -> List[str]:
    """
    Resolve component dependencies for correct Terraform ordering.
    
    Example:
      VPC → Subnet → EC2
      VPC must be created before Subnet
      Subnet must be created before EC2
    """
    graph = DependencyGraph()
    
    for comp_id, comp in components.items():
        graph.add_node(comp_id)
        
        # Subnet depends on VPC
        if comp['type'] == 'subnet' and comp['config'].get('vpcId'):
            graph.add_edge(comp['config']['vpcId'], comp_id)
        
        # EC2 depends on Subnet
        if comp['type'] == 'ec2' and comp['config'].get('subnetId'):
            graph.add_edge(comp['config']['subnetId'], comp_id)
    
    return graph.topological_sort()
```

---

### 2. API Endpoints

**Datei:** `backend/app/api/v1/terraform.py`

#### POST /api/v1/terraform/generate-from-json

**Input:**
```json
{
  "version": "1.0.0",
  "metadata": { "name": "production", "provider": "aws" },
  "components": { ... },
  "connections": [ ... ]
}
```

**Output:**
```json
{
  "success": true,
  "files": {
    "main.tf": "terraform { ... }",
    "vpc.tf": "resource \"aws_vpc\" { ... }",
    "ec2.tf": "resource \"aws_instance\" { ... }"
  },
  "metadata": {
    "component_count": 5,
    "connection_count": 2,
    "generated_at": "2026-05-16T12:00:00Z"
  }
}
```

**Fehlerbehandlung:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CIDR",
    "message": "VPC CIDR '10.0.0.0/33' is invalid",
    "component_id": "vpc-123"
  }
}
```

---

## Data Flow

### Adding a Component

```
1. User drags VPC from Palette
   ↓
2. Canvas receives 'drop' event
   ↓
3. Canvas.setupDropZone() extracts componentType
   ↓
4. Generate component with default config:
   {
     id: 'vpc-1647892345678',
     type: 'vpc',
     name: 'VPC 1',
     config: { cidr: '10.0.0.0/16', ... },
     position: { x: 400, y: 200 }
   }
   ↓
5. Canvas.addComponent(component)
   → Cytoscape adds node
   ↓
6. Dispatch 'component-added' event
   ↓
7. Page Controller updates ArchitectureState
   ↓
8. Tabs.openTab(component)
   → Opens Network tab + renders form
```

### Updating a Component

```
1. User changes VPC CIDR in Tab: '10.0.0.0/16' → '10.1.0.0/16'
   ↓
2. Input 'oninput' event triggers updateVPCCIDR()
   ↓
3. ConfigurationTabs.updateComponent(id, 'cidr', '10.1.0.0/16')
   ↓
4. Calculate new IP info inline:
   Total IPs: 65,536
   Usable: 65,531
   ↓
5. Dispatch 'component-updated' event
   ↓
6. Page Controller:
   - Updates ArchitectureState
   - Calls Canvas.updateComponent()
   ↓
7. Canvas updates node label:
   "VPC 1\n10.1.0.0/16"
   ↓
8. State saved to localStorage (auto-draft)
```

### Generating Terraform

```
1. User clicks "Save" button
   ↓
2. Page.saveArchitecture()
   ↓
3. Canvas.exportToJSON() returns:
   {
     components: { ... },
     connections: [ ... ]
   }
   ↓
4. Save to localStorage as draft
   ↓
5. POST to /api/v1/terraform/generate-from-json
   Body: Architecture JSON
   ↓
6. Backend:
   - TerraformGeneratorV2.generate(json)
   - Load Jinja2 templates
   - Render main.tf, variables.tf, vpc.tf, ec2.tf
   - Return { files: { ... } }
   ↓
7. Frontend:
   - Create ZIP with all .tf files
   - Download 'infrastructure.zip'
```

---

## State Management

### localStorage (Draft Autosave)

```javascript
// Save draft
localStorage.setItem('architecture-draft', JSON.stringify(state));

// Load draft
const draft = localStorage.getItem('architecture-draft');
if (draft) {
  loadArchitectureData(JSON.parse(draft));
}
```

### API (Persistent Storage)

```javascript
// Save to API
POST /api/architectures
Body: { name, components, connections }
Response: { id: 'arch-123' }

// Load from API
GET /api/architectures/arch-123
Response: { id, name, components, connections }

// Update existing
PUT /api/architectures/arch-123
Body: { name, components, connections }
```

---

## Component Types & Icons

| Type | Icon | Category | Canvas Color |
|------|------|----------|--------------|
| vpc | 🌐 | Network | Purple (#667eea) |
| subnet | 📦 | Network | Green/Blue/Pink (type-dependent) |
| igw | 🌍 | Network | Dark (#232F3E) |
| nat | 🔀 | Network | Orange (#D45B07) |
| ec2 | 🖥️ | Computing | Orange (#FF9900) |
| lambda | λ | Computing | Orange (#FF9900) |
| ecs | 🐳 | Computing | Orange (#FF9900) |
| alb | ⚖️ | Computing | Purple (#8C4FFF) |
| rds | 💾 | Data | Blue (#527FFF) |
| dynamodb | ⚡ | Data | Blue (#4053D6) |
| s3 | 📁 | Data | Green (#569A31) |
| elasticache | 🔄 | Data | Purple (#C925D1) |
| sg | 🛡️ | Security | Red (#DD344C) |
| nacl | 🔒 | Security | Dark Red (#B0084D) |
| iam | 👤 | Security | Red (#DD344C) |

---

## Performance Considerations

### Frontend

1. **Cytoscape Rendering**
   - Limit: ~500 nodes (Performance-Grenze)
   - Use `userZoomingEnabled: true` für große Graphs
   - Virtual Rendering für >1000 nodes (nicht implementiert)

2. **Event Debouncing**
   - CIDR Input: 300ms Debounce für IP Calculator
   - Canvas Drag: Update position on 'dragfree', nicht 'drag'

3. **State Updates**
   - Batch Updates wo möglich
   - Undo/Redo: Max 50 History-Einträge

### Backend

1. **Terraform Generation**
   - Time Complexity: O(n) für n Components
   - Jinja2 Rendering: ~10ms pro Template
   - Total: ~100ms für 10 Components

2. **API Response Time**
   - Target: <200ms für /generate-from-json
   - Caching: Template Pre-Loading

---

## Security Considerations

### Frontend

1. **XSS Prevention**
   - No `innerHTML` with user input
   - Use `textContent` für User-Namen
   - Sanitize JSON before rendering

2. **CSRF Protection**
   - API Tokens in Headers
   - SameSite Cookies

### Backend

1. **Input Validation**
   - Pydantic Schemas für alle Inputs
   - CIDR Validation (IP-Range, Prefix)
   - Component Type Whitelist

2. **Terraform Injection Prevention**
   - Jinja2 Auto-Escaping aktiviert
   - No `eval()` oder `exec()`
   - Whitelist für Resource Names

---

## Testing Strategy

### Frontend Unit Tests (Vitest)

```javascript
describe('InfrastructureCanvas', () => {
  it('should add component to canvas', () => {
    const canvas = new InfrastructureCanvas('test-container');
    const component = { id: 'vpc-1', type: 'vpc', ... };
    canvas.addComponent(component);
    expect(canvas.components.size).toBe(1);
  });
});
```

### Backend Unit Tests (pytest)

```python
def test_terraform_generator_vpc():
    generator = TerraformGeneratorV2()
    json_input = {
        "components": {
            "vpc-1": {
                "type": "vpc",
                "config": {"cidr": "10.0.0.0/16"}
            }
        }
    }
    result = generator.generate(json_input)
    assert "aws_vpc" in result['vpc.tf']
```

### E2E Tests (Playwright)

```javascript
test('should design VPC with EC2', async ({ page }) => {
  await page.goto('/infrastructure-designer.html');
  
  // Drag VPC
  await page.dragAndDrop('[data-component-type="vpc"]', '#canvas-container');
  
  // Configure VPC
  await page.fill('input[name="cidr"]', '10.0.0.0/16');
  
  // Verify IP Calculator
  await expect(page.locator('.inline-ip-info')).toContainText('65,536');
});
```

---

## Future Enhancements

### Planned Features

1. **Multi-Cloud Support**
   - Azure Resource Manager Templates
   - GCP Deployment Manager
   - Kubernetes YAML

2. **Cost Estimation**
   - Real-time Pricing API
   - Monthly Cost Breakdown
   - Comparison with Alternatives

3. **Collaboration**
   - Real-time Editing (WebSockets)
   - Comments on Components
   - Version History

4. **AI Assistance**
   - Auto-Suggest Components
   - Best Practice Warnings
   - Security Recommendations

5. **Edge Creation UI**
   - Click Node A → Click Node B → Create Edge
   - Connection Type Selection (DB, HTTP, etc.)
   - Port Configuration

---

## Troubleshooting

### Canvas zeigt keine Nodes

**Ursache:** Cytoscape.js nicht geladen  
**Lösung:** `npm install` + Dev-Server neu starten

### Tabs öffnen sich nicht

**Ursache:** Event Listener nicht registriert  
**Lösung:** Page Controller prüfen, `attachGlobalListeners()`

### IP Calculator zeigt falsche Werte

**Ursache:** CIDR-Parsing Fehler  
**Lösung:** CIDR-Format prüfen (`10.0.0.0/16`, nicht `10.0.0.0`)

### Terraform-Generierung schlägt fehl

**Ursache:** Template fehlt oder invalid JSON  
**Lösung:** Backend-Logs prüfen, Template-Pfad validieren

---

## Related Documentation

- [Quick Start Guide](./infrastructure-designer-quickstart.md)
- [User Guide](./infrastructure-designer-guide.md)
- [API Reference](./api/terraform-api.md)
- [Frontend README](../frontend/README_DESIGNER.md)

---

**Letzte Aktualisierung:** 2026-05-16
