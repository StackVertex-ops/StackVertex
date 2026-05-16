# Security Best Practices für OverCloud Entwickler

**Version:** 1.0  
**Last Updated:** 2026-05-16  
**Audience:** Developers, Contributors

---

## Übersicht

Dieses Dokument definiert verbindliche Security Best Practices für alle OverCloud-Entwickler. Diese Regeln müssen bei jedem Code-Commit eingehalten werden.

**Prinzipien:**
1. **Security by Default** - Sichere Konfiguration ist der Standard
2. **Fail Secure** - Bei Fehler → Zugriff verweigern
3. **Defense in Depth** - Mehrschichtige Sicherheit
4. **Least Privilege** - Minimale Permissions
5. **Secure by Design** - Sicherheit von Anfang an

---

## Code Security

### Niemals ❌

#### 1. Hard-coded Secrets

**BAD:**
```python
# ❌ NIEMALS!
AWS_ACCESS_KEY = "AKIA1234567890ABCDEF"
SECRET_KEY = "mysupersecretkey123"
DATABASE_PASSWORD = "admin123"
STRIPE_API_KEY = "sk_test_1234567890"
```

**GOOD:**
```python
# ✅ Aus .env laden
from app.config import settings

aws_role_arn = settings.AWS_ROLE_ARN  # Aus .env
secret_key = settings.SECRET_KEY      # Aus .env
```

**Detection:**
```bash
# Vor jedem Commit prüfen:
poetry run detect-secrets scan app/
# Oder Pre-commit Hook nutzen
```

---

#### 2. `eval()` oder `exec()` mit User Input

**BAD:**
```python
# ❌ KRITISCH - Remote Code Execution!
user_code = request.json["code"]
result = eval(user_code)  # User kann beliebigen Code ausführen!

# Beispiel Exploit:
# user_code = "__import__('os').system('rm -rf /')"
```

**GOOD:**
```python
# ✅ Keine dynamische Code-Ausführung mit User Input
# Wenn nötig: Whitelist von erlaubten Operationen
ALLOWED_OPERATIONS = {
    "add": lambda a, b: a + b,
    "subtract": lambda a, b: a - b,
}

operation = request.json["operation"]
if operation not in ALLOWED_OPERATIONS:
    raise ValueError("Invalid operation")

result = ALLOWED_OPERATIONS[operation](a, b)
```

---

#### 3. `os.system()` ohne Input Validation

**BAD:**
```python
# ❌ Command Injection!
filename = request.json["filename"]
os.system(f"cat {filename}")  # filename="../../../etc/passwd"
```

**GOOD:**
```python
# ✅ Nutze Python-Bibliotheken statt Shell
from pathlib import Path

filename = request.json["filename"]

# Path Traversal Prevention
base_dir = Path("/uploads")
file_path = (base_dir / filename).resolve()

if not file_path.is_relative_to(base_dir):
    raise ValueError("Invalid path")

with file_path.open("r") as f:
    content = f.read()
```

**Alternative (wenn Shell nötig):**
```python
import subprocess

# ✅ Nutze subprocess mit Liste (kein Shell Parsing!)
result = subprocess.run(
    ["cat", filename],  # Liste statt String!
    capture_output=True,
    check=True,
    timeout=5
)
```

---

#### 4. Passwörter in Logs

**BAD:**
```python
# ❌ NIEMALS Passwords loggen!
logger.info(f"User login: {email} with password {password}")

# ❌ Auch nicht gehashed!
logger.info(f"Password hash: {password_hash}")

# ❌ Auch nicht in Error Messages!
raise Exception(f"Login failed for {email} with {password}")
```

**GOOD:**
```python
# ✅ Nur User Identifier loggen
logger.info(f"User login attempt: {email}")

# ✅ Bei Fehler: Keine sensiblen Details
logger.warning(f"Login failed for {email} (invalid credentials)")

# ✅ Audit Log nutzen (keine Passwords!)
audit_logger.log_login_failed(email, ip_address)
```

