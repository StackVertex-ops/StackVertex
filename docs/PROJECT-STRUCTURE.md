# OverCloud - Projekt-Struktur

> Detaillierte Übersicht der Verzeichnisstruktur mit Erklärungen

---

## 📁 Root-Level

```
OverCloud/
├── .claude/                 # Claude Code Konfiguration
├── .git/                    # Git repository (nach git init)
├── .gitignore              # Git ignore rules
├── backend/                 # Python FastAPI Backend
├── frontend/                # Vanilla JS Frontend
├── docs/                    # Dokumentation
├── tasks/                   # Task Management (GSD)
├── infrastructure/          # Platform infrastructure (später)
├── scripts/                 # Build & deployment scripts (später)
├── README.md               # Projekt-Übersicht
├── QUICKSTART.md           # 30-Min Setup Guide
└── CLAUDE.md               # (veraltet, nutze .claude/CLAUDE.md)
```

---

## 🐍 Backend Struktur (Python + Poetry)

```
backend/
├── .venv/                   # ⭐ Projekt-lokale Virtual Environment
│   ├── bin/                # Python interpreter, pip, etc.
│   ├── lib/                # Installierte Packages
│   └── pyvenv.cfg          # venv Konfiguration
├── app/                     # Main Application Code
│   ├── __init__.py
│   ├── main.py             # FastAPI entry point
│   ├── api/                # API Endpoints (FastAPI Routers)
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── architectures.py   # CRUD für Architekturen
│   │   │   ├── deployments.py     # Stack Deployments
│   │   │   ├── evaluation.py      # Cost/Security Analysis
│   │   │   └── auth.py             # Authentication
│   │   └── dependencies.py         # Shared dependencies (DB session, etc.)
│   ├── core/               # Business Logic
│   │   ├── __init__.py
│   │   ├── json_engine/    # JSON Versioning & Storage
│   │   │   ├── __init__.py
│   │   │   ├── versioning.py      # Semver, diffs, migrations
│   │   │   └── storage.py         # Save/load JSON to/from DB
│   │   ├── iac_generator/  # Terraform Code Generation
│   │   │   ├── __init__.py
│   │   │   ├── terraform.py       # Main generator
│   │   │   ├── templates/         # Jinja2 templates
│   │   │   │   ├── aws/
│   │   │   │   ├── azure/         # (später)
│   │   │   │   └── gcp/           # (später)
│   │   │   └── builder.py         # Component → Terraform mapping
│   │   ├── deployment/     # AWS Deployment via Boto3
│   │   │   ├── __init__.py
│   │   │   ├── aws.py             # AWS SDK wrapper
│   │   │   ├── stack_manager.py   # Stack CRUD operations
│   │   │   └── outputs.py         # Parse Terraform outputs
│   │   ├── evaluation/     # Cost & Security Analysis
│   │   │   ├── __init__.py
│   │   │   ├── cost_estimator.py  # AWS Pricing API
│   │   │   ├── security_analyzer.py
│   │   │   └── recommender.py     # Alternative suggestions
│   │   └── orchestration/  # Multi-Cloud Orchestration (später)
│   ├── models/             # Data Models
│   │   ├── __init__.py
│   │   ├── database.py     # SQLAlchemy Base, engine, session
│   │   ├── orm/            # SQLAlchemy ORM Models
│   │   │   ├── architecture.py    # Architecture table
│   │   │   ├── deployment.py      # Deployment table
│   │   │   └── user.py            # User table
│   │   └── schemas/        # Pydantic Schemas (API validation)
│   │       ├── architecture.py
│   │       ├── deployment.py
│   │       └── user.py
│   ├── services/           # External Service Integrations
│   │   ├── __init__.py
│   │   ├── aws_client.py   # Boto3 client wrapper
│   │   ├── terraform_cli.py # Terraform CLI wrapper
│   │   └── pricing.py      # AWS Pricing API
│   ├── utils/              # Helper Functions
│   │   ├── __init__.py
│   │   ├── validators.py   # Custom validators
│   │   ├── security.py     # JWT, hashing, etc.
│   │   └── logger.py       # Logging setup
│   └── config.py           # Configuration (from .env)
├── tests/                   # Pytest Tests
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api/
│   │   ├── test_architectures.py
│   │   └── test_deployments.py
│   ├── test_core/
│   │   ├── test_json_engine.py
│   │   ├── test_iac_generator.py
│   │   └── test_evaluation.py
│   └── test_utils/
├── alembic/                 # Database Migrations
│   ├── versions/           # Migration files
│   ├── env.py              # Alembic environment
│   └── alembic.ini         # Alembic config
├── pyproject.toml          # ⭐ Poetry Dependencies & Config
├── poetry.lock             # Locked dependency versions
├── .env.example            # Example environment variables
├── .env                    # ⛔ Local env (gitignored)
└── README.md               # Backend-specific docs
```

