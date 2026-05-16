# OverCloud Developer's Encyclopedia - Teil 1

**Version:** 1.0  
**Datum:** 2026-05-16  
**Zielgruppe:** Entwickler die OverCloud verstehen und weiterentwickeln wollen  
**Autor:** Claude Agent (mit vollständiger Codebase-Analyse)

---

## Inhaltsverzeichnis

1. [Projekt-Übersicht](#1-projekt-übersicht)
2. [Architektur & Design Patterns](#2-architektur--design-patterns)
3. [Backend - Python Stack](#3-backend---python-stack)
4. [Frontend - JavaScript Stack](#4-frontend---javascript-stack)

---

## 1. Projekt-Übersicht

### 1.1 Was ist OverCloud?

OverCloud ist eine **Requirements-Driven Infrastructure as Code Platform** mit einem visuellen Designer:

**Das Kern-Konzept:**
```
User Input (Visual Designer)
    ↓
JSON State (Source of Truth)
    ↓
Terraform Code Generation
    ↓
AWS Deployment (via Terraform)
```

**Hauptmerkmale:**
- **JSON-First Architecture:** Alles wird als versionierbares JSON gespeichert
- **Visual Infrastructure Designer:** Drag & Drop AWS Components (VPC, EC2, RDS, S3, Lambda...)
- **Live Cost Estimation:** Kosten werden VOR dem Deployment berechnet
- **Terraform Code Generation:** Aus JSON wird produktionsreifer Terraform HCL Code generiert
- **Multi-Cloud Ready:** Abstraction Layer für AWS/Azure/GCP (aktuell nur AWS implementiert)
- **Audit Trail:** Jede Änderung wird geloggt und ist nachvollziehbar

### 1.2 Projektstruktur

```
/Users/andyschwarz/Documents/Privat/OverCloud/
├── .claude/                    # Claude Code Config
│   ├── CLAUDE.md              # Projekt-spezifische Rules
│   ├── settings.local.json    # Lokale Settings
│   └── commands/              # Custom slash commands
│
├── backend/                    # Python FastAPI Backend
│   ├── app/                   # Application Code
│   │   ├── main.py           # FastAPI Entry Point
│   │   ├── config.py         # Settings (Pydantic)
│   │   │
│   │   ├── api/              # REST API Endpoints (FastAPI Routers)
│   │   │   ├── auth.py       # Authentication (Login, Register, JWT)
│   │   │   ├── users.py      # User Management
│   │   │   ├── organisations.py  # Multi-Tenancy
│   │   │   ├── architectures.py  # Architecture CRUD
│   │   │   ├── designer.py   # Designer API (Components, Connections)
│   │   │   ├── terraform.py  # Terraform Generation
│   │   │   ├── deployments.py # Deployment Management
│   │   │   ├── costs.py      # Cost Estimation
│   │   │   ├── billing.py    # Stripe Integration
│   │   │   ├── admin.py      # SuperAdmin Endpoints
│   │   │   ├── audit.py      # Audit Logs
│   │   │   ├── cidr.py       # CIDR Calculator
│   │   │   ├── webhooks.py   # External Webhooks (Stripe, etc.)
│   │   │   └── websockets.py # Real-time Updates (WebSocket)
│   │   │
│   │   ├── repositories/     # Data Access Layer (DynamoDB)
│   │   │   ├── base.py       # BaseRepository (CRUD, S3 Offload)
│   │   │   ├── user.py       # UserRepository
│   │   │   ├── organisation.py   # OrganisationRepository
│   │   │   ├── architecture.py   # ArchitectureRepository
│   │   │   ├── deployment.py     # DeploymentRepository
│   │   │   └── audit_log.py      # AuditLogRepository
│   │   │
│   │   ├── models/           # SQLAlchemy Models (Legacy - wird zu DynamoDB migriert)
│   │   │   ├── user.py
│   │   │   ├── organisation.py
│   │   │   └── deployment.py
│   │   │
│   │   ├── schemas/          # Pydantic Schemas (Request/Response Validation)
│   │   │   ├── user.py       # UserCreate, UserResponse, TokenResponse
│   │   │   ├── organisation.py   # OrganisationCreate, etc.
│   │   │   ├── architecture.py   # ArchitectureCreate, ArchitectureResponse
│   │   │   ├── deployment.py     # DeploymentCreate, DeploymentStatus
│   │   │   └── cost.py           # CostEstimate, CostBreakdown
│   │   │
│   │   ├── services/         # Business Logic & External Integrations
│   │   │   ├── terraform_generator_v2.py  # Terraform Code Generation (Jinja2)
│   │   │   ├── terraform_executor.py      # Terraform Execution (subprocess)
│   │   │   ├── cost_calculator.py         # AWS Cost Estimation
│   │   │   ├── stripe_service.py          # Stripe Payment Integration
│   │   │   └── account_lockout.py         # Brute-Force Protection
│   │   │
│   │   ├── db/               # Database Connections
│   │   │   ├── dynamodb.py   # DynamoDB Client Setup
│   │   │   └── s3_storage.py # S3 Large Item Offload
│   │   │
│   │   ├── core/             # Core Utilities
│   │   │   └── logging.py    # Structured Logging (JSON, CloudWatch, Sentry)
│   │   │
│   │   ├── utils/            # Helper Functions
│   │   │   ├── cidr_calculator.py  # CIDR/IP Address Math
│   │   │   └── validation.py       # Input Validation Helpers
│   │   │
│   │   └── data/             # Static Data
│   │       └── aws_constraints.py  # AWS Service Limits & Constraints
│   │
│   ├── templates/            # Jinja2 Templates
│   │   └── terraform/
│   │       ├── components/   # Component-specific Templates (vpc.tf.j2, ec2.tf.j2...)
│   │       └── lambda_placeholder.py  # Lambda Function Boilerplate
│   │
│   ├── tests/                # Tests (pytest)
│   │   ├── unit/             # Unit Tests (Repositories, Services)
│   │   ├── integration/      # Integration Tests (API Endpoints)
│   │   └── conftest.py       # Pytest Fixtures (Mock DynamoDB, Auth)
│   │
│   ├── scripts/              # Utility Scripts
│   │   ├── seed_data.py      # Seed Development Data
│   │   └── create_superadmin.py  # Create SuperAdmin User
│   │
│   ├── alembic/              # Database Migrations (SQLAlchemy - Legacy)
│   │   └── versions/
│   │
│   ├── pyproject.toml        # Poetry Dependencies & Config
│   ├── lambda_handler.py     # AWS Lambda Entry Point (Mangum)
│   └── .env.example          # Environment Variables Template
│
├── frontend/                  # Vanilla JS Frontend (Vite + Tailwind)
│   ├── src/
│   │   ├── js/               # JavaScript Modules (ES6+)
│   │   │   │
│   │   │   ├── api/          # API Client Modules
│   │   │   │   ├── auth.js       # Authentication API
│   │   │   │   ├── billing.js    # Billing/Stripe API
│   │   │   │   ├── designer.js   # Designer API (Components, Connections)
│   │   │   │   └── architectures.js  # Architecture CRUD API
│   │   │   │
│   │   │   ├── state/        # State Management
│   │   │   │   └── ArchitectureState.js  # Central State Manager (JSON State)
│   │   │   │
│   │   │   ├── components/   # UI Components (Class-based)
│   │   │   │   ├── InfrastructureCanvas.js  # Cytoscape.js Canvas
│   │   │   │   ├── ComponentPalette.js      # Drag & Drop Component Palette
│   │   │   │   ├── ConfigurationTabs.js     # Tabbed Config Panel
│   │   │   │   ├── LiveCostPanel.js         # Real-time Cost Display
│   │   │   │   ├── CIDRCalculator.js        # CIDR Calculator Widget
│   │   │   │   └── properties-panel.js      # Component Properties Editor
│   │   │   │
│   │   │   ├── sync/         # State Synchronization
│   │   │   │   └── SyncCoordinator.js  # Canvas ↔ Tabs ↔ State Sync
│   │   │   │
│   │   │   ├── lib/          # Shared Libraries
│   │   │   │   ├── api-client.js         # Base API Client (fetch wrapper)
│   │   │   │   ├── auth.js               # Auth Helper (Token Management)
│   │   │   │   ├── aws-components.js     # AWS Component Definitions
│   │   │   │   ├── architecture-validator.js  # JSON Validation
│   │   │   │   └── dom-utils.js          # DOM Helper Functions
│   │   │   │
│   │   │   ├── pages/        # Page Controllers
│   │   │   │   ├── blueprint-builder.js   # Blueprint Builder Page
│   │   │   │   ├── blueprints.js          # Blueprints List Page
│   │   │   │   ├── login.js               # Login Page
│   │   │   │   ├── register.js            # Registration Page
│   │   │   │   ├── pricing.js             # Pricing Page
│   │   │   │   └── billing.js             # Billing Management Page
│   │   │   │
│   │   │   ├── examples/     # Demo Data
│   │   │   │   ├── simple-vpc-example.js  # Sample Architectures
│   │   │   │   └── smart-form-demo.js     # Form Examples
│   │   │   │
│   │   │   └── main.js       # Entry Point (imports all modules)
│   │   │
│   │   ├── css/              # Stylesheets
│   │   │   ├── main.css      # Tailwind Imports + Custom Styles
│   │   │   └── components/   # Component-specific CSS (falls nötig)
│   │   │
│   │   ├── *.html            # HTML Pages
│   │   │   ├── index.html               # Landing Page
│   │   │   ├── login.html               # Login Page
│   │   │   ├── register.html            # Registration Page
│   │   │   ├── dashboard.html           # User Dashboard
│   │   │   ├── infrastructure-designer.html  # Main Designer UI
│   │   │   ├── blueprints.html          # Blueprints Gallery
│   │   │   ├── pricing.html             # Pricing Plans
│   │   │   ├── billing.html             # Billing Management
│   │   │   └── cidr-calculator.html     # Standalone CIDR Tool
│   │   │
│   │   └── guides/           # User Guides (HTML)
│   │       ├── index.html         # Guides Index
│   │       └── aws-setup.html     # AWS Setup Tutorial
│   │
│   ├── public/               # Static Assets
│   │   └── (images, fonts, etc.)
│   │
│   ├── dist/                 # Build Output (Vite)
│   │
│   ├── tests/                # Frontend Tests
│   │   ├── e2e/              # End-to-End Tests (Playwright)
│   │   └── unit/             # Unit Tests (Vitest)
│   │
│   ├── vite.config.js        # Vite Configuration
│   ├── tailwind.config.js    # Tailwind CSS Configuration
│   ├── playwright.config.js  # Playwright Test Configuration
│   ├── package.json          # NPM Dependencies
│   └── .env.example          # Frontend Environment Variables
│
├── infrastructure/            # Platform Infrastructure (Terraform)
│   └── terraform/
│       ├── modules/          # Reusable Terraform Modules
│       └── environments/     # Environment-specific Configs
│           ├── dev/
│           ├── staging/
│           └── prod/
│
├── docs/                      # Documentation
│   ├── architecture/         # System Architecture Docs
│   ├── api/                  # API Documentation
│   └── encyclopedia/         # Diese Encyclopedia
│
├── tasks/                     # Task Management (GSD Framework)
│   ├── todo.md               # Current Tasks
│   ├── lessons.md            # Lessons Learned
│   └── archive/              # Completed Milestones
│
├── .github/                   # GitHub Actions CI/CD
│   ├── workflows/
│   │   ├── backend-ci.yml    # Backend Tests & Linting
│   │   ├── security.yml      # Security Scanning (Bandit, Safety)
│   │   ├── test.yml          # Full Test Suite
│   │   └── deploy.yml        # Deployment Pipeline
│   └── dependabot.yml        # Automated Dependency Updates
│
├── .gitignore                # Git Ignore Rules
├── .pre-commit-config.yaml   # Pre-Commit Hooks (Ruff, Black, etc.)
├── README.md                 # Project README
├── QUICKSTART.md             # Quick Start Guide
└── SECURITY.md               # Security Policy
```

### 1.3 Technology Stack Übersicht

**Backend:**
- **Runtime:** Python 3.11+
- **Framework:** FastAPI (async, modern, type hints)
- **Database:** AWS DynamoDB (NoSQL, Single Table Design)
- **Storage:** AWS S3 (Large Items Offload, Terraform State)
- **Authentication:** JWT (python-jose), bcrypt (Password Hashing)
- **API Client:** boto3 (AWS SDK for Python)
- **Template Engine:** Jinja2 (Terraform Code Generation)
- **Testing:** pytest, moto (AWS Mocking), httpx (HTTP Client for Tests)
- **Code Quality:** Black (Formatter), Ruff (Linter), mypy (Type Checker)
- **Dependencies:** Poetry (Dependency Management)

**Frontend:**
- **Core:** HTML5, CSS3, JavaScript ES6+ (Vanilla JS, kein Framework)
- **Build Tool:** Vite (Dev Server + Bundler)
- **Styling:** Tailwind CSS 4
- **Graph Visualization:** Cytoscape.js (Canvas für AWS Components)
- **State Management:** Custom Event-Driven System (ArchitectureState.js)
- **HTTP Client:** Fetch API (Native)
- **Testing:** Playwright (E2E), Vitest (Unit Tests - geplant)

**Infrastructure:**
- **Target Cloud:** AWS (Azure/GCP geplant)
- **IaC Output:** Terraform HCL
- **Deployment:** AWS Lambda (Backend), S3 + CloudFront (Frontend)
- **CI/CD:** GitHub Actions
- **Monitoring:** AWS CloudWatch, Sentry (geplant)

### 1.4 Data Flow - Von User Input zu AWS Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Interaction (Frontend)                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
User drags VPC from Component Palette → Infrastructure Canvas
Canvas fires 'component-added' event
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. State Management (ArchitectureState.js)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
state.components['vpc-1'] = {
  id: 'vpc-1',
  type: 'vpc',
  name: 'Main VPC',
  config: { cidr: '10.0.0.0/16', region: 'us-east-1' },
  position: { x: 100, y: 100 }
}
                              ↓
notify('component-added', { component })
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. UI Synchronization (SyncCoordinator)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
Canvas zeigt VPC Node
ConfigurationTabs öffnet VPC Config Tab
LiveCostPanel updated Cost Estimate
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Save to Backend (Designer API)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
POST /api/v1/designer/architectures
Body: { version: '1.0.0', metadata: {...}, components: {...} }
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Backend Processing (FastAPI)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
ArchitectureRepository.create(architecture_json)
DynamoDB: PK='ORG#uuid', SK='ARCH#uuid'
Item: { ..., architecture_json: {...}, created_at: '...' }
                              ↓
(Falls JSON > 300KB)
→ S3Storage.upload('org/arch-uuid.json', json_str)
→ DynamoDB stores S3 URI statt full JSON
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Terraform Generation (on Deploy)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
POST /api/v1/deployments { architecture_id: 'uuid' }
                              ↓
TerraformGeneratorV2.generate(architecture_json)
                              ↓
Jinja2 Templates:
  components/vpc.tf.j2 → vpc.tf
  components/ec2.tf.j2 → ec2.tf
  components/main.tf.j2 → main.tf
  components/variables.tf.j2 → variables.tf
  components/outputs.tf.j2 → outputs.tf
                              ↓
Files written to: /tmp/overcloud/deployments/{deployment_id}/
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Terraform Execution (TerraformExecutor)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
terraform init
terraform plan -out=tfplan
terraform apply tfplan
                              ↓
(Output wird gestreamt via WebSocket)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. AWS Deployment                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
Terraform creates:
  - VPC (10.0.0.0/16)
  - Subnets
  - Internet Gateway
  - Route Tables
  - Security Groups
  - EC2 Instances
  - RDS Databases
  - ... (je nach Architektur)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. Result & State Storage                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
Deployment Status: 'completed'
Terraform State: uploaded to S3
Outputs (Public IPs, DNS, etc.) saved to DynamoDB
                              ↓
User sees: "Deployment successful! Resources created."
```

---

## 2. Architektur & Design Patterns

### 2.1 System-Architektur (High-Level)

```
┌──────────────────────────────────────────────────────────────────────┐
│                              User                                     │
│                              Browser                                  │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTPS
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                          Frontend (Vite)                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ HTML Pages │  │ JavaScript │  │ Tailwind   │  │ Cytoscape  │    │
│  │            │  │ ES6 Modules│  │ CSS        │  │ Canvas     │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │
│                          ↓                                             │
│                  ArchitectureState (JSON)                              │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ REST API (JSON)
                                  │ WebSocket (Real-time)
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                              │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                       API Layer (Routers)                       │  │
│  │  auth │ users │ orgs │ architectures │ terraform │ deployments │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                  ↓                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Business Logic (Services)                    │  │
│  │  TerraformGenerator │ CostCalculator │ StripeService │ ...     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                  ↓                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                 Data Access Layer (Repositories)                │  │
│  │  UserRepo │ OrgRepo │ ArchRepo │ DeploymentRepo │ AuditRepo    │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                          │                       │
                          │                       │
                          ↓                       ↓
┌─────────────────────────────────┐  ┌──────────────────────────────┐
│         AWS DynamoDB             │  │          AWS S3              │
│  ┌────────────────────────────┐ │  │  ┌────────────────────────┐ │
│  │ overcloud-dev-main (Table) │ │  │  │ Large Architecture JSON│ │
│  │                            │ │  │  │ Terraform State Files  │ │
│  │ PK          SK             │ │  │  │ Deployment Artifacts   │ │
│  │ USER#uuid   METADATA       │ │  │  └────────────────────────┘ │
│  │ ORG#uuid    ARCH#uuid      │ │  │                              │
│  │ ARCH#uuid   VERSION#1      │ │  │                              │
│  └────────────────────────────┘ │  │                              │
└─────────────────────────────────┘  └──────────────────────────────┘
                          │
                          │ Terraform Apply (subprocess)
                          ↓
┌──────────────────────────────────────────────────────────────────────┐
│                              AWS                                      │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐       │
│  │ VPC  │  │ EC2  │  │ RDS  │  │ S3   │  │Lambda│  │ ...  │       │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘       │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Design Pattern #1: Repository Pattern (Backend)

**Problem:** Data Access Logic ist über ganze Codebase verteilt, schwer zu testen und zu ändern.

**Lösung:** Repository Pattern - Abstraction Layer über DynamoDB.

**Implementierung:**

```python
# backend/app/repositories/base.py

class BaseRepository(Generic[T]):
    """Base repository mit common DynamoDB operations."""
    
    def __init__(self, table: Optional[Table] = None, s3_storage: Optional[S3Storage] = None):
        self.table = table or get_dynamodb_table()
        self.s3_storage = s3_storage or S3Storage()
        self.large_item_threshold = settings.LARGE_ITEM_THRESHOLD  # 300KB
    
    def _put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Put item in DynamoDB with automatic timestamps."""
        now = datetime.utcnow().isoformat()
        if "created_at" not in item:
            item["created_at"] = now
        item["updated_at"] = now
        
        # Convert floats to Decimal (DynamoDB requirement)
        item = convert_floats_to_decimal(item)
        
        self.table.put_item(Item=item)
        return item
    
    def _get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """Get single item by primary key."""
        response = self.table.get_item(Key={"PK": pk, "SK": sk})
        return response.get("Item")
    
    def _query(
        self,
        key_condition: ConditionBase,
        filter_condition: Optional[ConditionBase] = None,
        # ... weitere Parameter
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Query items mit filtering und pagination."""
        # Implementation...
```

**Verwendung in konkreten Repositories:**

```python
# backend/app/repositories/user.py

from uuid import UUID
from typing import Optional
from boto3.dynamodb.conditions import Key, Attr
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository):
    """User Data Access - spezialisiert auf User Operations."""
    
    def create(self, user_data: dict) -> dict:
        """Create new user in DynamoDB."""
        user_id = user_data["id"]
        
        item = {
            "PK": f"USER#{user_id}",
            "SK": "METADATA",
            "entity_type": "user",
            **user_data
        }
        
        return self._put_item(item)
    
    def get(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID."""
        return self._get_item(pk=f"USER#{user_id}", sk="METADATA")
    
    def get_by_email(self, email: str) -> Optional[dict]:
        """Get user by email using GSI."""
        items, _ = self._query(
            key_condition=Key("email").eq(email),
            index_name="email-index"
        )
        return items[0] if items else None
    
    def update(self, user_id: UUID, updates: dict) -> dict:
        """Update user attributes."""
        return self._update_item(
            pk=f"USER#{user_id}",
            sk="METADATA",
            updates=updates
        )
    
    def delete(self, user_id: UUID) -> bool:
        """Delete user."""
        return self._delete_item(pk=f"USER#{user_id}", sk="METADATA")
```

**Vorteile:**
- **Testbar:** Einfach zu mocken (inject fake repository in tests)
- **Wiederverwendbar:** Common Operations nur 1x implementiert
- **Austauschbar:** DynamoDB → PostgreSQL? Nur Repository ändern
- **Type-Safe:** Type Hints für alle Methoden

**Verwendung in API Endpoints:**

```python
# backend/app/api/users.py

from fastapi import APIRouter, Depends
from app.repositories.user import UserRepository

router = APIRouter()

def get_user_repo(table=Depends(get_dynamodb_table)) -> UserRepository:
    """Dependency Injection - liefert UserRepository."""
    return UserRepository(table=table)

@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """Get user by ID."""
    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

### 2.3 Design Pattern #2: Dependency Injection (FastAPI)

**Problem:** Tight Coupling - Code hängt direkt von konkreten Implementierungen ab.

**Lösung:** Dependency Injection - Dependencies werden zur Runtime injected.

**FastAPI Dependency System:**

```python
# backend/app/db/dynamodb.py

def get_dynamodb_table():
    """Liefert DynamoDB Table - wird von FastAPI automatisch gecalled."""
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=settings.AWS_REGION,
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL  # Für Local Testing
    )
    table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)
    return table

# backend/app/api/auth.py

from fastapi import Depends
from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository

def get_user_repository(table=Depends(get_dynamodb_table)) -> UserRepository:
    """Dependency Chain: table -> UserRepository."""
    return UserRepository(table=table)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> dict:
    """Dependency Chain: oauth2_scheme -> token -> user_repo -> current_user."""
    # Decode JWT Token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get("sub")
    
    # Get user from DB via Repository
    user = user_repo.get(UUID(user_id))
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    return user

# Verwendung in Endpoint
@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    FastAPI Flow:
    1. Ruft get_current_user() auf
    2. get_current_user braucht token (oauth2_scheme) und user_repo (get_user_repository)
    3. get_user_repository braucht table (get_dynamodb_table)
    4. FastAPI resolved dependency tree automatisch
    5. Endpoint erhält fertigen current_user dict
    """
    return current_user
```

**Vorteile:**
- **Testbar:** Dependencies einfach austauschbar in Tests
- **Reusable:** get_current_user kann in jedem Endpoint verwendet werden
- **Type-Safe:** FastAPI validiert Types automatisch
- **Lazy:** Dependencies nur wenn nötig ausgeführt

**Testing mit Dependency Overrides:**

```python
# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.dynamodb import get_dynamodb_table

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB Table für Tests."""
    from moto import mock_dynamodb
    with mock_dynamodb():
        # Create fake table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            # ... weitere Config
        )
        yield table

@pytest.fixture
def client(mock_dynamodb_table):
    """TestClient mit gemockter DynamoDB."""
    # Override Dependency
    app.dependency_overrides[get_dynamodb_table] = lambda: mock_dynamodb_table
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup
    app.dependency_overrides.clear()

# Test
def test_get_user(client, mock_dynamodb_table):
    # Insert test user in mock table
    mock_dynamodb_table.put_item(Item={
        "PK": "USER#123",
        "SK": "METADATA",
        "email": "test@example.com",
        "name": "Test User"
    })
    
    # Call API
    response = client.get("/api/v1/users/123")
    
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

### 2.4 Design Pattern #3: JSON-First Architecture

**Problem:** Terraform HCL ist schwer versionierbar, schwer zu parsen, schwer zu manipulieren.

**Lösung:** JSON als Source of Truth - Terraform wird daraus generiert.

**JSON State Schema:**

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Production Web App",
    "description": "High-availability web application",
    "provider": "aws",
    "region": "us-east-1",
    "createdAt": "2026-05-16T10:00:00Z",
    "updatedAt": "2026-05-16T12:30:00Z"
  },
  "components": {
    "vpc-1": {
      "id": "vpc-1",
      "type": "vpc",
      "name": "Main VPC",
      "config": {
        "cidr": "10.0.0.0/16",
        "enable_dns_hostnames": true,
        "enable_dns_support": true,
        "tags": {
          "Environment": "production",
          "ManagedBy": "OverCloud"
        }
      },
      "position": { "x": 100, "y": 100 }
    },
    "subnet-1": {
      "id": "subnet-1",
      "type": "subnet",
      "name": "Public Subnet A",
      "config": {
        "cidr": "10.0.1.0/24",
        "availability_zone": "us-east-1a",
        "map_public_ip_on_launch": true,
        "vpc_id": "vpc-1"
      },
      "position": { "x": 120, "y": 250 }
    },
    "ec2-1": {
      "id": "ec2-1",
      "type": "ec2",
      "name": "Web Server",
      "config": {
        "instance_type": "t3.medium",
        "ami": "ami-0c55b159cbfafe1f0",
        "subnet_id": "subnet-1",
        "key_name": "my-key",
        "user_data": "#!/bin/bash\necho 'Hello World'",
        "tags": {
          "Name": "WebServer-1",
          "Role": "frontend"
        }
      },
      "position": { "x": 140, "y": 400 }
    }
  },
  "connections": [
    {
      "id": "vpc-1-subnet-1",
      "from": "vpc-1",
      "to": "subnet-1",
      "type": "contains"
    },
    {
      "id": "subnet-1-ec2-1",
      "from": "subnet-1",
      "to": "ec2-1",
      "type": "contains"
    }
  ],
  "ipAllocations": {
    "vpc-1": { "cidr": "10.0.0.0/16", "used": ["10.0.1.0/24"] },
    "subnet-1": { "cidr": "10.0.1.0/24", "used": [] }
  }
}
```

**Terraform Generation Flow:**

```python
# backend/app/services/terraform_generator_v2.py

