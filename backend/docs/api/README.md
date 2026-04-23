# OverCloud API Documentation

## Overview

OverCloud Backend API v0.1.0 - Requirements-driven Infrastructure-as-Code platform.

**Base URL:** `http://localhost:8000`  
**API Prefix:** `/api/v1`  
**Interactive Docs:** `/api/docs` (Swagger UI)

---

## Authentication

Currently **no authentication** (MVP Phase). Production will use JWT tokens.

---

## Core Concepts

### JSON-First Architecture
- **JSON is source of truth**, not Terraform
- Every architecture is stored as versioned JSON
- Terraform is generated output from JSON
- All changes create new versions

### Versioning
- Linear version chain: `v3 → v2 → v1`
- Each version has `parent_version_id`
- Updates create new version, original remains unchanged

### Components
- Building blocks of architecture (VPC, EC2, RDS, Lambda, S3, etc.)
- Each component has type, properties, configuration
- Relationships define connections between components

---

## API Endpoints

### 1. Validation

#### `POST /api/v1/validate`

Validate architecture JSON against schema.

**Request Body:**
```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "My Architecture",
    "description": "Description",
    "owner": "user@example.com",
    "region": "us-east-1",
    "tags": ["production", "web-app"]
  },
  "architecture": {
    "components": [...],
    "relationships": [...]
  }
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

**Response (422 Validation Failed):**
```json
{
  "valid": false,
  "errors": [
    {
      "path": "$.metadata.name",
      "message": "'name' is a required property"
    }
  ]
}
```

---

### 2. Architectures

#### `GET /api/v1/architectures`

List all architectures with pagination.

**Query Parameters:**
- `skip` (int, default: 0) - Offset
- `limit` (int, default: 100, max: 1000) - Page size
- `owner` (string, optional) - Filter by owner

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "My Architecture",
      "owner": "user@example.com",
      "version": "1.0.0",
      "parent_version_id": null,
      "created_at": "2026-04-18T10:00:00Z",
      "updated_at": "2026-04-18T10:00:00Z",
      "architecture_json": {...}
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

---

#### `POST /api/v1/architectures`

Create new architecture.

**Request Body:**
```json
{
  "version": "1.0.0",
  "metadata": {...},
  "architecture": {...}
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "My Architecture",
  "parent_version_id": null,
  ...
}
```

---

#### `GET /api/v1/architectures/{id}`

Get architecture by ID.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "architecture_json": {...},
  ...
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Architecture {id} not found"
}
```

---

#### `PUT /api/v1/architectures/{id}`

Update architecture (creates new version).

**Request Body:** Full architecture JSON (same as POST)

**Response (200 OK):**
```json
{
  "id": "new-uuid",
  "parent_version_id": "old-uuid",
  ...
}
```

---

#### `DELETE /api/v1/architectures/{id}`

Delete architecture version.

**Response (204 No Content)**

---

#### `GET /api/v1/architectures/{id}/versions`

Get version history (chain of parent versions).

**Response (200 OK):**
```json
[
  {"id": "v3-uuid", "parent_version_id": "v2-uuid", ...},
  {"id": "v2-uuid", "parent_version_id": "v1-uuid", ...},
  {"id": "v1-uuid", "parent_version_id": null, ...}
]
```

---

#### `GET /api/v1/architectures/{id}/diff/{other_id}`

Compare two architecture versions.

**Response (200 OK):**
```json
{
  "added": {
    "components": [{"id": "new-component", ...}]
  },
  "removed": {
    "components": [{"id": "old-component", ...}]
  },
  "modified": {
    "components": {
      "component-id": {
        "old": {...},
        "new": {...}
      }
    }
  },
  "summary": "Added 1 component, removed 1 component, modified 2 components"
}
```

---

### 3. Cost Estimation

#### `POST /api/v1/costs/estimate`

Estimate cost for architecture JSON.

**Request Body:** Architecture JSON

**Response (200 OK):**
```json
{
  "total_monthly_cost": 125.50,
  "total_hourly_cost": 0.172,
  "currency": "USD",
  "components": [
    {
      "component_id": "web-server",
      "component_name": "Web Server",
      "component_type": "ec2",
      "monthly_cost": 15.20,
      "hourly_cost": 0.0208,
      "breakdown": {
        "instance": "t3.small",
        "region": "us-east-1",
        "hours_per_month": 730
      }
    }
  ]
}
```

---

#### `GET /api/v1/costs/architectures/{id}/estimate`