### Wichtige Backend Files:

- **`.venv/`** - Virtual environment (lokal, nicht systemweit!)
- **`pyproject.toml`** - Poetry dependencies, project metadata
- **`app/main.py`** - FastAPI app initialization
- **`app/config.py`** - Liest `.env`, konfiguriert App
- **`alembic/`** - Database schema migrations

---

## 🌐 Frontend Struktur (Vanilla JS + Vite)

```
frontend/
├── node_modules/            # ⭐ NPM Dependencies (lokal)
├── src/                     # Source Code
│   ├── js/                 # JavaScript
│   │   ├── main.js         # Entry point
│   │   ├── router.js       # Client-side routing (optional)
│   │   ├── api/            # API Client
│   │   │   ├── client.js          # Fetch wrapper
│   │   │   ├── architectures.js   # Architecture API calls
│   │   │   ├── deployments.js
│   │   │   └── auth.js
│   │   ├── components/     # UI Components (class-based)
│   │   │   ├── ArchitectureBuilder.js
│   │   │   ├── CostEstimator.js
│   │   │   ├── DeploymentDashboard.js
│   │   │   ├── ComponentLibrary.js    # Drag-and-drop components
│   │   │   ├── JSONViewer.js
│   │   │   └── TerraformViewer.js
│   │   ├── lib/            # Utilities
│   │   │   ├── state.js           # PubSub event system
│   │   │   ├── validators.js      # Client-side validation
│   │   │   └── utils.js           # Helper functions
│   │   └── pages/          # Page Controllers
│   │       ├── home.js
│   │       ├── builder.js         # Architecture builder page
│   │       ├── dashboard.js       # Deployments dashboard
│   │       └── login.js
│   ├── css/                # Styles
│   │   ├── main.css        # Tailwind imports + global styles
│   │   └── components/     # Component-specific styles
│   │       ├── architecture-builder.css
│   │       └── cost-estimator.css
│   └── index.html          # ⭐ Main HTML template
├── public/                  # Static Assets
│   ├── assets/
│   │   ├── logo.svg
│   │   └── icons/
│   ├── images/
│   └── favicon.ico
├── dist/                    # ⛔ Build Output (gitignored)
│   ├── index.html
│   ├── assets/
│   │   ├── main-[hash].js
│   │   └── main-[hash].css
│   └── ...
├── package.json            # ⭐ NPM Dependencies & Scripts
├── package-lock.json       # Locked dependency versions
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
└── README.md               # Frontend-specific docs
```

### Wichtige Frontend Files:

- **`node_modules/`** - NPM packages (lokal, nicht systemweit!)
- **`src/index.html`** - Main entry point (Vite injects scripts)
- **`src/js/main.js`** - JavaScript entry point
- **`src/css/main.css`** - Tailwind imports
- **`vite.config.js`** - Vite dev server + build config
- **`dist/`** - Production build output (deploy to S3)

---

## 📄 Dokumentation

```
docs/
├── architecture/           # System Design Docs
│   ├── overview.md                # High-level architecture
│   ├── json-schema-design.md      # JSON schema rationale
│   ├── api-design.md              # API contracts
│   └── deployment-model.md        # How deployments work
├── json-schemas/           # JSON Schema Definitions
│   ├── architecture-v1.0.0.schema.json  # ⭐ Core schema
│   ├── deployment-v1.0.0.schema.json
│   └── blueprint-v1.0.0.schema.json
├── api/                    # API Documentation
│   ├── openapi.yaml               # OpenAPI spec (auto-generated by FastAPI)
│   └── endpoints.md               # Endpoint documentation
├── user-guides/            # User Documentation
│   ├── getting-started.md
│   ├── creating-architectures.md
│   └── deploying-stacks.md
├── SETUP.md                # ⭐ Complete setup guide
└── PROJECT-STRUCTURE.md    # This file
```

