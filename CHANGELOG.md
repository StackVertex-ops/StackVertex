# OverCloud - Changelog

Alle wichtigen Änderungen, Bugfixes und neuen Features werden hier dokumentiert.

Format: `[Komponente] Typ: Beschreibung`

---

## 2026-05-17

### Test Suite - COMPLETE FIX (12 → 0 Failures) ✅

**🐛 Alle Test-Fehler behoben:**

- **[backend] Organisation Type Field Fix**
  - Problem: `KeyError: 'type'` in API Responses
  - Lösung: Schema-Feld direkt `type` genannt + `map_org_type_field()` Mapping
  - Dateien: `app/schemas/organisation.py`, `app/api/organisations.py` (5 Stellen)
  - Tests: ✅ 1 FIXED

- **[backend] JWT Token Uniqueness**
  - Problem: Refresh liefert identische Tokens (identische `exp` bei schnellen Requests)
  - Lösung: `iat` (issued at) + `jti` (JWT ID mit UUID) hinzugefügt
  - Dateien: `app/api/auth.py` (create_access_token, create_refresh_token)
  - Tests: ✅ 1 FIXED

- **[backend] Billing Decimal Type Safety**
  - Problem: `TypeError: float * Decimal` nicht unterstützt
  - Lösung: Auto-Konvertierung in `calculate_monthly_cost_example()` + `float()` in Test-Assertions
  - Dateien: `app/models/billing.py`, `tests/test_billing.py`
  - Tests: ✅ 3 FIXED

- **[tests] User Status Update Fix**
  - Problem: `TypeError: unexpected keyword argument 'status'`
  - Lösung: Dict `{"status": "inactive"}` statt keyword args
  - Dateien: `tests/integration/test_refresh_token_flow.py`
  - Tests: ✅ 1 FIXED

- **[tests] CSRF Protection Tests**
  - Problem: Fehlende `client` Parameter + falsches `auth_provider` Feld
  - Lösung: `client` zu allen Methoden + `auth_provider` entfernt (existiert nicht im Schema)
  - Dateien: `tests/test_csrf_protection.py`
  - Tests: ✅ 8 FIXED

**📊 Ergebnis:**
- Start: 12 FAILED, 631 PASSED
- Jetzt: **0 FAILED, 643 PASSED** ✅
- **26 SKIPPED** (valide Gründe: AWS-Mocking, Rate-Limit-Testing, etc.)

---

### Billing & Voucher System - MAJOR UPDATE

**🚀 Neue Features:**

- **[backend] Pricing-Page mit 4 Tiers (PAYG, STARTER, PRO, ENTERPRISE)**
  - Hybrid Pricing Model: Base Fee + AWS Cost Markup %
  - Live Cost Calculator mit Voucher-Integration
  - Tier-Vergleichstabelle
  - Dateien:
    - `frontend/src/pricing.html`
    - `frontend/src/js/pages/pricing.js`
    - `docs/billing-system.md`

- **[backend] Vollständiges Gutscheinsystem**
  - Flexible Rabatte: Percentage (10%-100%) oder Fixed Amount (EUR)
  - Granulare Anwendung: Base Fee, AWS Markup, oder Beide
  - Verwendungslimits: Einmalig, n-mal, oder unbegrenzt
  - Zeitsteuerung: valid_from, valid_until
  - User-Limitierung: Jeder User kann jeden Voucher nur 1x verwenden
  - Dateien:
    - `backend/app/repositories/voucher.py`
    - `backend/app/services/voucher_service.py`
    - `backend/app/api/voucher.py`

- **[backend] Voucher API - 9 Endpoints**
  - **Public:** validate, redeem, remove
  - **Admin (SuperAdmin only):** create, list, get, stats, deactivate, reactivate
  - Rate Limiting: 5-20 Requests/Minute je nach Endpoint
  - Audit Logging für alle Voucher-Aktionen
  - Dokumentation: `docs/api/VOUCHER_API.md`

- **[frontend] Admin Voucher Management UI**
  - Voucher Table mit Actions (Stats, Deactivate, Reactivate)
  - Create Voucher Modal mit vollständigem Formular
  - Usage Statistics View
  - Dateien:
    - `frontend/src/admin-vouchers.html`
    - `frontend/src/js/pages/admin-vouchers.js`
    - `frontend/src/js/api/voucher.js`

