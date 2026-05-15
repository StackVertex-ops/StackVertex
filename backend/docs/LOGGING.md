# Logging & Monitoring

OverCloud Backend verwendet **Structured Logging** (JSON-Format) für Production-Deployments mit optionaler Integration von **AWS CloudWatch** und **Sentry** für Error Tracking.

---

## 📋 Features

### ✅ Structured Logging (JSON Format)
- **Development:** Human-readable format
- **Production:** JSON format für Log-Aggregation (CloudWatch, ELK, etc.)
- Automatische Context-Fields (timestamp, level, logger, request info)
- Exception Tracebacks in Logs

### ☁️ AWS CloudWatch Integration (Optional)
- Automatischer Log-Upload zu CloudWatch Logs
- Log Group: `/overcloud/backend`
- Stream: `{environment}-api`
- Async Batch-Upload (alle 10 Sekunden)

### 🔔 Sentry Error Tracking (Optional)
- Automatisches Capture von Errors
- Performance Tracing (Traces & Profiling)
- GDPR-konform (kein PII)
- Environment-basiertes Sampling

---

## 🚀 Konfiguration

### Environment Variables

Füge zu `.env` hinzu:

```bash
# Logging Level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# JSON Logging (für Production)
LOG_JSON_FORMAT=true

# AWS CloudWatch (optional)
ENABLE_CLOUDWATCH=false

# Sentry Error Tracking (optional)
ENABLE_SENTRY=false
SENTRY_DSN=https://xxxxxxxxxxxxx@sentry.io/xxxxxxx

# Environment Name
ENV=production  # development, staging, production
```

### Development Setup (Default)

```bash
LOG_LEVEL=DEBUG
LOG_JSON_FORMAT=false
ENABLE_CLOUDWATCH=false
ENABLE_SENTRY=false
ENV=development
```

**Output:**
```
2026-05-15 08:50:23 - app.main - INFO - OverCloud API starting
2026-05-15 08:50:23 - app.api.auth - INFO - User logged in: user@example.com
```

### Production Setup

```bash
LOG_LEVEL=INFO
LOG_JSON_FORMAT=true
ENABLE_CLOUDWATCH=true
ENABLE_SENTRY=true
SENTRY_DSN=https://xxxxxxxxxxxxx@sentry.io/xxxxxxx
ENV=production
```

**Output (JSON):**
```json
{
  "timestamp": "2026-05-15 08:50:23",
  "level": "INFO",
  "logger": "app.main",
  "message": "OverCloud API starting",
  "version": "0.1.0",
  "environment": "production"
}
```

---

## 📦 Installation

### Base Logging (Always Installed)

```bash
poetry install
```

Installiert: `python-json-logger`

### CloudWatch Logging (Optional)

```bash
poetry install --extras cloudwatch
```

Installiert: `watchtower`

### Sentry Error Tracking (Optional)

```bash
poetry install --extras sentry
```

Installiert: `sentry-sdk[fastapi]`

### Full Monitoring Stack

```bash
poetry install --extras monitoring
```

Installiert: `watchtower`, `sentry-sdk[fastapi]`

---

## 🧑‍💻 Usage in Code

### Logging Examples

```python
import logging

logger = logging.getLogger(__name__)

# Simple log
logger.info("User registered successfully")

# Log with context (wird zu JSON-Fields)
logger.info(
    "User registered",
    extra={
        "user_id": user_id,
        "email": email,
        "plan": "free"
    }
)

# Error with exception traceback
try:
    deploy_architecture(arch_id)
except Exception as e:
    logger.error(
        f"Deployment failed: {e}",
        exc_info=True,  # Include traceback
        extra={
            "architecture_id": str(arch_id),
            "user_id": str(user_id)
        }
    )
```

### JSON Output (Production)

```json
{
  "timestamp": "2026-05-15 09:15:42",
  "level": "INFO",
  "logger": "app.api.auth",
  "message": "User registered",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "plan": "free"
}
```

### Exception Logging

```json
{
  "timestamp": "2026-05-15 09:20:15",
  "level": "ERROR",
  "logger": "app.services.deployment",
  "message": "Deployment failed: Terraform execution error",
  "architecture_id": "abc-def-123",
  "user_id": "user-456",
  "exception": "Traceback (most recent call last):\n  File \"...\", line 42, in deploy\n    ..."
}
```

---

## ☁️ CloudWatch Setup

### AWS Credentials