---

#### 5. SQL String Building

**BAD (SQL Injection):**
```python
# ❌ SQL Injection!
user_id = request.query_params["user_id"]
query = f"SELECT * FROM users WHERE id = {user_id}"
db.execute(query)  # user_id = "1 OR 1=1"
```

**GOOD:**
```python
# ✅ DynamoDB nutzt boto3 SDK (kein SQL)
from boto3.dynamodb.conditions import Key

response = table.query(
    KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")
)
# Boto3 escaped automatisch → kein Injection möglich
```

**Falls SQL nötig (PostgreSQL):**
```python
# ✅ SQLAlchemy ORM nutzen
user = session.query(User).filter(User.id == user_id).first()

# ✅ Oder Parameterized Queries
result = db.execute(
    "SELECT * FROM users WHERE id = :user_id",
    {"user_id": user_id}
)
```

---

### Immer ✅

#### 1. Input Validation (Pydantic)

**ALWAYS validate ALL inputs:**

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr  # ✅ Email Format validiert
    password: str = Field(min_length=8, max_length=128)  # ✅ Length constraints
    name: str = Field(min_length=1, max_length=100)
    
    @validator("password")
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v

class ArchitectureUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(max_length=1000)
    architecture_json: dict  # ✅ Validiert via JSON Schema
    
    @validator("architecture_json")
    def validate_architecture(cls, v):
        """Validate architecture JSON structure."""
        required_keys = ["version", "components", "connections"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Missing required key: {key}")
        return v
```

**API Endpoint:**
```python
@router.post("/users")
async def create_user(user: UserCreate):  # ✅ Pydantic validiert automatisch
    # Input ist garantiert valid hier
    ...
```

---

#### 2. Output Encoding

**HTML Escaping (Frontend):**
```javascript
// ❌ XSS!
element.innerHTML = userInput;

// ✅ Text Content (escaped)
element.textContent = userInput;

// ✅ Oder escaping Library
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);
element.innerHTML = clean;
```

**JSON Encoding (Backend):**
```python
# ✅ FastAPI macht automatisch JSON encoding
@router.get("/users/{id}")
async def get_user(id: UUID) -> UserResponse:
    user = repo.get(id)
    return user  # FastAPI serialisiert sicher
```

---

#### 3. Parameterized Queries (DynamoDB)

**ALWAYS use boto3 SDK:**

```python
from boto3.dynamodb.conditions import Key, Attr

# ✅ GOOD
response = table.query(
    KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & 
                           Key("SK").begins_with("PROFILE")
)

# ✅ GOOD (Filter)
response = table.scan(
    FilterExpression=Attr("email").eq(email) & Attr("status").eq("ACTIVE")
)

# ❌ BAD (niemals String Concatenation!)
# query = f"SELECT * FROM users WHERE email = '{email}'"  # NoSQL Injection!
```

---

#### 4. Least Privilege Permissions

**IAM Policies (AWS):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:eu-central-1:123456789012:table/OverCloud-Users"
    }
  ]
}
```

**Nicht:**
```json
{
  "Effect": "Allow",
  "Action": "dynamodb:*",  // ❌ Zu weit!
  "Resource": "*"  // ❌ Alle Tabellen!
}
```

**Code-Level (RBAC):**
```python
# ✅ Check user role BEFORE action
@router.delete("/architectures/{id}")
async def delete_architecture(
    id: UUID,
    current_user: dict = Depends(get_current_user)
):
    # Check permissions
    architecture = repo.get(id)
    
    # 1. User in Organisation?
    if architecture.org_id not in current_user["organisations"]:
        raise HTTPException(403, "Not authorized")
    
    # 2. User hat required role?
    user_role = get_user_role(current_user["id"], architecture.org_id)
    if user_role < UserRole.ADMIN:
        raise HTTPException(403, "Requires ADMIN role")
    
    # 3. Jetzt erst löschen
    repo.delete(id)
```