class TerraformGeneratorV2:
    """Generiert Terraform HCL aus JSON Architecture."""
    
    def generate(self, architecture_json: Dict[str, Any]) -> Dict[str, str]:
        """
        Input: Architecture JSON (siehe oben)
        Output: Dict of Terraform files
        {
            'main.tf': '...',
            'variables.tf': '...',
            'vpc.tf': '...',
            'ec2.tf': '...',
            'outputs.tf': '...'
        }
        """
        files = {}
        
        # 1. Extract data
        components = architecture_json['components']
        connections = architecture_json['connections']
        
        # 2. Group components by type
        components_by_type = self._group_components_by_type(components)
        # {'vpc': [vpc-1], 'subnet': [subnet-1], 'ec2': [ec2-1]}
        
        # 3. Generate main.tf (provider config)
        files['main.tf'] = self._generate_main_tf(architecture_json)
        
        # 4. Generate component-specific files
        for comp_type, comps in components_by_type.items():
            # vpc.tf, ec2.tf, rds.tf, ...
            filename = f'{comp_type}.tf'
            files[filename] = self._generate_component_file(
                comp_type, comps, components, connections
            )
        
        # 5. Generate outputs.tf
        files['outputs.tf'] = self._generate_outputs_tf(components)
        
        return files
    
    def _generate_component_file(
        self, comp_type: str, components: List[dict], all_components: dict, connections: List[dict]
    ) -> str:
        """Generate .tf file for specific component type using Jinja2."""
        
        # Load Jinja2 template
        template = self.env.get_template(f'components/{comp_type}.tf.j2')
        
        # Render template
        return template.render(
            components=components,
            all_components=all_components,
            connections=connections
        )
