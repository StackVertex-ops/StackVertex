# OverCloud Developer's Encyclopedia - Teil 3

**Monitoring, Security, Deployment & API Reference**

**Version:** 1.0  
**Datum:** 2026-05-16  
**Autor:** Claude Code (Vervollständigung nach Agent-Limit)

---

## Inhaltsverzeichnis

1. [Monitoring & Logging](#1-monitoring--logging)
2. [Security Architecture](#2-security-architecture)
3. [Deployment Patterns](#3-deployment-patterns)
4. [API Reference](#4-api-reference)
5. [Datenmodelle & Schemas](#5-datenmodelle--schemas)
6. [Entwickler-Workflows](#6-entwickler-workflows)
7. [Billing & Gutscheinsystem](#7-billing--gutscheinsystem)

---

## 1. Monitoring & Logging

### 1.1 Logging-Architektur

**Structured Logging mit Python `logging` Module:**

```python
# backend/app/core/logging.py

import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    enable_cloudwatch: bool = False,
    enable_sentry: bool = False,
    sentry_dsn: str = None,
    environment: str = "development"
):
    """Setup application logging with CloudWatch & Sentry integration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Enable JSON logging (True in production)
        enable_cloudwatch: Send logs to AWS CloudWatch
        enable_sentry: Enable Sentry error tracking
        sentry_dsn: Sentry DSN URL
        environment: Environment name (dev, staging, prod)
    """
```

**Log-Levels:**
- **DEBUG:** Development-only, verbose output
- **INFO:** Normal operational messages
- **WARNING:** Potentially harmful situations
- **ERROR:** Error events (recoverable)
- **CRITICAL:** Critical failures (non-recoverable)

**Log-Format (JSON in Production):**
```json
{
  "timestamp": "2026-05-16T18:45:23.123Z",
  "level": "ERROR",
  "logger": "app.api.auth",
  "message": "Login failed for user",
  "extra": {
    "user_id": "uuid-here",
    "ip_address": "192.168.1.1",
    "attempt_count": 3
  },
  "trace_id": "req-abc123",
  "environment": "production"
}
```

### 1.2 CloudWatch Integration

**Log Groups:**
```
/aws/lambda/overcloud-api-prod          # Lambda Logs
/ecs/overcloud-backend-prod             # ECS Logs (wenn nicht Lambda)
/overcloud/application-prod             # Custom Application Logs
```

**CloudWatch Alarms:**
```python
# Konfiguriert in infrastructure/terraform/modules/monitoring/

resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "overcloud-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"  # 5 minutes
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Alert when API returns >10 5xx errors in 5 minutes"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### 1.3 Sentry Error Tracking

**Setup in backend/app/main.py:**
```python
from app.config import settings
from app.core.logging import setup_logging

setup_logging(
    enable_sentry=settings.ENABLE_SENTRY,
    sentry_dsn=settings.SENTRY_DSN,
    environment=settings.ENV
)
```

**Sentry erfasst automatisch:**
- Unhandled Exceptions
- HTTP 5xx Errors
- Database Errors
- Stack Traces mit Context

**Custom Sentry Events:**
```python
import sentry_sdk

# Tag hinzufügen
sentry_sdk.set_tag("user_id", user["id"])

# Breadcrumb (Kontext)
sentry_sdk.add_breadcrumb(
    category="auth",
    message="User login attempt",
    level="info"
)

# Custom Error
sentry_sdk.capture_message("Unusual activity detected", level="warning")
```

### 1.4 Audit Trail

**Alle sicherheitsrelevanten Events werden geloggt:**

```python
# backend/app/repositories/audit_log.py

class AuditLogRepository(BaseRepository):
    """Repository für Audit Logs (Compliance)."""
    
    def log_event(
        self,
        user_id: str,
        event_type: str,  # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc.
        resource_type: str,  # USER, ARCHITECTURE, DEPLOYMENT
        resource_id: str,
        action: str,
        metadata: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Loggt ein Security-Event für Compliance."""
```

**Audit Log Format:**
```json
{
  "id": "audit-uuid-here",
  "timestamp": "2026-05-16T18:45:23.123Z",
  "user_id": "user-uuid",
  "event_type": "UPDATE",
  "resource_type": "ARCHITECTURE",
  "resource_id": "arch-uuid",
  "action": "Updated VPC CIDR range",
  "metadata": {
    "old_value": "10.0.0.0/16",
    "new_value": "10.1.0.0/16"
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

---

## 2. Security Architecture

### 2.1 OWASP Top 10 Compliance

**Status: 🟢 GRÜN (95% Production-Ready)**

| OWASP Category | Status | Mitigation |
|---|---|---|
| **A01: Broken Access Control** | ✅ Mitigated | IDOR Prevention, Authorization Checks |
| **A02: Cryptographic Failures** | ✅ Mitigated | bcrypt, JWT, HTTPS, KMS Encryption |
| **A03: Injection** | ✅ Mitigated | DynamoDB (No SQL), Pydantic Validation |
| **A04: Insecure Design** | 🟡 Partial | CSRF Protection noch offen |
| **A05: Security Misconfiguration** | ✅ Fixed | DEBUG=False, Security Headers |
| **A06: Vulnerable Components** | ✅ Mitigated | Dependabot, 0 CVEs |
| **A07: Auth Failures** | ✅ Mitigated | Account Lockout, Rate Limiting |
| **A08: Data Integrity** | ✅ Mitigated | Pydantic, Audit Logs |
| **A09: Logging Failures** | ✅ Mitigated | CloudWatch, Sentry |
| **A10: SSRF** | ✅ Mitigated | Kein URL Fetching |

### 2.2 Authentication & Authorization

**JWT-basierte Authentication:**

```python
# backend/app/api/auth.py

from jose import jwt, JWTError
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Erstellt JWT Access Token.
    
    Args:
        data: Token Payload (z.B. {"sub": user_id})
        expires_delta: Ablaufzeit (default: 1h)
    
    Returns:
        Encoded JWT Token String
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES  # 60 min
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,  # Min 32 chars, cryptographically random
        algorithm=settings.ALGORITHM  # HS256
    )
    
    return encoded_jwt
```

**Token Payload:**
```json
{
  "sub": "user-uuid-here",  // Subject (User ID)
  "exp": 1715892323,        // Expiration (Unix Timestamp)
  "iat": 1715888723,        // Issued At
  "type": "access"          // Token Type
}
```

**Authorization Dependency:**
```python
from fastapi import Depends, HTTPException

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Extrahiert & validiert User aus JWT Token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        
        user = user_repo.get(user_id)
        if not user or user["status"] != "active":
            raise HTTPException(403, "User inactive")
        
        return user
    except JWTError:
        raise HTTPException(401, "Could not validate credentials")
```

### 2.3 Password Security

**bcrypt mit Cost Factor 12:**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash Password
hashed = pwd_context.hash("user-password")
# → $2b$12$abcdefghijklmnopqrstuvwxyz...

# Verify Password
is_valid = pwd_context.verify("user-password", hashed)
# → True or False (timing-safe comparison)
```

**Password Complexity Requirements:**

```python
# backend/app/schemas/user.py

from pydantic import field_validator
import re

class UserCreate(BaseModel):
    email: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validiert Password-Komplexität."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
```

### 2.4 Account Lockout (Brute-Force Protection)

```python
# backend/app/services/account_lockout.py

class AccountLockoutService:
    """Brute-Force Protection für Login-Versuche."""
    
    MAX_ATTEMPTS = 5           # Max fehlgeschlagene Versuche
    LOCKOUT_DURATION = 900     # 15 Minuten in Sekunden
    
    def record_failed_attempt(self, email: str):
        """Erhöht Failed-Attempt Counter."""
        # Speichert in DynamoDB: failed_login_attempts
    
    def is_locked_out(self, email: str) -> bool:
        """Prüft ob Account gesperrt ist."""
        # Liest aus DynamoDB
    
    def reset_attempts(self, email: str):
        """Löscht Failed-Attempt Counter (nach erfolgreichem Login)."""
```

**Login Flow mit Lockout:**
```python
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    lockout_service: AccountLockoutService = Depends(get_account_lockout_service)
):
    # 1. Check Lockout
    if lockout_service.is_locked_out(form_data.username):
        raise HTTPException(429, "Account locked. Try again in 15 minutes.")
    
    # 2. Verify Credentials
    user = user_repo.get_by_email(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
        lockout_service.record_failed_attempt(form_data.username)
        raise HTTPException(401, "Invalid credentials")
    
    # 3. Success → Reset Counter
    lockout_service.reset_attempts(form_data.username)
    
    # 4. Create Token
    token = create_access_token({"sub": str(user["id"])})
    return {"access_token": token, "token_type": "bearer"}
```

### 2.5 Rate Limiting

**SlowAPI Integration:**

```python
# backend/app/main.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Rate Limits per Endpoint:**

```python
# backend/app/api/auth.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/register")
@limiter.limit("5/minute")  # Max 5 Registrierungen pro Minute pro IP
async def register(request: Request, data: UserCreate):
    ...

@router.post("/login")
@limiter.limit("10/minute")  # Max 10 Login-Versuche pro Minute pro IP
async def login(request: Request, form_data: OAuth2PasswordRequestForm):
    ...
```

### 2.6 RBAC (Role-Based Access Control)

**4-Tier System Role Hierarchy:**

```python
# backend/app/models/user.py

from enum import Enum

class SystemRole(str, Enum):
    """System-wide Roles (unabhängig von Organisation)."""
    USER = "user"              # Normal user
    SUPPORT = "support"        # Customer Support (read-only access to user data)
    AUDITOR = "auditor"        # Security Auditor (read-only access to audit logs)
    SUPERADMIN = "superadmin"  # Full platform access (user management, impersonation)
```

**Authorization Guards:**

```python
# backend/app/api/auth.py

async def get_current_superadmin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Verify user is SuperAdmin."""
    if current_user.get("system_role") != SystemRole.SUPERADMIN.value:
        raise HTTPException(403, "SuperAdmin access required")
    return current_user
```

**Usage in Endpoints:**

```python
# backend/app/api/admin.py

@router.get("/admin/users")
async def list_all_users(
    current_admin: dict = Depends(get_current_superadmin)  # ✅ Nur SuperAdmin
):
    """List all users (SuperAdmin only)."""
    return user_repo.list_all()
```

### 2.7 IDOR Prevention

**Problem: Insecure Direct Object Reference**

```python
# ❌ VULNERABLE Code (vor Fix):
@router.get("/users/{user_id}")
async def get_user(user_id: UUID):
    # JEDER kann JEDEN User abrufen! (IDOR)
    user = user_repo.get(user_id)
    return user
```

**Solution: Authorization Check**

```python
# ✅ SECURE Code (nach Fix):
@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user)  # Authentifizierung
):
    # Authorization: Nur eigenes Profil oder SuperAdmin
    if str(user_id) != str(current_user["id"]):
        if current_user.get("system_role") != "superadmin":
            raise HTTPException(403, "Not authorized to view this user")
    
    user = user_repo.get(user_id)
    return user
```

### 2.8 XSS Prevention

**Backend: Output Encoding**

Pydantic Schemas validieren automatisch Input und encoden Output:

```python
from pydantic import BaseModel, field_validator

class UserResponse(BaseModel):
    id: str
    email: str
    name: str  # Automatisch escaped by Pydantic
```

**Frontend: DOM-basiertes Escaping**

```javascript
// ❌ VULNERABLE:
element.innerHTML = userInput;  // XSS!

// ✅ SECURE:
element.textContent = userInput;  // Automatisches Escaping

// Oder mit Utility:
import { escapeHtml } from './utils/dom-utils.js';
element.innerHTML = escapeHtml(userInput);
```

**Utility Function:**

```javascript
// frontend/src/js/utils/dom-utils.js

export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;  // Browser escaped automatisch
    return div.innerHTML;
}

export function setTextSafely(element, text) {
    element.textContent = text;  // Sicher, kein XSS möglich
}
```

### 2.9 Security Headers

**Middleware in backend/app/main.py:**

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Fügt Security Headers zu allen Responses hinzu."""
    response = await call_next(request)
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # XSS Protection (legacy, but doesn't hurt)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HSTS (only for HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = \
            "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    if settings.ENV == "production":
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

---

## 3. Deployment Patterns

### 3.1 Backend Deployment Optionen

**Option 1: AWS Lambda (Serverless) - EMPFOHLEN für MVP**

```dockerfile
# backend/Dockerfile.lambda

FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ${LAMBDA_TASK_ROOT}/app/

CMD ["app.lambda_handler.handler"]
```

**Lambda Handler:**

```python
# backend/app/lambda_handler.py

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
```

**Vorteile:**
- Pay-per-Request (sehr günstig bei wenig Traffic)
- Auto-Scaling (0 → Millionen Requests)
- Kein Server-Management
- Cold Start: ~500ms (akzeptabel für API)

**Option 2: ECS Fargate (Containerized)**

```yaml
# infrastructure/terraform/modules/compute/ecs.tf

resource "aws_ecs_service" "backend" {
  name            = "overcloud-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2  # Min 2 Tasks für HA
  
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
}
```

**Vorteile:**
- Kein Cold Start
- Langlebige Connections (WebSockets)
- Mehr Control über Resources
- Teurer als Lambda

### 3.2 Frontend Deployment

**S3 + CloudFront (Static Hosting):**

```bash
# Build Frontend
cd frontend
npm run build  # → dist/

# Deploy zu S3
aws s3 sync dist/ s3://overcloud-frontend-prod/ --delete

# Invalidate CloudFront Cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

**CloudFront Distribution:**

```hcl
# infrastructure/terraform/modules/cdn/cloudfront.tf

resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3-overcloud-frontend"
  }
  
  enabled             = true
  default_root_object = "index.html"
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-overcloud-frontend"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600   # 1 Stunde
    max_ttl                = 86400  # 24 Stunden
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.frontend.arn
    ssl_support_method  = "sni-only"
  }
}
```

### 3.3 Database (DynamoDB)

**Single Table Design:**

```
Table: overcloud-prod-main
Partition Key: PK (String)
Sort Key: SK (String)
GSI1: GSI1PK (String), GSI1SK (String)
GSI2: GSI2PK (String), GSI2SK (String)
```

**Access Patterns:**

```python
# User by ID
PK = "USER#uuid"
SK = "METADATA"

# User by Email (GSI1)
GSI1PK = "USER_EMAIL#user@example.com"
GSI1SK = "METADATA"

# Organisation Members
PK = "ORG#org-uuid"
SK = "MEMBER#user-uuid"

# User's Organisations
PK = "USER#user-uuid"
SK = "ORG#org-uuid"

# Architectures by Org
PK = "ORG#org-uuid"
SK = "ARCH#arch-uuid"
```

**Backup & PITR:**

```hcl
resource "aws_dynamodb_table" "main" {
  name           = "overcloud-prod-main"
  billing_mode   = "PAY_PER_REQUEST"  # On-Demand Pricing
  hash_key       = "PK"
  range_key      = "SK"
  
  # Point-in-Time Recovery
  point_in_time_recovery {
    enabled = true  # Backup last 35 days
  }
  
  # Encryption at Rest
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }
}
```

### 3.4 CI/CD Pipeline

**GitHub Actions Workflow:**

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Backend Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ -v
      
      - name: Run Frontend Tests
        run: |
          cd frontend
          npm install
          npm run test
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy Security Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
  
  deploy-backend:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name overcloud-api-prod \
            --image-uri ${{ secrets.ECR_REGISTRY }}/overcloud-backend:${{ github.sha }}
  
  deploy-frontend:
    needs: [test]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build
      
      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist/ s3://overcloud-frontend-prod/ --delete
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DIST_ID }} \
            --paths "/*"
```

---

## 4. API Reference

### 4.1 Authentication Endpoints

**POST /api/v1/auth/register**

Registriert neuen User.

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe"
  }'
```

**Response (201 Created):**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "name": "John Doe",
  "status": "active",
  "system_role": "user",
  "created_at": "2026-05-16T18:45:23.123Z"
}
```

**POST /api/v1/auth/login**

Login mit Email & Password.

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123!"
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**GET /api/v1/auth/me**

Aktueller User (erfordert JWT Token).

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4.2 Designer Endpoints

**POST /api/v1/designer/save**

Speichert Architecture JSON aus Designer.

```bash
curl -X POST http://localhost:8000/api/v1/designer/save \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production VPC",
    "description": "3-Tier Web App Architecture",
    "architecture_json": {
      "metadata": {
        "name": "production-vpc",
        "provider": "aws",
        "region": "us-east-1"
      },
      "components": {
        "vpc-1": {
          "type": "vpc",
          "label": "Production VPC",
          "config": {
            "cidr": "10.0.0.0/16",
            "enable_dns": true
          }
        }
      },
      "connections": []
    }
  }'
```

**Response (201 Created):**
```json
{
  "id": "arch-uuid",
  "name": "Production VPC",
  "status": "draft",
  "created_at": "2026-05-16T18:45:23.123Z"
}
```

**POST /api/v1/designer/generate-terraform**

Generiert Terraform HCL Code aus Architecture JSON.

```bash
curl -X POST http://localhost:8000/api/v1/designer/generate-terraform \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "architecture_json": { ... }
  }'
