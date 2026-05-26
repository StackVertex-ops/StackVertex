# StackVertex Development Setup

> Complete guide to setting up your development environment with Claude Code tooling

---

## Prerequisites

### Required Software

#### 1. Python 3.11+
```bash
# macOS (using Homebrew)
brew install python@3.11

# Verify installation
python3 --version  # Should show 3.11.x or higher
pip3 --version
```

#### 2. Node.js 20+ (für Claude Code Tools only)
```bash
# macOS (using Homebrew)
brew install node@20

# Verify installation
node --version   # Should show v20.x.x
npm --version
```

#### 3. Git
```bash
# macOS (usually pre-installed, otherwise)
brew install git

# Verify
git --version
```

#### 4. Poetry (Python Dependency Management)
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"

# WICHTIG: Konfiguriere Poetry für projekt-lokale venvs
poetry config virtualenvs.in-project true
# Das erstellt .venv/ im Projektordner statt in ~/.cache/pypoetry/

# Verify
poetry --version
poetry config --list | grep virtualenvs.in-project  # Should show: true
```

#### 5. AWS CLI (für Cloud Deployments)
```bash
# macOS
brew install awscli

# Verify
aws --version

# Configure (später, wenn AWS Account ready)
aws configure
```

#### 6. Terraform (für IaC Generation)
```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify
terraform --version
```

#### 7. Docker (Optional, für lokale PostgreSQL)
```bash
# macOS - Download from https://www.docker.com/products/docker-desktop
# Or via Homebrew
brew install --cask docker

# Verify
docker --version
docker-compose --version
```

#### 8. Claude Code CLI
```bash
# Sollte bereits installiert sein
# Falls nicht, siehe: https://code.claude.com/docs

# Verify
claude --version
```

---

### Optional Tools

#### VS Code Extensions (empfohlen)
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Ruff (charliermarsh.ruff)
- Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)

#### Homebrew Installation (falls noch nicht installiert)
```bash
# macOS
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## Phase 1: Claude Code Tooling Setup

### 1. Install Superpowers MCP

Superpowers provides structured workflows for TDD, debugging, and code review.

```bash
# Install Superpowers MCP
npx @joshuapowell/superpowers install

# Or clone and install manually
git clone https://github.com/joshuapowell/superpowers.git ~/.claude/mcp/superpowers
cd ~/.claude/mcp/superpowers
npm install
```

**Configure in Claude Code settings:**

Edit `~/.claude/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "superpowers": {
        "command": "node",
        "args": ["/Users/YOUR_USERNAME/.claude/mcp/superpowers/index.js"],
        "env": {}
      }
    }
  }
}
```

**Verify installation:**
- Restart Claude Code
- Run `/brainstorming` or `/execute-plan` to test

---

### 2. Install GSD v2 Framework

GSD prevents context rot by using fresh agent sessions for each task.

```bash
# Install GSD v2 CLI
npm install -g @gsd-build/cli

# Initialize GSD in project
cd /Users/andyschwarz/Documents/Privat/StackVertex
gsd init
```

**Configure GSD:**

Edit `.gsd/config.json`:

```json
{
  "version": "2.0",
  "phases": [
    "research",
    "planning",
    "implementation",
    "validation"
  ],
  "agents": {
    "backend": {
      "role": "Backend Architect",
      "responsibilities": ["Core logic", "API design", "Database"]
    },
    "frontend": {
      "role": "Frontend Engineer",
      "responsibilities": ["UI/UX", "React components", "State management"]
    },
    "devops": {
      "role": "DevOps Engineer",
      "responsibilities": ["IaC", "Deployment", "Cloud integrations"]
    },
    "data": {
      "role": "Data Architect",
      "responsibilities": ["JSON schemas", "Versioning", "Data models"]
    },
    "security": {
      "role": "Security Auditor",
      "responsibilities": ["Security reviews", "IAM", "Compliance"]
    },
    "qa": {
      "role": "QA Engineer",
      "responsibilities": ["Testing", "CI/CD", "Quality gates"]
    }
  },
  "taskTracking": {
    "file": "tasks/todo.md",
    "lessonsFile": "tasks/lessons.md",
    "decisionsFile": "tasks/decisions.md"
  }
}
```

**Verify installation:**

```bash
gsd status
gsd --help
```

---

### 3. Enable Claude Code Agent Swarm

Agent Teams allow multiple Claude Code instances to work together.

**Option A: Environment Variable**

```bash
# Add to your shell profile (~/.zshrc or ~/.bashrc)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Reload shell
source ~/.zshrc
```

**Option B: Settings File**

Edit `~/.claude/settings.json`:

```json
{
  "experimental": {
    "agentTeams": true
  }
}
```

**Verify:**
- Restart Claude Code
- Check if `/team-create` command is available

---

### 4. Install Vibe Kanban (Optional - Phase 2)

Visual orchestration for multiple agents.

```bash
# Install Vibe Kanban CLI
npm install -g vibe-kanban

# Initialize in project
cd /Users/andyschwarz/Documents/Privat/StackVertex
vibe-kanban init

# Start Vibe Kanban UI
vibe-kanban start
```

