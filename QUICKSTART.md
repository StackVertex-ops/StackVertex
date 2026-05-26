# StackVertex - Quick Start Guide

> Get StackVertex running locally in ~30 minutes

---

## 🚀 Installation Steps

### Step 1: Install Prerequisites (10-15 min)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Install Node.js 20+ (for frontend build tools + Claude Code tools)
brew install node@20

# Install Poetry (Python dependency management)
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# WICHTIG: Konfiguriere Poetry für projekt-lokale venvs
poetry config virtualenvs.in-project true
# Das erstellt .venv/ im Projektordner statt systemweit

# Install AWS CLI (optional, for later)
brew install awscli

# Install Terraform (optional, for later)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify installations
python3 --version   # Should be 3.11+
node --version      # Should be v20+
poetry --version
```

---

### Step 2: Clone & Setup Project (5 min)

```bash
# Navigate to project directory
cd /Users/andyschwarz/Documents/Privat/StackVertex

# Initialize git (if not done)
git init

# Create .gitignore
# (Already exists in project, but verify it's there)
cat .gitignore
```

---

### Step 3: Install Claude Code Tools (10 min)

#### 3a. Install Superpowers MCP

```bash
# Option 1: Quick install
npx @joshuapowell/superpowers install

# Option 2: Manual install (if npx fails)
mkdir -p ~/.claude/mcp
git clone https://github.com/joshuapowell/superpowers.git ~/.claude/mcp/superpowers
cd ~/.claude/mcp/superpowers
npm install
```

**Configure Superpowers:**

Edit `~/.claude/settings.json` (create if doesn't exist):

```json
{
  "mcp": {
    "servers": {
      "superpowers": {
        "command": "node",
        "args": ["/Users/andyschwarz/.claude/mcp/superpowers/index.js"],
        "env": {}
      }
    }
  }
}
```

**Test:** Restart Claude Code, then run `/brainstorming`

---

#### 3b. Install GSD v2 Framework

```bash
# Install GSD CLI globally
npm install -g @gsd-build/cli

# Initialize in project
cd /Users/andyschwarz/Documents/Privat/StackVertex
gsd init

# Verify
gsd status
```

**Note:** GSD config is already in `.gsd/config.json` (created by setup)

---

#### 3c. Enable Agent Swarm

```bash
# Add to ~/.zshrc
echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Verify
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS  # Should print: 1
```

**Test:** Restart Claude Code, then check if `/team-create` command exists

---

### Step 4: Initialize Backend (Python)

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex

# Create backend directory
mkdir -p backend
cd backend

# Stelle sicher, dass venv lokal erstellt wird
poetry config virtualenvs.in-project true

# Initialize Poetry project
poetry init --name overcloud-backend --python "^3.11" --no-interaction

# Add dependencies
poetry add fastapi uvicorn pydantic boto3 pydantic-settings
poetry add psycopg2-binary sqlalchemy alembic
poetry add python-jose passlib bcrypt python-multipart
poetry add jinja2 python-dotenv

# Add dev dependencies
poetry add --group dev pytest pytest-asyncio pytest-cov black ruff mypy httpx

# Install all dependencies (erstellt backend/.venv/)
poetry install
```

**Verify:**

```bash
# Check dass .venv lokal ist
ls -la .venv/  # Sollte existieren in backend/

# Activate venv
poetry shell

# Check Python version (sollte aus .venv kommen)
python --version  # Should be 3.11+
which python      # Should show: .../backend/.venv/bin/python

# List installed packages
poetry show
```

**WICHTIG:** Dein Python läuft jetzt aus `backend/.venv/bin/python`, **nicht** systemweit!

---

### Step 5: Initialize Frontend (Vanilla JS)

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex

# Create frontend structure
mkdir -p frontend/{src,public,dist}
mkdir -p frontend/src/{js,css,components,lib}
mkdir -p frontend/public/{assets,images}

# Initialize package.json
cd frontend
npm init -y