```

**Jinja2 Template Beispiel:**

```jinja2
{# backend/templates/terraform/components/vpc.tf.j2 #}

# ============================================================================
# VPC Resources
# ============================================================================

{% for vpc in components %}
resource "aws_vpc" "{{ vpc.id }}" {
  cidr_block           = "{{ vpc.config.cidr }}"
  enable_dns_hostnames = {{ vpc.config.enable_dns_hostnames | lower }}
  enable_dns_support   = {{ vpc.config.enable_dns_support | lower }}

  tags = {
    Name = "{{ vpc.name }}"
    {% for key, value in vpc.config.tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
  }
}
{% endfor %}
```

**Generierter Terraform Output:**

```hcl
# vpc.tf

# ============================================================================
# VPC Resources
# ============================================================================

resource "aws_vpc" "vpc-1" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "Main VPC"
    Environment = "production"
    ManagedBy   = "OverCloud"
  }
}
```

**Vorteile JSON-First:**
- **Versionierbar:** JSON kann in Git committed werden
- **Language-Agnostic:** Nicht auf Terraform locked (könnten auch Pulumi/CDK generieren)
- **Parseable:** JavaScript kann JSON nativ lesen/schreiben (Frontend!)
- **Validierbar:** JSON Schema Validation möglich
- **Reversible:** Aus bestehendem Terraform wieder JSON extrahieren (TODO)

### 2.5 Design Pattern #4: Event-Driven Architecture (Frontend)

**Problem:** Components müssen miteinander kommunizieren, ohne sich zu kennen (Loose Coupling).

**Lösung:** Custom Events - Components dispatchen Events, andere subscriben.

**Implementierung:**

```javascript
// frontend/src/js/state/ArchitectureState.js

export class ArchitectureState {
    constructor() {
        this.state = { version: '1.0.0', components: {}, connections: [] };
        this.listeners = [];
    }
    
    // Subscribe Pattern
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            // Unsubscribe function
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }
    
    // Notify all subscribers
    notify(changeType, payload) {
        this.listeners.forEach(listener => {
            listener(changeType, payload, this.state);
        });
    }
    
    // State Mutations
    addComponent(type, name, config, position) {
        const id = this.generateId(type);
        const component = { id, type, name, config, position };
        
        this.state.components[id] = component;
        this.notify('component-added', { component });
        
        return id;
    }
    
    updateComponent(componentId, updates) {
        const component = this.state.components[componentId];
        Object.assign(component.config, updates.config);
        
        this.notify('component-updated', { componentId, component });
    }
    
    deleteComponent(componentId) {
        const component = this.state.components[componentId];
        delete this.state.components[componentId];
        
        this.notify('component-deleted', { componentId, component });
    }
}
```

**Verwendung in Components:**

```javascript
// frontend/src/js/components/InfrastructureCanvas.js

export class InfrastructureCanvas {
    constructor(containerId, architectureState) {
        this.cy = cytoscape({ container: document.getElementById(containerId) });
        this.state = architectureState;
        
        // Subscribe to state changes
        this.state.subscribe(this.handleStateChange.bind(this));
    }
    