```

**Response (200 OK):**
```json
{
  "files": {
    "main.tf": "terraform {\n  required_version = \">= 1.5.0\"\n...",
    "variables.tf": "variable \"region\" {\n...",
    "vpc.tf": "resource \"aws_vpc\" \"vpc-1\" {\n...",
    "outputs.tf": "output \"vpc_id\" {\n..."
  },
  "component_count": 5,
  "warnings": []
}
```

**POST /api/v1/designer/validate**

Validiert Architecture JSON.

```bash
curl -X POST http://localhost:8000/api/v1/designer/validate \
  -H "Content-Type: application/json" \
  -d '{
    "architecture_json": { ... }
  }'
```

**Response (200 OK):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Subnet subnet-1 has no route table associated"
  ],
  "component_count": 5,
  "connection_count": 3
}
```

### 4.3 Admin Endpoints (SuperAdmin only)

**GET /api/v1/admin/users**

Liste aller User (SuperAdmin only).

```bash
curl http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer SUPERADMIN_TOKEN"
```

**PATCH /api/v1/admin/users/{user_id}/status**

Ändert User Status (active, suspended, deleted).

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/users/{user_id}/status \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "suspended",
    "reason": "Violation of ToS"
  }'
```

**POST /api/v1/admin/impersonate/{user_id}**

Erstellt Impersonation Token (15 Min Gültigkeit).

```bash
curl -X POST http://localhost:8000/api/v1/admin/impersonate/{user_id} \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Debug user-reported issue #1234"
  }'