Estimate cost for saved architecture.

**Response:** Same as POST /costs/estimate

---

### 4. Deployments

#### `POST /api/v1/architectures/{id}/deploy`

Deploy architecture to AWS.

**Request Body:**
```json
{
  "architecture_id": "uuid",
  "deployed_by": "user@example.com",
  "aws_credentials": {
    "AWS_ACCESS_KEY_ID": "AKIA...",
    "AWS_SECRET_ACCESS_KEY": "...",
    "AWS_SESSION_TOKEN": "..." (optional)
  }
}
```

**Response (201 Created):**
```json
{
  "id": "deployment-uuid",
  "architecture_id": "uuid",
  "status": "PENDING",
  "deployed_by": "user@example.com",
  "terraform_version": "1.5.0",
  "created_at": "2026-04-18T10:00:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null
}
```

**Deployment Status:**
- `PENDING` - Queued
- `GENERATING` - Generating Terraform
- `INITIALIZING` - Running terraform init
- `PLANNING` - Running terraform plan
- `APPLYING` - Running terraform apply
- `SUCCESS` - Deployed successfully
- `FAILED` - Deployment failed
- `DESTROYING` - Running terraform destroy
- `DESTROYED` - Infrastructure destroyed

---

#### `GET /api/v1/deployments/{id}`

Get deployment status.

**Response (200 OK):**
```json
{
  "id": "deployment-uuid",
  "status": "SUCCESS",
  "outputs": {
    "vpc_id": "vpc-123",
    "instance_ids": ["i-123", "i-456"]
  },
  "plan_output": "Plan: 5 to add, 0 to change...",
  "apply_output": "Apply complete! Resources: 5 added...",
  ...
}
```

---

#### `GET /api/v1/deployments`

List deployments.

**Query Parameters:**
- `skip`, `limit` - Pagination
- `architecture_id` (uuid, optional) - Filter by architecture
- `status` (string, optional) - Filter by status (PENDING, SUCCESS, FAILED, etc.)

**Response (200 OK):**
```json
{
  "items": [...],
  "total": 10,
  "skip": 0,
  "limit": 100
}
```

---

#### `DELETE /api/v1/deployments/{id}`

Destroy deployed infrastructure.

**Request Body (optional):**
```json
{
  "aws_credentials": {...}
}
```

**Response (204 No Content)**

---

#### `GET /api/v1/deployments/{id}/logs`

Get deployment logs.

**Response (200 OK):**
```json
{
  "deployment_id": "uuid",
  "plan_output": "...",
  "apply_output": "...",
  "error_message": null
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "metadata", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently **no rate limiting** (MVP). Production will implement per-user limits.

---

## Versioning

API Version: **v1**  
Schema Version: **1.0.0**

Breaking changes will increment API version (`/api/v2`).

---

## Example Workflows

### 1. Create and Deploy Architecture

```bash
# 1. Validate architecture
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Content-Type: application/json" \
  -d @architecture.json

# 2. Create architecture
ARCH_ID=$(curl -X POST http://localhost:8000/api/v1/architectures \
  -H "Content-Type: application/json" \
  -d @architecture.json | jq -r '.id')

# 3. Estimate cost
curl http://localhost:8000/api/v1/costs/architectures/$ARCH_ID/estimate

# 4. Deploy
DEPLOY_ID=$(curl -X POST http://localhost:8000/api/v1/architectures/$ARCH_ID/deploy \
  -H "Content-Type: application/json" \
  -d '{"deployed_by":"user@example.com","aws_credentials":{...}}' | jq -r '.id')

# 5. Check status
curl http://localhost:8000/api/v1/deployments/$DEPLOY_ID
```

### 2. Update Existing Architecture

```bash
# 1. Get current version
curl http://localhost:8000/api/v1/architectures/$ARCH_ID > current.json

# 2. Modify JSON (edit current.json)

# 3. Update (creates new version)
NEW_ARCH_ID=$(curl -X PUT http://localhost:8000/api/v1/architectures/$ARCH_ID \
  -H "Content-Type: application/json" \
  -d @current.json | jq -r '.id')

# 4. Compare versions
curl http://localhost:8000/api/v1/architectures/$ARCH_ID/diff/$NEW_ARCH_ID
```

---

## Next Steps

- Production authentication (JWT)
- Rate limiting
- WebSocket support for deployment status updates
- Multi-cloud support (Azure, GCP)
- Blueprint marketplace
