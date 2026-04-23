# OverCloud API - Beispiele & Usage Guide

Praktische Beispiele für alle OverCloud API Endpoints mit DynamoDB Backend.

---

## 🚀 Quick Start

**Backend starten (lokal mit DynamoDB Local):**

```bash
# Environment setzen
export DYNAMODB_TABLE_NAME=overcloud-dev-main
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=fakekey
export AWS_SECRET_ACCESS_KEY=fakesecret

# Backend starten
poetry run uvicorn app.main:app --reload --port 8001
```

**Base URL:** `http://localhost:8001`

---

## 📖 Inhaltsverzeichnis

- [Health Check](#health-check)
- [Architectures API](#architectures-api)
- [Deployments API](#deployments-api)
- [Audit Logs API](#audit-logs-api)
- [Cost Estimation API](#cost-estimation-api)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)

---

## Health Check

### GET /health

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Architectures API

### 1. Create Architecture

**POST /api/v1/architectures**

```bash
curl -X POST http://localhost:8001/api/v1/architectures \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Web Application",
    "description": "Scalable web app with load balancer and database",
    "version": "1.0.0",
    "owner": "team@example.com",
    "architecture_json": {
      "version": "1.0.0",
      "metadata": {
        "name": "Production Web Application",
        "created_by": "Architecture Team"
      },
      "requirements": {
        "compute": {
          "type": "container",
          "replicas": 3,
          "cpu": "2vcpu",
          "memory": "4GB"
        },
        "database": {
          "type": "relational",
          "engine": "postgresql",
          "version": "15",
          "storage": "100GB"
        },
        "networking": {
          "public_access": true,
          "ssl": true,
          "load_balancer": true
        }
      },
      "components": [
        {
          "id": "load-balancer",
          "type": "alb",
          "properties": {
            "scheme": "internet-facing",
            "cross_zone": true
          }
        },
        {
          "id": "web-service",
          "type": "ecs_service",
          "properties": {
            "image": "myapp:latest",
            "port": 3000,
            "desired_count": 3,
            "cpu": 1024,
            "memory": 2048
          }
        },
        {
          "id": "database",
          "type": "rds_postgresql",
          "properties": {
            "instance_class": "db.t3.medium",
            "allocated_storage": 100,
            "engine_version": "15.2",
            "multi_az": true
          }
        }
      ],
      "connections": [
        {
          "from": "load-balancer",
          "to": "web-service",
          "type": "http"
        },
        {
          "from": "web-service",
          "to": "database",
          "type": "tcp",
          "port": 5432
        }
      ]
    }
  }'
```

**Response:**
```json
{
  "id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
  "name": "Production Web Application",
  "description": "Scalable web app with load balancer and database",
  "version": "1.0.0",
  "owner": "team@example.com",
  "architecture_json": { ... },
  "created_at": "2026-04-19T19:46:04.600617",
  "updated_at": "2026-04-19T19:46:04.600617"
}
```

**Status:** `201 Created`

---

### 2. Get Architecture

**GET /api/v1/architectures/{id}**

```bash
ARCH_ID="a13ed937-7fee-43f0-a1de-62e3b6201a74"
curl http://localhost:8001/api/v1/architectures/$ARCH_ID
```

**Response:**
```json
{
  "id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
  "name": "Production Web Application",
  "description": "Scalable web app with load balancer and database",
  "version": "1.0.0",
  "owner": "team@example.com",
  "architecture_json": {
    "version": "1.0.0",
    "components": [ ... ]
  },
  "created_at": "2026-04-19T19:46:04.600617",
  "updated_at": "2026-04-19T19:46:04.600617"
}
```

**Status:** `200 OK`

**Errors:**
- `404 Not Found` - Architecture nicht gefunden

---

### 3. List Architectures

**GET /api/v1/architectures**

```bash
# Alle Architectures (paginiert)
curl "http://localhost:8001/api/v1/architectures?skip=0&limit=10"

# Filter by owner
curl "http://localhost:8001/api/v1/architectures?owner=team@example.com&limit=10"
```

**Response:**
```json
{
  "items": [
    {
      "id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
      "name": "Production Web Application",
      "version": "1.0.0",
      "owner": "team@example.com",
      "created_at": "2026-04-19T19:46:04.600617"
    },
    {
      "id": "b24fe048-8eff-54e1-b2ef-73f4c7302b85",
      "name": "Development Environment",
      "version": "1.0.0",
      "owner": "team@example.com",
      "created_at": "2026-04-19T19:50:12.123456"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 10
}
```

**Query Parameters:**
- `skip` (int, default: 0) - Offset für Pagination
- `limit` (int, default: 100, max: 1000) - Items pro Seite
- `owner` (string, optional) - Filter nach Owner

---

### 4. Update Architecture

**PUT /api/v1/architectures/{id}**

```bash
curl -X PUT http://localhost:8001/api/v1/architectures/$ARCH_ID \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated: Production-ready web application with HA",
    "architecture_json": {
      "version": "1.1.0",
      "components": [ ... ]
    }
  }'
```

**Response:**
```json
{
  "id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
  "name": "Production Web Application",
  "description": "Updated: Production-ready web application with HA",
  "version": "1.0.0",
  "architecture_json": {
    "version": "1.1.0",
    "components": [ ... ]
  },
  "updated_at": "2026-04-19T20:15:30.789012"
}
```

**Status:** `200 OK`

**Note:** Partial Update - nur übergebene Felder werden aktualisiert.

---

### 5. Delete Architecture

**DELETE /api/v1/architectures/{id}**

```bash
curl -X DELETE http://localhost:8001/api/v1/architectures/$ARCH_ID
```

**Response:** (leer)

**Status:** `204 No Content`

**Errors:**
- `404 Not Found` - Architecture nicht gefunden

---

### 6. Get Version History

**GET /api/v1/architectures/{id}/versions**

```bash
curl "http://localhost:8001/api/v1/architectures/$ARCH_ID/versions?limit=10"
```

**Response:**
```json
[
  {
    "id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
    "name": "Production Web Application",
    "version": "1.1.0",
    "created_at": "2026-04-19T20:15:30.789012"
  },
  {
    "id": "c35fg159-9fff-65f2-c3fg-84g5d8403c96",
    "name": "Production Web Application",
    "version": "1.0.0",
    "created_at": "2026-04-19T19:46:04.600617"
  }
]
```

**Query Parameters:**
- `limit` (int, optional) - Max. Anzahl Versionen

---

### 7. Compare Versions (Diff)

**GET /api/v1/architectures/{id}/diff/{other_id}**

```bash
OLD_ID="c35fg159-9fff-65f2-c3fg-84g5d8403c96"
NEW_ID="a13ed937-7fee-43f0-a1de-62e3b6201a74"

curl "http://localhost:8001/api/v1/architectures/$OLD_ID/diff/$NEW_ID?component_level=true"
```

**Response:**
```json
{
  "version_a": {
    "id": "c35fg159-9fff-65f2-c3fg-84g5d8403c96",
    "name": "Production Web Application",
    "version": "1.0.0",
    "created_at": "2026-04-19T19:46:04.600617"
  },
  "version_b": {
    "id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
    "name": "Production Web Application",
    "version": "1.1.0",
    "created_at": "2026-04-19T20:15:30.789012"
  },
  "diff": {
    "added": ["requirements.database.multi_az"],
    "removed": [],
    "modified": ["components.web-service.desired_count"],
    "summary": "1 added, 0 removed, 1 modified"
  },
  "component_diff": {
    "added_components": [],
    "removed_components": [],
    "modified_components": ["web-service"]
  }
}
```

---

### 8. Validate Architecture JSON

**POST /api/v1/architectures/validate**

```bash
curl -X POST http://localhost:8001/api/v1/architectures/validate \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "components": [
      {
        "id": "web-server",
        "type": "ecs_service",
        "properties": {
          "image": "nginx:latest"
        }
      }
    ]
  }'
```

**Success Response:**
```json
{
  "valid": true,
  "version": "1.0.0",
  "validated_at": "2026-04-19T20:30:45.123456"
}
```

**Error Response:**
```json
{
  "valid": false,
  "errors": [
    "components[0].properties: missing required field 'port'",
    "components[0].properties: 'cpu' must be a number"
  ],
  "version": "1.0.0"
}
```

**Status:**
- `200 OK` - Valid
- `422 Unprocessable Entity` - Invalid

---

## Deployments API

### 1. Deploy Architecture

**POST /api/v1/architectures/{id}/deploy**

```bash
curl -X POST http://localhost:8001/api/v1/architectures/$ARCH_ID/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "deployed_by": "ops@example.com",
    "aws_credentials": {
      "access_key_id": "AKIAIOSFODNN7EXAMPLE",
      "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
      "region": "us-east-1"
    }
  }'
```

**Response:**
```json
{
  "id": "d46gh260-0ggg-76g3-d4gh-95h6e9504d07",
  "architecture_id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
  "status": "pending",
  "deployed_by": "ops@example.com",
  "started_at": "2026-04-19T20:45:00.000000",
  "terraform_version": null
}
```

**Status:** `201 Created`

---

### 2. Get Deployment Status

**GET /api/v1/deployments/{id}**

```bash
DEPLOY_ID="d46gh260-0ggg-76g3-d4gh-95h6e9504d07"
curl http://localhost:8001/api/v1/deployments/$DEPLOY_ID
```

**Response:**
```json
{
  "id": "d46gh260-0ggg-76g3-d4gh-95h6e9504d07",
  "architecture_id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
  "status": "applying",
  "deployed_by": "ops@example.com",
  "terraform_version": "1.5.7",
  "started_at": "2026-04-19T20:45:00.000000",
  "progress_percentage": 60,
  "current_step": "Applying infrastructure changes",
  "elapsed_seconds": 45.23,
  "estimated_remaining_seconds": 30.15
}
```

**Possible Status Values:**
- `pending` - Waiting to start
- `generating` - Generating Terraform code
- `initializing` - Initializing Terraform
- `planning` - Planning infrastructure changes
- `applying` - Applying infrastructure changes
- `success` - Deployment completed successfully
- `failed` - Deployment failed
- `destroying` - Destroying infrastructure
- `destroyed` - Infrastructure destroyed
- `cancelled` - Deployment cancelled

---

### 3. List Deployments

**GET /api/v1/deployments**

```bash
# All deployments
curl "http://localhost:8001/api/v1/deployments?limit=20"

# Filter by architecture
curl "http://localhost:8001/api/v1/deployments?architecture_id=$ARCH_ID"

# Filter by status
curl "http://localhost:8001/api/v1/deployments?status=success"
```

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 1000)
- `architecture_id` (UUID, optional)
- `status` (string, optional)

---

### 4. Get Deployment Logs

**GET /api/v1/deployments/{id}/logs**

```bash
curl http://localhost:8001/api/v1/deployments/$DEPLOY_ID/logs
```

**Response:**
```json
{
  "deployment_id": "d46gh260-0ggg-76g3-d4gh-95h6e9504d07",
  "plan_output": "Terraform will perform the following actions:\n\n  # aws_instance.web will be created...",
  "apply_output": "aws_instance.web: Creating...\naws_instance.web: Creation complete after 45s",
  "error_message": null
}
```

**Note:** Outputs werden automatisch aus S3 geladen (transparent).

---

### 5. Cancel Deployment

**POST /api/v1/deployments/{id}/cancel**

```bash
curl -X POST http://localhost:8001/api/v1/deployments/$DEPLOY_ID/cancel
```

**Response:**
```json
{
  "deployment_id": "d46gh260-0ggg-76g3-d4gh-95h6e9504d07",
  "status": "cancelled",
  "message": "Deployment cancelled successfully"
}
```

**Status:** `200 OK`

**Errors:**
- `400 Bad Request` - Deployment kann nicht gecancelt werden (z.B. bereits abgeschlossen)
- `404 Not Found` - Deployment nicht gefunden

---

### 6. Retry Deployment

**POST /api/v1/deployments/{id}/retry**

```bash
curl -X POST http://localhost:8001/api/v1/deployments/$DEPLOY_ID/retry \
  -H "Content-Type: application/json" \
  -d '{
    "aws_credentials": {
      "access_key_id": "AKIAIOSFODNN7EXAMPLE",
      "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
      "region": "us-east-1"
    }
  }'
```

**Response:**
```json
{
  "id": "e57hi371-1hhh-87h4-e5hi-06i7f0615e18",
  "architecture_id": "a13ed937-7fee-43f0-a1de-62e3b6201a74",
  "status": "pending",
  "deployed_by": "ops@example.com",
  "started_at": "2026-04-19T21:00:00.000000"
}
```

**Status:** `201 Created` (neues Deployment erstellt)

---

### 7. Destroy Deployment

**DELETE /api/v1/deployments/{id}**

```bash
curl -X DELETE http://localhost:8001/api/v1/deployments/$DEPLOY_ID \
  -H "Content-Type: application/json" \
  -d '{
    "aws_credentials": {
      "access_key_id": "AKIAIOSFODNN7EXAMPLE",
      "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
      "region": "us-east-1"
    }
  }'
```

**Response:** (leer)

**Status:** `204 No Content`

---

## Audit Logs API

### 1. List Audit Logs

**GET /api/v1/audit-logs**

```bash
# All logs
curl "http://localhost:8001/api/v1/audit-logs?limit=50"

# Filter by user
curl "http://localhost:8001/api/v1/audit-logs?user=ops@example.com"

# Filter by action
curl "http://localhost:8001/api/v1/audit-logs?action=deploy_start"

# Filter by resource
curl "http://localhost:8001/api/v1/audit-logs?resource_type=deployment"
```

**Response:**
```json
{
  "items": [
    {
      "id": "f68ij482-2iii-98i5-f6ij-17j8g1726f29",
      "user": "ops@example.com",
      "action": "deploy_start",
      "resource_type": "deployment",
      "resource_id": "d46gh260-0ggg-76g3-d4gh-95h6e9504d07",
      "ip_address": "192.168.1.100",
      "user_agent": "curl/7.79.1",
      "details": {
        "architecture_id": "a13ed937-7fee-43f0-a1de-62e3b6201a74"
      },
      "success": true,
      "error_message": null,
      "timestamp": "2026-04-19T20:45:00.123456"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 1000)
- `user` (string, optional)
- `action` (string, optional)
- `resource_type` (string, optional)
- `resource_id` (UUID, optional)

---

### 2. Get Audit Statistics

**GET /api/v1/audit-logs/stats**

```bash
curl http://localhost:8001/api/v1/audit-logs/stats
```

**Response:**
```json
{
  "total_logs": 1234,
  "failed_actions": 45,
  "actions": {
    "deploy_start": 500,
    "deploy_cancel": 20,
    "deploy_retry": 15,
    "architecture_create": 300,
    "architecture_update": 250,
    "architecture_delete": 100
  },
  "top_users": [
    {
      "user": "ops@example.com",
      "count": 600
    },
    {
      "user": "dev@example.com",
      "count": 400
    }
  ],
  "last_updated": "2026-04-19T21:00:00.000000"
}
```

**Note:** Pre-aggregated statistics (O(1) query, < 10ms!)

---

## Cost Estimation API

### 1. Estimate from JSON

**POST /api/v1/costs/estimate**

```bash
curl -X POST http://localhost:8001/api/v1/costs/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "components": [
      {
        "id": "web-service",
        "type": "ecs_service",
        "properties": {
          "cpu": 1024,
          "memory": 2048,
          "desired_count": 3
        }
      },
      {
        "id": "database",
        "type": "rds_postgresql",
        "properties": {
          "instance_class": "db.t3.medium",
          "multi_az": true
        }
      }
    ]
  }'
```

**Response:**
```json
{
  "total_hourly": 0.45,
  "total_monthly": 324.00,
  "total_yearly": 3888.00,
  "currency": "USD",
  "components": [
    {
      "component_id": "web-service",
      "component_type": "ecs_service",
      "component_name": "web-service",
      "hourly_cost": 0.15,
      "monthly_cost": 108.00,
      "breakdown": {
        "compute": 108.00
      }
    },
    {
      "component_id": "database",
      "component_type": "rds_postgresql",
      "component_name": "database",
      "hourly_cost": 0.30,
      "monthly_cost": 216.00,
      "breakdown": {
        "instance": 150.00,
        "storage": 40.00,
        "multi_az": 26.00
      }
    }
  ],
  "breakdown_by_type": {
    "compute": 108.00,
    "database": 216.00
  }
}
```

---

### 2. Estimate for Saved Architecture

**GET /api/v1/costs/architectures/{id}/estimate**

```bash
curl http://localhost:8001/api/v1/costs/architectures/$ARCH_ID/estimate
```

**Response:** (gleiche Struktur wie oben)

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success, no content
- `400 Bad Request` - Invalid request
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Validation Errors

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    },
    {
      "type": "string_too_short",
      "loc": ["body", "version"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

---

## Performance Tips

### 1. Pagination

Immer `limit` Parameter verwenden:

```bash
# Gut (schnell)
curl "http://localhost:8001/api/v1/architectures?limit=10"

# Schlecht (langsam bei vielen Items)
curl "http://localhost:8001/api/v1/architectures?limit=1000"
```

### 2. Filtering

Filter in DynamoDB nutzen statt client-seitig:

```bash
# Gut (DynamoDB GSI Query)
curl "http://localhost:8001/api/v1/architectures?owner=team@example.com"

# Schlecht (alle laden, dann filtern)
curl "http://localhost:8001/api/v1/architectures?limit=1000" | jq '.items[] | select(.owner=="team@example.com")'
```

### 3. Caching

Wiederholte GET-Requests cachen:

```bash
# Cache-Header setzen
curl -H "Cache-Control: max-age=300" http://localhost:8001/api/v1/architectures/$ARCH_ID
```

### 4. Batch Operations

Mehrere Requests parallel statt sequenziell:

```bash
# Parallel (schnell)
curl http://localhost:8001/api/v1/architectures/id1 & \
curl http://localhost:8001/api/v1/architectures/id2 & \
wait

# Sequenziell (langsam)
curl http://localhost:8001/api/v1/architectures/id1
curl http://localhost:8001/api/v1/architectures/id2
```

---

## WebSocket (Real-time Updates)

### Connect to Deployment Status

```javascript
const ws = new WebSocket('ws://localhost:8001/api/v1/ws/deployments/d46gh260-0ggg-76g3-d4gh-95h6e9504d07');

ws.onopen = () => {
  console.log('Connected to deployment status');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status update:', data);
  // { type: 'status_update', status: 'applying', progress_percentage: 60, ... }
};

// Request current status
ws.send(JSON.stringify({ action: 'get_status' }));

// Ping
ws.send(JSON.stringify({ action: 'ping' }));
```

---

## Rate Limiting

**Current Limits:**
- 100 requests per minute per IP (planned)
- 1000 requests per hour per user (planned)

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1619712000
```

---

## Authentication (Future)

**Planned:**
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -d '{"username":"user","password":"pass"}' | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/v1/architectures
```

---

## Further Resources

- **Swagger UI:** http://localhost:8001/api/docs
- **ReDoc:** http://localhost:8001/api/redoc
- **OpenAPI JSON:** http://localhost:8001/api/openapi.json
- **Migration Guide:** [DYNAMODB_MIGRATION.md](../DYNAMODB_MIGRATION.md)
- **Testing Guide:** [TESTING.md](../TESTING.md)

---

**Last Updated:** 2026-04-19  
**API Version:** 0.1.0  
**Backend:** DynamoDB + S3
