# OverCloud Services Architecture

## Overview

OverCloud Backend follows **Clean Architecture** principles with clear separation of concerns.

```
┌─────────────────────────────────────────────────┐
│            FastAPI Application (main.py)         │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │   API Routers   │  (app/api/)
        │  - validation   │
        │  - architectures│
        │  - costs        │
        │  - deployments  │
        └────────┬────────┘
                 │
    ┌────────────┴────────────────┐
    │                             │
┌───┴────┐                  ┌─────┴──────┐
│  CRUD  │                  │  Services  │
│ Layer  │                  │   Layer    │
└───┬────┘                  └─────┬──────┘
    │                             │
    │  ┌─────────────────────────┴─────────────┐
    │  │      Core Business Logic               │
    │  │  - JSON Versioning Engine             │
    │  │  - Terraform Generator                │
    │  │  - Cost Estimator                     │
    │  │  - Deployment Manager                 │
    │  └───────────────────────────────────────┘
    │
┌───┴────────┐
│  Database  │  (SQLAlchemy)
│   Models   │
└────────────┘
```

---

## Layer Responsibilities

### 1. API Layer (`app/api/`)

**Purpose:** HTTP request/response handling

**Files:**
- `validation.py` - JSON schema validation endpoints
- `architectures.py` - Architecture CRUD endpoints
- `costs.py` - Cost estimation endpoints
- `deployments.py` - Deployment management endpoints

**Responsibilities:**
- Request validation (Pydantic schemas)
- Response formatting
- HTTP status codes
- Error handling (HTTPException)
- Dependency injection (Database sessions)

**Example:**
```python
@router.post("/architectures", status_code=201)
async def create_architecture(
    data: ArchitectureCreate,
    db: Session = Depends(get_db)
):
    architecture = create_architecture_crud(db, data)
    return ArchitectureResponse.model_validate(architecture)
```

---

### 2. CRUD Layer (`app/crud/`)

**Purpose:** Database operations (Create, Read, Update, Delete)

**Files:**
- `architecture.py` - Architecture database operations
- `deployment.py` - Deployment database operations

**Responsibilities:**
- Direct database queries (SQLAlchemy ORM)
- Filtering, pagination, sorting
- Transaction management
- No business logic (just data access)

**Example:**
```python
def get_architectures(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner: Optional[str] = None
) -> Tuple[List[Architecture], int]:
    query = db.query(Architecture)
    if owner:
        query = query.filter(Architecture.owner == owner)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total
```

---

### 3. Services Layer (`app/services/`)

**Purpose:** External integrations & orchestration

**Files:**
- `pricing_data.py` - AWS pricing data loader
- `cost_estimator.py` - Cost calculation service
- `terraform_executor.py` - Terraform CLI wrapper
- `deployment_manager.py` - Deployment orchestration

**Responsibilities:**
- External service calls (AWS SDK, Terraform CLI)
- Complex orchestration workflows
- Caching, retries, error handling
- Environment variable management

**Example:**
```python
class TerraformExecutor:
    def apply(self, auto_approve: bool = False) -> ExecutionResult:
        args = ["terraform", "apply"]
        if auto_approve:
            args.append("-auto-approve")
        
        result = subprocess.run(
            args,
            cwd=self.working_dir,
            capture_output=True,
            timeout=self.timeout
        )
        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout.decode(),
            stderr=result.stderr.decode()
        )
```

---

### 4. Core Business Logic (`app/core/`)

**Purpose:** Domain logic & algorithms

**Modules:**

#### `json_engine/` - JSON Versioning Engine
- `versioning.py` - Version tracking & management
- `diff.py` - JSON diff generation
- `validator.py` - Schema validation
- `migrations/` - Schema migration framework

**Key Concept:** Linear version chain with parent-child relationships.

```python
class VersioningService:
    def create_version(
        self,
        db: Session,
        architecture_json: Dict,
        parent_version_id: Optional[UUID] = None
    ) -> Architecture:
        # Validate JSON
        # Create new Architecture record
        # Link to parent
        # Store diff for fast comparison
```

---

#### `terraform_generator/` - Terraform Code Generator