    handleStateChange(changeType, payload, state) {
        switch (changeType) {
            case 'component-added':
                this.addNode(payload.component);
                break;
            case 'component-updated':
                this.updateNode(payload.componentId, payload.component);
                break;
            case 'component-deleted':
                this.removeNode(payload.componentId);
                break;
            case 'connection-added':
                this.addEdge(payload.connection);
                break;
        }
    }
    
    addNode(component) {
        this.cy.add({
            data: {
                id: component.id,
                label: component.name,
                type: component.type
            },
            position: component.position
        });
    }
    
    // User clicks on node
    onNodeClick(nodeId) {
        const component = this.state.state.components[nodeId];
        
        // Dispatch event (other components can listen)
        this.state.notify('component-selected', { componentId: nodeId, component });
    }
}
```

```javascript
// frontend/src/js/components/ConfigurationTabs.js

export class ConfigurationTabs {
    constructor(containerId, architectureState) {
        this.container = document.getElementById(containerId);
        this.state = architectureState;
        this.openTabs = new Map();
        
        // Subscribe to state
        this.state.subscribe(this.handleStateChange.bind(this));
    }
    
    handleStateChange(changeType, payload, state) {
        switch (changeType) {
            case 'component-selected':
                // Open tab when component is clicked
                this.openTab(payload.componentId, payload.component);
                break;
            case 'component-updated':
                // Update tab content
                this.updateTab(payload.componentId, payload.component);
                break;
            case 'component-deleted':
                // Close tab
                this.closeTab(payload.componentId);
                break;
        }
    }
    
    openTab(componentId, component) {
        // Create tab UI
        const tab = this.createTab(componentId, component);
        this.openTabs.set(componentId, tab);
    }
    
    // User changes config in tab
    onConfigChange(componentId, newConfig) {
        // Update state (notifies all subscribers)
        this.state.updateComponent(componentId, { config: newConfig });
    }
}
```

**Flow Diagram:**

```
User clicks VPC in Canvas
    ↓
InfrastructureCanvas.onNodeClick('vpc-1')
    ↓
state.notify('component-selected', { componentId: 'vpc-1', component: {...} })
    ↓
ConfigurationTabs.handleStateChange('component-selected', ...)
    ↓
ConfigurationTabs.openTab('vpc-1', component)
    ↓
Tab opens with VPC config form
    ↓
User changes CIDR: 10.0.0.0/16 → 10.1.0.0/16
    ↓
ConfigurationTabs.onConfigChange('vpc-1', { cidr: '10.1.0.0/16' })
    ↓
state.updateComponent('vpc-1', { config: { cidr: '10.1.0.0/16' } })
    ↓
state.notify('component-updated', { componentId: 'vpc-1', component: {...} })
    ↓
InfrastructureCanvas.handleStateChange('component-updated', ...)
    ↓
InfrastructureCanvas.updateNode('vpc-1', newComponent)
    ↓
Canvas re-renders VPC node mit updated label
    ↓
LiveCostPanel.handleStateChange('component-updated', ...)
    ↓
LiveCostPanel recalculates cost estimate
```

**Vorteile:**
- **Loose Coupling:** Canvas kennt Tabs nicht, Tabs kennen Canvas nicht
- **Bidirectional Sync:** Änderungen in Canvas → Tabs, Änderungen in Tabs → Canvas
- **Extensible:** Neue Components einfach hinzufügbar (subscribe to events)
- **Testable:** Components einzeln testbar

---

## 3. Backend - Python Stack

### 3.1 Core Framework: FastAPI

**Was ist FastAPI?**

FastAPI ist ein modernes Python Web Framework:
- **Async/Await:** Native Unterstützung für asynchrone Programmierung (wie Node.js)
- **Type Hints:** Nutzt Python Type Hints für automatische Validierung
- **Auto-Docs:** Generiert OpenAPI (Swagger) Dokumentation automatisch
- **Fast:** Performance vergleichbar mit Node.js und Go (dank Starlette + Pydantic)
- **Developer Experience:** Autocomplete, Type Checking, weniger Bugs

**Warum FastAPI für OverCloud?**

1. **Performance:** Terraform-Generierung und AWS API Calls brauchen schnelle I/O
2. **Type Safety:** Architecture JSON muss validiert werden - Pydantic integriert
3. **Async:** WebSocket Streaming für Real-time Deployment Updates
4. **Auto-Docs:** API Docs für Frontend Devs automatisch verfügbar unter `/api/docs`

**Grundlegende Konzepte:**

**A) Routers (API Endpoints)**

```python
# backend/app/api/architectures.py

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

router = APIRouter()

@router.post("/architectures", status_code=status.HTTP_201_CREATED)
async def create_architecture(
    architecture: ArchitectureCreate,  # Request Body (Pydantic Model)
    current_user: dict = Depends(get_current_user),  # Dependency Injection
    arch_repo: ArchitectureRepository = Depends(get_arch_repo)
) -> ArchitectureResponse:  # Response Model (Pydantic)
    """
    Create new architecture.
    
    1. FastAPI parst Request Body JSON
    2. Validiert gegen ArchitectureCreate Schema (Pydantic)
    3. Injected current_user (aus JWT Token)
    4. Injected arch_repo (DynamoDB Repository)
    5. Business Logic läuft
    6. Return wird zu JSON serialisiert (ArchitectureResponse)
    """
    
    # Validation (automatic via Pydantic)
    # architecture.name ist garantiert string
    # architecture.components ist garantiert dict
    
    # Authorization Check
    if not current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    
    # Business Logic
    arch_dict = arch_repo.create(
        org_id=UUID(current_user['organisation_id']),
        architecture_data={
            "name": architecture.name,
            "components": architecture.components,
            "connections": architecture.connections,
            # ...
        }
    )
    
    # Return (FastAPI serializes to JSON)
    return ArchitectureResponse(**arch_dict)
```

**B) Path Parameters**

```python
@router.get("/architectures/{architecture_id}")
async def get_architecture(
    architecture_id: UUID,  # Path Parameter (automatic parsing & validation)
    arch_repo: ArchitectureRepository = Depends(get_arch_repo)
):
    """
    GET /api/v1/architectures/550e8400-e29b-41d4-a716-446655440000
    
    FastAPI:
    1. Parsed architecture_id aus URL
    2. Validated als UUID (raises 422 wenn invalid)
    3. Konvertiert string → UUID object
    """
    
    arch = arch_repo.get(architecture_id)
    
    if not arch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Architecture not found")
    
    return arch
```

**C) Query Parameters**

```python
@router.get("/architectures")
async def list_architectures(
    skip: int = 0,          # Query Param: ?skip=10
    limit: int = 100,       # Query Param: ?limit=50
    search: str = None,     # Query Param: ?search=vpc (optional)
    arch_repo: ArchitectureRepository = Depends(get_arch_repo)
):
    """
    GET /api/v1/architectures?skip=10&limit=50&search=vpc
    
    FastAPI parsed Query Params automatisch
    """
    
    architectures, last_key = arch_repo.list(skip=skip, limit=limit)
    
    return {
        "items": architectures,
        "total": len(architectures),
        "skip": skip,
        "limit": limit
    }
```

**D) Request Body (Pydantic Models)**

```python
# backend/app/schemas/architecture.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

class ArchitectureCreate(BaseModel):
    """Request Schema for POST /architectures."""
    
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    components: Dict[str, dict] = Field(default_factory=dict)
    connections: List[dict] = Field(default_factory=list)
    
    # Pydantic Config
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Production Web App",
                "description": "High-availability architecture",
                "components": {
                    "vpc-1": {
                        "type": "vpc",
                        "config": {"cidr": "10.0.0.0/16"}
                    }
                },
                "connections": []
            }
        }
    }

class ArchitectureResponse(BaseModel):
    """Response Schema - what API returns."""
    
    id: UUID
    organisation_id: UUID
    name: str
    description: Optional[str]
    components: Dict[str, dict]
    connections: List[dict]
    created_at: datetime
    updated_at: datetime
    
    # Pydantic Config
    model_config = {"from_attributes": True}  # Allows ORM models
```

**E) Response Models & Status Codes**

```python
@router.post("/architectures", status_code=status.HTTP_201_CREATED, response_model=ArchitectureResponse)
async def create_architecture(...) -> ArchitectureResponse:
    """
    status_code=201: Override default 200
    response_model=ArchitectureResponse: FastAPI serializes return value to this schema
    """
    return arch_dict

@router.delete("/architectures/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_architecture(...):
    """204 No Content - no response body."""
    arch_repo.delete(architecture_id)
    return  # No return value
```

**F) Exception Handling**

```python
from fastapi import HTTPException

@router.get("/architectures/{id}")
async def get_architecture(architecture_id: UUID, ...):
    arch = arch_repo.get(architecture_id)
    
    if not arch:
        # Raises HTTP 404 with JSON body: {"detail": "Not found"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Architecture not found"
        )
    
    return arch

# Custom Exception Handler (in main.py)
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

### 3.2 Validation: Pydantic

**Was ist Pydantic?**

Pydantic ist eine Data Validation Library die Python Type Hints zur Runtime validiert:
- **Type Coercion:** Automatische Konvertierung (string → int, string → datetime, etc.)
- **Validation:** Field constraints (min_length, regex, etc.)
- **Serialization:** Python objects → JSON
- **Deserialization:** JSON → Python objects

**OverCloud Schemas Overview:**

```
backend/app/schemas/
├── user.py           # User, UserCreate, UserUpdate, UserResponse, TokenResponse
├── organisation.py   # OrganisationCreate, OrganisationResponse, MemberCreate
├── architecture.py   # ArchitectureCreate, ArchitectureResponse, ArchitectureUpdate
├── deployment.py     # DeploymentCreate, DeploymentResponse, DeploymentStatus
└── cost.py          # CostEstimate, CostBreakdown, CostItem
```

**Beispiel: User Schemas**

```python
# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

# Enums
class SystemRole(str, Enum):
    """System-wide roles."""
    USER = "user"
    SUPPORT = "support"
    AUDITOR = "auditor"
    SUPERADMIN = "superadmin"

class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# Request Schema (User Registration)
class UserCreate(BaseModel):
    """Schema für POST /auth/register."""
    
    email: EmailStr  # Validated email format (Pydantic special type)
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure strong password."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "password": "SecurePass123"
            }
        }
    }

# Response Schema (API returns this)
class UserResponse(BaseModel):
    """Schema für GET /users/{id} response."""
    
    id: UUID
    email: EmailStr
    name: str
    system_role: SystemRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    
    # Don't include password hash in response!
    
    model_config = {"from_attributes": True}  # Allows SQLAlchemy models

# JWT Token Response
class TokenResponse(BaseModel):
    """Schema für POST /auth/login response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until token expires")

class TokenPayload(BaseModel):
    """JWT Token Payload (decoded)."""
    
    sub: str  # Subject (user_id)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    system_role: SystemRole
```