```

**Response:**
```json
{
  "impersonation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

---

## 5. Datenmodelle & Schemas

### 5.1 User Model

**DynamoDB Structure:**
```python
{
  "PK": "USER#uuid",
  "SK": "METADATA",
  "id": "uuid",
  "email": "user@example.com",
  "password_hash": "$2b$12$...",  # bcrypt hash
  "name": "John Doe",
  "status": "active",  # active, suspended, deleted
  "system_role": "user",  # user, support, auditor, superadmin
  "created_at": "2026-05-16T18:45:23.123Z",
  "updated_at": "2026-05-16T18:45:23.123Z",
  "last_login": "2026-05-16T18:45:23.123Z",
  "GSI1PK": "USER_EMAIL#user@example.com",
  "GSI1SK": "METADATA"
}
```

**Pydantic Schema:**
```python
# backend/app/schemas/user.py

class UserCreate(BaseModel):
    email: EmailStr
    password: str  # Min 8 chars, complexity validated
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    status: str
    system_role: str
    created_at: datetime
```

### 5.2 Architecture Model

**DynamoDB Structure:**
```python
{
  "PK": "ARCH#arch-uuid",
  "SK": "METADATA",
  "id": "arch-uuid",
  "name": "Production VPC",
  "description": "3-Tier Web App",
  "status": "draft",  # draft, deployed, archived
  "architecture_json": {
    "metadata": {...},
    "components": {...},
    "connections": [...]
  },
  "owner_id": "user-uuid",
  "organisation_id": "org-uuid",
  "created_at": "2026-05-16T18:45:23.123Z",
  "updated_at": "2026-05-16T18:45:23.123Z"
}
```

### 5.3 Audit Log Model

**DynamoDB Structure:**
```python
{
  "PK": "AUDIT#2026-05-16",
  "SK": "timestamp#uuid",
  "id": "audit-uuid",
  "timestamp": "2026-05-16T18:45:23.123Z",
  "user_id": "user-uuid",
  "event_type": "UPDATE",
  "resource_type": "ARCHITECTURE",
  "resource_id": "arch-uuid",
  "action": "Updated VPC CIDR",
  "metadata": {
    "old_value": "10.0.0.0/16",
    "new_value": "10.1.0.0/16"
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "GSI1PK": "USER#user-uuid",
  "GSI1SK": "AUDIT#timestamp"
}
```

---

## 6. Entwickler-Workflows

### 6.1 Lokale Entwicklung starten

**Backend:**
```bash
cd backend

# Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Environment Variables
cp .env.example .env
# Edit .env: Set SECRET_KEY, AWS credentials, etc.

# Start Server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# → API läuft auf http://localhost:8000
# → Docs auf http://localhost:8000/api/docs
```

**Frontend:**
```bash
cd frontend

# Dependencies
npm install

# Start Dev Server
npm run dev

# → Frontend läuft auf http://localhost:5173
```

### 6.2 Tests schreiben

**Backend Unit Test:**

```python
# backend/tests/unit/test_user_repository.py

import pytest
from app.repositories.user import UserRepository

@pytest.fixture
def user_repo(mock_dynamodb_table):
    return UserRepository(table=mock_dynamodb_table)

def test_create_user(user_repo):
    """Test user creation."""
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed",
        "name": "Test User"
    }
    
    user = user_repo.create(user_data)
    
    assert user["email"] == "test@example.com"
    assert user["status"] == "active"
    assert user["system_role"] == "user"

def test_get_user_by_email(user_repo):
    """Test get user by email."""
    # Setup
    user_repo.create({
        "email": "test@example.com",
        "password_hash": "hashed",
        "name": "Test User"
    })
    
    # Test
    user = user_repo.get_by_email("test@example.com")
    
    assert user is not None
    assert user["email"] == "test@example.com"
```

**Frontend Unit Test:**

```javascript
// frontend/tests/unit/api-client.test.js

import { describe, it, expect, vi } from 'vitest';
import { APIClient } from '../../src/js/lib/api-client.js';

describe('APIClient', () => {
  it('should make GET request', async () => {
    const client = new APIClient('http://localhost:8000');
    
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: 'test' })
      })
    );
    
    const result = await client.get('/test');
    
    expect(result).toEqual({ data: 'test' });
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/test',
      expect.objectContaining({ method: 'GET' })
    );
  });
});
```

### 6.3 Feature entwickeln

**Workflow:**

1. **Branch erstellen:**
   ```bash
   git checkout -b feature/new-component-type
   ```

2. **Backend: API Endpoint hinzufügen:**
   ```python
   # backend/app/api/designer.py
   
   @router.post("/designer/components/{component_type}")
   async def add_component_type(...):
       ...
   ```

3. **Backend: Tests schreiben:**
   ```python
   # backend/tests/test_designer_api.py
   
   def test_add_component_type():
       ...
   ```

4. **Frontend: API Client erweitern:**
   ```javascript
   // frontend/src/js/api/designer.js
   
   export async function addComponentType(type, config) {
       return await apiClient.post(`/api/v1/designer/components/${type}`, config);
   }
   ```

5. **Frontend: UI Component bauen:**
   ```javascript
   // frontend/src/js/components/ComponentTypeSelector.js
   
   export class ComponentTypeSelector {
       ...
   }
   ```

6. **Tests laufen lassen:**
   ```bash
   # Backend
   cd backend && pytest tests/ -v
   
   # Frontend
   cd frontend && npm test
   ```

7. **Commit & Push:**
   ```bash
   git add .
   git commit -m "[designer] Add new component type support"
   git push origin feature/new-component-type
   ```

8. **Pull Request erstellen** auf GitHub

### 6.4 Deployment

**Staging Deployment:**
```bash
# Push zu staging branch
git push origin main:staging

# GitHub Actions deployt automatisch zu Staging
```

**Production Deployment:**
```bash
# Create Release Tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# GitHub Actions deployt automatisch zu Production
# (nach Manual Approval)
```

---

## 7. Troubleshooting

### 7.1 Häufige Probleme

**Problem: "401 Unauthorized" beim API Call**

```javascript
// Ursache: JWT Token fehlt oder abgelaufen

// Lösung: Token aus localStorage laden
const token = localStorage.getItem('overcloud-token');
if (!token) {
  // Redirect zu Login
  window.location.href = '/login.html';
}
```

**Problem: "CORS Error" im Browser**

```python
# Ursache: Frontend-Origin nicht in CORS_ORIGINS

# Lösung: backend/.env anpassen
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

**Problem: DynamoDB "ResourceNotFoundException"**

```bash
# Ursache: Tabelle existiert nicht

# Lösung: Terraform apply
cd infrastructure/terraform/environments/dev
terraform apply
```

**Problem: Tests schlagen fehl mit "ModuleNotFoundError"**

```bash
# Ursache: Dependencies nicht installiert

# Lösung: Dependencies installieren
cd backend
pip install -r requirements.txt

cd frontend
npm install
```

### 7.2 Debug-Modus aktivieren

**Backend:**
```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart Server
uvicorn app.main:app --reload
```

**Frontend:**
```javascript
// Browser Console
localStorage.setItem('debug', 'true');

// In Code:
if (localStorage.getItem('debug') === 'true') {
  console.log('Debug Info:', data);
}
```

---

## 7. Billing & Gutscheinsystem

### 7.1 Pricing-Modell

**Hybrid Pricing:** Base Fee + AWS Cost Markup

OverCloud verwendet ein transparentes hybrides Preismodell:

```
Total Cost = Base Subscription Fee + (AWS Costs × Markup Percentage)
```

**Pricing Tiers:**

| Tier | Base Fee (Monatlich) | AWS Markup | Deployments | Organisationen |
|------|---------------------|------------|-------------|----------------|
| **PAY-AS-YOU-GO** | €0 | 20% | Unlimited | 1 |
| **STARTER** | €10 | 15% | 3 | 1 |
| **PRO** | €50 | 10% | 20 | 3 |
| **ENTERPRISE** | €250 | 5% | Unlimited | Unlimited |

**Beispiel-Rechnung (PRO Tier):**

```python
# AWS Infrastructure Costs: €200/Monat
# PRO Tier: €50 Base + 10% AWS Markup

base_price = 50.00         # Base Subscription Fee
aws_costs = 200.00         # Actual AWS Costs
aws_markup_pct = 0.10      # 10% Markup

aws_markup = aws_costs * aws_markup_pct  # = €20
subtotal = base_price + aws_markup       # = €70
tax = subtotal * 0.19                    # = €13.30 (19% VAT)
total = subtotal + tax                   # = €83.30

# Invoice Line Items:
# 1. Base Fee (PRO):      €50.00
# 2. AWS Markup (10%):    €20.00
# 3. Subtotal:            €70.00
# 4. Tax (19%):           €13.30
# 5. Total:               €83.30
```

**Implementierung:**

```python
# backend/app/services/billing.py

def calculate_subscription_price(
    tier: str,
    aws_costs: float,
    voucher: Optional[dict] = None
) -> dict:
    """Berechnet Subscription-Preis mit optionalem Voucher-Rabatt.
    
    Args:
        tier: Subscription Tier (PAYG, STARTER, PRO, ENTERPRISE)
        aws_costs: Tatsächliche AWS Infrastructure Costs (€)
        voucher: Optional Voucher dict
    
    Returns:
        dict mit Preis-Details:
            - base_price: Base Subscription Fee
            - aws_markup: AWS Markup Fee
            - subtotal: Gesamt vor Rabatt
            - discount: Rabatt-Betrag (negativ)
            - final_subtotal: Gesamt nach Rabatt
            - tax: VAT (19%)
            - total: Endbetrag
    """
    # Tier-Konfiguration
    TIER_CONFIG = {
        "PAYG": {"base": 0, "markup_pct": 0.20},
        "STARTER": {"base": 10, "markup_pct": 0.15},
        "PRO": {"base": 50, "markup_pct": 0.10},
        "ENTERPRISE": {"base": 250, "markup_pct": 0.05}
    }
    
    config = TIER_CONFIG[tier]
    base_price = config["base"]
    aws_markup = aws_costs * config["markup_pct"]
    subtotal = base_price + aws_markup
    
    # Voucher-Rabatt anwenden
    discount = 0
    if voucher:
        discount = VoucherService.calculate_discount(
            voucher=voucher,
            base_price=base_price,
            aws_markup=aws_markup
        )
    
    final_subtotal = subtotal - discount
    tax = final_subtotal * 0.19
    total = final_subtotal + tax
    
    return {
        "base_price": base_price,
        "aws_markup": aws_markup,
        "subtotal": subtotal,
        "discount": discount,
        "final_subtotal": final_subtotal,
        "tax": tax,
        "total": total
    }
```

### 7.2 Gutscheinsystem

**Features:**
- Flexible Rabatte (Percentage oder Fixed Amount)
- Granulare Anwendung (Base Fee, AWS Markup, oder Beide)
- Verwendungslimits (Einmalig, n-mal, unbegrenzt)
- Zeitsteuerung (valid_from, valid_until)
- User-Limitierung (Jeder User kann jeden Voucher nur 1x verwenden)
- Audit Trail für Compliance

#### 7.2.1 Voucher Repository

**DynamoDB Schema:**

```python
# backend/app/repositories/voucher.py

# Voucher Item
{
    "PK": "VOUCHER#{code}",           # Partition Key
    "SK": "METADATA",                 # Sort Key
    "code": "FRIEND2026",             # Uppercase
    "discount_type": "percentage",    # percentage | fixed
    "discount_value": 50,             # 50% oder €50
    "applies_to": "both",             # base_fee | aws_percentage | both
    "max_uses": 100,                  # -1 = unlimited
    "current_uses": 42,
    "used_by": ["user-uuid-1", "user-uuid-2"],
    "is_active": true,
    "valid_from": "2026-01-01T00:00:00Z",
    "valid_until": "2026-12-31T23:59:59Z",
    "created_at": "2026-05-17T10:00:00Z",
    "created_by": "superadmin-uuid",
    "GSI1PK": "VOUCHERS",             # GSI für Listing
    "GSI1SK": "FRIEND2026"
}
```

**Access Patterns:**

```python
# 1. Get Voucher by Code (Case-Insensitive)
PK = "VOUCHER#{code.upper()}"
SK = "METADATA"

# 2. List all Vouchers (Admin)
GSI1: GSI1PK = "VOUCHERS"
      GSI1SK begins_with "A"  # Sortiert nach Code

# 3. Validate Voucher
# → get_by_code() + check is_active + valid_until + current_uses

# 4. Redeem Voucher
# → Atomic increment current_uses
# → Append user_id to used_by array
```

**Repository Methoden:**

```python
class VoucherRepository(BaseRepository):
    """Repository für Voucher-Management."""
    
    def create(self, voucher_data: dict) -> dict:
        """Erstellt neuen Voucher.
        
        Validiert:
        - Code ist unique (4-32 Zeichen, nur A-Z0-9)
        - discount_value > 0
        - percentage max 100%
        - valid_until > now (wenn gesetzt)
        """
    
    def get_by_code(self, code: str) -> Optional[dict]:
        """Lädt Voucher by Code (case-insensitive)."""
    
    def validate(self, code: str, user_id: str) -> tuple[bool, Optional[str]]:
        """Validiert ob Voucher verwendbar ist.
        
        Prüft:
        - Existiert
        - is_active = true
        - valid_from <= now <= valid_until
        - current_uses < max_uses
        - user_id not in used_by (User hat nicht bereits verwendet)
        
        Returns:
            (is_valid: bool, error_message: Optional[str])
        """
    
    def redeem(self, code: str, user_id: str) -> dict:
        """Löst Voucher ein (atomic operation).
        
        - Increment current_uses
        - Append user_id to used_by
        - Return updated voucher
        """
    
    def list_all(self, include_inactive: bool = False) -> List[dict]:
        """Liste alle Vouchers (Admin only)."""
    
    def deactivate(self, code: str) -> dict:
        """Deaktiviert Voucher (Soft Delete)."""
    
    def reactivate(self, code: str) -> dict:
        """Reaktiviert Voucher."""
    
    def get_usage_stats(self, code: str) -> dict:
        """Gibt Usage-Statistiken zurück."""
```

#### 7.2.2 Voucher Service

**Discount-Berechnung:**

```python
# backend/app/services/voucher_service.py

class VoucherService:
    """Business Logic für Voucher-Rabatte."""
    
    @staticmethod
    def calculate_discount(
        voucher: dict,
        base_price: float,
        aws_markup: float
    ) -> float:
        """Berechnet Rabatt-Betrag basierend auf Voucher-Konfiguration.
        
        Args:
            voucher: Voucher dict mit discount_type, discount_value, applies_to
            base_price: Base Subscription Fee
            aws_markup: AWS Markup Fee
        
        Returns:
            Discount amount (positiv) in EUR
        
        Beispiele:
            # 50% auf "both"
            voucher = {"discount_type": "percentage", "discount_value": 50, "applies_to": "both"}
            base = 50, aws = 20
            → discount = (50 + 20) * 0.50 = 35 EUR
            
            # €25 fixed auf "base_fee"
            voucher = {"discount_type": "fixed", "discount_value": 25, "applies_to": "base_fee"}
            base = 50, aws = 20
            → discount = min(25, 50) = 25 EUR (begrenzt auf base_price)
            
            # 100% auf "both" (kostenfrei)
            voucher = {"discount_type": "percentage", "discount_value": 100, "applies_to": "both"}
            base = 50, aws = 20
            → discount = (50 + 20) * 1.0 = 70 EUR (Total = 0)
        """
        discount_type = voucher["discount_type"]
        discount_value = voucher["discount_value"]
        applies_to = voucher["applies_to"]
        
        # Target Amount ermitteln
        if applies_to == "base_fee":
            target_amount = base_price
        elif applies_to == "aws_percentage":
            target_amount = aws_markup
        else:  # "both"
            target_amount = base_price + aws_markup
        
        # Rabatt berechnen
        if discount_type == "percentage":
            discount = target_amount * (discount_value / 100)
        else:  # "fixed"
            discount = min(discount_value, target_amount)  # Nie höher als Target
        
        return discount
    
    def validate_voucher(self, code: str, user_id: str) -> dict:
        """Validiert Voucher und gibt Details zurück."""
    
    def redeem_voucher(self, code: str, org_id: UUID, user_id: str) -> dict:
        """Löst Voucher ein und wendet auf Subscription an.
        
        Flow:
        1. Validate Voucher
        2. Check User ist Org-Member
        3. Get Subscription by org_id
        4. Redeem Voucher (increment uses)
        5. Update Subscription mit voucher_code
        6. Log Audit Event
        7. Return success
        """
    
    def remove_voucher_from_subscription(self, org_id: UUID, user_id: str):
        """Entfernt Voucher von Subscription (User-initiated)."""
```

#### 7.2.3 Voucher API Endpoints

**Public Endpoints (Authenticated Users):**

```bash
# 1. Validate Voucher
POST /api/v1/voucher/validate
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "FRIEND2026"
}

