# Architecture Builder - Produktdokumentation

> **Status:** ✅ Implementiert (MVP)
> **Version:** 1.0.0
> **Zielgruppe:** Benutzer + Entwickler

---

## Übersicht

Der **Architecture Builder** ist das Herzstück von StackVertex. Hier erstellen und bearbeiten Benutzer ihre Cloud-Architekturen über ein benutzerfreundliches Formular. Die Architektur wird als JSON gespeichert und kann optional im JSON-Editor verfeinert werden.

### Hauptfunktionen

- ✅ Formular-basierte Erstellung/Bearbeitung
- ✅ JSON-Editor für fortgeschrittene Benutzer (optional)
- ✅ Versionierung (Semantic Versioning)
- ✅ Cloud Provider Selection (AWS, Azure, GCP)
- ✅ Functional & Non-Functional Requirements
- ✅ Validierung & Formatierung

---

## User Flow

### Create-Modus (Neue Architektur)

```
1. User klickt "Neue Architektur erstellen"
   ↓
2. Formular anzeigen (leer)
   - Grundlegende Infos (Name, Beschreibung, Version)
   - Cloud Provider & Region
   - Functional Requirements (Workload, Traffic, Storage, Compute)
   - Non-Functional Requirements (Availability, Scalability, Security, Performance, Cost)
   ↓
3. User füllt Formular aus
   ↓
4. User klickt "Weiter zum Builder"
   ↓
5. JSON-Editor anzeigen (generiert aus Formular)
   - JSON ist bearbeitbar
   - Validierung & Formatierung verfügbar
   ↓
6. User klickt "Architektur speichern"
   ↓
7. Backend: POST /api/v1/architectures
   - ID wird vom Backend vergeben
   - Architektur wird in DB gespeichert
   ↓
8. Redirect zur Architektur-Liste
```

### Edit-Modus (Bestehende Architektur bearbeiten)

```
1. User klickt "Bearbeiten" in Architektur-Detail-View
   ↓
2. Backend: GET /api/v1/architectures/{id}
   - Lade vollständige Architektur
   ↓
3. Formular anzeigen (befüllt mit existierenden Daten)
   - Name, Beschreibung aus architecture.name/description
   - Requirements aus architecture.architecture_json.requirements
   - Provider, Region aus architecture.architecture_json.metadata
   ↓
4. User ändert Formular-Felder
   ↓
5. User klickt "Änderungen speichern" (Submit)
   ↓
6. JSON-Editor anzeigen (Merge von Formular + existierendem JSON)
   - Formular-Daten → metadata, requirements
   - Bestehendes JSON → architecture.components, architecture.relationships
   - ⚠️ WICHTIG: Components & Relationships bleiben erhalten!
   ↓
7. Optional: User bearbeitet JSON manuell
   ↓
8. User klickt "Architektur speichern"
   ↓
9. Backend: PUT /api/v1/architectures/{id}
   - Gleiche ID, Architektur wird aktualisiert
   ↓
10. Redirect zur Architektur-Liste
```

---

## Datenstrukturen

### Backend-Response-Format