- `generator.py` - Main generation orchestrator
- `component_mapper.py` - Component type → Terraform template mapping
- `file_builder.py` - Terraform file structure builder
- `validators.py` - Terraform HCL validation
- `filters.py` - Jinja2 custom filters

**Key Concept:** Jinja2 templates → HCL generation → Validation.

```python
class TerraformGenerator:
    def generate(
        self,
        architecture_json: Dict,
        validate: bool = True
    ) -> TerraformProject:
        # 1. Parse architecture JSON
        # 2. Map components to templates
        # 3. Render Jinja2 templates
        # 4. Build file structure (main.tf, variables.tf, etc.)
        # 5. Validate HCL (terraform validate)
        return TerraformProject(files={...})
```

**Templates:**
- `templates/terraform/provider.tf.j2` - AWS provider config
- `templates/terraform/networking/*.tf.j2` - VPC, subnets, security groups
- `templates/terraform/compute/*.tf.j2` - EC2, Lambda
- `templates/terraform/storage/*.tf.j2` - S3, EBS
- `templates/terraform/database/*.tf.j2` - RDS, DynamoDB
- `templates/terraform/load_balancing/*.tf.j2` - ALB, NLB

---

### 5. Models Layer (`app/models/`)

**Purpose:** Database schema definitions

**Files:**
- `database.py` - Database connection & Base model
- `architecture.py` - Architecture model
- `deployment.py` - Deployment model & status enum

**Example:**
```python
class Architecture(Base):
    __tablename__ = "architectures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False, index=True)
    owner = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False, default="1.0.0")
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("architectures.id"), nullable=True)
    architecture_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

### 6. Schemas Layer (`app/schemas/`)

**Purpose:** Request/response validation (Pydantic)

**Files:**
- `architecture.py` - Architecture schemas
- `deployment.py` - Deployment schemas
- `cost.py` - Cost estimation schemas
- `validation.py` - Validation result schemas

**Example:**
```python
class ArchitectureCreate(BaseModel):
    name: str
    owner: str
    architecture_json: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class ArchitectureResponse(BaseModel):
    id: UUID
    name: str
    owner: str
    version: str
    parent_version_id: Optional[UUID]
    created_at: datetime
    architecture_json: Dict[str, Any]
```

---

## Data Flow Examples

### 1. Create Architecture Flow

```
Client → POST /api/v1/architectures
   ↓
API Layer (architectures.py)
   ├─→ Validate request body (Pydantic)
   ├─→ Validate JSON schema (json_engine/validator.py)
   ↓
CRUD Layer (crud/architecture.py)
   ├─→ Create Architecture record
   ├─→ Link parent_version if update
   ├─→ Commit to database
   ↓
Response → ArchitectureResponse (201 Created)
```

---

### 2. Deploy Architecture Flow

```
Client → POST /api/v1/architectures/{id}/deploy
   ↓
API Layer (deployments.py)
   ├─→ Validate request (AWS credentials)
   ↓
Service Layer (deployment_manager.py)
   ├─→ Load architecture from DB (CRUD)
   ├─→ Generate Terraform (terraform_generator/)
   ├─→ Create workspace directory
   ├─→ Write Terraform files
   ├─→ Create Deployment record (CRUD)
   ↓
Terraform Executor (services/terraform_executor.py)
   ├─→ terraform init
   ├─→ terraform validate
   ├─→ terraform plan → save output
   ├─→ terraform apply → save output
   ├─→ terraform output → extract outputs
   ↓
Update Deployment Status (CRUD)
   ├─→ Mark SUCCESS or FAILED
   ├─→ Store logs (plan_output, apply_output)
   ↓
Response → DeploymentResponse (201 Created)
```

---

### 3. Cost Estimation Flow

```
Client → GET /api/v1/costs/architectures/{id}/estimate
   ↓
API Layer (costs.py)
   ├─→ Load architecture (CRUD)
   ↓
Service Layer (cost_estimator.py)
   ├─→ Parse architecture JSON
   ├─→ For each component:
   │     ├─→ Load pricing data (pricing_data.py)
   │     ├─→ Calculate cost (service-specific)
   │     └─→ Accumulate total
   ↓