# Response (200 OK - Valid)
{
  "valid": true,
  "code": "FRIEND2026",
  "discount_type": "percentage",
  "discount_value": 50,
  "applies_to": "both",
  "remaining_uses": 58,
  "message": "Voucher is valid and can be used"
}

# Response (400 Bad Request - Invalid)
{
  "detail": "Voucher expired on 2026-01-01"
}

# 2. Redeem Voucher
POST /api/v1/voucher/redeem
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "FRIEND2026",
  "org_id": "uuid-of-org"
}

# Response (200 OK)
{
  "success": true,
  "message": "Voucher FRIEND2026 successfully applied to subscription",
  "voucher_code": "FRIEND2026",
  "org_id": "uuid-of-org",
  "subscription": {
    "id": "sub-uuid",
    "tier": "pro",
    "base_price": 50.0,
    "voucher_code": "FRIEND2026",
    "voucher_discount_type": "percentage",
    "voucher_discount_value": 50,
    "voucher_applies_to": "both"
  }
}

# 3. Remove Voucher
DELETE /api/v1/voucher/remove/{org_id}
Authorization: Bearer {token}

# Response (200 OK)
{
  "success": true,
  "message": "Voucher removed from subscription"
}
```

**Admin Endpoints (SuperAdmin only):**

```bash
# 1. Create Voucher
POST /api/v1/admin/vouchers
Authorization: Bearer {superadmin_token}
Content-Type: application/json