**Access UI:** http://localhost:3333

**Note:** Vibe Kanban is optional for Phase 0/1. Install when you have 5+ parallel tasks.

---

## Phase 2: Project Dependencies Setup

### 1. Initialize Python Backend

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex

# Create backend directory
mkdir -p backend
cd backend

# WICHTIG: Stelle sicher, dass Poetry projekt-lokale venv nutzt
poetry config virtualenvs.in-project true

# Initialize Poetry project
poetry init --name stackvertex-backend --python "^3.11" --no-interaction

# Add core dependencies
poetry add fastapi uvicorn pydantic boto3 pydantic-settings
poetry add psycopg2-binary sqlalchemy alembic
poetry add python-jose passlib bcrypt python-multipart
poetry add jinja2 python-dotenv

# Add dev dependencies
poetry add --group dev pytest pytest-asyncio pytest-cov black ruff mypy
poetry add --group dev httpx  # For testing FastAPI

# Install dependencies (erstellt automatisch backend/.venv/)
poetry install

# Verify: .venv sollte im backend/ Ordner sein
ls -la .venv/  # Sollte existieren
```

**Was passiert hier:**
- Poetry erstellt `backend/.venv/` (statt systemweit)
- Alle Dependencies landen in `backend/.venv/lib/python3.11/site-packages/`
- Projekt ist isoliert von anderen Python-Projekten

### 2. Initialize Frontend (Vanilla JS)

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex

# Create frontend directory structure
mkdir -p frontend/{src,public,dist}
mkdir -p frontend/src/{js,css,components,lib}
mkdir -p frontend/public/{assets,images}

cd frontend

# Initialize package.json for build tools only
npm init -y

# Install build tools (Vite for fast dev server + bundling)
# node_modules/ wird automatisch im frontend/ Ordner erstellt
npm install --save-dev vite
npm install --save-dev tailwindcss postcss autoprefixer
npm install --save-dev @tailwindcss/forms @tailwindcss/typography

# Initialize Tailwind CSS
npx tailwindcss init -p

# Verify: node_modules sollte lokal sein
ls -la node_modules/  # Sollte existieren in frontend/
```

**Was passiert hier:**
- npm erstellt `frontend/node_modules/` (automatisch lokal)
- Alle Dependencies landen in `frontend/node_modules/`
- Kein globales Install nötig (außer Build Tools wie Vite selbst)

### 3. Create .gitignore

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/  # Poetry erstellt backend/.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Poetry
# poetry.lock sollte NICHT ignoriert werden für reproducible builds
# Nur ignorieren bei Libraries, nicht bei Applications

# Node.js (frontend build tools only)
node_modules/  # npm erstellt frontend/node_modules/
frontend/dist/
frontend/.vite/

# Testing
coverage/
.nyc_output/
.pytest_cache/

# Misc
.DS_Store
*.log
*.pem

# Local env files
.env
.env.local
.env.development
.env.test
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# Terraform
*.tfstate
*.tfstate.backup
.terraform/
terraform.tfvars
*.tfvars

# AWS
.aws/

# GSD
.gsd/sessions/
.gsd/cache/

# Temp files
tmp/
temp/

