# SuperAdmin Dashboard

## Überblick

Das SuperAdmin Dashboard ermöglicht SuperAdmins die vollständige Verwaltung der StackVertex-Plattform.

## Features

### 1. Dashboard Statistiken
- Gesamtzahl der User (mit aktiven/suspendierten)
- Gesamtzahl der Organisationen
- Gesamtzahl der Architectures (mit deployed/draft)

### 2. User Management
- Liste aller User mit Filter/Suche
- User-Details anzeigen
- User-Status ändern (active, inactive, suspended)
- System-Role ändern (user, support, auditor, superadmin)
- **Passwort zurücksetzen** (generiert sicheres 16-Zeichen Passwort)
- **User impersonation** (15 Minuten Session, vollständig geloggt)

### 3. Organisation Management
- Liste aller Organisationen
- Organisation-Details (Typ, Plan, Status, Mitglieder)
- Architectures pro Organisation anzeigen

### 4. Audit Logs
- Vollständige Audit-Trail aller Admin-Aktionen
- Filter nach:
  - User Email
  - Action Type
  - Resource Type
  - Resource ID
  - Datum (start/end)
- Pagination (100 Items pro Seite)

## Zugriff

### URL
```
http://localhost:5173/src/admin.html
```

### Authentifizierung
- Nur SuperAdmins haben Zugriff
- Nicht-SuperAdmins werden automatisch zur Startseite umgeleitet
- Token-basierte Auth (JWT)

## API Endpoints

### Backend (FastAPI)

#### Statistiken
```
GET /api/v1/admin/statistics
```

**Response:**
```json
{
  "users": {
    "total": 42,
    "active": 38,
    "suspended": 4
  },
  "organisations": {
    "total": 15
  },
  "architectures": {
    "total": 67,
    "deployed": 45,
    "draft": 22
  },
  "timestamp": "2026-05-17T00:30:00Z"
}
```

#### Passwort zurücksetzen
```
POST /api/v1/admin/users/{user_id}/reset-password
```

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "new_password": "xK9#mP2$nL4@qR7&",
  "message": "Password reset successful. User should change this password after login."
}
```

**Security:**
- Generiert sicheres 16-Zeichen Passwort mit:
  - Kleinbuchstaben (a-z)
  - Großbuchstaben (A-Z)
  - Ziffern (0-9)
  - Sonderzeichen (!@#$%^&*...)
- Aktion wird als CRITICAL im Audit Log erfasst

#### User impersonation
```
POST /api/v1/admin/impersonate/{user_id}
Body: { "reason": "Customer reported bug, need to investigate" }
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "impersonated_user_email": "user@example.com",
  "impersonated_user_id": "123e4567-e89b-12d3-a456-426614174000",
  "warning": "This token expires in 15 minutes. All actions are logged."
}
```

**Security:**
- Token nur 15 Minuten gültig
- Aktion wird als CRITICAL im Audit Log erfasst
- `reason` ist Pflichtfeld (min. 10 Zeichen)
- Token enthält `impersonated_by` Field für Audit-Trail

## UI Komponenten

### Tabs
- **Users**: User-Liste mit Suche und Aktionen
- **Organisations**: Organisations-Liste
- **Audit Logs**: Audit-Log-Liste mit Filtern

### Modals
- **Password Reset Modal**: Zeigt neues Passwort an (Copy-Button)
- **Impersonation Modal**: Bestätigung mit Reason-Eingabe

### Action Buttons (Users Table)
- **Reset Password**: Generiert neues Passwort
- **Impersonate**: Übernimmt User-Session

## Sicherheit

### Audit Logging
Alle Admin-Aktionen werden geloggt:
- `admin.list_users`
- `admin.view_user`
- `admin.update_user_status`
- `admin.update_system_role`
- `admin.reset_password` (CRITICAL)
- `admin.impersonate_user` (CRITICAL)
- `admin.view_statistics`
- `admin.list_organisations`
- `admin.view_audit_logs`

### Authorization
- Alle Endpoints prüfen SuperAdmin-Role
- Dependency: `get_current_superadmin()`
- Regular Users/Support/Auditor haben KEINEN Zugriff

### Best Practices
- Impersonation nur für Debugging/Support
- Immer Reason angeben (wird geloggt)
- Passwörter sofort kopieren (werden nicht erneut angezeigt)
- Regelmäßig Audit Logs überprüfen

## Tests

### Unit Tests
```bash
cd backend
poetry run pytest tests/unit/test_admin_api.py -v
poetry run pytest tests/unit/test_password_utils.py -v
```

### Integration Tests
```bash
poetry run pytest tests/integration/test_auth_api.py -v
```

## Entwicklung

### Backend
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Öffne: `http://localhost:5173/src/admin.html`

## Deployment

### Produktions-Build
```bash
cd frontend
npm run build
```

Build-Output: `frontend/dist/`

### Umgebungsvariablen
```bash
# Backend
SECRET_KEY=<random-secret-key>
DATABASE_URL=<dynamodb-endpoint>

# Frontend
VITE_API_URL=https://api.stackvertex.io
```

## Roadmap

### Geplante Features
- [ ] User-Gruppen Management
- [ ] Erweiterte Statistiken (Grafiken)
- [ ] Export von Audit Logs (CSV/JSON)
- [ ] Email-Benachrichtigung bei Password Reset
- [ ] 2FA für SuperAdmins
- [ ] Rate Limiting pro User
- [ ] Erweiterte Suchfilter

## Support

Bei Fragen oder Problemen:
- Dokumentation: `/docs/`
- API Docs: `http://localhost:8000/docs`
- GitHub Issues: [StackVertex Issues](https://github.com/...)