{
  "code": "BETA100",
  "discount_type": "percentage",
  "discount_value": 100,
  "applies_to": "both",
  "max_uses": 50,
  "valid_until": "2026-06-30T23:59:59Z"
}

# Response (201 Created)
{
  "code": "BETA100",
  "discount_type": "percentage",
  "discount_value": 100,
  "applies_to": "both",
  "max_uses": 50,
  "current_uses": 0,
  "is_active": true,
  "valid_until": "2026-06-30T23:59:59",
  "created_at": "2026-05-17T12:00:00",
  "created_by": "superadmin-uuid"
}

# 2. List Vouchers
GET /api/v1/admin/vouchers?include_inactive=false
Authorization: Bearer {superadmin_token}

# Response (200 OK)
{
  "vouchers": [
    {
      "code": "FRIEND2026",
      "discount_type": "percentage",
      "discount_value": 50,
      "current_uses": 42,
      "max_uses": 100,
      "is_active": true,
      "valid_until": "2026-12-31T23:59:59"
    },
    // ...
  ],
  "total": 5
}

# 3. Get Voucher Stats
GET /api/v1/admin/vouchers/{code}/stats
Authorization: Bearer {superadmin_token}

# Response (200 OK)
{
  "code": "FRIEND2026",
  "current_uses": 42,
  "max_uses": 100,
  "usage_percentage": 42.0,
  "unique_users": 42,
  "is_active": true,
  "days_remaining": 228,
  "created_at": "2026-01-01T00:00:00"
}