```javascript
// GET /api/v1/architectures/{id}
{
  // DB-Felder (Top-Level)
  "id": "550e8400-e29b-41d4-a716-446655440000",  // ← DB-ID (UUID)
  "name": "E-Commerce Platform",
  "description": "Hochverfügbare E-Commerce-Lösung",
  "version": "1.2.0",
  "owner": "user",
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-26T14:30:00Z",

  // JSON-Struktur (vollständige Architecture-Definition)
  "architecture_json": {
    "version": "1.2.0",
    "metadata": {
      "name": "E-Commerce Platform",
      "description": "...",
      "provider": "aws",
      "region": "eu-central-1",
      "tags": ["production", "ecommerce"]
    },
    "requirements": {
      "functional": {
        "workload_type": "web_application",
        "expected_traffic": {
          "concurrent_users": 1000,
          "requests_per_second": 100,
          "data_transfer_gb_month": 500
        },
        "storage_needs": {
          "database_size_gb": 50,
          "file_storage_gb": 100,
          "requires_object_storage": true
        },
        "compute_needs": {
          "cpu_intensive": false,
          "memory_intensive": false,
          "gpu_required": false
        }
      },
      "non_functional": {
        "availability": {
          "target_uptime_percent": 99.95,
          "multi_az": true,
          "disaster_recovery": true
        },
        "scalability": {
          "auto_scaling": true,
          "scale_to_zero": false,
          "global_distribution": false
        },
        "security": {
          "compliance_requirements": ["GDPR", "PCI-DSS"],
          "data_encryption": {
            "at_rest": true,
            "in_transit": true
          },
          "network_isolation": true,
          "public_access": true
        },
        "performance": {
          "max_latency_ms": 200,
          "cdn_required": true
        },
        "cost": {
          "monthly_budget_usd": 500,
          "cost_optimization_priority": "medium"
        }
      }
    },
    "architecture": {
      "components": [
        {
          "id": "comp-ec2-1",
          "type": "compute",
          "service": "ec2",
          "config": { ... }
        },
        {
          "id": "comp-rds-1",
          "type": "database",
          "service": "rds",
          "config": { ... }
        }
      ],
      "relationships": [
        {
          "from": "comp-ec2-1",
          "to": "comp-rds-1",
          "type": "uses"
        }
      ]
    },
    "evaluation": {
      "cost": {
        "monthly_estimate_usd": 450,
        "breakdown": { ... }
      },
      "security": {
        "score": 85,
        "findings": [ ... ]
      }
    }
  }
}
```

### Payload-Format für API-Calls

```javascript
// POST /api/v1/architectures (Create)
// PUT /api/v1/architectures/{id} (Update)
{
  "name": "E-Commerce Platform",       // Top-Level (required)
  "description": "...",                 // Top-Level (optional)
  "version": "1.0.0",                   // Top-Level (required)
  "architecture_json": { ... },        // Vollständiges JSON (required)
  "owner": "user"                      // Top-Level (required)
}
```

**Wichtig:**
- `name`, `description`, `version` müssen auf **Top-Level** sein (Backend-Schema)
- Zusätzlich können sie auch in `architecture_json.metadata` sein
- Backend speichert beides getrennt

---

## Formular-Felder

### Grundlegende Informationen

| Feld | Typ | Erforderlich | Beschreibung |
|------|-----|--------------|--------------|
| Name | `text` | ✅ Ja | Name der Architektur (z.B. "E-Commerce Platform") |
| Beschreibung | `textarea` | ❌ Nein | Kurze Beschreibung (max. 500 Zeichen) |
| Version | `text` | ✅ Ja | Semantic Versioning (z.B. "1.0.0") |

### Cloud Provider

| Feld | Typ | Werte | Erforderlich |
|------|-----|-------|--------------|
| Provider | `radio` | `aws`, `azure`, `gcp` | ✅ Ja |
| Region | `select` | Provider-spezifisch | ✅ Ja |

**Verfügbarkeit:**
- AWS: ✅ Verfügbar (MVP)
- Azure: 🔜 Coming Soon
- GCP: 🔜 Coming Soon

### Functional Requirements

#### Workload-Typ
- `web_application` (Standard)
- `api_service`
- `static_website`
- `data_processing`
- `microservices`
- `serverless_function`
- `container_workload`
- `batch_job`

#### Traffic
- Gleichzeitige Nutzer (Number)
- Requests pro Sekunde (Number)

#### Storage
- Datenbank-Größe (GB)
- File Storage (GB)
- Object Storage benötigt (Checkbox)

#### Compute
- CPU-intensiv (Checkbox)
- RAM-intensiv (Checkbox)
- GPU benötigt (Checkbox)

### Non-Functional Requirements

#### Availability
- Ziel-Uptime (%) (90-100%, default: 99.9)
- Multi-AZ Deployment (Checkbox)
- Disaster Recovery (Checkbox)