CloudWatch Logging benötigt AWS Credentials mit **CloudWatch Logs Permissions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/overcloud/*"
    }
  ]
}
```

### IAM Role (Empfohlen für EC2/ECS)

```bash
# Keine Credentials in .env nötig
# IAM Role wird automatisch verwendet
ENABLE_CLOUDWATCH=true
AWS_REGION=us-east-1
```

### Access Keys (Development)

```bash
ENABLE_CLOUDWATCH=true
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### CloudWatch Logs Console

Logs sichtbar unter:
```
AWS Console > CloudWatch > Logs > Log Groups > /overcloud/backend
```

Stream: `production-api`, `staging-api`, `development-api`

---

## 🔔 Sentry Setup

### 1. Sentry Account erstellen

- Gehe zu [sentry.io](https://sentry.io)
- Erstelle neues Projekt (Type: **FastAPI** oder **Python**)
- Kopiere **DSN** (z.B. `https://abc123@sentry.io/456789`)

### 2. Configure .env

```bash
ENABLE_SENTRY=true
SENTRY_DSN=https://abc123@sentry.io/456789
ENV=production
```

### 3. Error Tracking

**Automatisch erfasst:**
- Alle unbehandelten Exceptions
- HTTP 500 Errors
- Background Task Failures

**Sentry Dashboard zeigt:**
- Error Count & Frequency
- Stack Traces
- User Context (falls verfügbar)
- Performance Traces

### Sampling Rates

- **Production:** 10% Traces, 10% Profiles (weniger Traffic)
- **Development:** 100% Traces, 100% Profiles (volle Visibility)

---

## 🛠️ Troubleshooting

### Problem: Logs nicht in CloudWatch

**Lösung:**
1. Prüfe AWS Credentials: `aws sts get-caller-identity`
2. Prüfe IAM Permissions (siehe oben)
3. Prüfe Region: `AWS_REGION=us-east-1`
4. Check Logs: Startup sollte zeigen "CloudWatch logging enabled"

### Problem: Sentry sendet keine Events

**Lösung:**
1. Prüfe DSN: Muss mit `https://` starten
2. Prüfe `ENABLE_SENTRY=true`
3. Teste manuell:
   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Test from backend")
   ```
4. Check Sentry Dashboard > Issues

### Problem: JSON-Logs unleserlich in Development

**Lösung:**
```bash
# Development: Human-readable
LOG_JSON_FORMAT=false

# Production: JSON
LOG_JSON_FORMAT=true
```

### Problem: Zu viele Logs (Performance)

**Lösung:**
```bash
# Reduziere Log Level
LOG_LEVEL=WARNING  # Nur Warnings & Errors
```

Third-Party Libraries sind bereits auf WARNING gesetzt:
- boto3, botocore, urllib3, s3transfer, passlib

---

## 📊 Best Practices

### ✅ DO

- **Verwende `extra={}` für Context-Fields**
  ```python
  logger.info("Action completed", extra={"user_id": user_id})
  ```

- **Log Errors mit `exc_info=True`**
  ```python
  logger.error("Error occurred", exc_info=True)
  ```

- **Strukturierte Messages (JSON-freundlich)**
  ```python
  logger.info("User login", extra={"user_id": id, "method": "email"})
  ```

### ❌ DON'T

- **Keine Secrets loggen**
  ```python
  # BAD
  logger.info(f"Password: {password}")  # NEVER!
  
  # GOOD
  logger.info("User authenticated", extra={"user_id": id})
  ```

- **Keine PII loggen (GDPR)**
  ```python
  # BAD
  logger.info(f"Email: {email}, Address: {address}")
  
  # GOOD
  logger.info("Profile updated", extra={"user_id": hashed_id})
  ```

- **Kein excessives Logging**
  ```python
  # BAD (loops)
  for item in items:
      logger.debug(f"Processing {item}")  # Too much!
  
  # GOOD
  logger.info(f"Processing {len(items)} items")
  logger.debug(f"First item: {items[0]}")
  ```

---

## 🎯 Production Checklist

- [ ] `LOG_JSON_FORMAT=true` gesetzt
- [ ] `LOG_LEVEL=INFO` (oder WARNING)
- [ ] `ENABLE_CLOUDWATCH=true` (wenn AWS)
- [ ] CloudWatch IAM Permissions konfiguriert
- [ ] `ENABLE_SENTRY=true` gesetzt
- [ ] Sentry DSN in `.env` (kein Commit!)
- [ ] Test Error triggern → Sentry Dashboard prüfen
- [ ] CloudWatch Log Group existiert
- [ ] Keine Secrets in Logs

---

## 📚 Links

- [python-json-logger Docs](https://github.com/madzak/python-json-logger)
- [Watchtower (CloudWatch) Docs](https://github.com/kislyuk/watchtower)
- [Sentry Python SDK Docs](https://docs.sentry.io/platforms/python/)
- [AWS CloudWatch Logs](https://docs.aws.amazon.com/cloudwatch/index.html)

---

**Letztes Update:** 2026-05-15
