# SuperAdmin User erstellen

## Überblick

Um das Admin Dashboard zu nutzen, benötigst du einen User mit der `system_role = superadmin`.

## Methoden

### Methode 1: Backend CLI Script (Empfohlen)

Erstelle ein CLI-Script für User-Management:

**Datei:** `backend/scripts/create_superadmin.py`

```python
#!/usr/bin/env python3
"""Create SuperAdmin User via CLI."""

import asyncio
import sys
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository
from app.models.user import SystemRole


async def create_superadmin(email: str, name: str, password: str):
    """Create SuperAdmin user."""
    # Get DynamoDB table
    table = await get_dynamodb_table()
    user_repo = UserRepository(table=table)

    # Check if user exists
    existing = user_repo.get_by_email(email)
    if existing:
        print(f"❌ User {email} already exists!")
        return

    # Create user
    user = user_repo.create(
        email=email,
        name=name,
        password=password
    )

    # Promote to SuperAdmin
    user_repo.update_system_role(
        user_id=user["id"],
        system_role=SystemRole.SUPERADMIN
    )

    print(f"✅ SuperAdmin user created successfully!")
    print(f"   Email: {email}")
    print(f"   Name: {name}")
    print(f"   ID: {user['id']}")
    print(f"\nYou can now login at: http://localhost:5173/src/login.html")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create SuperAdmin user")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--name", required=True, help="Full name")
    parser.add_argument("--password", required=True, help="Password")

    args = parser.parse_args()

    asyncio.run(create_superadmin(args.email, args.name, args.password))
```

**Ausführen:**
```bash
cd backend
poetry run python scripts/create_superadmin.py \
  --email admin@stackvertex.io \
  --name "Super Admin" \
  --password "YourSecurePassword123!"
```

---

### Methode 2: DynamoDB AWS CLI

Erstelle User direkt in DynamoDB (nur für Test-Umgebungen):

```bash
# 1. User ID generieren
USER_ID=$(uuidgen)
ORG_ID=$(uuidgen)

# 2. Password hashen (mit Python)
HASHED_PASSWORD=$(python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('YourSecurePassword123!'))")

# 3. User Item erstellen
aws dynamodb put-item \
  --table-name stackvertex-dev \
  --item '{
    "PK": {"S": "USER#'$USER_ID'"},
    "SK": {"S": "METADATA"},
    "id": {"S": "'$USER_ID'"},
    "email": {"S": "admin@stackvertex.io"},
    "name": {"S": "Super Admin"},
    "password_hash": {"S": "'$HASHED_PASSWORD'"},
    "auth_provider": {"S": "local"},
    "status": {"S": "active"},
    "system_role": {"S": "superadmin"},
    "personal_org_id": {"S": "'$ORG_ID'"},
    "created_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
    "updated_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
    "GSI1PK": {"S": "user_by_email"},
    "GSI1SK": {"S": "admin@stackvertex.io"}
  }'

# 4. Personal Organisation erstellen
aws dynamodb put-item \
  --table-name stackvertex-dev \
  --item '{
    "PK": {"S": "ORG#'$ORG_ID'"},
    "SK": {"S": "METADATA"},
    "id": {"S": "'$ORG_ID'"},
    "name": {"S": "Admin Organisation"},
    "type": {"S": "personal"},
    "owner_user_id": {"S": "'$USER_ID'"},
    "plan": {"S": "enterprise"},
    "status": {"S": "active"},
    "created_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
    "updated_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
    "GSI1PK": {"S": "organisation"},
    "GSI1SK": {"S": "'$ORG_ID'"}
  }'

echo "✅ SuperAdmin user created!"
echo "Email: admin@stackvertex.io"
echo "Password: YourSecurePassword123!"
```

---

### Methode 3: Backend API + Manual Promotion

1. **Registriere User normal über API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@stackvertex.io",
    "name": "Super Admin",
    "password": "YourSecurePassword123!"
  }'
```

2. **Extrahiere User-ID aus Response**

3. **Promote zu SuperAdmin (direkt in DB):**
```python
# Python Script oder DynamoDB Console
from app.repositories.user import UserRepository
from app.models.user import SystemRole
from uuid import UUID

user_repo = UserRepository(table=table)
user_repo.update_system_role(
    user_id=UUID("user-id-hier"),
    system_role=SystemRole.SUPERADMIN
)
```

---

## Verifikation

### 1. User in DB prüfen
```bash
aws dynamodb get-item \
  --table-name stackvertex-dev \
  --key '{"PK": {"S": "USER#<user-id>"}, "SK": {"S": "METADATA"}}'
```

**Erwartete Ausgabe:**
```json
{
  "Item": {
    "email": {"S": "admin@stackvertex.io"},
    "system_role": {"S": "superadmin"},
    "status": {"S": "active"}
  }
}
```

### 2. Login testen
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@stackvertex.io&password=YourSecurePassword123!"
```

**Erwartete Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "email": "admin@stackvertex.io",
    "system_role": "superadmin"
  }
}
```

### 3. Admin Dashboard aufrufen
```bash
# Browser öffnen:
open http://localhost:5173/src/admin.html

# Oder mit curl:
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/admin/statistics
```

---

## Sicherheit

### Best Practices
- **Starkes Passwort verwenden** (min. 16 Zeichen)
- **Email nur für SuperAdmins** (z.B. admin@company.com)
- **Niemals in Production hardcoden**
- **Secrets Manager verwenden** für initiale Admin-Credentials
- **2FA aktivieren** (Roadmap Feature)

### Credentials Management
```bash
# Production: Use AWS Secrets Manager
aws secretsmanager create-secret \
  --name stackvertex/superadmin-credentials \
  --secret-string '{
    "email": "admin@stackvertex.io",
    "password": "GeneratedSecurePassword123!@#"
  }'
```

---

## Troubleshooting

### Problem: "User not found" beim Login
- Prüfe ob User in DB existiert
- Prüfe Email (case-sensitive in DB: lowercase)
- Prüfe `GSI1PK` und `GSI1SK` (Query-Index)

### Problem: "Access denied: SuperAdmin required"
- Prüfe `system_role` in DB
- Sollte `superadmin` sein (nicht `user`)
- Token neu generieren (logout/login)

### Problem: "Invalid password"
- Password-Hash korrekt?
- Bcrypt-Limit (72 bytes) beachten
- Passwort im Login lowercase?

---

## Nächste Schritte

Nach SuperAdmin-Erstellung:
1. Login unter `/src/login.html`
2. Admin Dashboard öffnen: `/src/admin.html`
3. Weitere User erstellen (über UI)
4. System-Statistiken prüfen
5. Audit Logs aktivieren

---

**Wichtig:** SuperAdmin-Credentials sicher aufbewahren!