**Verwendung in API:**

```python
# backend/app/api/auth.py

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,  # Pydantic validates request body
    user_repo: UserRepository = Depends(get_user_repo)
) -> UserResponse:  # Pydantic serializes response
    """
    Request (JSON):
    {
      "email": "test@example.com",
      "name": "Test User",
      "password": "SecurePass123"
    }
    
    Pydantic Validation:
    1. email format valid? ✅
    2. name min_length=1? ✅
    3. password min_length=8? ✅
    4. password has uppercase? ✅
    5. password has digit? ✅
    
    If any validation fails → HTTP 422 Unprocessable Entity
    """
    
    # Check if user exists
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(409, "Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Create user
    user = user_repo.create({
        "id": str(uuid4()),
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "system_role": SystemRole.USER.value,
        "status": UserStatus.ACTIVE.value
    })
    
    # Return (Pydantic serializes to UserResponse)
    return UserResponse(**user)
    # Output JSON:
    # {
    #   "id": "uuid",
    #   "email": "test@example.com",
    #   "name": "Test User",
    #   "system_role": "user",
    #   "status": "active",
    #   "created_at": "2026-05-16T10:00:00Z",
    #   "updated_at": "2026-05-16T10:00:00Z"
    # }
```

**Wichtige Pydantic Features:**

**A) Field Validation**

```python
from pydantic import BaseModel, Field

class ComponentConfig(BaseModel):
    instance_type: str = Field(
        pattern=r'^t[23]\.(nano|micro|small|medium|large|xlarge|2xlarge)$',
        description="EC2 instance type"
    )
    
    disk_size: int = Field(
        ge=8,      # greater or equal
        le=16384,  # less or equal
        description="Disk size in GB"
    )
    
    cidr: str = Field(
        pattern=r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$',
        description="CIDR block (e.g., 10.0.0.0/16)"
    )
```

**B) Custom Validators**

```python
from pydantic import field_validator, model_validator

class ArchitectureCreate(BaseModel):
    name: str
    components: Dict[str, dict]
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name doesn't contain forbidden characters."""
        forbidden = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in forbidden):
            raise ValueError(f'Name cannot contain: {", ".join(forbidden)}')
        return v
    
    @model_validator(mode='after')
    def validate_components(self):
        """Ensure at least one VPC exists."""
        vpcs = [c for c in self.components.values() if c.get('type') == 'vpc']
        if not vpcs:
            raise ValueError('Architecture must contain at least one VPC')
        return self
```

**C) Type Coercion**

```python
from pydantic import BaseModel
from datetime import datetime

class Example(BaseModel):
    count: int
    created_at: datetime

# Input (JSON):
data = {
    "count": "42",  # String
    "created_at": "2026-05-16T10:00:00Z"  # String
}

# Pydantic automatically converts:
obj = Example(**data)
# obj.count == 42 (int)
# obj.created_at == datetime(2026, 5, 16, 10, 0, 0) (datetime object)
```

**D) Nested Models**

```python
class VPCConfig(BaseModel):
    cidr: str
    enable_dns_hostnames: bool = True
    enable_dns_support: bool = True

class SubnetConfig(BaseModel):
    cidr: str
    availability_zone: str
    map_public_ip_on_launch: bool = False

class Component(BaseModel):
    id: str
    type: str
    name: str
    config: VPCConfig | SubnetConfig  # Union type

class Architecture(BaseModel):
    name: str
    components: Dict[str, Component]  # Nested validation
```

### 3.3 Database: DynamoDB (Single Table Design)

**Was ist DynamoDB?**

DynamoDB ist AWS's vollständig verwaltete NoSQL Datenbank:
- **Serverless:** Keine Server zu managen, pay-per-request
- **Scalable:** Automatische Skalierung (Millionen Requests/Sekunde)
- **Fast:** Single-digit millisecond latency
- **Key-Value:** Flexible Schema, JSON Documents

**OverCloud DynamoDB Design:**

**Single Table Design Pattern:**

Statt viele Tables (users, organisations, architectures, deployments, ...) nutzt OverCloud **eine einzige Table** mit PK/SK Pattern.

**Warum Single Table?**
- **Cost:** Weniger Tables = günstiger
- **Performance:** Weniger Roundtrips (Query kann mehrere Entity Types joinen)
- **Atomic Transactions:** DynamoDB Transactions über mehrere Items (gleiche Partition)

**Table Schema:**

```
Table: overcloud-dev-main

Primary Keys:
- PK (Partition Key) - String - HASH
- SK (Sort Key) - String - RANGE

Global Secondary Indexes (GSI):
- email-index: email (HASH) → Für User Lookup by Email
- org-index: organisation_id (HASH) → Für Multi-Tenancy Queries
```

**Entity Patterns:**

```python
# USER
PK: "USER#{user_id}"
SK: "METADATA"
Attributes: email, name, hashed_password, system_role, status, created_at, updated_at

# USER <-> ORGANISATION Membership
PK: "USER#{user_id}"
SK: "ORG#{org_id}"
Attributes: role (owner, admin, member), joined_at

# ORGANISATION
PK: "ORG#{org_id}"
SK: "METADATA"
Attributes: name, slug, status, subscription_status, created_at, updated_at

# ORGANISATION Members (reverse relation)
PK: "ORG#{org_id}"
SK: "MEMBER#{user_id}"
Attributes: role, joined_at

# ARCHITECTURE
PK: "ORG#{org_id}"
SK: "ARCH#{architecture_id}"
Attributes: name, description, components (JSON or S3 URI), connections, created_at, updated_at, created_by

# ARCHITECTURE VERSION (immutable history)
PK: "ARCH#{architecture_id}"
SK: "VERSION#{version_number}"
Attributes: components, connections, created_at, created_by

# DEPLOYMENT
PK: "ORG#{org_id}"
SK: "DEPLOY#{deployment_id}"
Attributes: architecture_id, status, terraform_state_s3_uri, outputs, logs_s3_uri, created_at, updated_at

# AUDIT LOG
PK: "ORG#{org_id}"
SK: "AUDIT#{timestamp}#{action}"
Attributes: user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at
```

**Beispiel Queries:**

```python
# Get User by ID
response = table.get_item(
    Key={
        "PK": f"USER#{user_id}",
        "SK": "METADATA"
    }
)
user = response.get("Item")

# Get User by Email (GSI)
response = table.query(
    IndexName='email-index',
    KeyConditionExpression=Key('email').eq('test@example.com')
)
user = response['Items'][0] if response['Items'] else None

# Get all Organisations for a User
response = table.query(
    KeyConditionExpression=Key('PK').eq(f'USER#{user_id}') & Key('SK').begins_with('ORG#')
)
memberships = response['Items']
# [
#   {PK: 'USER#123', SK: 'ORG#456', role: 'owner'},
#   {PK: 'USER#123', SK: 'ORG#789', role: 'member'}
# ]

# Get all Architectures in an Organisation
response = table.query(
    KeyConditionExpression=Key('PK').eq(f'ORG#{org_id}') & Key('SK').begins_with('ARCH#')
)
architectures = response['Items']

# Get all Deployments for an Architecture (Cross-Partition Query - use Scan with FilterExpression)
response = table.scan(
    FilterExpression=Attr('architecture_id').eq(str(architecture_id))
)
deployments = response['Items']
```

**S3 Offload Pattern (Large Items):**

DynamoDB hat ein Item Size Limit von 400KB. OverCloud nutzt S3 für große Architecture JSONs:

```python
# backend/app/db/s3_storage.py

class S3Storage:
    """S3 helper für Large Item Offload."""
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket = settings.S3_LARGE_ITEMS_BUCKET
    
    def upload(self, key: str, data: str) -> str:
        """Upload data to S3."""
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data.encode('utf-8'),
            ContentType='application/json',
            ServerSideEncryption='AES256'  # Encrypted at rest
        )
        return f"s3://{self.bucket}/{key}"
    
    def download(self, s3_uri: str) -> str:
        """Download data from S3."""
        # Parse s3://bucket/key
        parts = s3_uri.replace('s3://', '').split('/', 1)
        bucket, key = parts[0], parts[1]
        
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    
    def delete(self, s3_uri: str) -> bool:
        """Delete object from S3."""
        parts = s3_uri.replace('s3://', '').split('/', 1)
        bucket, key = parts[0], parts[1]
        
        self.s3_client.delete_object(Bucket=bucket, Key=key)
        return True
```

**Verwendung in Repository:**

```python
# backend/app/repositories/architecture.py

class ArchitectureRepository(BaseRepository):
    """Architecture Data Access with S3 Offload."""
    
    def create(self, org_id: UUID, architecture_data: dict) -> dict:
        """Create architecture with automatic S3 offload for large items."""
        
        architecture_id = uuid4()
        
        # Serialize components & connections to JSON string
        components_json = json.dumps(architecture_data['components'])
        connections_json = json.dumps(architecture_data['connections'])
        
        # Check size
        total_size = len(components_json) + len(connections_json)
        
        if total_size > self.large_item_threshold:  # 300KB
            # Store in S3
            s3_key = f"organisations/{org_id}/architectures/{architecture_id}/data.json"
            full_json = json.dumps({
                "components": architecture_data['components'],
                "connections": architecture_data['connections']
            })
            s3_uri = self.s3_storage.upload(s3_key, full_json)
            
            # Store S3 reference in DynamoDB
            item = {
                "PK": f"ORG#{org_id}",
                "SK": f"ARCH#{architecture_id}",
                "entity_type": "architecture",
                "id": str(architecture_id),
                "name": architecture_data['name'],
                "description": architecture_data.get('description'),
                "data_s3_uri": s3_uri,  # S3 Reference
                "data_size": total_size,
                "created_by": architecture_data.get('created_by')
            }
        else:
            # Store inline in DynamoDB
            item = {
                "PK": f"ORG#{org_id}",
                "SK": f"ARCH#{architecture_id}",
                "entity_type": "architecture",
                "id": str(architecture_id}",
                "name": architecture_data['name'],
                "description": architecture_data.get('description'),
                "components": architecture_data['components'],  # Inline
                "connections": architecture_data['connections'],  # Inline
                "created_by": architecture_data.get('created_by')
            }
        
        return self._put_item(item)
    
    def get(self, architecture_id: UUID) -> Optional[dict]:
        """Get architecture with automatic S3 download if needed."""
        
        # First try to find it (we need org_id)
        # In practice: Query GSI or scan (inefficient - TODO: improve)
        response = self.table.scan(
            FilterExpression=Attr('id').eq(str(architecture_id)) & Attr('entity_type').eq('architecture')
        )
        
        if not response['Items']:
            return None
        
        item = response['Items'][0]
        
        # Check if data is in S3
        if 'data_s3_uri' in item:
            # Download from S3
            full_json_str = self.s3_storage.download(item['data_s3_uri'])
            full_json = json.loads(full_json_str)
            
            # Merge into item
            item['components'] = full_json['components']
            item['connections'] = full_json['connections']
            del item['data_s3_uri']  # Remove S3 reference from response
        
        return item
```