Response → CostEstimateResponse (200 OK)
```

---

## Key Design Patterns

### 1. Dependency Injection
Database sessions injected via FastAPI `Depends()`:
```python
db: Session = Depends(get_db)
```

### 2. Repository Pattern
CRUD layer acts as repositories for database access.

### 3. Service Layer Pattern
Complex business logic lives in services, not API routes.

### 4. Separation of Concerns
- API: HTTP handling
- CRUD: Data access
- Services: External integrations
- Core: Business logic

### 5. Immutability (Versioning)
Updates create new versions, never modify existing records.

---

## Configuration (`app/config.py`)

Centralized settings via Pydantic `BaseSettings`:

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./overcloud.db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Terraform
    TERRAFORM_BINARY: str = "terraform"
    TERRAFORM_WORKSPACE_DIR: str = "/tmp/overcloud/deployments"
    TERRAFORM_TEMPLATE_DIR: str = "backend/templates/terraform"
    
    # Pricing Data
    PRICING_DATA_DIR: str = "backend/data/aws_pricing"
    
    # Versioning
    CURRENT_SCHEMA_VERSION: str = "1.0.0"
```

---

## Error Handling Strategy

### 1. Validation Errors (422)
Pydantic automatically validates request bodies.

### 2. Business Logic Errors (400)
Services raise `ValueError` → API catches → HTTPException(400)

### 3. Not Found Errors (404)
CRUD returns `None` → API checks → HTTPException(404)

### 4. Internal Errors (500)
Catch-all exception handler logs error → HTTPException(500)

**Example:**
```python
try:
    deployment_id = deployment_manager.start_deployment(...)
except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
    logger.error(f"Deployment failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

---

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies (DB, subprocess, file I/O)
- Fast, deterministic

### Integration Tests
- Test service layer with real database (SQLite in-memory)
- Test Terraform generation end-to-end
- Slower, but comprehensive

### E2E Tests
- Test full API workflows
- Validate request/response cycles
- DB state verification

**Coverage Target:** 80%+ across all modules.

---

## Performance Considerations

### 1. Database
- Indexes on `id`, `owner`, `created_at`
- Pagination for large result sets
- Connection pooling (SQLAlchemy)

### 2. Caching
- Pricing data loaded once via `@lru_cache`
- Terraform templates loaded on startup

### 3. Async Operations
- Deployment runs in background (future: Celery tasks)
- Status polling via GET requests (future: WebSockets)

---

## Security

### 1. Credentials
- AWS credentials never stored in database
- Passed in request body, used immediately
- Written to workspace with 600 permissions
- Workspace cleaned up after 30 days

### 2. Input Validation
- JSON schema validation (architecture format)
- Pydantic validation (API requests)
- SQL injection protection (SQLAlchemy ORM)

### 3. Terraform Execution
- Isolated workspace per deployment
- Timeout protection (600s default)
- Error output sanitization (no credentials in logs)

---

## Future Enhancements

1. **Async Task Queue** (Celery + Redis)
   - Background deployments
   - Retry logic
   - Progress updates

2. **WebSocket Support**
   - Real-time deployment status
   - Log streaming

3. **Multi-Cloud Support**
   - Abstract providers (AWS, Azure, GCP)
   - Provider-specific generators

4. **Caching Layer** (Redis)
   - Cost estimates (TTL: 1 hour)
   - Architecture lookups
   - Session storage

5. **Authentication & Authorization**
   - JWT tokens
   - Role-based access control
   - Multi-tenancy

---

## Deployment

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production (AWS Lambda)
Use **Mangum** adapter for FastAPI on Lambda.

---

## Monitoring

### Logging
- Structured logging (JSON format)
- Levels: DEBUG, INFO, WARNING, ERROR
- CloudWatch integration (production)

### Metrics
- Request count, latency (per endpoint)
- Deployment success/failure rates
- Terraform execution times

### Alerts
- Failed deployments
- API errors (5xx)
- High latency (p95 > 1s)

---

## Conclusion

OverCloud backend is built with **clean architecture**, **separation of concerns**, and **production-readiness** in mind. Each layer has clear responsibilities, making the codebase maintainable, testable, and scalable.

For more details, see:
- [API Documentation](../api/README.md)
- [Deployment Guide](../deployment/GUIDE.md)
- [JSON Schema Specification](../../docs/json-schemas/architecture-v1.0.0.schema.json)
