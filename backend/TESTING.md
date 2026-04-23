# Testing Guide - DynamoDB Local

Lokales Testing mit DynamoDB Local (ohne AWS Account).

## 🚀 Quick Start (3 Schritte)

### 1. Docker starten

```bash
# Docker Desktop öffnen und starten
# Warten bis "Docker is running" erscheint
```

### 2. DynamoDB Local + Tabelle erstellen

```bash
cd backend

# DynamoDB Local starten
./scripts/start_dynamodb_local.sh

# Tabelle mit allen GSIs erstellen
./scripts/create_dynamodb_table.sh
```

### 3. Backend starten

```bash
# Environment variables setzen
export DYNAMODB_TABLE_NAME=overcloud-dev-main
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=fakekey
export AWS_SECRET_ACCESS_KEY=fakesecret

# Backend starten (Port 8001 wegen DynamoDB auf 8000)
poetry run uvicorn app.main:app --reload --port 8001
```

✅ **Backend läuft auf:** http://localhost:8001

---

## 📋 Manuelle Tests

### Health Check

```bash
curl http://localhost:8001/health
# {"status":"healthy","version":"0.1.0"}
```

### Swagger UI öffnen

```bash
open http://localhost:8001/api/docs
```

### CRUD Flow testen

```bash
# Einfacher Test (nur Create, Get, List)
./test_simple.sh

# Vollständiger Test (mit Update, Delete, Cost Estimation)
./scripts/test_api_local.sh
```

**Dieser Test macht:**
1. ✅ Health Check
2. ✅ Architecture erstellen
3. ✅ Architecture abrufen
4. ✅ Liste abrufen
5. ✅ Architecture updaten
6. ✅ Cost Estimation
7. ✅ Architecture löschen
8. ✅ Deletion verifizieren

---

## 🧪 Erwartete Ergebnisse

### ✅ Erfolgreicher Test

```bash
$ ./scripts/test_api_local.sh

🧪 Testing OverCloud API...

1️⃣  Health Check
{
  "status": "healthy",
  "version": "0.1.0"
}

2️⃣  Create Architecture
Created Architecture: 123e4567-e89b-12d3-a456-426614174000
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Test Web App",
  "version": "1.0.0",
  ...
}

3️⃣  Get Architecture
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Test Web App",
  ...
}

...

✅ All tests completed!
```

### ❌ Häufige Fehler

#### Fehler: "Cannot connect to Docker"

```bash
Cannot connect to the Docker daemon. Is the docker daemon running?
```

**Lösung:** Docker Desktop starten

#### Fehler: "Table does not exist"

```bash
ResourceNotFoundException: Requested resource not found: Table
```

**Lösung:** Tabelle erstellen
```bash
./scripts/create_dynamodb_table.sh
```

#### Fehler: "Unable to locate credentials"

```bash
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Lösung:** Environment Variables setzen
```bash
export AWS_ACCESS_KEY_ID=fakekey
export AWS_SECRET_ACCESS_KEY=fakesecret
```

---

## 🔍 Debug Commands

### DynamoDB Local Status

```bash
# Check if running
docker ps | grep dynamodb-local

# View logs
docker logs -f dynamodb-local

# Stop
docker stop dynamodb-local
```

### Tabelle inspizieren

```bash
# Describe table
aws dynamodb describe-table \
    --table-name overcloud-dev-main \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

# List items
aws dynamodb scan \
    --table-name overcloud-dev-main \
    --endpoint-url http://localhost:8000 \
    --region us-east-1 \
    --max-items 10
```

### Backend Logs

```bash
# Mit verbose logging starten
export LOG_LEVEL=DEBUG
poetry run uvicorn app.main:app --reload --log-level debug
```

---

## 🎯 Test-Szenarien

### Szenario 1: Architecture CRUD

```bash
# Create
ARCH_ID=$(curl -s -X POST http://localhost:8001/api/v1/architectures \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","owner":"me","version":"1.0","architecture_json":{}}' \
  | jq -r '.id')

# Read
curl http://localhost:8001/api/v1/architectures/$ARCH_ID | jq

# Update
curl -X PUT http://localhost:8001/api/v1/architectures/$ARCH_ID \
  -H "Content-Type: application/json" \
  -d '{"description":"Updated"}' | jq

# Delete
curl -X DELETE http://localhost:8001/api/v1/architectures/$ARCH_ID
```

### Szenario 2: Deployment Flow (Mock)

```bash
# Deploy Architecture
DEPLOY_ID=$(curl -s -X POST http://localhost:8001/api/v1/architectures/$ARCH_ID/deploy \
  -H "Content-Type: application/json" \
  -d '{"deployed_by":"test@example.com"}' \
  | jq -r '.id')

# Get Status
curl http://localhost:8001/api/v1/deployments/$DEPLOY_ID | jq '.status'

# Get Logs
curl http://localhost:8001/api/v1/deployments/$DEPLOY_ID/logs | jq

# Cancel
curl -X POST http://localhost:8001/api/v1/deployments/$DEPLOY_ID/cancel
```

**Note:** Deployment wird fehlschlagen (Terraform nicht verfügbar), aber API funktioniert!

### Szenario 3: Audit Logs

```bash
# List audit logs
curl http://localhost:8001/api/v1/audit-logs?limit=20 | jq

# Stats (pre-aggregated)
curl http://localhost:8001/api/v1/audit-logs/stats | jq
```

---

## 📊 Performance Check

```bash
# Test response time
time curl -s http://localhost:8001/api/v1/architectures > /dev/null

# Should be < 100ms for local DynamoDB
```

---

## 🧹 Cleanup

```bash
# Stop DynamoDB Local
docker stop dynamodb-local
docker rm dynamodb-local

# Clear data (DynamoDB Local uses in-memory storage)
# Data is lost when container stops
```

---

## 🚢 Next Steps

Nach erfolgreichem lokalem Test:

1. **AWS Setup:** Echte DynamoDB Tabelle deployen
   ```bash
   cd infrastructure/terraform/environments/dev
   terraform apply -target=module.database-dynamodb
   ```

2. **Production Test:** Mit echtem AWS testen
   ```bash
   unset DYNAMODB_ENDPOINT_URL  # Use real AWS
   export AWS_PROFILE=overcloud-dev
   poetry run uvicorn app.main:app --reload --port 8001
   ```

3. **Monitoring:** CloudWatch Dashboards einrichten

4. **CI/CD:** GitHub Actions für automatische Tests

---

## 💡 Tipps

- **Development:** Immer DynamoDB Local verwenden (schneller, kostenlos)
- **Integration Tests:** DynamoDB Local in Docker Compose
- **Production Tests:** Separate Test-Tabelle in AWS
- **CI/CD:** DynamoDB Local Container in GitHub Actions

---

**Viel Erfolg beim Testen!** 🚀
