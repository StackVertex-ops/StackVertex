# OverCloud Admin System

System-level Administration für Support, Compliance & Security.

---

## Überblick

Das Admin System ermöglicht berechtigten Mitarbeitern (SuperAdmins, Support, Auditoren) Zugriff auf Kundendaten für:

- **Support**: Debugging von Kundenproblemen
- **Compliance**: DSGVO-Anfragen, Datenexport
- **Security**: Verdacht auf Missbrauch, Incident Response
- **Billing**: Zahlungsprobleme, Subscription-Management

**Wichtig**: Alle Admin-Aktionen werden im Audit Trail geloggt (Compliance & Security).

---

## System Roles

### 1. USER (Standard)

Reguläre User ohne besondere Berechtigungen.

- Zugriff nur auf eigene Daten
- Zugriff nur auf Organisationen, in denen sie Mitglied sind

### 2. SUPERADMIN

System-Administrator mit vollem Zugriff auf ALLE Daten.

**Berechtigungen:**
- Alle User & Organisationen lesen/bearbeiten
- User Status ändern (aktivieren/deaktivieren/suspendieren)
- System Roles ändern (andere SuperAdmins erstellen)
- User impersonieren (für Support-Cases)
- Audit Logs einsehen

**Sicherheit:**
- MUSS 2FA aktiviert haben
- Alle Aktionen werden geloggt
- Kritische Aktionen (Impersonation, Role Changes) triggern Alerts

### 3. SUPPORT

Support-Mitarbeiter mit Read-Only Zugriff.

**Berechtigungen:**
- User & Organisationen lesen (aber nicht bearbeiten)
- Audit Logs einsehen
- Kann NICHT impersonieren
- Kann NICHT Rollen/Status ändern

**Use Cases:**
- Kunde hat Probleme beim Login
- Kunde findet seine Daten nicht
- Allgemeine Support-Anfragen

### 4. AUDITOR

Compliance/Audit-Mitarbeiter mit Read-Only Zugriff auf Logs.

**Berechtigungen:**
- Audit Logs einsehen (für Compliance)
- Kann NICHT User/Orgs einsehen
- Kann NICHT bearbeiten
- Kann NICHT impersonieren

**Use Cases:**
- DSGVO Audit
- Security Audit
- Compliance Reports

---

## Admin API Endpoints

Alle Endpoints unter `/api/v1/admin/*` benötigen entsprechende Berechtigungen.

### User Management (SuperAdmin only)

#### List All Users

```http
GET /api/v1/admin/users?skip=0&limit=100
Authorization: Bearer <superadmin_token>
```

**Response:**
```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "system_role": "user",
    "status": "active",
    "personal_org_id": "uuid",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00"
  }
]
```

#### Get User Details

```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <superadmin_token>
```

#### Update User Status

```http
PATCH /api/v1/admin/users/{user_id}/status
Authorization: Bearer <superadmin_token>
Content-Type: application/json

{
  "status": "suspended",
  "reason": "Suspicious activity detected - investigating fraud"
}
```

**Statuses:**
- `active` - Normal user
- `inactive` - Deactivated (soft delete)
- `suspended` - Temporarily suspended (security)
- `pending_email_verification` - Email not verified yet

#### Update System Role

```http
PATCH /api/v1/admin/users/{user_id}/system-role
Authorization: Bearer <superadmin_token>
Content-Type: application/json

{
  "system_role": "support",
  "reason": "New support team member - onboarding"
}
```

**⚠️ CRITICAL**: Promoting to SuperAdmin wird als CRITICAL Event geloggt und triggert Alerts!

### Organisation Management (SuperAdmin only)

#### List All Organisations

```http
GET /api/v1/admin/organisations?skip=0&limit=100
Authorization: Bearer <superadmin_token>
```

#### Get Organisation Architectures

```http
GET /api/v1/admin/organisations/{org_id}/architectures
Authorization: Bearer <superadmin_token>
```

### Audit Logs (Support, Auditor, SuperAdmin)

#### Query Audit Logs

```http
GET /api/v1/admin/audit-logs?user=user@example.com&action=deploy_start&skip=0&limit=100
Authorization: Bearer <support_or_superadmin_token>
```