---

#### 5. Error Handling (No Stack Traces in Prod)

**Exception Handler (app/main.py):**

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    
    # Log full error für Debugging
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "user": getattr(request.state, "user", None)
        }
    )
    
    # Production: Generic error message
    if settings.ENV == "production":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request.state.request_id  # Für Support
            }
        )
    
    # Development: Full stack trace
    else:
        raise exc
```

**Custom Exceptions:**
```python
class OverCloudException(Exception):
    """Base exception für OverCloud."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class ArchitectureNotFoundError(OverCloudException):
    """Architecture nicht gefunden."""
    def __init__(self, architecture_id: UUID):
        super().__init__(
            f"Architecture {architecture_id} not found",
            status_code=404
        )

# Usage:
architecture = repo.get(id)
if not architecture:
    raise ArchitectureNotFoundError(id)
```

---

## Authentication & Authorization

### JWT Tokens

#### Token Creation

```python
from datetime import datetime, timedelta
import jwt

def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token."""
    
    # ✅ Short expiration (15-60 min)
    expiration = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # ✅ Minimal payload (kein sensible Daten!)
    payload = {
        "sub": user_id,  # Subject (User ID)
        "email": email,
        "exp": expiration,
        "iat": datetime.utcnow(),  # Issued At
        "type": "access"  # Token Type
    }
    
    # ✅ Strong SECRET_KEY (256-bit)
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    return token
```

#### Token Verification

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> dict:
    """Verify JWT and extract user."""
    
    try:
        # ✅ Verify signature + expiration
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # ✅ Check token type
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        
        # ✅ Extract user
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        
        # ✅ Load user from DB (optional)
        user = user_repo.get(user_id)
        if not user or user["status"] != "ACTIVE":
            raise HTTPException(401, "User not found or inactive")
        
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

---

### Password Handling

#### Password Hashing

```python
from passlib.context import CryptContext

# ✅ bcrypt mit cost factor 12
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

#### Password Validation

```python
import re
import httpx
import hashlib

async def validate_password_strength(password: str) -> None:
    """Validate password meets security requirements."""
    
    # Min/Max Length
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(password) > 128:
        raise ValueError("Password too long")
    
    # Complexity
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain special character")
    
    # Pwned Password Check (haveibeenpwned.com)
    if await is_password_pwned(password):
        raise ValueError("Password has been compromised in a data breach")

async def is_password_pwned(password: str) -> bool:
    """Check if password is in haveibeenpwned database."""
    # k-anonymity: Only send first 5 chars of SHA-1 hash
    sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=5.0
        )
        
        if response.status_code != 200:
            # Bei Fehler: Nicht blockieren (fail open für UX)
            logger.warning(f"Pwned password check failed: {response.status_code}")
            return False
        
        # Check if suffix in response
        return suffix in response.text
```

---

### RBAC (Role-Based Access Control)

#### Permission Checks

```python
from enum import IntEnum

class UserRole(IntEnum):
    """User roles (hierarchisch)."""
    VIEWER = 1
    MEMBER = 2
    ADMIN = 3
    OWNER = 4

async def check_org_permission(
    org_id: UUID,
    current_user: dict,
    required_role: UserRole
) -> None:
    """Check if user has required role in organisation."""
    
    # 1. User in Organisation?
    membership = org_repo.get_membership(org_id, current_user["id"])
    if not membership:
        raise HTTPException(403, "Not a member of this organisation")
    
    # 2. User hat required role?
    user_role = UserRole(membership["role"])
    if user_role < required_role:
        raise HTTPException(
            403,
            f"Requires {required_role.name} role (you are {user_role.name})"
        )

# Usage:
@router.delete("/organisations/{org_id}/users/{user_id}")
async def remove_user(
    org_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    # Check permission BEFORE action
    await check_org_permission(org_id, current_user, UserRole.ADMIN)
    
    # OK, user ist ADMIN+
    org_repo.remove_member(org_id, user_id)
```