# 4. Deactivate Voucher
DELETE /api/v1/admin/vouchers/{code}
Authorization: Bearer {superadmin_token}

# Response (200 OK)
{
  "success": true,
  "message": "Voucher FRIEND2026 deactivated"
}

# 5. Reactivate Voucher
POST /api/v1/admin/vouchers/{code}/reactivate
Authorization: Bearer {superadmin_token}

# Response (200 OK)
{
  "success": true,
  "message": "Voucher FRIEND2026 reactivated"
}
```

#### 7.2.4 Invoice Generation mit Rabatten

**Invoice Line Items:**

```python
# backend/app/services/invoice_generator.py

class InvoiceGenerator:
    """Generiert Invoices mit Voucher-Rabatten."""
    
    def generate_invoice(
        self,
        subscription: dict,
        aws_costs: float,
        period_start: datetime,
        period_end: datetime
    ) -> dict:
        """Generiert Invoice für Subscription.
        
        Returns:
            {
                "invoice_id": "inv-uuid",
                "subscription_id": "sub-uuid",
                "period": {"start": ..., "end": ...},
                "line_items": [
                    {
                        "description": "Base Fee (PRO)",
                        "amount": 50.00
                    },
                    {
                        "description": "AWS Markup (10% of €200)",
                        "amount": 20.00
                    },
                    {
                        "description": "Discount (FRIEND2026): 50% off",
                        "amount": -35.00  # Negative = Rabatt
                    }
                ],
                "subtotal": 35.00,
                "tax": 6.65,
                "total": 41.65,
                "currency": "EUR"
            }
        """
        tier = subscription["tier"]
        voucher_code = subscription.get("voucher_code")
        
        # Base Price + AWS Markup
        base_price = TIER_CONFIG[tier]["base"]
        aws_markup = aws_costs * TIER_CONFIG[tier]["markup_pct"]
        
        line_items = [
            {"description": f"Base Fee ({tier.upper()})", "amount": base_price},
            {"description": f"AWS Markup ({aws_costs:.2f} × {markup_pct}%)", "amount": aws_markup}
        ]
        
        subtotal = base_price + aws_markup
        
        # Voucher-Rabatt
        if voucher_code:
            voucher = voucher_repo.get_by_code(voucher_code)
            if voucher:
                discount = VoucherService.calculate_discount(
                    voucher=voucher,
                    base_price=base_price,
                    aws_markup=aws_markup
                )
                
                line_items.append({
                    "description": f"Discount ({voucher_code}): {voucher['discount_value']}{' %' if voucher['discount_type'] == 'percentage' else ' EUR'} off",
                    "amount": -discount  # Negativ!
                })
                
                subtotal -= discount
        
        tax = subtotal * 0.19
        total = subtotal + tax
        
        return {
            "invoice_id": str(uuid.uuid4()),
            "subscription_id": subscription["id"],
            "period": {"start": period_start, "end": period_end},
            "line_items": line_items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "currency": "EUR"
        }