- **[frontend] Billing Page - Voucher Integration**
  - Voucher Input Field mit Live-Validierung
  - Active Voucher Display
  - Remove Voucher Button
  - Rabatt-Anzeige in Cost Breakdown
  - Dateien:
    - `frontend/src/billing.html` (erweitert)
    - `frontend/src/js/pages/billing.js` (erweitert)

- **[backend] Invoice Generator - Discount Line Items**
  - Voucher-Rabatte als negative Line Items in Invoices
  - Format: "Discount (FRIEND2026): -€35.00"
  - Datei: `backend/app/services/invoice_generator.py`

**✅ Tests:**

- **37 neue Unit Tests (100% bestanden)**
  - Repository Tests: `backend/tests/test_voucher_repository.py` (19 Tests)
    - Create, Duplicate, Validation, Case-Insensitive Lookup
    - Validate (active, expired, usage limit)
    - Redeem, List, Deactivate/Reactivate, Stats
  - Service Tests: `backend/tests/test_voucher_service.py` (18 Tests)
    - Validate, Apply Discount (percentage, fixed, applies_to)
    - 100% discount (kostenfrei)
    - Fixed discount exceeds target
    - Redeem, Remove, Calculate subscription price
  - **Gesamt-Test-Count:** 124 Tests → **161 Tests**

**📚 Dokumentation:**

- **[docs] Encyclopedia Teil 3 erweitert**
  - Neues Kapitel: "7. Billing & Gutscheinsystem"
  - Unterkapitel: 7.1 Pricing-Modell, 7.2 Gutscheinsystem, 7.3 API Endpoints
  - Datei: `docs/encyclopedia/TEIL_3_MONITORING_SECURITY_API.md`

- **[docs] Voucher System Dokumentation erweitert**
  - Integration mit Subscription System
  - Beispiel-Flows: Create → Validate → Redeem → Invoice
  - Security Considerations (Brute-Force Prevention, Atomic Redemption)
  - Monitoring & Analytics (CloudWatch Alarms, Revenue Impact Dashboard)
  - Datei: `VOUCHER_SYSTEM.md`

- **[docs] API-Dokumentation erstellt**
  - Vollständige API Reference für alle 9 Endpoints
  - Request/Response Beispiele
  - Error Codes & Messages
  - Code-Beispiele (JavaScript, Python, cURL)
  - Rate Limits
  - Datei: `docs/api/VOUCHER_API.md`

- **[docs] README.md aktualisiert**
  - Features-Liste erweitert (Hybrid Pricing, Voucher System)
  - Test-Statistik: 124 → 161 Tests
  - Datei: `README.md`

**🐛 Bugfixes:**

- **[backend] Fix: Syntax-Fehler in billing.py**
  - Problem: Import-Fehler verhindert Billing-Service
  - Lösung: Syntax korrigiert
  - Datei: `backend/app/services/billing.py`

- **[backend] Fix: AuditLogger Import-Fehler**
  - Problem: `audit_logger` Import fehlgeschlagen in mehreren Services
  - Ursache: Falscher Import-Pfad
  - Lösung: Korrekter Import von `app.services.audit_logger`
  - Dateien:
    - `backend/app/services/aws_credentials.py`
    - `backend/app/services/data_upload.py`

**🔐 Security:**

- **[backend] SuperAdmin-Only Voucher Creation**
  - Nur SuperAdmins können Vouchers erstellen/verwalten
  - `get_current_superadmin` Dependency in Admin-Endpoints
  - 403 Forbidden für normale User

- **[backend] Atomic Voucher Redemption**
  - DynamoDB Conditional Updates verhindern Race Conditions
  - User kann Voucher nur 1x verwenden (used_by Array Check)
  - Usage Limit wird atomar inkrementiert

- **[backend] Code Injection Prevention**
  - Voucher Code nur A-Z0-9 (Regex Pattern Validation)
  - Pydantic Models validieren alle Inputs
  - SQL Injection nicht möglich (DynamoDB NoSQL)

- **[backend] Rate Limiting**
  - Public Endpoints: 5-10 Requests/Minute
  - Admin Endpoints: 10-20 Requests/Minute
  - SlowAPI Integration

**📊 Monitoring:**

- **[backend] Audit Logging für alle Voucher-Aktionen**
  - Events: `voucher.validate`, `voucher.redeem`, `voucher.remove`
  - Events: `admin.create_voucher`, `admin.deactivate_voucher`, `admin.reactivate_voucher`
  - Details: User Email, Voucher Code, Org ID, Timestamp, Success/Failure

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