---

## 🛠️ Tasks & Claude Code Config

```
tasks/
├── todo.md                 # ⭐ Current tasks (GSD)
├── lessons.md              # Lessons learned (self-improvement)
├── decisions.md            # ⭐ Architectural Decision Records (ADRs)
└── archive/                # Completed milestones

.claude/
├── CLAUDE.md               # ⭐ Project rules & guidelines
├── settings.local.json     # Claude Code settings
├── commands/               # Custom Slash Commands
│   ├── blueprint.md               # /blueprint command
│   ├── deploy.md                  # /deploy command
│   └── review-architecture.md     # /review-architecture command
├── skills/                 # Superpowers Skills (MCP)
│   └── (populated by Superpowers install)
└── agents/                 # Agent Team Definitions
    ├── backend-architect.json
    ├── frontend-engineer.json
    ├── devops-engineer.json
    ├── data-architect.json
    ├── security-auditor.json
    └── qa-engineer.json
```

---

## 🚀 Infrastructure (später)

```
infrastructure/
├── terraform/              # Terraform for OverCloud platform itself
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── backend/               # Lambda/ECS for backend
│   │   ├── frontend/              # S3 + CloudFront for frontend
│   │   └── database/              # RDS PostgreSQL
│   └── environments/
│       ├── dev/
│       ├── staging/
│       └── production/
└── docker/                 # Docker configs
    ├── backend.Dockerfile
    └── docker-compose.yml         # Local dev environment
```

---

## 🔒 Wichtige .gitignore Regeln

```gitignore
# Python (Backend)
backend/.venv/              # ⭐ Virtual environment (lokal!)
backend/__pycache__/
backend/.pytest_cache/
backend/.mypy_cache/
backend/.ruff_cache/

# Node.js (Frontend)
frontend/node_modules/      # ⭐ NPM packages (lokal!)
frontend/dist/              # Build output
frontend/.vite/

# Environment Variables
.env                        # ⛔ NIEMALS committen!
.env.local

# Terraform (Generated)
generated/                  # Generated Terraform code
*.tfstate
.terraform/

# User Data
architectures/*.json        # User-created architectures (optional)
deployments/logs/
```

---

## 🎯 Wichtige Pfade für Development

### Backend Development:
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/backend

# Activate venv
poetry shell

# Python läuft aus:
.venv/bin/python

# Dependencies in:
.venv/lib/python3.11/site-packages/
```

### Frontend Development:
```bash
cd /Users/andyschwarz/Documents/Privat/OverCloud/frontend

# Start dev server
npm run dev

# Dependencies in:
node_modules/
```

---

## ✅ Verification Checklist

Nach Setup solltest du diese Struktur haben:

```bash
# Check Backend venv (lokal!)
ls backend/.venv/bin/python  # ✅ Sollte existieren

# Check Frontend node_modules (lokal!)
ls frontend/node_modules/vite/  # ✅ Sollte existieren

# Check Documentation
ls docs/json-schemas/architecture-v1.0.0.schema.json  # ✅ Sollte existieren

# Check Tasks
ls tasks/todo.md tasks/decisions.md  # ✅ Sollte existieren

# Check Claude Code Config
ls .claude/CLAUDE.md  # ✅ Sollte existieren
```

---

## 🚀 Next Steps After Setup

1. **Create Backend Scaffolding:**
   - `backend/app/main.py` (FastAPI app)
   - `backend/app/config.py` (Environment config)
   - `backend/app/models/database.py` (SQLAlchemy setup)

2. **Create Frontend Scaffolding:**
   - `frontend/src/index.html` (Main HTML)
   - `frontend/src/js/main.js` (Entry point)
   - `frontend/src/css/main.css` (Tailwind imports)
   - `frontend/vite.config.js` (Vite config)

3. **Implement Core Features:**
   - JSON schema validation
   - Architecture CRUD API
   - Basic UI for architecture builder

---

**Last Updated:** 2026-03-22