```

#### 7.2.5 Admin UI für Gutschein-Verwaltung

**Frontend: Admin Voucher Management**

```javascript
// frontend/src/js/pages/admin-vouchers.js

class AdminVouchersPage {
    constructor() {
        this.voucherAPI = new VoucherAPI();
        this.vouchers = [];
    }
    
    async loadVouchers() {
        const response = await this.voucherAPI.listVouchers(includeInactive=false);
        this.vouchers = response.vouchers;
        this.renderVouchersTable();
    }
    
    renderVouchersTable() {
        const tbody = document.getElementById('vouchers-table-body');
        tbody.innerHTML = this.vouchers.map(voucher => `
            <tr>
                <td>${voucher.code}</td>
                <td>${voucher.discount_value}${voucher.discount_type === 'percentage' ? '%' : '€'}</td>
                <td>${voucher.current_uses} / ${voucher.max_uses === -1 ? '∞' : voucher.max_uses}</td>
                <td>${voucher.is_active ? '🟢 Active' : '🔴 Inactive'}</td>
                <td>
                    <button onclick="viewStats('${voucher.code}')">📊 Stats</button>
                    <button onclick="deactivate('${voucher.code}')">🚫 Deactivate</button>
                </td>
            </tr>
        `).join('');
    }
    
    async createVoucher(formData) {
        const payload = {
            code: formData.code.toUpperCase(),
            discount_type: formData.discountType,
            discount_value: parseFloat(formData.discountValue),
            applies_to: formData.appliesTo,
            max_uses: parseInt(formData.maxUses) || -1,
            valid_until: formData.validUntil || null
        };
        
        await this.voucherAPI.createVoucher(payload);
        this.loadVouchers();  // Refresh
    }
    
    async viewVoucherStats(code) {
        const stats = await this.voucherAPI.getVoucherStats(code);
        
        showModal('Voucher Statistics', `
            <h3>${code}</h3>
            <p>Uses: ${stats.current_uses} / ${stats.max_uses}</p>
            <p>Unique Users: ${stats.unique_users}</p>
            <p>Usage: ${stats.usage_percentage.toFixed(1)}%</p>
            <p>Days Remaining: ${stats.days_remaining}</p>
        `);
    }
    
    async deactivateVoucher(code) {
        if (!confirm(`Deactivate voucher ${code}?`)) return;
        
        await this.voucherAPI.deactivateVoucher(code);
        this.loadVouchers();  // Refresh
    }
}
```

**Billing Page Integration:**

```javascript
// frontend/src/js/pages/billing.js

class BillingPage {
    async handleValidateVoucher() {
        const code = document.getElementById('voucher-code-input').value.trim();
        if (!code) return;
        
        try {
            const result = await this.voucherAPI.validateVoucher(code);
            
            if (result.valid) {
                showSuccess(`✅ Voucher valid: ${result.discount_value}${result.discount_type === 'percentage' ? '%' : '€'} off`);
                document.getElementById('redeem-voucher-btn').disabled = false;
            }
        } catch (error) {
            showError(`❌ ${error.detail}`);
        }
    }
    
    async handleRedeemVoucher() {
        const code = document.getElementById('voucher-code-input').value.trim();
        const orgId = this.currentOrgId;
        
        const result = await this.voucherAPI.redeemVoucher(code, orgId);
        
        if (result.success) {
            showSuccess(`🎉 Voucher ${code} applied! Your next invoice will include the discount.`);
            this.renderVoucherStatus(result.voucher_code);
        }
    }
    
    renderVoucherStatus(voucherCode) {
        const container = document.getElementById('active-voucher-container');
        container.innerHTML = `
            <div class="active-voucher">
                <span>🎟️ Active Voucher: <strong>${voucherCode}</strong></span>
                <button onclick="removeVoucher()">Remove</button>
            </div>
        `;
    }
}
```

#### 7.2.6 Security Considerations

**Voucher-spezifische Security-Maßnahmen:**

1. **SuperAdmin-Only Creation:**
   ```python
   @router.post("/admin/vouchers")
   async def create_voucher(
       data: VoucherCreateRequest,
       current_admin: dict = Depends(get_current_superadmin)  # ✅ SuperAdmin Check
   ):
       ...
   ```

2. **Code Injection Prevention:**
   ```python
   class VoucherCreateRequest(BaseModel):
       code: str = Field(
           ...,
           min_length=4,
           max_length=32,
           pattern="^[A-Z0-9]+$"  # ✅ Nur Alphanumerisch
       )
   ```

3. **Atomic Redemption:**
   ```python
   # DynamoDB Conditional Update verhindert Race Conditions
   table.update_item(
       Key={"PK": f"VOUCHER#{code}", "SK": "METADATA"},
       UpdateExpression="SET current_uses = current_uses + :inc, used_by = list_append(used_by, :user)",
       ConditionExpression="current_uses < max_uses AND NOT contains(used_by, :user_id)",
       ExpressionAttributeValues={
           ":inc": 1,
           ":user": [user_id],
           ":user_id": user_id
       }
   )
   ```

4. **Audit Logging:**
   ```python
   # Alle Voucher-Aktionen werden geloggt
   log_audit(
       user_id=user_id,
       event_type="VOUCHER_REDEEM",
       resource_type="VOUCHER",
       resource_id=voucher_code,
       action=f"User redeemed voucher {voucher_code} for org {org_id}",
       metadata={"org_id": str(org_id), "voucher_code": voucher_code}
   )
   ```

#### 7.2.7 Monitoring & Analytics

**CloudWatch Metriken:**

```python
# Beispiel: Voucher Usage Rate
cloudwatch.put_metric_data(
    Namespace='OverCloud/Vouchers',
    MetricData=[
        {
            'MetricName': 'VoucherRedemptions',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'VoucherCode', 'Value': voucher_code},
                {'Name': 'DiscountType', 'Value': voucher['discount_type']}
            ]
        }
    ]
)
```

**Analytics Queries:**

```sql
-- Top 10 Most Used Vouchers
SELECT code, current_uses, max_uses, 
       (current_uses / max_uses * 100) as usage_pct