---

## Secrets Management

### Development (.env)

**`.env.example` (committed):**
```bash
# REQUIRED
SECRET_KEY=generate-with-python-secrets-module
DATABASE_URL=http://localhost:8000
AWS_REGION=eu-central-1

# OPTIONAL
ENV=development
DEBUG=true
LOG_LEVEL=INFO
```

**`.env` (gitignored!):**
```bash
# Generate SECRET_KEY:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"

SECRET_KEY=xvL9K_R8Qm7F3pT2yN5wH1jC4dG6sB0aZ9eX8vU7kI6
DATABASE_URL=http://localhost:8000
AWS_REGION=eu-central-1
ENV=development
DEBUG=true
```

**`.gitignore`:**
```
.env
.env.local
.env.*.local
*.key
*.pem
```

---

### Production (AWS Secrets Manager)

#### Store Secret

```python
from app.services.secrets_manager import get_secrets_manager

secrets_mgr = get_secrets_manager()

# Store AWS Role ARN encrypted
secret_name = secrets_mgr.store_aws_role_arn(
    org_id="123e4567-e89b-12d3-a456-426614174000",
    aws_role_arn="arn:aws:iam::123456789012:role/OverCloudCustomerRole"
)

# Store in DynamoDB (reference only!)
org_repo.update(
    org_id,
    {"aws_role_arn_secret": secret_name}  # NOT the actual ARN!
)
```

#### Retrieve Secret

```python
# Get secret reference from DynamoDB
org = org_repo.get(org_id)
secret_name = org["aws_role_arn_secret"]

# Retrieve decrypted secret from Secrets Manager
aws_role_arn = secrets_mgr.retrieve_aws_role_arn(secret_name)

# Use for AssumeRole
sts_client = boto3.client("sts")
response = sts_client.assume_role(
    RoleArn=aws_role_arn,
    RoleSessionName=f"overcloud-{org_id}"
)
```

---

## Input Validation

### Path Traversal Prevention

**BAD:**
```python
# ❌ Path Traversal!
filename = request.query_params["file"]
with open(f"/uploads/{filename}") as f:
    content = f.read()

# Exploit: file=../../../etc/passwd
```

**GOOD:**
```python
from pathlib import Path

filename = request.query_params["file"]

# ✅ Resolve und check bounds
base_dir = Path("/uploads").resolve()
file_path = (base_dir / filename).resolve()

if not file_path.is_relative_to(base_dir):
    raise HTTPException(400, "Invalid file path")

with file_path.open("r") as f:
    content = f.read()
```

---

### File Upload Security

```python
from pathlib import Path
import magic  # python-magic library

ALLOWED_EXTENSIONS = {".tf", ".json", ".yaml", ".yml"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def validate_upload(file: UploadFile) -> None:
    """Validate uploaded file."""
    
    # 1. Extension Check
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {file_ext} not allowed")
    
    # 2. Size Check
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    # 3. MIME Type Check (actual file content)
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ["text/plain", "application/json"]:
        raise HTTPException(400, f"Invalid file content (MIME: {mime_type})")
    
    # 4. Sanitize Filename
    safe_filename = Path(file.filename).name  # Remove path components
    
    # Reset file pointer
    await file.seek(0)
    
    return safe_filename
```

---

## Logging Best Practices

### What to Log ✅

```python
# ✅ GOOD
logger.info(f"User {user_id} logged in from {ip_address}")
logger.info(f"Architecture {arch_id} deployed by {user_id}")
logger.warning(f"Failed login attempt for {email} from {ip_address}")
logger.error(f"Deployment {deploy_id} failed: {error_type}")
```

### What NOT to Log ❌

