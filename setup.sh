#!/bin/bash

# OverCloud - Automatisches Setup Script
# Installiert alle Prerequisites und initialisiert das Projekt
#
# Usage: ./setup.sh
#
# Autor: Claude (OverCloud Team)
# Datum: 2026-03-22

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Prompt user for confirmation
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Main setup
main() {
    print_header "OverCloud Setup Script"
    print_info "Dieses Script installiert alle Prerequisites und initialisiert OverCloud"
    echo ""

    # Confirm start
    if ! confirm "Möchtest du mit dem Setup fortfahren?"; then
        print_warning "Setup abgebrochen."
        exit 0
    fi

    # Step 1: Check/Install Homebrew
    print_header "Step 1/8: Homebrew"
    if command_exists brew; then
        print_success "Homebrew ist bereits installiert"
        brew --version
    else
        print_warning "Homebrew nicht gefunden"
        if confirm "Homebrew installieren?"; then
            print_info "Installiere Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            print_success "Homebrew installiert"
        else
            print_error "Homebrew wird benötigt. Setup abgebrochen."
            exit 1
        fi
    fi

    # Step 2: Check/Install Python 3.11+
    print_header "Step 2/8: Python 3.11+"
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [[ $PYTHON_MAJOR -ge 3 ]] && [[ $PYTHON_MINOR -ge 11 ]]; then
            print_success "Python $PYTHON_VERSION ist installiert"
        else
            print_warning "Python $PYTHON_VERSION ist zu alt (brauche 3.11+)"
            if confirm "Python 3.11 installieren?"; then
                brew install python@3.11
                print_success "Python 3.11 installiert"
            else
                print_error "Python 3.11+ wird benötigt. Setup abgebrochen."
                exit 1
            fi
        fi
    else
        print_warning "Python nicht gefunden"
        if confirm "Python 3.11 installieren?"; then
            brew install python@3.11
            print_success "Python 3.11 installiert"
        else
            print_error "Python wird benötigt. Setup abgebrochen."
            exit 1
        fi
    fi

    # Step 3: Check/Install Node.js 20+
    print_header "Step 3/8: Node.js 20+"
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [[ $NODE_VERSION -ge 20 ]]; then
            print_success "Node.js $(node --version) ist installiert"
        else
            print_warning "Node.js v$NODE_VERSION ist zu alt (brauche v20+)"
            if confirm "Node.js 20 installieren?"; then
                brew install node@20
                print_success "Node.js 20 installiert"
            else
                print_error "Node.js 20+ wird benötigt. Setup abgebrochen."
                exit 1
            fi
        fi
    else
        print_warning "Node.js nicht gefunden"
        if confirm "Node.js 20 installieren?"; then
            brew install node@20
            print_success "Node.js 20 installiert"
        else
            print_error "Node.js wird benötigt. Setup abgebrochen."
            exit 1
        fi
    fi

    # Step 4: Check/Install Poetry
    print_header "Step 4/8: Poetry"
    if command_exists poetry; then
        print_success "Poetry ist bereits installiert"
        poetry --version
    else
        print_warning "Poetry nicht gefunden"
        if confirm "Poetry installieren?"; then
            print_info "Installiere Poetry..."
            curl -sSL https://install.python-poetry.org | python3 -

            # Add to PATH
            export PATH="$HOME/.local/bin:$PATH"

            # Add to shell config
            SHELL_CONFIG=""
            if [[ -f "$HOME/.zshrc" ]]; then
                SHELL_CONFIG="$HOME/.zshrc"
            elif [[ -f "$HOME/.bashrc" ]]; then
                SHELL_CONFIG="$HOME/.bashrc"
            fi

            if [[ -n "$SHELL_CONFIG" ]]; then
                if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_CONFIG"; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
                    print_info "PATH zu $SHELL_CONFIG hinzugefügt"
                fi
            fi

            print_success "Poetry installiert"
        else
            print_error "Poetry wird benötigt. Setup abgebrochen."
            exit 1
        fi
    fi

    # Configure Poetry for in-project venv
    print_info "Konfiguriere Poetry für projekt-lokale venvs..."
    poetry config virtualenvs.in-project true
    print_success "Poetry konfiguriert (virtualenvs.in-project = true)"

    # Step 5: Optional - AWS CLI
    print_header "Step 5/8: AWS CLI (Optional)"
    if command_exists aws; then
        print_success "AWS CLI ist bereits installiert"
        aws --version
    else
        print_warning "AWS CLI nicht gefunden"
        if confirm "AWS CLI installieren? (Wird später für Deployments gebraucht)"; then
            brew install awscli
            print_success "AWS CLI installiert"
        else
            print_warning "Übersprungen - kann später installiert werden"
        fi
    fi

    # Step 6: Optional - Terraform
    print_header "Step 6/8: Terraform (Optional)"
    if command_exists terraform; then
        print_success "Terraform ist bereits installiert"
        terraform --version | head -n1
    else
        print_warning "Terraform nicht gefunden"
        if confirm "Terraform installieren? (Wird für IaC-Generation gebraucht)"; then
            brew tap hashicorp/tap
            brew install hashicorp/tap/terraform
            print_success "Terraform installiert"
        else
            print_warning "Übersprungen - kann später installiert werden"
        fi
    fi

    # Step 7: Initialize Backend
    print_header "Step 7/8: Backend initialisieren"

    if [[ ! -d "backend" ]]; then
        print_info "Erstelle backend/ Verzeichnis..."
        mkdir -p backend
    fi

    cd backend

    if [[ ! -f "pyproject.toml" ]]; then
        print_info "Initialisiere Poetry Projekt..."
        poetry init --name overcloud-backend --python "^3.11" --no-interaction

        print_info "Installiere Backend Dependencies..."
        poetry add fastapi uvicorn pydantic boto3 pydantic-settings
        poetry add psycopg2-binary sqlalchemy alembic
        poetry add python-jose passlib bcrypt python-multipart
        poetry add jinja2 python-dotenv

        print_info "Installiere Dev Dependencies..."
        poetry add --group dev pytest pytest-asyncio pytest-cov black ruff mypy httpx

        print_info "Installiere alle Dependencies..."
        poetry install

        print_success "Backend initialisiert"
    else
        print_warning "pyproject.toml existiert bereits"
        if confirm "Dependencies neu installieren?"; then
            poetry install
            print_success "Dependencies installiert"
        else
            print_warning "Übersprungen"
        fi
    fi

    # Verify .venv exists
    if [[ -d ".venv" ]]; then
        print_success "Virtual Environment erstellt: backend/.venv/"
    else
        print_error ".venv nicht gefunden!"
    fi

    cd ..

    # Step 8: Initialize Frontend
    print_header "Step 8/8: Frontend initialisieren"

    if [[ ! -d "frontend" ]]; then
        print_info "Erstelle frontend/ Verzeichnisstruktur..."
        mkdir -p frontend/{src,public,dist}
        mkdir -p frontend/src/{js,css,components,lib}
        mkdir -p frontend/public/{assets,images}
    fi

    cd frontend

    if [[ ! -f "package.json" ]]; then
        print_info "Initialisiere NPM Projekt..."
        npm init -y

        print_info "Installiere Frontend Dependencies..."
        npm install --save-dev vite
        npm install --save-dev tailwindcss postcss autoprefixer
        npm install --save-dev @tailwindcss/forms @tailwindcss/typography

        print_info "Initialisiere Tailwind CSS..."
        npx tailwindcss init -p

        print_success "Frontend initialisiert"
    else
        print_warning "package.json existiert bereits"
        if confirm "Dependencies neu installieren?"; then
            npm install
            print_success "Dependencies installiert"
        else
            print_warning "Übersprungen"
        fi
    fi

    # Verify node_modules exists
    if [[ -d "node_modules" ]]; then
        print_success "Node modules installiert: frontend/node_modules/"
    else
        print_error "node_modules nicht gefunden!"
    fi

    cd ..

    # Step 9: Create .gitignore if not exists
    print_header "Finalisierung"

    if [[ ! -f ".gitignore" ]]; then
        print_info "Erstelle .gitignore..."
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
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Node.js
node_modules/
frontend/dist/
frontend/.vite/

# Environment
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
.DS_Store

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

# Temp
tmp/
temp/

# Generated
generated/
deployments/logs/
architectures/*.json
EOF
        print_success ".gitignore erstellt"
    else
        print_info ".gitignore existiert bereits"
    fi

    # Initialize git if not exists
    if [[ ! -d ".git" ]]; then
        print_info "Initialisiere Git Repository..."
        git init
        git add .
        git commit -m "[setup] Initialize OverCloud project with Python backend + Vanilla JS frontend"
        print_success "Git Repository initialisiert"
    else
        print_info "Git Repository existiert bereits"
    fi

    # Final Summary
    print_header "Setup abgeschlossen!"

    echo -e "${GREEN}✓ Alle Prerequisites installiert${NC}"
    echo -e "${GREEN}✓ Backend initialisiert (Python + Poetry)${NC}"
    echo -e "${GREEN}✓ Frontend initialisiert (Vanilla JS + Vite)${NC}"
    echo ""

    print_info "Verzeichnisstruktur:"
    echo "  backend/.venv/          ← Python Virtual Environment"
    echo "  frontend/node_modules/  ← NPM Dependencies"
    echo ""

    print_info "Nächste Schritte:"
    echo ""
    echo "  1. Backend testen:"
    echo "     cd backend"
    echo "     poetry shell"
    echo "     python --version"
    echo ""
    echo "  2. Frontend testen:"
    echo "     cd frontend"
    echo "     npm run dev  (nachdem src/index.html erstellt wurde)"
    echo ""
    echo "  3. Claude Code Tools installieren:"
    echo "     Siehe docs/SETUP.md für Superpowers, GSD, Agent Swarm"
    echo ""

    print_success "Setup erfolgreich abgeschlossen! 🚀"
    echo ""
    print_info "Für Details siehe:"
    echo "  - QUICKSTART.md"
    echo "  - docs/SETUP.md"
    echo "  - docs/PROJECT-STRUCTURE.md"
}

# Run main function
main