#### Scalability
- Auto-Scaling (Checkbox)
- Scale to Zero (Checkbox)
- Globale Verteilung (Checkbox)

#### Security
- Verschlüsselung at-rest (Checkbox, default: ✅)
- Verschlüsselung in-transit (Checkbox, default: ✅)
- Private Network (VPC) (Checkbox, default: ✅)
- Öffentlicher Zugang (Checkbox, default: ✅)

#### Performance
- Max. Latenz (ms) (default: 500)
- CDN benötigt (Checkbox)

#### Cost
- Monats-Budget (USD) (default: 100)
- Kosten-Optimierung: `low` | `medium` | `high`

---

## JSON-Editor

### Funktionen

- **Syntax-Highlighting** (geplant)
- **Line Numbers** ✅
  - Synchrones Scrolling mit Editor
- **Validierung** ✅
  - JSONLint für präzise Fehlersuche
  - Bracket-Matching Algorithmus
  - Zeigt Fehlerzeile + Beschreibung
- **Formatierung** ✅
  - Pretty-Print mit Einrückung
  - Sortierung (optional)

### Keyboard Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `Ctrl/Cmd + S` | Speichern |
| `Ctrl/Cmd + F` | Formatieren |
| `Ctrl/Cmd + V` | Validieren |

---

## Technische Details

### Frontend-Komponenten

```
frontend/src/js/
├── pages/
│   └── architecture-builder.js       # Main Page Controller
├── components/
│   └── architecture-form.js          # Form Component
└── lib/
    ├── api-client.js                 # HTTP Client (Fetch Wrapper)
    └── example-architectures.js      # Example Templates
```

### Wichtige Funktionen

#### `renderArchitectureBuilder(container, architectureId)`
Main Entry Point für die Builder-Page.

**Parameter:**
- `container` - DOM-Element für Rendering
- `architectureId` - Optional: UUID für Edit-Modus

**Flow:**
1. Loading State anzeigen
2. Wenn `architectureId` vorhanden: GET `/api/v1/architectures/{id}`
3. `renderBuilderUI()` aufrufen
4. Event Handlers einrichten

---

#### `renderFormStep(architecture)`
Rendert das Formular (Step 1).

**Parameter:**
- `architecture` - Optional: Existierende Architektur (Backend-Format)

**Logik:**
```javascript
if (architecture && architecture.architecture_json) {
    // Edit-Modus: Transform Backend → Form
    formData = {
        ...architecture.architecture_json,
        metadata: {
            ...architecture.architecture_json.metadata,
            name: architecture.name,              // Top-Level überschreiben
            description: architecture.description
        },
        version: architecture.version
    };
}
```

---

#### `handleFormSubmit(container, formData, existingArchitecture)`
Verarbeitet Formular-Submit, zeigt JSON-Editor.

**Parameter:**
- `container` - DOM-Element
- `formData` - Extrahierte Formular-Daten
- `existingArchitecture` - Optional: Existierende Architektur (Backend-Format)

**Logik:**
```javascript
if (existingArchitecture && existingArchitecture.architecture_json) {
    // Edit-Modus: Merge statt Überschreiben
    architecture = {
        ...existingArchitecture.architecture_json,
        metadata: {
            ...existingArchitecture.architecture_json.metadata,
            ...formData.metadata,  // Formular überschreibt
            updated_at: new Date().toISOString()
        },
        version: formData.version,
        requirements: formData.requirements
        // components & relationships bleiben ERHALTEN!
    };
} else {
    // Create-Modus: Neues Objekt
    architecture = {
        ...formData,
        metadata: { ...formData.metadata, created_at, updated_at },
        architecture: { components: [], relationships: [] }
    };
}
```

**⚠️ WICHTIG:** Im Edit-Modus werden `architecture.components` und `architecture.relationships` **nicht** überschrieben!

---

#### `saveArchitecture(jsonEditor, existingArchitecture)`
Speichert die Architektur im Backend.