```python
# ❌ BAD - Sensitive Data!
logger.info(f"Password: {password}")
logger.info(f"JWT Token: {token}")
logger.debug(f"Credit card: {credit_card_number}")
logger.info(f"AWS Role ARN: {aws_role_arn}")
logger.debug(f"Full user object: {user}")  # Might contain passwords!
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# ✅ Structured logging (JSON)
logger.info(
    "user_login",
    user_id=str(user_id),
    email=user["email"],
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    timestamp=datetime.utcnow().isoformat()
)
```

---

## Dependencies

### Update Process

```bash
# Weekly: Check outdated packages
cd backend
poetry show --outdated

# Monthly: Update all
poetry update

# Verify tests pass
poetry run pytest

# Security scan
poetry run safety check
poetry run bandit -r app/
```

### Vulnerability Scanning

```bash
# Python
poetry run safety check --json

# Output:
{
  "vulnerabilities": [
    {
      "package": "requests",
      "installed_version": "2.25.0",
      "vulnerability": "CVE-2023-32681",
      "fixed_version": "2.31.0"
    }
  ]
}

# Fix:
poetry add requests@^2.31.0
poetry lock
poetry run pytest
```

---

## Pre-Commit Hooks

### Setup

```bash
# Install
pip install pre-commit

# Create config (.pre-commit-config.yaml)
cat > .pre-commit-config.yaml <<EOF
repos:
  # Secret Detection
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  
  # Python Linting
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.11
  
  # Security Scanning
  - repo: local
    hooks:
      - id: bandit
        name: bandit
        entry: poetry run bandit
        language: system
        args: ['-r', 'app/', '-ll']
        pass_filenames: false
EOF

# Activate
pre-commit install

# Test
pre-commit run --all-files
```

---

## Code Review Checklist

### Before Submitting PR

- [ ] **No secrets** in code (`detect-secrets scan`)
- [ ] **Input validation** (Pydantic Schemas)
- [ ] **Authentication check** (JWT dependency)
- [ ] **Authorization check** (RBAC permissions)
- [ ] **Error handling** (try/except, custom exceptions)
- [ ] **Logging** (no sensitive data)
- [ ] **Tests** (unit + integration)
- [ ] **Documentation** (docstrings, comments)

### Security Review

- [ ] **OWASP Top 10** checklist
- [ ] **Injection** prevented (parameterized queries)
- [ ] **XSS** prevented (output encoding)
- [ ] **CSRF** N/A (stateless JWT)
- [ ] **Path Traversal** prevented (`Path.is_relative_to`)
- [ ] **Rate Limiting** (if auth endpoint)
- [ ] **Audit Logging** (security events)

---

## Emergency Response

### Secret Leaked in Git

**1. Sofort rotieren:**
```bash
# Generate new secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
nano .env  # Replace SECRET_KEY

# Update Secrets Manager (production)
aws secretsmanager put-secret-value \
  --secret-id overcloud/prod/secret-key \
  --secret-string "NEW_SECRET_KEY"

# Redeploy
```

**2. Aus Git History entfernen:**
```bash
# Install BFG Repo Cleaner
brew install bfg

# Remove secret from history
bfg --replace-text secrets.txt  # File mit Secrets

# Force push (CAREFUL!)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

**3. Alert betroffene User:**
```bash
# Invalidate all JWT tokens (change SECRET_KEY)
# Force re-login für alle User
```

---

## Tools & Resources

### Security Tools

- **detect-secrets** - Secret detection (pre-commit)
- **bandit** - Python security linter
- **safety** - Dependency vulnerability scanner
- **trivy** - Container + IaC scanner
- **gitleaks** - Git history secret scan

### External Resources

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [HaveIBeenPwned API](https://haveibeenpwned.com/API/v3)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)

---

**Document Owner:** Andy Schwarz  
**Questions:** schwarz23andy@gmail.com  
**Last Updated:** 2026-05-16