# Generated files
generated/
deployments/logs/
architectures/*.json  # User-created architectures (optional: might want to commit)
EOF
```

### 4. Initialize Git Repository

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex

# Initialize git if not already done
git init

# Add all files
git add .

# Initial commit
git commit -m "[setup] Initialize StackVertex project with Python backend + Vanilla JS frontend"
```

---

## Phase 3: Custom Slash Commands

Create custom commands for StackVertex workflows.

### 1. Create Slash Commands Directory

Already created at `.claude/commands/`

### 2. Example: `/blueprint` Command

Create `.claude/commands/blueprint.md`:

```markdown
# Blueprint Creator

You are helping the user create a new cloud architecture blueprint.

## Steps:
1. Ask about the workload type (web app, API, static site, etc.)
2. Gather requirements:
   - Expected traffic (concurrent users, requests/sec)
   - Storage needs (database size, file storage)
   - Availability requirements (uptime %, multi-AZ)
   - Security requirements (compliance, encryption)
   - Budget constraints (monthly USD)
3. Analyze requirements and make architectural decisions
4. Generate JSON architecture definition (following architecture-v1.0.0.schema.json)
5. Run evaluation (cost, security, scalability, availability)
6. Show user the complete JSON + visualized architecture
7. Ask for approval before saving

## Output:
- Valid JSON matching `docs/json-schemas/architecture-v1.0.0.schema.json`
- Saved to `architectures/{name}-{timestamp}.json`
- Summary of costs, security score, and recommendations

## Important:
- Follow requirements-driven design principles
- Show impact analysis before finalizing
- Suggest alternatives if better options exist
- Always validate against JSON schema
```

### 3. Example: `/deploy` Command

Create `.claude/commands/deploy.md`:

```markdown
# Deploy Architecture

Deploy a saved architecture to the cloud.

## Steps:
1. List available architectures from `architectures/`
2. User selects one
3. Load JSON and validate against schema
4. Generate Terraform code from JSON
5. Show Terraform plan (dry-run)
6. Explain what will be created/changed/destroyed
7. Show cost estimate
8. Ask for confirmation
9. Apply Terraform (if approved)
10. Save deployment metadata
11. Show outputs (IPs, URLs, credentials)

## Safety Checks:
- Always run `terraform plan` first
- Require explicit user approval
- Never apply without confirmation
- Log all actions to `deployments/logs/`

## Output:
- Terraform code in `generated/terraform/{architecture-id}/`
- Deployment record in `deployments/{deployment-id}.json`
- Stack outputs displayed to user
```

### 4. Example: `/review-architecture` Command

Create `.claude/commands/review-architecture.md`:

```markdown
# Architecture Review

Perform comprehensive review of an architecture definition.

## Checks:
1. **JSON Schema Validation** - Is it valid?
2. **Cost Analysis** - Within budget? Any cost-saving opportunities?
3. **Security Audit**:
   - Public exposure appropriate?
   - Encryption enabled?
   - IAM roles follow least privilege?
   - Compliance requirements met?
4. **Scalability Assessment**:
   - Auto-scaling configured?
   - Bottlenecks identified?
   - Can it handle expected traffic?
5. **Availability Check**:
   - Single points of failure?
   - Multi-AZ setup?
   - Meets uptime target?
6. **Complexity Analysis**:
   - Simpler alternatives exist?
   - Over-engineered or under-engineered?
7. **Best Practices**:
   - Follows AWS Well-Architected Framework?
   - Naming conventions consistent?
   - Tags properly applied?

## Output:
- Overall score (0-100)
- List of issues (critical, high, medium, low)
- Specific recommendations
- Alternative architectures (if applicable)
```

---

## Phase 4: Agent Team Definitions

Create agent team configurations.

### 1. Backend Architect Agent

Create `.claude/agents/backend-architect.json`:

```json
{
  "name": "Backend Architect",
  "role": "backend",
  "description": "Designs and implements core business logic, APIs, and database schemas",
  "responsibilities": [
    "Core business logic implementation",
    "REST/GraphQL API design",
    "Database schema design",
    "Integration with cloud services",
    "Performance optimization"
  ],
  "skills": [
    "NestJS",
    "Prisma",
    "PostgreSQL",
    "TypeScript",
    "API design",
    "Database optimization"
  ],
  "workflows": [
    "/brainstorming",
    "/execute-plan"
  ],
  "codeReviewFocus": [
    "Business logic correctness",
    "API contract adherence",
    "Database query performance",
    "Error handling",
    "Type safety"
  ]
}
```

### 2. Frontend Engineer Agent

Create `.claude/agents/frontend-engineer.json`:

```json
{
  "name": "Frontend Engineer",
  "role": "frontend",
  "description": "Builds UI/UX, React components, and client-side logic",
  "responsibilities": [
    "React component implementation",
    "UI/UX design implementation",
    "State management",
    "Form validation",
    "Client-side routing",
    "Accessibility (WCAG 2.1 AA)"
  ],
  "skills": [
    "Next.js 14+",
    "React Server Components",
    "shadcn/ui",
    "Tailwind CSS",
    "Zustand",
    "React Hook Form"
  ],
  "workflows": [
    "/brainstorming",
    "/execute-plan"
  ],
  "codeReviewFocus": [
    "Component composition",
    "Performance (memoization, lazy loading)",
    "Accessibility",
    "Type safety",
    "Responsive design"
  ]
}
```

### 3. Create Remaining Agent Definitions

Similarly, create:
- `.claude/agents/devops-engineer.json`
- `.claude/agents/data-architect.json`
- `.claude/agents/security-auditor.json`
- `.claude/agents/qa-engineer.json`

---

## Phase 5: Verification

### Check Installation

```bash
# Check Node.js
node --version  # Should be 20+

# Check pnpm
pnpm --version

# Check GSD
gsd --version

# Check Claude Code experimental features
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS  # Should be 1
```

### Test Claude Code Tools

In Claude Code CLI:

```
/brainstorming
> Should show Superpowers brainstorming interface

/team-create name="Backend Team"
> Should create an agent team

/blueprint
> Should start blueprint creation workflow
```

---

## Troubleshooting

### Superpowers Not Loading
- Check `~/.claude/settings.json` for correct path
- Verify `node` is in PATH
- Check Superpowers installation: `ls ~/.claude/mcp/superpowers`

### Agent Teams Not Available
- Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Restart Claude Code
- Check Claude Code version (must be latest)

### GSD Commands Not Found
- Reinstall: `npm uninstall -g @gsd-build/cli && npm install -g @gsd-build/cli`
- Check PATH: `which gsd`

---

## Next Steps

After setup is complete:

1. ✅ All tools installed and verified
2. Read [CLAUDE.md](./.claude/CLAUDE.md) for development guidelines
3. Review [tasks/todo.md](../tasks/todo.md) for current tasks
4. Start with JSON schema validation
5. Build first prototype (backend scaffolding)

---

**Setup Complete! Ready to build StackVertex.** 🚀

---

Last updated: 2026-03-22
