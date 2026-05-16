# OverCloud Security Quick Fixes

**Priorität: CRITICAL - Vor Production Launch fixen!**

---

## 1. DEBUG Mode deaktivieren (5 Minuten)

### Problem
Debug-Modus zeigt detaillierte Stack Traces + interne Pfade.

### Fix
```python
# backend/app/config.py
class Settings(BaseSettings):
    DEBUG: bool = False  # ÄNDERN: von True zu False
    
    @field_validator("DEBUG")
    @classmethod
    def validate_debug_mode(cls, v, values):
        if v and values.get("ENV") == "production":
            raise ValueError("DEBUG=True not allowed in production")
        return v
```

**Deployment:**
```bash
# .env (Production)
DEBUG=False
ENV=production
```

---

## 2. IDOR Fixes - Authorization Checks (30 Minuten)

### Problem
Jeder User kann andere User-Profile abrufen.

### Fix 1: GET /api/v1/users/{id}
```python
# backend/app/api/users.py:64
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # NEU: Authorization Check
    if str(user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(**user)
```

### Fix 2: GET /api/v1/users (Admin-only)
```python
# backend/app/api/users.py:42
@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # NEU: Admin Check (TODO: Implementiere is_admin Funktion)
    # if not current_user.get("is_admin"):
    #     raise HTTPException(403, "Admin access required")
    
    # TEMP: Nur eigenes Profil erlauben
    items = [user_repo.get(UUID(current_user["id"]))]
    total = 1
    
    return UserListResponse(
        items=[UserResponse(**item) for item in items if item],
        total=total,
        skip=skip,
        limit=limit
    )
```

---

## 3. XSS Prevention - Frontend (1 Stunde)

### Problem
`innerHTML` mit User Input → XSS möglich.

### Fix: Nutze textContent statt innerHTML
```javascript
// frontend/src/js/main.js
// VORHER:
mainContainer.innerHTML = '<p>' + message + '</p>';

// NACHHER:
const p = document.createElement('p');
p.textContent = message;  // Auto-escaped!
mainContainer.appendChild(p);
```

### Alternative: DOMPurify
```bash
npm install dompurify
```

```javascript
import DOMPurify from 'dompurify';

// Wenn HTML nötig
function renderHTML(userHTML) {
    const clean = DOMPurify.sanitize(userHTML);
    container.innerHTML = clean;
}
```

---

## 4. Password Policy verschärfen (15 Minuten)

### Problem
Nur Länge geprüft, keine Komplexität.

### Fix
```python
# backend/app/schemas/user.py:26
import re
from pydantic import field_validator

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=12, max_length=128)  # Min 12 statt 8
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Enforce password complexity."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        
        # Check complexity
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain special character")
        
        # Blacklist common passwords
        common = ["password", "12345678", "qwerty", "admin123"]
        if v.lower() in common:
            raise ValueError("Password too common")
        
        return v
```

---

## 5. Rate Limiting auf fehlende Endpoints (15 Minuten)

### Problem
Architectures/Deployments ohne Rate Limit.

### Fix
```python
# backend/app/api/architectures.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("", response_model=ArchitectureResponse)
@limiter.limit("1000/hour" if settings.TESTING else "50/hour")  # NEU
async def create_architecture(request: Request, ...):
    # ...
```

**Endpoints die Rate Limiting brauchen:**
- POST /api/v1/architectures - `50/hour`
- POST /api/v1/deployments - `20/hour`
- GET /api/v1/users/{id} - `100/minute`

---

## 6. Hardcoded API URL fixen (5 Minuten)

### Problem
Frontend nutzt `http://localhost:8000` hardcoded.

### Fix
```bash
# frontend/.env.production
VITE_API_BASE_URL=https://api.overcloud.io
```

```javascript
// frontend/src/js/lib/api-client.js
export class APIClient {
    constructor(baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') {
        this.baseURL = baseURL.replace(/\/$/, '');
    }
}
```

---

## 7. Terraform Command Injection Fix (30 Minuten)

### Problem
`subprocess.run()` ohne Input Validation.