**Query Parameters:**
- `user` - Filter by user email
- `action` - Filter by action (deploy_start, admin.view_user, etc.)
- `resource_type` - Filter by resource type (deployment, user, organisation)
- `resource_id` - Filter by specific resource UUID
- `start_date` - Filter by start date (ISO 8601)
- `end_date` - Filter by end date (ISO 8601)
- `skip` - Pagination offset
- `limit` - Max items (max: 1000)

### User Impersonation (SuperAdmin only)

#### Impersonate User

```http
POST /api/v1/admin/impersonate/{user_id}
Authorization: Bearer <superadmin_token>
Content-Type: application/json

{
  "reason": "Customer reported bug in deployment process - need to investigate"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900,
  "impersonated_user_email": "user@example.com",
  "impersonated_user_id": "uuid",
  "warning": "This token expires in 15 minutes. All actions are logged."
}
```

**⚠️ CRITICAL**:
- Token ist nur 15 Minuten gültig
- ALLE Aktionen werden geloggt mit `impersonated_by` Info
- Triggert CRITICAL Alert im Monitoring
- Benötigt Reason (min. 10 Zeichen)

**Use Case:**
1. Kunde meldet Bug: "Kann kein Deployment erstellen"
2. SuperAdmin impersoniert User
3. SuperAdmin reproduziert Bug
4. SuperAdmin behebt Bug
5. Token läuft nach 15min ab

### System Stats (Support, SuperAdmin)

#### Get System Statistics

```http
GET /api/v1/admin/stats
Authorization: Bearer <support_or_superadmin_token>
```

**Response:**
```json
{
  "users": {
    "total": 42,
    "active": 42
  },
  "organisations": {
    "total": 15
  },
  "audit": {
    "total_logs": 1000,
    "failed_count": 10,
    "action_counts": {
      "deploy_start": 500,
      "deploy_destroy": 300
    },
    "user_counts": {
      "user@example.com": 100
    },
    "last_updated": "2026-01-01T00:00:00"
  },
  "timestamp": "2026-01-01T00:00:00"
}
```

---

## SuperAdmin erstellen

### Initial Setup (erster SuperAdmin)

```bash
cd backend

# Mit zufälligem Passwort
python scripts/create_superadmin.py \
  --email admin@overcloud.io \
  --name "Super Admin"

# Mit eigenem Passwort
python scripts/create_superadmin.py \
  --email admin@overcloud.io \
  --name "Super Admin" \
  --password "YourSecurePassword123!"
```

**Output:**
```
================================================================================
SuperAdmin created successfully!
================================================================================
Email:    admin@overcloud.io
Name:     Super Admin
User ID:  abc-123-def-456
Password: X9$kL3m!pQ7&vN2@wR5
================================================================================

IMPORTANT:
- Store this password securely (password manager)
- Enable 2FA after first login (coming soon)
- Change password after first login
- This password will NOT be shown again
================================================================================
```

### Weiteren SuperAdmin erstellen (aus bestehendem Account)

```bash
# 1. Login als SuperAdmin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@overcloud.io&password=YourPassword"

# 2. Promote User zu SuperAdmin
curl -X PATCH http://localhost:8000/api/v1/admin/users/{user_id}/system-role \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "system_role": "superadmin",
    "reason": "New CTO - requires SuperAdmin access"
  }'
```

---

## Sicherheit & Best Practices

### 1. Separate Admin Accounts

**❌ FALSCH:**
- Andy hat einen Account für reguläre Nutzung UND Admin-Tasks

**✅ RICHTIG:**
- Andy hat `andy@overcloud.io` (regular user)
- Andy hat `andy.admin@overcloud.io` (superadmin)
- Admin-Account nur für Admin-Tasks verwenden

### 2. 2FA Pflicht

**Alle SuperAdmins MÜSSEN 2FA aktiviert haben.**

TODO: Implementierung in Phase 2
- Google Authenticator / Authy
- Backup Codes generieren
- Admin API blockiert ohne 2FA

### 3. IP Whitelisting (Optional)

Für Produktionsumgebungen: Admin API nur von bestimmten IPs erreichbar.

**Terraform Config:**
```hcl
resource "aws_security_group_rule" "admin_api" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = [
    "1.2.3.4/32",  # Office IP
    "5.6.7.8/32"   # VPN IP
  ]
  security_group_id = aws_security_group.api.id

  # Only for /api/v1/admin/* endpoints
}
```

