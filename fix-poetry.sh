#!/bin/bash

# OverCloud - Poetry Installation Fix
# Nutzt Homebrew Python statt CommandLineTools Python

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Poetry Installation Fix${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Install Homebrew Python
print_info "Step 1: Homebrew Python 3.11 installieren..."

if command -v brew >/dev/null 2>&1; then
    print_success "Homebrew gefunden"
else
    print_error "Homebrew nicht installiert!"
    echo "Installiere zuerst Homebrew:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

brew install python@3.11
print_success "Python 3.11 installiert"

# Step 2: Verify Homebrew Python
print_info "Step 2: Homebrew Python verifizieren..."

HOMEBREW_PYTHON="/opt/homebrew/bin/python3.11"
if [[ ! -f "$HOMEBREW_PYTHON" ]]; then
    # Try Intel Mac path
    HOMEBREW_PYTHON="/usr/local/bin/python3.11"
fi

if [[ ! -f "$HOMEBREW_PYTHON" ]]; then
    print_error "Homebrew Python nicht gefunden!"
    echo "Versuche manuell:"
    echo "  which python3.11"
    exit 1
fi

print_success "Homebrew Python gefunden: $HOMEBREW_PYTHON"
$HOMEBREW_PYTHON --version

# Step 3: Install Poetry with Homebrew Python
print_info "Step 3: Poetry mit Homebrew Python installieren..."

curl -sSL https://install.python-poetry.org | $HOMEBREW_PYTHON -

print_success "Poetry installiert"

# Step 4: Add to PATH
print_info "Step 4: Poetry zu PATH hinzufügen..."

POETRY_BIN="$HOME/.local/bin"
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

export PATH="$HOME/.local/bin:$PATH"

# Step 5: Configure Poetry
print_info "Step 5: Poetry konfigurieren..."

$POETRY_BIN/poetry config virtualenvs.in-project true
print_success "Poetry konfiguriert (virtualenvs.in-project = true)"

# Step 6: Verify
print_info "Step 6: Verification..."

if command -v poetry >/dev/null 2>&1; then
    print_success "Poetry ist im PATH"
    poetry --version
else
    print_error "Poetry nicht im PATH gefunden!"
    echo ""
    echo "Führe manuell aus:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  poetry --version"
    echo ""
    echo "Oder reload deine Shell:"
    echo "  source ~/.zshrc"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Poetry Installation abgeschlossen!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

print_info "Nächste Schritte:"
echo "  1. Reload Shell: source ~/.zshrc"
echo "  2. Verify: poetry --version"
echo "  3. Run Setup: ./setup.sh"
echo ""