### Fix
```python
# backend/app/core/terraform_generator/validators.py:122
import shlex
from pathlib import Path

def _run_terraform_command(self, args: List[str], working_dir: Path, timeout: int = 120):
    # Validate working_dir gegen Whitelist
    allowed_base = Path(settings.TERRAFORM_WORKSPACE_DIR).resolve()
    working_dir_resolved = working_dir.resolve()
    
    if not str(working_dir_resolved).startswith(str(allowed_base)):
        raise ValueError(f"Invalid working directory: {working_dir}")
    
    # Sanitize terraform binary
    terraform_binary = shlex.quote(self.terraform_binary)
    
    # Escape arguments
    safe_args = [shlex.quote(arg) for arg in args]
    
    cmd = [terraform_binary] + safe_args
    
    result = subprocess.run(
        cmd,
        cwd=working_dir_resolved,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False  # WICHTIG!
    )
    
    return result.returncode == 0, result.stdout, result.stderr
```

---

## 8. JWT Token Lifetime verkürzen (10 Minuten)

### Problem
24h Token-Laufzeit zu lang.

### Fix
```python
# backend/app/config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1h statt 24h
```

**Hinweis:** Refresh Token Flow später implementieren (siehe Full Report).

---

## Deployment Checklist

### Pre-Production
- [ ] DEBUG=False gesetzt
- [ ] SECRET_KEY stark genug (32+ chars, gemischt)
- [ ] CORS_ORIGINS nur Production-Domains
- [ ] AWS Credentials via IAM Roles (keine Keys in .env)
- [ ] STRIPE_ENABLED + Webhook Secret konfiguriert
- [ ] Rate Limits getestet

### Production Environment Variables
```bash
# .env (Production)
ENV=production
DEBUG=False
SECRET_KEY=<generiere mit: python -c "import secrets; print(secrets.token_urlsafe(32))">
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=https://app.overcloud.io

# AWS
AWS_REGION=eu-central-1
DYNAMODB_TABLE_NAME=overcloud-prod-main
S3_LARGE_ITEMS_BUCKET=overcloud-prod-large-items

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Stripe
STRIPE_ENABLED=True
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Logging
LOG_LEVEL=INFO
LOG_JSON_FORMAT=True
ENABLE_CLOUDWATCH=True
ENABLE_SENTRY=True
SENTRY_DSN=https://...@sentry.io/...
```

---

## Testing nach Fixes

### Manual Tests
```bash
# 1. Test IDOR
curl -H "Authorization: Bearer <token-user-a>" \
  http://localhost:8000/api/v1/users/<user-b-id>
# Erwarte: 403 Forbidden

# 2. Test XSS
# Erstelle Architektur mit Name: <script>alert(1)</script>
# Prüfe: Wird als Text angezeigt, nicht ausgeführt

# 3. Test Rate Limit
for i in {1..60}; do
  curl -X POST http://localhost:8000/api/v1/architectures \
    -H "Authorization: Bearer <token>" -d '{...}'
done
# Erwarte: Nach ~50 Requests → 429 Too Many Requests

# 4. Test Weak Password
curl -X POST http://localhost:8000/api/v1/auth/register \
  -d '{"email":"test@test.com","name":"Test","password":"password123"}'
# Erwarte: 422 Validation Error
```

### Automated Tests
```bash
cd backend
poetry run pytest tests/security/test_idor.py
poetry run pytest tests/security/test_rate_limiting.py
poetry run pytest tests/security/test_password_policy.py
```

---

## Nach Quick Fixes

**Security Level:** MEDIUM → HIGH  
**Production-Ready:** JA (mit Einschränkungen)

**Noch offen (nicht kritisch):**
- CSRF Protection (implementiere später via Middleware)
- Refresh Token Flow (verbessert Token-Management)
- DSGVO Endpoints (für EU-Launch)
- Enhanced Security Logging

Siehe **SECURITY_AUDIT_REPORT.md** für vollständige Details.

---

**Geschätzte Zeit für alle Quick Fixes: 3-4 Stunden**  
**Empfehlung: Vor Go-Live implementieren!**