# Install build tools
npm install --save-dev vite
npm install --save-dev tailwindcss postcss autoprefixer
npm install --save-dev @tailwindcss/forms @tailwindcss/typography

# Initialize Tailwind CSS
npx tailwindcss init -p
```

**Verify:**

```bash
npm list --depth=0  # Shows installed packages
```

---

### Step 6: Verify Everything Works

#### Backend Test:

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex/backend

# Check Python environment
poetry run python --version

# Run Black formatter (should do nothing if no Python files yet)
poetry run black --check .

# Run Ruff linter
poetry run ruff check .
```

#### Frontend Test:

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex/frontend

# Check Vite
npx vite --version

# Check Tailwind
npx tailwindcss --help
```

#### Claude Code Tools Test:

Open Claude Code CLI and run:

```
/brainstorming
> Should open Superpowers brainstorming mode

/team-create name="Test Team"
> Should create agent team (if swarm enabled)
```

---

## ✅ Setup Complete!

You now have:
- ✅ Python 3.11+ with Poetry
- ✅ Node.js 20+ with npm
- ✅ FastAPI backend scaffolding
- ✅ Vite + Tailwind frontend scaffolding
- ✅ Claude Code tools (Superpowers, GSD, Agent Swarm)

---

## 🎯 Next Steps

### Option A: Follow Full Setup Guide
👉 See [`docs/SETUP.md`](./docs/SETUP.md) for complete setup with custom slash commands, agent definitions, etc.

### Option B: Start Coding Immediately
👉 Tell Claude Code: **"Tools sind ready, let's start implementation!"**

I will then:
1. Create backend scaffolding (FastAPI app structure)
2. Create frontend scaffolding (Vite + Tailwind boilerplate)
3. Implement first feature (JSON schema validation)

---

## 📚 Useful Commands

### Backend (Python)

```bash
cd /Users/andyschwarz/Documents/Privat/StackVertex/backend

# Option 1: Activate venv (dann kannst du commands direkt ausführen)
poetry shell
python --version  # Sollte aus .venv kommen
uvicorn app.main:app --reload

# Option 2: Run commands mit poetry run (ohne shell activation)
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type check
poetry run mypy .

# Exit venv (wenn du in poetry shell bist)
exit
```

**Tipp:** Wenn du `poetry shell` ausführst, kannst du danach alle Commands **ohne** `poetry run` nutzen!

### Frontend (Vanilla JS)

```bash
# Start Vite dev server (after src/ files exist)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Git

```bash
# Check status
git status

# Stage all files
git add .

# Commit with message
git commit -m "[scope] Description"

# View log
git log --oneline -10
```

---

## 🆘 Troubleshooting

### Poetry not found
```bash
# Re-install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Konfiguriere für projekt-lokale venvs
poetry config virtualenvs.in-project true
```

### .venv nicht im backend/ Ordner
```bash
cd backend

# Check Poetry config
poetry config virtualenvs.in-project  # Sollte: true

# Falls false, setze auf true
poetry config virtualenvs.in-project true

# Remove alte venv und neu erstellen
poetry env remove python
poetry install

# Verify
ls -la .venv/  # Sollte jetzt existieren
```

### Superpowers not loading
```bash
# Check settings file exists
cat ~/.claude/settings.json

# Verify path in settings matches installation
ls -la ~/.claude/mcp/superpowers
```

### Agent Swarm not working
```bash
# Check environment variable
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS

# Re-add if missing
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

### Python version issues
```bash
# Use specific Python version
poetry env use python3.11

# Remove old venv and recreate
poetry env remove python
poetry install
```

---

## 📞 Need Help?

- **Full setup guide:** [`docs/SETUP.md`](./docs/SETUP.md)
- **Project rules:** [`.claude/CLAUDE.md`](./.claude/CLAUDE.md)
- **Architecture decisions:** [`tasks/decisions.md`](./tasks/decisions.md)
- **Current tasks:** [`tasks/todo.md`](./tasks/todo.md)

---

**You're all set! Time to build StackVertex.** 🚀