### 3.4 Authentication: JWT (python-jose)

**Was ist JWT?**

JSON Web Token (JWT) ist ein Standard für stateless Authentication:
- **Self-contained:** Token enthält alle User-Daten (kein Session Store nötig)
- **Signed:** Token kann nicht manipuliert werden (HMAC SHA256 Signature)
- **Expirable:** Token hat Ablaufzeit (Security)

**JWT Struktur:**

```
Header.Payload.Signature

# Decoded:
{
  "header": {
    "alg": "HS256",        # Algorithm
    "typ": "JWT"           # Type
  },
  "payload": {
    "sub": "user-uuid",    # Subject (User ID)
    "exp": 1717656000,     # Expiration (Unix Timestamp)
    "iat": 1717652400,     # Issued At
    "system_role": "user"  # Custom Claims
  },
  "signature": "..."       # HMAC SHA256(header + payload, SECRET_KEY)
}
```

**OverCloud JWT Implementation:**

```python
# backend/app/api/auth.py

from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import settings

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token.
    
    Args:
        data: Payload data (must include 'sub' for user_id)
        expires_delta: Token lifetime (default: settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    
    # Add expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    # Sign with SECRET_KEY
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,  # Must be 32+ chars, cryptographically random
        algorithm=settings.ALGORITHM  # HS256
    )
    
    return encoded_jwt

# Usage in Login Endpoint
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repo),
    lockout_service: AccountLockoutService = Depends(get_account_lockout_service)
):
    """
    Login flow:
    1. Get user by email
    2. Verify password
    3. Check account lockout
    4. Create JWT token
    5. Return token
    """
    
    # 1. Get user
    user = user_repo.get_by_email(form_data.username)  # username field = email
    
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # 2. Verify password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    if not pwd_context.verify(form_data.password, user['hashed_password']):
        # Increment failed login attempts
        lockout_service.record_failed_attempt(form_data.username)
        raise HTTPException(401, "Invalid credentials")
    
    # 3. Check account lockout
    if lockout_service.is_locked_out(form_data.username):
        raise HTTPException(429, "Account temporarily locked due to too many failed attempts")
    
    # 4. Check user status
    if user['status'] != 'active':
        raise HTTPException(403, "Account is inactive")
    
    # 5. Reset failed attempts
    lockout_service.reset_attempts(form_data.username)
    
    # 6. Create token
    access_token = create_access_token(
        data={
            "sub": user['id'],  # Subject = User ID
            "system_role": user['system_role']
        }
    )
    
    # 7. Return token
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Seconds
    )
```

**Token Verification:**

```python
# backend/app/api/auth.py

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),  # Extracts token from Authorization header
    user_repo: UserRepository = Depends(get_user_repo)
) -> dict:
    """
    Verify JWT token and return current user.
    
    Called automatically for protected endpoints via Depends(get_current_user).
    """
    
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        # Decode & verify token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract user_id
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Check expiration (automatic via jwt.decode - raises JWTError if expired)
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception
    
    # Get user from DB
    user = user_repo.get(UUID(user_id))
    
    if user is None:
        raise credentials_exception
    
    if user['status'] != 'active':
        raise HTTPException(403, "User account is inactive")
    
    return user

# Protected Endpoint Example
@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)  # Automatic token verification
):
    """
    Request:
    GET /api/v1/users/me
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
    FastAPI Flow:
    1. oauth2_scheme extracts token from header
    2. get_current_user() decodes & verifies token
    3. get_current_user() queries user from DB
    4. Endpoint receives verified current_user dict
    """
    return UserResponse(**current_user)
```

**Password Hashing (bcrypt):**

```python
# backend/app/api/auth.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Registration
@router.post("/register")
async def register(user_data: UserCreate, ...):
    # Hash password (slow by design - prevents brute force)
    hashed_password = pwd_context.hash(user_data.password)
    # → "$2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
    
    # Store hashed password (NEVER store plain text!)
    user = user_repo.create({
        "email": user_data.email,
        "hashed_password": hashed_password,
        # ...
    })
    
    return user

# Login
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), ...):
    user = user_repo.get_by_email(form_data.username)
    
    # Verify password (constant-time comparison - prevents timing attacks)
    is_valid = pwd_context.verify(form_data.password, user['hashed_password'])
    
    if not is_valid:
        raise HTTPException(401, "Invalid credentials")
    
    # ... create token
```

**Security Best Practices:**

1. **Strong SECRET_KEY:** Mindestens 32 Zeichen, kryptographisch random
2. **Short Token Lifetime:** OverCloud nutzt 1 Stunde (TODO: Refresh Token Pattern)
3. **HTTPS Only:** Tokens dürfen nur über HTTPS übertragen werden
4. **No Sensitive Data in Token:** Token ist Base64-encoded (nicht encrypted!), daher keine Passwords/Credit Cards
5. **Revocation:** Bei User Logout → Token bleibt gültig bis exp (TODO: Token Blacklist oder Refresh Token Pattern)

### 3.5 Rate Limiting: SlowAPI

**Warum Rate Limiting?**

Schutz vor:
- **Brute Force Attacks:** Login-Versuche limitieren
- **DoS Attacks:** API Überlastung verhindern
- **Abuse:** Scraping, excessive API calls

**OverCloud Implementation:**

```python
# backend/app/main.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter
limiter = Limiter(key_func=get_remote_address)  # Limit by IP address

# Add to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# backend/app/api/auth.py

@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(request: Request, ...):
    """
    Rate Limit:
    - 5 requests per minute per IP
    - Returns HTTP 429 Too Many Requests wenn exceeded
    """
    # ... login logic

@router.post("/register")
@limiter.limit("3/hour")  # Max 3 registrations per hour per IP
async def register(request: Request, ...):
    # ... registration logic
```

**Testing Disable:**

```python
# backend/app/config.py

class Settings(BaseSettings):
    TESTING: bool = False  # Set True in tests

# backend/tests/conftest.py

@pytest.fixture
def client():
    settings.TESTING = True  # Disable rate limiting in tests
    with TestClient(app) as client:
        yield client
```

### 3.6 Terraform Generation: Jinja2 Templates

**Flow:**

```
Architecture JSON (Frontend State)
    ↓
POST /api/v1/deployments { architecture_id }
    ↓
TerraformGeneratorV2.generate(architecture_json)
    ↓
Jinja2 Templates (components/*.tf.j2)
    ↓
Rendered Terraform HCL (.tf files)
    ↓
Written to /tmp/overcloud/deployments/{deployment_id}/
    ↓
terraform init && terraform plan && terraform apply
```

**Beispiel Template:**

```jinja2
{# backend/templates/terraform/components/ec2.tf.j2 #}

# ============================================================================
# EC2 Instances
# ============================================================================

{% for ec2 in components %}
resource "aws_instance" "{{ ec2.id }}" {
  ami           = "{{ ec2.config.ami }}"
  instance_type = "{{ ec2.config.instance_type }}"
  
  {% if ec2.config.subnet_id %}
  subnet_id = aws_subnet.{{ ec2.config.subnet_id }}.id
  {% endif %}
  
  {% if ec2.config.security_group_ids %}
  vpc_security_group_ids = [
    {% for sg_id in ec2.config.security_group_ids %}
    aws_security_group.{{ sg_id }}.id,
    {% endfor %}
  ]
  {% endif %}
  
  {% if ec2.config.user_data %}
  user_data = <<-EOF
{{ ec2.config.user_data | indent(4) }}
  EOF
  {% endif %}
  
  {% if ec2.config.key_name %}
  key_name = "{{ ec2.config.key_name }}"
  {% endif %}
  
  tags = {
    Name = "{{ ec2.name }}"
    {% for key, value in ec2.config.tags.items() %}
    {{ key }} = "{{ value }}"
    {% endfor %}
    ManagedBy = "OverCloud"
  }
}
{% endfor %}
```

**Generator Code:**

```python
# backend/app/services/terraform_generator_v2.py

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class TerraformGeneratorV2:
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            backend_dir = Path(__file__).parent.parent.parent
            template_dir = backend_dir / "templates" / "terraform"
        
        self.env = Environment(
            loader=FileSystemLoader([
                str(template_dir),
                str(template_dir / "components")
            ]),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self, architecture_json: Dict[str, Any]) -> Dict[str, str]:
        """
        Returns:
        {
            'main.tf': '...',
            'variables.tf': '...',
            'vpc.tf': '...',
            'ec2.tf': '...',
            'outputs.tf': '...'
        }
        """
        files = {}
        
        components = architecture_json['components']
        connections = architecture_json['connections']
        
        # Group by type
        components_by_type = {}
        for comp_id, comp in components.items():
            comp_type = comp['type']
            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append(comp)
        
        # Generate files
        for comp_type, comps in components_by_type.items():
            template = self.env.get_template(f'components/{comp_type}.tf.j2')
            files[f'{comp_type}.tf'] = template.render(
                components=comps,
                all_components=components,
                connections=connections
            )
        
        # ... generate main.tf, variables.tf, outputs.tf
        
        return files
```

---

## 4. Frontend - JavaScript Stack

### 4.1 Build Tool: Vite

**Was ist Vite?**

Vite ist ein moderner Build Tool (Nachfolger von Webpack):
- **Fast:** Dev Server startet in Millisekunden (nutzt native ES Modules)
- **Hot Module Replacement (HMR):** Instant Updates ohne Page Reload
- **Optimized Production Build:** Rollup-basiert, Tree-Shaking, Minification

**Warum Vite für OverCloud?**