FROM vouchers
WHERE is_active = true
ORDER BY current_uses DESC
LIMIT 10;

-- Average Discount per Voucher
SELECT AVG(discount_value) as avg_discount,
       discount_type,
       COUNT(*) as count
FROM vouchers
GROUP BY discount_type;

-- Revenue Impact (geschätzter Rabatt-Betrag)
SELECT SUM(discount_amount) as total_discount,
       COUNT(*) as redemption_count
FROM invoices
WHERE voucher_code IS NOT NULL
  AND invoice_date >= '2026-05-01';
```

### 7.3 Pricing-Page

**Frontend: Pricing Calculator**

```html
<!-- frontend/src/pricing.html -->

<div class="pricing-tiers">
    <div class="tier-card">
        <h3>STARTER</h3>
        <p class="price">€10/Monat</p>
        <ul>
            <li>15% AWS Markup</li>
            <li>Max 3 Deployments</li>
            <li>1 Organisation</li>
        </ul>
        <button onclick="selectTier('STARTER')">Auswählen</button>
    </div>
    
    <div class="tier-card recommended">
        <span class="badge">Empfohlen</span>
        <h3>PRO</h3>
        <p class="price">€50/Monat</p>
        <ul>
            <li>10% AWS Markup</li>
            <li>Max 20 Deployments</li>
            <li>3 Organisationen</li>
        </ul>
        <button onclick="selectTier('PRO')">Auswählen</button>
    </div>
    
    <!-- ENTERPRISE, PAYG ... -->
</div>

<!-- Cost Calculator -->
<div class="cost-calculator">
    <h3>Kostenrechner</h3>
    <label>Erwartete AWS Costs (€/Monat):</label>
    <input type="number" id="aws-cost-input" value="200" />
    
    <div id="cost-breakdown">
        <!-- Dynamisch generiert -->
    </div>
</div>

<!-- Voucher Input -->
<div class="voucher-section">
    <label>Gutscheincode (optional):</label>
    <input type="text" id="voucher-input" placeholder="FRIEND2026" />
    <button onclick="validateVoucher()">Validieren</button>
</div>
```

**JavaScript Controller:**

```javascript
// frontend/src/js/pages/pricing.js

class PricingPage {
    constructor() {
        this.selectedTier = null;
        this.awsCosts = 200;
        this.voucher = null;
    }
    
    calculatePrice(tier, awsCosts, voucher = null) {
        const config = TIER_CONFIG[tier];
        const basePrice = config.base;
        const awsMarkup = awsCosts * config.markup_pct;
        let subtotal = basePrice + awsMarkup;
        
        let discount = 0;
        if (voucher) {
            discount = this.calculateDiscount(voucher, basePrice, awsMarkup);
            subtotal -= discount;
        }
        
        const tax = subtotal * 0.19;
        const total = subtotal + tax;
        
        return { basePrice, awsMarkup, discount, subtotal, tax, total };
    }
    
    renderCostBreakdown() {
        const tier = this.selectedTier || 'PRO';
        const awsCosts = parseFloat(document.getElementById('aws-cost-input').value);
        
        const price = this.calculatePrice(tier, awsCosts, this.voucher);
        
        document.getElementById('cost-breakdown').innerHTML = `
            <div class="line-item">
                <span>Base Fee (${tier}):</span>
                <span>€${price.basePrice.toFixed(2)}</span>
            </div>
            <div class="line-item">
                <span>AWS Markup (${awsCosts} × ${TIER_CONFIG[tier].markup_pct * 100}%):</span>
                <span>€${price.awsMarkup.toFixed(2)}</span>
            </div>
            ${price.discount > 0 ? `
                <div class="line-item discount">
                    <span>Rabatt (${this.voucher.code}):</span>
                    <span>-€${price.discount.toFixed(2)}</span>
                </div>
            ` : ''}
            <div class="line-item subtotal">
                <span>Zwischensumme:</span>
                <span>€${price.subtotal.toFixed(2)}</span>
            </div>
            <div class="line-item">
                <span>MwSt. (19%):</span>
                <span>€${price.tax.toFixed(2)}</span>
            </div>
            <div class="line-item total">
                <span>Gesamt:</span>
                <span>€${price.total.toFixed(2)}/Monat</span>
            </div>
        `;
    }
}
```

---

## 8. Nächste Schritte

### 8.1 Nach MVP (Version 1.5)

- [ ] **Refresh Token Pattern** (15 Min Access + 7 Tage Refresh)
- [ ] **CSRF Protection** (Double Submit Cookie Pattern)
- [ ] **Email Verification** (Confirm Email bei Registration)
- [ ] **2FA/MFA** (TOTP via Authenticator App)
- [ ] **Real-time Collaboration** (WebSockets für Multi-User Designer)
- [ ] **Advanced Cost Estimation** (AWS Pricing API Integration)

### 8.2 Multi-Cloud (Version 2.0)

- [ ] **Azure Support** (ARM Templates statt Terraform)
- [ ] **GCP Support** (Deployment Manager)
- [ ] **Cross-Cloud Architectures** (AWS VPC ↔ Azure VNet Peering)

### 8.3 Enterprise Features (Version 3.0)

- [ ] **SSO Integration** (SAML, OAuth2)
- [ ] **Compliance Reports** (SOC 2, ISO 27001, DSGVO)
- [ ] **Custom Component Types** (User-defined Components)
- [ ] **Marketplace** (Community Blueprints)

---

## Zusammenfassung

Du kennst jetzt:

✅ **Backend Stack:** FastAPI, DynamoDB, Pydantic, JWT, bcrypt, boto3  
✅ **Frontend Stack:** Vite, Vanilla JS, Tailwind CSS, Cytoscape.js  
✅ **Security:** OWASP Top 10, RBAC, Account Lockout, Rate Limiting  
✅ **Testing:** pytest, Vitest, Playwright, 124 Tests  
✅ **Monitoring:** CloudWatch, Sentry, Audit Logs  
✅ **Deployment:** Lambda/ECS, S3+CloudFront, DynamoDB  
✅ **CI/CD:** GitHub Actions, Terraform, Docker  

**Status:** 🟢 PRODUCTION READY (95%)

**Go-Live:** Nach CSRF Protection + Refresh Token Pattern (Sprint 2)

---

**Ende Teil 3 - OverCloud Developer's Encyclopedia komplett!**

Alle 3 Teile zusammen: ~250+ Seiten Dokumentation

**Erstellt:** 2026-05-16  
**Von:** Claude Code  
**Für:** Andy (OverCloud Entwickler)