### 4. Audit Trail

**Alle Admin-Aktionen werden geloggt:**

```json
{
  "user": "admin@overcloud.io",
  "action": "admin.view_user",
  "resource_type": "user",
  "resource_id": "abc-123",
  "timestamp": "2026-01-01T12:00:00",
  "ip_address": "1.2.3.4",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "reason": "Support ticket #1234"
  },
  "success": true
}
```

**Kritische Actions triggern Alerts:**
- `admin.impersonate_user` → CRITICAL
- `admin.update_system_role` (to SuperAdmin) → CRITICAL
- `admin.update_user_status` (suspend) → WARNING

### 5. Time-Limited Impersonation

**Impersonation Tokens:**
- Max 15 Minuten gültig (nicht verlängerbar)
- Enthalten `impersonated_by` Field im JWT
- Alle Aktionen werden mit Kontext geloggt
- User sieht NICHT, dass er impersoniert wurde (by design)

### 6. Reason Required

**Kritische Actions benötigen Reason-Field:**
- Impersonation
- Status Changes (suspend, inactive)
- System Role Changes

**Mindestlänge: 10 Zeichen** (erzwingt echte Begründung, nicht nur "test")

### 7. Regular Audits

**Monatlich:**
- Review aller SuperAdmin Accounts (noch aktiv?)
- Review aller Impersonation Events (legitim?)
- Review aller Role Changes (documented?)

**Automation:**
```bash
# Liste aller SuperAdmins
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer <token>" \
  | jq '.[] | select(.system_role == "superadmin")'

# Alle Impersonation Events (letzte 30 Tage)
curl -X GET "http://localhost:8000/api/v1/admin/audit-logs?action=admin.impersonate_user" \
  -H "Authorization: Bearer <token>"
```

---

## Compliance (DSGVO)

### Art. 32 DSGVO - Security Requirements

Das Admin System erfüllt DSGVO Art. 32 Anforderungen:

1. **Pseudonymisierung & Verschlüsselung**
   - Passwörter: bcrypt hashed
   - Secrets: AWS Secrets Manager (verschlüsselt)
   - Tokens: JWT (signiert)

2. **Vertraulichkeit**
   - Admin API nur über HTTPS
   - IP Whitelisting (optional)
   - 2FA Pflicht für SuperAdmins

3. **Integrität**
   - Audit Trail (unveränderlich)
   - Alle Änderungen werden geloggt
   - Keine Löschung von Logs möglich

4. **Verfügbarkeit**
   - High Availability Setup (AWS Multi-AZ)
   - Backups (DynamoDB Point-in-Time Recovery)
   - Disaster Recovery Plan

5. **Regelmäßige Tests**
   - Unit Tests für Admin API
   - Security Audits (quartalsweise)
   - Penetration Tests (jährlich)

### DSGVO Auskunft (Art. 15)

**Kunde fordert Auskunft über seine Daten:**

```bash
# 1. SuperAdmin impersoniert User
curl -X POST http://localhost:8000/api/v1/admin/impersonate/{user_id} \
  -H "Authorization: Bearer <superadmin_token>" \
  -d '{"reason": "DSGVO Art. 15 Auskunftsanfrage - Ticket #1234"}'

# 2. Exportiere User Daten
curl -X GET http://localhost:8000/api/v1/dsgvo/export \
  -H "Authorization: Bearer <impersonation_token>"

# 3. Sende Export an Kunden (verschlüsselt)
```

### DSGVO Löschung (Art. 17)

**Kunde fordert Löschung ("Recht auf Vergessenwerden"):**

```bash
# 1. SuperAdmin löscht User Account
curl -X DELETE http://localhost:8000/api/v1/admin/users/{user_id} \
  -H "Authorization: Bearer <superadmin_token>" \
  -d '{
    "reason": "DSGVO Art. 17 Löschungsanfrage - Ticket #1234",
    "confirm_data_loss": true
  }'
```

**Was wird gelöscht:**
- User Account (soft delete → status: inactive)
- Personal Organisation (soft delete)
- Alle Architectures (soft delete)
- Alle Deployments (destroy + soft delete)

**Was bleibt:**
- Audit Logs (Compliance-Pflicht, 3 Jahre)
- Billing Data (Steuerrecht, 10 Jahre)
- Anonymisierte Analytics