**Parameter:**
- `jsonEditor` - Textarea-Element mit JSON
- `existingArchitecture` - Optional: Existierende Architektur (Backend-Format)

**Logik:**
```javascript
const architecture = JSON.parse(jsonEditor.value);

// Payload mit Fallback-Hierarchie
const payload = {
    name: architecture.metadata?.name
          || existingArchitecture?.name
          || 'Unnamed Architecture',
    description: architecture.metadata?.description
                 || existingArchitecture?.description
                 || null,
    version: architecture.version
             || existingArchitecture?.version
             || '1.0.0',
    architecture_json: architecture,
    owner: existingArchitecture?.owner || 'user'
};

// Create oder Update?
if (existingArchitecture?.id) {
    await updateArchitecture(existingArchitecture.id, payload);
} else {
    await createArchitecture(payload);
}
```

**Fallback-Hierarchie:**
1. JSON-Metadata (`architecture.metadata.name`)
2. Existierende Architektur (`existingArchitecture.name`)
3. Default-Wert (`'Unnamed Architecture'`)

---

### API-Endpunkte

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| `GET` | `/api/v1/architectures` | Liste aller Architekturen |
| `GET` | `/api/v1/architectures/{id}` | Einzelne Architektur |
| `POST` | `/api/v1/architectures` | Neue Architektur erstellen |
| `PUT` | `/api/v1/architectures/{id}` | Architektur aktualisieren |
| `DELETE` | `/api/v1/architectures/{id}` | Architektur löschen |

**Response Codes:**
- `200 OK` - GET erfolgreich
- `201 Created` - POST erfolgreich
- `204 No Content` - DELETE erfolgreich (⚠️ **kein Body!**)
- `400 Bad Request` - Validierungsfehler
- `404 Not Found` - Architektur nicht gefunden
- `422 Unprocessable Entity` - Ungültige UUID

---

## Häufige Fehlerquellen

### 1. ID-Verwechslung

❌ **FALSCH:**
```javascript
await updateArchitecture(architecture.metadata.id, payload);
await deleteArchitecture(architecture.architecture_json.metadata.id);
```

✅ **RICHTIG:**
```javascript
await updateArchitecture(architecture.id, payload);  // DB-ID!
await deleteArchitecture(architecture.id);           // DB-ID!
```

**Regel:** Für API-Calls **immer** `architecture.id` verwenden (DB-ID), **niemals** `architecture.metadata.id` oder `architecture.architecture_json.metadata.id`!

---

### 2. JSON-Parsing bei 204 No Content

❌ **FALSCH:**
```javascript
async delete(endpoint) {
    const response = await fetch(url, { method: 'DELETE' });
    return await response.json();  // Fehler bei 204!
}
```

✅ **RICHTIG:**
```javascript
async delete(endpoint) {
    const response = await fetch(url, { method: 'DELETE' });
    if (response.status === 204) return null;
    return await response.json();
}
```

---

### 3. Komponenten beim Edit überschreiben

❌ **FALSCH:**
```javascript
// Edit-Modus
const architecture = {
    ...formData,
    architecture: {
        components: [],      // ← ALLE COMPONENTS VERLOREN!
        relationships: []
    }
};
```

✅ **RICHTIG:**
```javascript
// Edit-Modus
const architecture = {
    ...existingArchitecture.architecture_json,  // ← Alles übernehmen
    metadata: { ...existingArchitecture.architecture_json.metadata, ...formData.metadata },
    requirements: formData.requirements
    // components & relationships bleiben erhalten!
};
```

---

## Zukünftige Erweiterungen

Siehe: `docs/architecture/architecture-builder-redesign.md`

- **Visual Canvas** mit Drag & Drop
- **Service Configuration Wizards** (detaillierte Forms pro AWS-Service)
- **Real-Time Cost Estimation**
- **Validation & Warnings**
- **Templates & Blueprints**

---

**Dokumentiert am:** 2026-03-26
**Version:** 1.0.0