- **Developer Experience:** Instant Feedback beim Development
- **No Framework Lock-in:** Funktioniert mit Vanilla JS (kein React/Vue nötig)
- **Tailwind Integration:** Native Vite Plugin für Tailwind CSS

**Konfiguration:**

```javascript
// frontend/vite.config.js

import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),  // Tailwind CSS Integration
  ],
  root: 'src',  // HTML files sind in src/
  publicDir: '../public',  // Static assets
  build: {
    outDir: '../dist',  // Build output
    emptyOutDir: true,
    sourcemap: true,  // Source maps für Debugging
  },
  server: {
    port: 5173,  // Dev Server Port
    open: true,  // Auto-open Browser
    proxy: {
      // Proxy API calls to Backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
})
```

**Commands:**

```bash
# Development (mit HMR)
npm run dev
# → http://localhost:5173

# Production Build
npm run build
# → dist/ folder mit minified files

# Preview Production Build
npm run preview
```

**ES6 Modules (nativ):**

```javascript
// frontend/src/js/main.js

// Import modules
import { InfrastructureCanvas } from './components/InfrastructureCanvas.js';
import { ArchitectureState } from './state/ArchitectureState.js';
import { ComponentPalette } from './components/ComponentPalette.js';

// Initialize
const state = new ArchitectureState();
const canvas = new InfrastructureCanvas('canvas-container', state);
const palette = new ComponentPalette('palette-container', state);
```

```html
<!-- frontend/src/infrastructure-designer.html -->

<!DOCTYPE html>
<html>
<head>
  <title>Infrastructure Designer</title>
  <link rel="stylesheet" href="/css/main.css">
</head>
<body>
  <div id="canvas-container"></div>
  <div id="palette-container"></div>
  
  <!-- Vite automatically handles module imports -->
  <script type="module" src="/js/main.js"></script>
</body>
</html>
```

### 4.2 Styling: Tailwind CSS

**Was ist Tailwind?**

Tailwind ist ein Utility-First CSS Framework:
- **Keine Custom CSS nötig:** Alles via Klassen (`p-4`, `bg-blue-500`, `rounded-lg`)
- **Responsive:** Mobile-first, breakpoints (`md:w-1/2`, `lg:w-1/3`)
- **Dark Mode:** Native Support (`dark:bg-gray-800`)
- **Production Optimization:** Unused CSS wird automatisch entfernt (PurgeCSS)

**OverCloud Tailwind Config:**

```javascript
// frontend/tailwind.config.js

export default {
  content: [
    "./src/**/*.{html,js}",  // Scan all HTML/JS for used classes
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors für AWS Components
        'aws-orange': '#FF9900',
        'aws-blue': '#527FFF',
        'aws-green': '#569A31',
        'overcloud-primary': '#667eea',
        'overcloud-secondary': '#764ba2',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

**Usage Examples:**

```html
<!-- Button -->
<button class="
  px-4 py-2           <!-- padding -->
  bg-blue-500         <!-- background color -->
  hover:bg-blue-600   <!-- hover state -->
  text-white          <!-- text color -->
  font-semibold       <!-- font weight -->
  rounded-lg          <!-- border radius -->
  shadow-md           <!-- box shadow -->
  transition-colors   <!-- smooth transitions -->
  duration-200        <!-- animation duration -->
">
  Save Architecture
</button>

<!-- Card -->
<div class="
  p-6                 <!-- padding: 1.5rem -->
  bg-white            <!-- background -->
  dark:bg-gray-800    <!-- dark mode -->
  rounded-lg          <!-- border radius -->
  shadow-lg           <!-- box shadow -->
  border              <!-- border: 1px solid -->
  border-gray-200     <!-- border color -->
  dark:border-gray-700
">
  <h2 class="text-2xl font-bold mb-4">VPC Configuration</h2>
  <p class="text-gray-600 dark:text-gray-400">Configure your VPC settings.</p>
</div>

<!-- Responsive Layout -->
<div class="
  grid                <!-- CSS Grid -->
  grid-cols-1         <!-- 1 column (mobile) -->
  md:grid-cols-2      <!-- 2 columns (tablet+) -->
  lg:grid-cols-3      <!-- 3 columns (desktop+) -->
  gap-4               <!-- gap between items -->
">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>
```

**CSS File:**

```css
/* frontend/src/css/main.css */

/* Tailwind Base */
@import "tailwindcss";

/* Custom Styles (wenig nötig mit Tailwind) */
.canvas-container {
  /* Cytoscape.js spezifische Styles */
  width: 100%;
  height: calc(100vh - 64px);
}

.component-palette-item:hover {
  /* Custom Hover Effect */
  transform: scale(1.05);
  transition: transform 0.2s;
}
```

### 4.3 Graph Visualization: Cytoscape.js

**Was ist Cytoscape.js?**

Cytoscape.js ist eine Graph Visualization Library:
- **Nodes & Edges:** Darstellung von Netzwerken/Graphen
- **Layout Algorithms:** Automatic Positioning (Breadth-First, Grid, Force-Directed)
- **Interactive:** Drag, Zoom, Pan, Click Events
- **Customizable:** Styles, Shapes, Colors

**OverCloud Usage:**

Infrastructure Canvas visualisiert AWS Components als Graph:
- **Nodes:** VPC, EC2, RDS, S3, Lambda, ...
- **Edges:** Verbindungen (Subnet in VPC, EC2 in Subnet, RDS in Subnet, ...)

**Implementation:**

```javascript
// frontend/src/js/components/InfrastructureCanvas.js

import cytoscape from 'cytoscape';

export class InfrastructureCanvas {
    constructor(containerId, architectureState) {
        this.container = document.getElementById(containerId);
        this.state = architectureState;
        this.cy = null;
        
        this.init();
        this.setupEventHandlers();
        
        // Subscribe to state changes
        this.state.subscribe(this.handleStateChange.bind(this));
    }
    
    init() {
        this.cy = cytoscape({
            container: this.container,
            
            style: [
                // VPC Node Style
                {
                    selector: 'node[type="vpc"]',
                    style: {
                        'background-color': '#667eea',
                        'label': 'data(label)',
                        'color': '#fff',
                        'width': 200,
                        'height': 150,
                        'shape': 'roundrectangle',
                        'border-width': 3,
                        'border-color': '#764ba2',
                        'font-size': '12px',
                        'text-wrap': 'wrap',
                        'text-max-width': '180px'
                    }
                },
                
                // EC2 Node Style
                {
                    selector: 'node[type="ec2"]',
                    style: {
                        'background-color': '#FF9900',
                        'label': 'data(label)',
                        'width': 120,
                        'height': 80,
                        'shape': 'roundrectangle'
                    }
                },
                
                // RDS Node Style
                {
                    selector: 'node[type="rds"]',
                    style: {
                        'background-color': '#527FFF',
                        'label': 'data(label)',
                        'width': 120,
                        'height': 80,
                        'shape': 'roundrectangle'
                    }
                },
                
                // S3 Node Style
                {
                    selector: 'node[type="s3"]',
                    style: {
                        'background-color': '#569A31',
                        'label': 'data(label)',
                        'width': 100,
                        'height': 100,
                        'shape': 'barrel'  # S3 bucket = barrel shape
                    }
                },
                
                // Edge Style
                {
                    selector: 'edge',
                    style: {
                        'width': 3,
                        'line-color': '#cbd5e1',
                        'target-arrow-color': '#cbd5e1',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }
                },
                
                // Selected Node
                {
                    selector: ':selected',
                    style: {
                        'border-width': 5,
                        'border-color': '#3b82f6'
                    }
                }
            ],
            
            layout: {
                name: 'breadthfirst',  # Hierarchical layout
                directed: true,
                spacingFactor: 1.5
            }
        });
    }
    
    setupEventHandlers() {
        // Node Click
        this.cy.on('tap', 'node', (event) => {
            const node = event.target;
            const componentId = node.id();
            const component = this.state.state.components[componentId];
            
            // Notify state (opens ConfigurationTabs)
            this.state.notify('component-selected', { componentId, component });
        });
        
        // Node Drag (update position in state)
        this.cy.on('dragfree', 'node', (event) => {
            const node = event.target;
            const position = node.position();
            
            this.state.updateComponent(node.id(), { position });
        });
        
        // Edge Click
        this.cy.on('tap', 'edge', (event) => {
            const edge = event.target;
            const connectionId = edge.id();
            // ... handle edge selection
        });
    }
    
    handleStateChange(changeType, payload, state) {
        switch (changeType) {
            case 'component-added':
                this.addNode(payload.component);
                break;
            case 'component-updated':
                this.updateNode(payload.componentId, payload.component);
                break;
            case 'component-deleted':
                this.removeNode(payload.componentId);
                break;
            case 'connection-added':
                this.addEdge(payload.connection);
                break;
            case 'connection-deleted':
                this.removeEdge(payload.connectionId);
                break;
        }
    }
    
    addNode(component) {
        this.cy.add({
            data: {
                id: component.id,
                label: this.formatNodeLabel(component),
                type: component.type
            },
            position: component.position || { x: 0, y: 0 }
        });
        
        // Apply layout
        this.applyLayout();
    }
    
    updateNode(componentId, component) {
        const node = this.cy.$(`#${componentId}`);
        
        if (node.length > 0) {
            node.data('label', this.formatNodeLabel(component));
            
            if (component.position) {
                node.position(component.position);
            }
        }
    }
    
    removeNode(componentId) {
        this.cy.remove(`#${componentId}`);
    }
    
    addEdge(connection) {
        this.cy.add({
            data: {
                id: connection.id,
                source: connection.from,
                target: connection.to
            }
        });
    }
    
    removeEdge(connectionId) {
        this.cy.remove(`#${connectionId}`);
    }
    
    formatNodeLabel(component) {
        // Format label with component details
        let label = `${component.name}\n`;
        
        if (component.type === 'vpc') {
            label += `CIDR: ${component.config.cidr}`;
        } else if (component.type === 'ec2') {
            label += `${component.config.instance_type}\n`;
            if (component.config.private_ip) {
                label += `IP: ${component.config.private_ip}`;
            }
        }
        // ... weitere types
        
        return label;
    }
    
    applyLayout(layoutName = 'breadthfirst') {
        this.cy.layout({
            name: layoutName,
            directed: true,
            spacingFactor: 1.5,
            animate: true,
            animationDuration: 500
        }).run();
    }
    
    // Export as PNG
    exportAsPNG() {
        const png = this.cy.png({
            scale: 2,
            full: true,
            bg: '#ffffff'
        });
        
        // png = base64 data URL
        return png;
    }
    
