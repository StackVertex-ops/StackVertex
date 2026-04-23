# OverCloud - Changelog

Alle wichtigen Änderungen, Bugfixes und neuen Features werden hier dokumentiert.

Format: `[Komponente] Typ: Beschreibung`

---

## 2026-03-26

### Frontend - Architecture Builder

**🐛 Bugfixes:**

- **[frontend] Fix: Edit-Modus aktualisiert statt neue Architektur zu erstellen**
  - Problem: Bearbeiten einer Architektur erstellt Duplikat
  - Ursache: `existingArchitecture?.metadata?.id` statt `existingArchitecture?.id`
  - Lösung: DB-ID verwenden (`architecture.id`)
  - Datei: `frontend/src/js/pages/architecture-builder.js:791`

- **[frontend] Fix: DELETE-Requests schlagen fehl (422 Error)**
  - Problem: Löschen funktioniert nicht
  - Ursache: API-Client parst JSON bei 204 No Content Response
  - Lösung: 204 Status abfangen und `null` zurückgeben
  - Datei: `frontend/src/js/lib/api-client.js:40-43`

- **[frontend] Fix: Name und Beschreibung gehen beim Update verloren**
  - Problem: Nach Update heißen Architekturen "Unnamed Architecture"
  - Ursache: Keine Fallbacks für Name/Description aus existingArchitecture
  - Lösung: Fallback-Hierarchie: JSON-Metadata → existingArchitecture → Default
  - Datei: `frontend/src/js/pages/architecture-builder.js:787-792`

**✨ Verbesserungen:**

- **[frontend] UX: Formular wird auch im Edit-Modus angezeigt**
  - Motivation: Benutzer sollen primär über Formular arbeiten, JSON-Editor optional
  - Änderungen:
    - Formular immer anzeigen (auch im Edit-Modus)
    - Backend-Daten in Formular-Format transformieren
    - Formular-Daten mit existierendem JSON mergen (Components/Relationships bleiben erhalten)
  - Dateien:
    - `frontend/src/js/pages/architecture-builder.js:84` (currentStep)
    - `frontend/src/js/pages/architecture-builder.js:171-186` (renderFormStep)
    - `frontend/src/js/pages/architecture-builder.js:418-453` (handleFormSubmit)
    - `frontend/src/js/pages/architecture-builder.js:398` (architecture durchreichen)

**📝 Wichtige Erkenntnisse:**

- **ID-Struktur:** Es gibt zwei IDs:
  - `architecture.id` = DB-ID (für API-Calls verwenden!)
  - `architecture.architecture_json.metadata.id` = JSON-ID (NICHT für API verwenden!)

- **Backend-Response-Format:**
  ```javascript
  {
    id, name, description, version, owner, created_at, updated_at,  // Top-Level
    architecture_json: { metadata, requirements, architecture, ... }
  }
  ```

- **Payload-Format für POST/PUT:**
  ```javascript
  {
    name, description, version, owner,  // Top-Level (erforderlich)
    architecture_json: { ... }          // Vollständiges JSON
  }
  ```

---

## Template für zukünftige Einträge

```markdown
## YYYY-MM-DD

### [Komponente] - [Feature/Bereich]

**🐛 Bugfixes:**
- [komponente] Fix: Beschreibung
  - Problem: ...
  - Ursache: ...
  - Lösung: ...
  - Datei: ...

**✨ Verbesserungen:**
- [komponente] Feature: Beschreibung
  - Dateien: ...

**🚀 Neue Features:**
- [komponente] Feature: Beschreibung
  - Dateien: ...

**⚠️ Breaking Changes:**
- [komponente] Breaking: Beschreibung
  - Migration: ...
```