---

## Monitoring & Alerts

### CloudWatch Alarms

**CRITICAL Events:**
```yaml
AdminImpersonationAlarm:
  MetricFilter: { action = "admin.impersonate_user" }
  Threshold: 1
  Action: SNS → PagerDuty → On-Call Engineer

AdminRoleChangeAlarm:
  MetricFilter: { action = "admin.update_system_role" AND new_role = "superadmin" }
  Threshold: 1
  Action: SNS → Slack #security

AdminSuspendUserAlarm:
  MetricFilter: { action = "admin.update_user_status" AND new_status = "suspended" }
  Threshold: 1
  Action: SNS → Slack #security
```

### Sentry Integration

**Error Tracking:**
```python
# In admin.py
if severity == "CRITICAL":
    sentry_sdk.capture_message(
        f"CRITICAL: {action} by {admin_email}",
        level="critical",
        extra={
            "admin_id": admin_id,
            "action": action,
            "details": details
        }
    )
```

---

## Troubleshooting

### Problem: "SuperAdmin access required"

**Symptom:**
```json
{"detail": "SuperAdmin access required"}
```

**Lösung:**
1. Check `system_role` in JWT Token:
   ```bash
   echo "<token>" | jwt decode -
   # Look for: "system_role": "superadmin"
   ```

2. Check User in Database:
   ```bash
   aws dynamodb get-item \
     --table-name overcloud \
     --key '{"PK": {"S": "USER#<user_id>"}, "SK": {"S": "METADATA"}}'
   ```

3. Update System Role (if necessary):
   ```bash
   python scripts/create_superadmin.py --email your@email.com --name "Your Name"
   ```

### Problem: Impersonation Token abgelaufen

**Symptom:**
```json
{"detail": "Token expired"}
```

**Lösung:**
- Impersonation Token ist nur 15 Minuten gültig
- Generiere neuen Token mit `/admin/impersonate/{user_id}`
- Benötigst du länger? → Frag dich: Ist Impersonation wirklich nötig?

### Problem: Audit Logs nicht sichtbar

**Symptom:**
Keine Logs in `/admin/audit-logs`

**Lösung:**
1. Check DynamoDB Table:
   ```bash
   aws dynamodb query \
     --table-name overcloud \
     --key-condition-expression "PK = :pk" \
     --expression-attribute-values '{":pk": {"S": "AUDIT#202601"}}'
   ```

2. Check IAM Permissions (Lambda für Audit Stream)

3. Check CloudWatch Logs

---

## Roadmap

### Phase 1: MVP (Current)
- [x] SystemRole Enum (USER, SUPERADMIN, SUPPORT, AUDITOR)
- [x] Admin API Endpoints (User Management, Org Management)
- [x] User Impersonation (15min tokens)
- [x] Audit Logging (alle Admin Actions)
- [x] SuperAdmin Creation Script

### Phase 2: Security Hardening
- [ ] 2FA Pflicht für SuperAdmins
- [ ] IP Whitelisting für Admin API
- [ ] Session Management (revoke tokens)
- [ ] Admin Dashboard (Frontend)
- [ ] Automated Alerts (Slack, PagerDuty)

### Phase 3: Advanced Features
- [ ] Role-Based Access Control (RBAC) - feingranular
- [ ] Time-based Access (z.B. Support nur während Arbeitszeit)
- [ ] Approval Workflows (z.B. Impersonation benötigt 2nd Admin approval)
- [ ] Audit Log Export (CSV, JSON)
- [ ] Compliance Reports (DSGVO, ISO 27001)

### Phase 4: Automation
- [ ] Auto-expire unused SuperAdmin accounts (90 Tage inaktiv)
- [ ] Auto-rotate Admin credentials
- [ ] Anomaly Detection (ungewöhnliche Admin Activity)
- [ ] Compliance Automation (quarterly audits)

---

## Support

Bei Fragen oder Problemen:
- **Email**: support@overcloud.io
- **Slack**: #admin-system (interner Channel)
- **Docs**: https://docs.overcloud.io/admin

**Security Incidents:**
- **Email**: security@overcloud.io (PGP-Key verfügbar)
- **Phone**: +49 XXX XXXXXXX (24/7 Hotline)
- **Severity**: CRITICAL (sofortiger Response)