    // Export as JSON
    exportAsJSON() {
        return this.cy.json();
    }
    
    // Import from JSON
    importFromJSON(json) {
        this.cy.json(json);
    }
}
```

**Layout Algorithms:**

```javascript
// Breadth-First (Hierarchical)
cy.layout({ name: 'breadthfirst', directed: true }).run();

// Grid (Ordered)
cy.layout({ name: 'grid', rows: 3, cols: 3 }).run();

// Force-Directed (Organic, Spring-like)
cy.layout({ name: 'cose', animate: true }).run();

// Manual (No auto-layout)
cy.layout({ name: 'preset' }).run();
```

### 4.4 State Management: ArchitectureState.js

**Problem:** Verschiedene UI Components (Canvas, Tabs, Cost Panel, ...) müssen synchron bleiben.

**Lösung:** Central State Manager mit Event-Driven Updates.

**Implementation:**

```javascript
// frontend/src/js/state/ArchitectureState.js

export class ArchitectureState {
    constructor() {
        this.state = {
            version: '1.0.0',
            metadata: {
                name: 'Unbenannte Architektur',
                description: '',
                provider: 'aws',
                region: 'us-east-1',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            },
            components: {},      # { [componentId]: component }
            connections: [],     # [{ id, from, to, type }]
            ipAllocations: {}    # CIDR tracking
        };
        
        this.listeners = [];
        this.history = [];       # For Undo/Redo
        this.historyIndex = -1;
        this.maxHistorySize = 50;
    }
    
    // ========================================================================
    // Subscription Pattern
    // ========================================================================
    
    subscribe(listener) {
        """
        Subscribe to state changes.
        
        Usage:
        const unsubscribe = state.subscribe((changeType, payload, state) => {
            console.log('State changed:', changeType, payload);
        });
        
        // Later: unsubscribe()
        """
        this.listeners.push(listener);
        
        // Return unsubscribe function
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }
    
    notify(changeType, payload) {
        """Notify all subscribers of state change."""
        this.listeners.forEach(listener => {
            try {
                listener(changeType, payload, this.state);
            } catch (error) {
                console.error('Listener error:', error);
            }
        });
    }
    
    // ========================================================================
    // Component Management
    // ========================================================================
    
    addComponent(type, name, config = {}, position = null) {
        const id = this.generateId(type);
        
        const component = {
            id,
            type,
            name,
            config: {
                ...config,
                createdAt: new Date().toISOString()
            },
            position: position || this.getDefaultPosition(type)
        };
        
        this.state.components[id] = component;
        this.state.metadata.updatedAt = new Date().toISOString();
        
        this.saveToHistory();
        this.notify('component-added', { component });
        
        return id;
    }
    
    updateComponent(componentId, updates) {
        const component = this.state.components[componentId];
        if (!component) {
            console.warn(`Component ${componentId} not found`);
            return;
        }
        
        // Merge updates
        if (updates.name !== undefined) {
            component.name = updates.name;
        }
        if (updates.config) {
            Object.assign(component.config, updates.config);
        }
        if (updates.position) {
            component.position = updates.position;
        }
        
        this.state.metadata.updatedAt = new Date().toISOString();
        
        this.saveToHistory();
        this.notify('component-updated', { componentId, component });
    }
    
    deleteComponent(componentId) {
        const component = this.state.components[componentId];
        if (!component) return;
        
        // Remove component
        delete this.state.components[componentId];
        
        // Remove connections involving this component
        this.state.connections = this.state.connections.filter(
            conn => conn.from !== componentId && conn.to !== componentId
        );
        
        this.saveToHistory();
        this.notify('component-deleted', { componentId, component });
    }
    
    getComponent(componentId) {
        return this.state.components[componentId];
    }
    
    getAllComponents() {
        return Object.values(this.state.components);
    }
    
    // ========================================================================
    // Connection Management
    // ========================================================================
    
    addConnection(fromId, toId, connectionType = 'contains') {
        // Check if connection already exists
        const existing = this.state.connections.find(
            c => c.from === fromId && c.to === toId
        );
        if (existing) {
            console.warn('Connection already exists');
            return existing.id;
        }
        
        const connection = {
            id: `${fromId}-${toId}`,
            from: fromId,
            to: toId,
            type: connectionType
        };
        
        this.state.connections.push(connection);
        
        this.saveToHistory();
        this.notify('connection-added', { connection });
        
        return connection.id;
    }
    
    deleteConnection(connectionId) {
        const index = this.state.connections.findIndex(c => c.id === connectionId);
        if (index === -1) return;
        
        const connection = this.state.connections[index];
        this.state.connections.splice(index, 1);
        
        this.saveToHistory();
        this.notify('connection-deleted', { connectionId, connection });
    }
    
    // ========================================================================
    // History Management (Undo/Redo)
    // ========================================================================
    
    saveToHistory() {
        // Remove future history if we're not at the end
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        
        // Add current state to history
        this.history.push(JSON.parse(JSON.stringify(this.state)));
        
        // Limit history size
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }
    }
    
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.state = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
            this.notify('state-restored', { source: 'undo' });
        }
    }
    
    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.state = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
            this.notify('state-restored', { source: 'redo' });
        }
    }
    
    // ========================================================================
    // Persistence (LocalStorage & Backend)
    // ========================================================================
    
    saveDraft() {
        """Save to LocalStorage (auto-save)."""
        try {
            localStorage.setItem('overcloud-draft', JSON.stringify(this.state));
            console.log('Draft saved to LocalStorage');
        } catch (error) {
            console.error('Failed to save draft:', error);
        }
    }
    
    loadDraft() {
        """Load from LocalStorage."""
        try {
            const draft = localStorage.getItem('overcloud-draft');
            if (draft) {
                this.state = JSON.parse(draft);
                this.notify('state-restored', { source: 'draft' });
                return true;
            }
        } catch (error) {
            console.error('Failed to load draft:', error);
        }
        return false;
    }
    
    async saveToBackend(architectureId = null) {
        """Save to Backend API."""
        try {
            const endpoint = architectureId
                ? `/api/v1/architectures/${architectureId}`
                : '/api/v1/architectures';
            
            const method = architectureId ? 'PUT' : 'POST';
            
            const response = await fetch(endpoint, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(this.state)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            this.notify('state-saved', { architectureId: data.id });
            
            return data;
        } catch (error) {
            console.error('Failed to save to backend:', error);
            throw error;
        }
    }
    
    async loadFromBackend(architectureId) {
        """Load from Backend API."""
        try {
            const response = await fetch(`/api/v1/architectures/${architectureId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Replace current state
            this.state = {
                version: data.version || '1.0.0',
                metadata: data.metadata,
                components: data.components,
                connections: data.connections || [],
                ipAllocations: data.ipAllocations || {}
            };
            
            this.saveToHistory();
            this.notify('state-restored', { source: 'backend', architectureId });
            
            return data;
        } catch (error) {
            console.error('Failed to load from backend:', error);
            throw error;
        }
    }
    
    // ========================================================================
    // Helpers
    // ========================================================================
    
    generateId(type) {
        """Generate unique ID for component."""
        const existingIds = Object.keys(this.state.components)
            .filter(id => id.startsWith(`${type}-`))
            .map(id => parseInt(id.split('-')[1]))
            .filter(n => !isNaN(n));
        
        const nextNum = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;
        
        return `${type}-${nextNum}`;
    }
    
    getDefaultPosition(type) {
        """Get default position for new component."""
        const components = Object.values(this.state.components);
        
        if (components.length === 0) {
            return { x: 200, y: 200 };
        }
        
        // Offset from last component
        const last = components[components.length - 1];
        return {
            x: last.position.x + 150,
            y: last.position.y + 50
        };
    }
    
    getAuthToken() {
        """Get JWT token from localStorage."""
        return localStorage.getItem('overcloud-token');
    }
    
    // ========================================================================
    // Export/Import
    // ========================================================================
    
    exportJSON() {
        """Export state as JSON string."""
        return JSON.stringify(this.state, null, 2);
    }
    
    importJSON(jsonString) {
        """Import state from JSON string."""
        try {
            const imported = JSON.parse(jsonString);
            this.state = imported;
            this.saveToHistory();
            this.notify('state-restored', { source: 'import' });
            return true;
        } catch (error) {
            console.error('Failed to import JSON:', error);
            return false;
        }
    }
}
```

**Usage Example:**

```javascript
// frontend/src/js/pages/infrastructure-designer.js

import { ArchitectureState } from '../state/ArchitectureState.js';
import { InfrastructureCanvas } from '../components/InfrastructureCanvas.js';
import { ConfigurationTabs } from '../components/ConfigurationTabs.js';
import { ComponentPalette } from '../components/ComponentPalette.js';
import { LiveCostPanel } from '../components/LiveCostPanel.js';

// Initialize
const state = new ArchitectureState();

// Initialize UI Components (all subscribe to state)
const canvas = new InfrastructureCanvas('canvas', state);
const tabs = new ConfigurationTabs('tabs', state);
const palette = new ComponentPalette('palette', state);
const costPanel = new LiveCostPanel('cost-panel', state);

// Load draft from LocalStorage
if (state.loadDraft()) {
    console.log('Draft loaded');
}

// Auto-save every 30 seconds
setInterval(() => {
    state.saveDraft();
}, 30000);

// Save button
document.getElementById('save-btn').addEventListener('click', async () => {
    try {
        const result = await state.saveToBackend();
        alert('Architecture saved!');
    } catch (error) {
        alert('Failed to save: ' + error.message);
    }
});

// Undo/Redo buttons
document.getElementById('undo-btn').addEventListener('click', () => {
    state.undo();
});

document.getElementById('redo-btn').addEventListener('click', () => {
    state.redo();
});
```

---

**Ende Teil 1**

Teil 1 umfasst:
- Projekt-Übersicht (Was ist OverCloud, Projektstruktur, Technology Stack, Data Flow)
- Architektur & Design Patterns (Repository Pattern, Dependency Injection, JSON-First, Event-Driven)
- Backend - Python Stack (FastAPI, Pydantic, DynamoDB, JWT, Rate Limiting, Terraform Generation)
- Frontend - JavaScript Stack (Vite, Tailwind, Cytoscape.js, State Management)

**Nächste Teile:**
- **Teil 2:** Infrastructure, DevOps, Testing, Monitoring, Security
- **Teil 3:** API Reference, User Flows, State Machines, Error Handling
