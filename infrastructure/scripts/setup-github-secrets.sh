#!/bin/bash
#
# StackVertex - Setup GitHub Secrets für Pluralsight
#
# Usage: ./setup-github-secrets.sh
#
# WICHTIG: Rufe dieses Script VOR dem Deployment auf
# Es setzt alle nötigen GitHub Secrets für den Deploy-Workflow

set -e

echo "🔐 StackVertex - GitHub Secrets Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) nicht installiert${NC}"
    echo "Installation: brew install gh"
    exit 1
fi

# Check gh auth
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Nicht bei GitHub eingeloggt${NC}"
    echo "Bitte einloggen:"
    gh auth login
fi

echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
echo ""

# AWS Credentials abfragen
echo "📋 Bitte Pluralsight AWS Credentials eingeben:"
echo ""

read -p "AWS Access Key ID (AKIA...): " AWS_KEY
read -sp "AWS Secret Access Key: " AWS_SECRET
echo ""

if [ -z "$AWS_KEY" ] || [ -z "$AWS_SECRET" ]; then
    echo -e "${RED}❌ AWS Credentials dürfen nicht leer sein${NC}"
    exit 1
fi

# SECRET_KEY generieren
echo ""
echo "🔑 Generiere SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Secrets setzen
echo ""
echo "🚀 Setze GitHub Secrets..."

gh secret set AWS_ACCESS_KEY_ID --body "$AWS_KEY"
echo -e "${GREEN}✅ AWS_ACCESS_KEY_ID gesetzt${NC}"

gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET"
echo -e "${GREEN}✅ AWS_SECRET_ACCESS_KEY gesetzt${NC}"

gh secret set SECRET_KEY --body "$SECRET_KEY"
echo -e "${GREEN}✅ SECRET_KEY generiert & gesetzt${NC}"

# Optional: Weitere Secrets
echo ""
read -p "Slack Webhook URL (optional, Enter zum Überspringen): " SLACK_URL
if [ -n "$SLACK_URL" ]; then
    gh secret set SLACK_WEBHOOK_URL --body "$SLACK_URL"
    echo -e "${GREEN}✅ SLACK_WEBHOOK_URL gesetzt${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ GitHub Secrets Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Secrets gesetzt:"
echo "  - AWS_ACCESS_KEY_ID"
echo "  - AWS_SECRET_ACCESS_KEY"
echo "  - SECRET_KEY"
if [ -n "$SLACK_URL" ]; then
    echo "  - SLACK_WEBHOOK_URL"
fi
echo ""
echo "Nächster Schritt: ./deploy-pluralsight-actions.sh"
echo ""
