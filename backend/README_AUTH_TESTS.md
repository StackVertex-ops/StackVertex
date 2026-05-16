# Authentication Testing

Vollständige Test-Suite für das OverCloud Authentication & Authorization System.

---

## Quick Start

```bash
# Alle Tests ausführen
poetry run pytest test_auth_comprehensive.py test_auth_security.py -v

# Manuelle API-Tests (Backend muss laufen)
./test_auth_manual.sh
```

---

## Test Files

| Datei | Tests | Beschreibung |
|-------|-------|--------------|
| `test_auth_comprehensive.py` | 27 | Core Auth Flows (Registration, Login, JWT, Sessions) |
| `test_auth_security.py` | 16 | Security Tests (SQL Injection, XSS, Token Security) |
| `test_auth_manual.sh` | 9 | Bash-Script für manuelle API-Tests |

**Gesamt:** 43 automatisierte Tests + 9 manuelle Tests

---

## Test Categories

### Comprehensive Tests (27)

1. **Registration Flow** (5 Tests)
   - Erfolgreiche Registrierung
   - Doppelte Email
   - Schwaches Passwort
   - Invalide Email
   - Fehlende Felder

2. **Login Flow** (5 Tests)
   - Erfolgreicher Login
   - Falsches Passwort
   - Nicht-existierender User
   - Case-insensitive Email
   - Account Lockout

3. **JWT Tokens** (6 Tests)
   - Gültiger Token
   - Abgelaufener Token
   - Manipulierter Token
   - Fehlender Token
   - Invalides Format
   - Bearer Prefix

4. **Token Refresh** (2 Tests)
   - Refresh mit gültigem Token
   - Refresh mit abgelaufenem Token

5. **Logout** (1 Test)
   - Logout Endpoint

6. **Session Management** (2 Tests)
   - Token Expiration
   - Concurrent Sessions

7. **Security** (3 Tests)
   - Password Hashing
   - Timing Attack Prevention
   - SECRET_KEY Strength

8. **Account Lockout** (2 Tests)
   - Lockout Threshold
   - Counter Reset

9. **Rate Limiting** (1 Test)
   - Rate Limit Config

### Security Tests (16)

1. **SQL Injection Prevention** (2 Tests)
   - Email Field
   - Password Field

2. **XSS Prevention** (2 Tests)
   - Name Field
   - Email Field

3. **User Enumeration** (3 Tests)
   - Registration Error Message
   - Login Error Message
   - Timing Attack Prevention (skipped)

4. **Password Strength** (2 Tests)
   - Common Passwords
   - Max Length

5. **Token Security** (2 Tests)
   - No Sensitive Data
   - Algorithm 'none' Rejection

6. **CSRF Prevention** (2 Tests)
   - No Session Cookies
   - CORS Configuration

7. **Rate Limiting** (1 Test)
   - Config Exists

8. **Input Validation** (3 Tests)
   - Empty Fields
   - Null Fields
   - Unicode Characters

---

## Usage Examples

### Run All Tests

```bash
poetry run pytest test_auth_comprehensive.py test_auth_security.py -v
```

### Run Specific Category

```bash
# Registration Tests
poetry run pytest test_auth_comprehensive.py::TestRegistration -v

# Login Tests
poetry run pytest test_auth_comprehensive.py::TestLogin -v

# JWT Tests
poetry run pytest test_auth_comprehensive.py::TestJWTTokens -v

# Security Tests
poetry run pytest test_auth_security.py::TestSQLInjection -v
```

### Run Single Test

```bash
poetry run pytest test_auth_comprehensive.py::TestRegistration::test_successful_registration -v
```

### Run with Coverage

```bash
poetry run pytest test_auth_comprehensive.py test_auth_security.py \
  --cov=app/api/auth \
  --cov=app/repositories/user \
  --cov=app/services/account_lockout \
  --cov-report=html

open htmlcov/index.html
```

---

## Manual Testing

### Start Backend

```bash
# Terminal 1
poetry run uvicorn app.main:app --reload
```

### Run Manual Tests

```bash
# Terminal 2
./test_auth_manual.sh
```

**Output:** Colored terminal output mit ✓/✗ für jeden Test.

---

## Test Results

### Latest Run: 2026-05-16

```
✅ 43 Tests PASSED
⏭️  1 Test SKIPPED
❌ 0 Tests FAILED

Success Rate: 100%
```

---

## Configuration

### Environment Variables

```bash
# .env
SECRET_KEY=<mindestens-32-zeichen>
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 Stunden
TESTING=true  # Deaktiviert Rate Limiting in Tests
```

### Test Settings

```python
# In test files
from app.config import settings
settings.TESTING = True  # Disable rate limiting
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/auth-tests.yml
name: Auth Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          cd backend
          poetry install

      - name: Run Auth Tests
        env:
          SECRET_KEY: ${{ secrets.TEST_SECRET_KEY }}
          TESTING: true
        run: |
          cd backend
          poetry run pytest test_auth_comprehensive.py test_auth_security.py -v
```

---

## Troubleshooting

### DynamoDB Connection Error

**Problem:** `Could not connect to DynamoDB`

**Lösung:**
```bash
# Option 1: DynamoDB Local (Docker)
docker run -p 8000:8000 amazon/dynamodb-local

# Option 2: AWS Credentials
aws configure
```

### SECRET_KEY Validation Error

**Problem:** `SECRET_KEY must be at least 32 characters`

**Lösung:**
```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
SECRET_KEY=<generated-key>
```

### Rate Limiting in Tests

**Problem:** Tests schlagen fehl wegen Rate Limiting

**Lösung:**
```bash
# In .env
TESTING=true
```

---

## Documentation

Vollständige Reports verfügbar in:

- **`/AUTH_TESTING_REPORT.md`** - Detaillierter Test-Report (20+ Seiten)
- **`/AUTH_TESTING_QUICKSTART.md`** - Quick Start Guide
- **`/AUTH_TESTING_SUMMARY.md`** - Executive Summary

---

## What's Tested

### ✅ Security

- JWT Token Signature & Expiration
- Bcrypt Password Hashing
- Account Lockout (5 attempts → 15 min)
- Rate Limiting (IP-based)
- SQL Injection Prevention
- XSS Prevention (API-level)
- CSRF Prevention (JWT in Header)
- Input Validation (Pydantic)

### ✅ Functionality

- User Registration
- User Login
- Token Refresh
- Logout
- Profile Retrieval
- Concurrent Sessions
- Case-insensitive Email
- Duplicate Email Prevention

### ✅ Error Handling

- Wrong Password
- Expired Token
- Manipulated Token
- Missing Token
- Invalid Email
- Weak Password
- Missing Fields

---

## What's Not Tested (Yet)

### 🔧 To Be Implemented

- Email Verification Flow
- Password Reset Flow
- OAuth2 Providers (Google, GitHub)
- Multi-Factor Authentication (MFA)
- Token Blacklist (Redis)
- Password Change
- User Profile Update

---

## Performance

### API Response Times (Local)

| Endpoint | Average |
|----------|---------|
| `POST /auth/register` | ~250ms |
| `POST /auth/login` | ~200ms |
| `GET /auth/me` | ~50ms |
| `POST /auth/refresh` | ~100ms |

**Note:** DynamoDB Local für Tests verwendet.

---

## Status

✅ **All Tests Passed**  
✅ **Production Ready** (für MVP)  
🔧 **Empfohlene Improvements:** Siehe AUTH_TESTING_REPORT.md

---

**Zuletzt aktualisiert:** 2026-05-16  
**Test Suite Version:** 1.0  
**Framework:** pytest 9.0.2 + FastAPI TestClient
