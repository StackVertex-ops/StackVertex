#!/bin/bash
#
# StackVertex - Dev Environment Deployment
#
# Komplettes Deployment für Dev-Umgebung via GitHub Actions
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🚀 StackVertex - Dev Environment Deployment"
echo "============================================="
echo ""

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) nicht installiert${NC}"
    echo "Installation: brew install gh"
    exit 1
fi

# Check gh auth
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Nicht bei GitHub eingeloggt${NC}"
    echo "Login: gh auth login"
    exit 1
fi

# Check Secrets
echo "🔍 Prüfe GitHub Secrets..."
if ! gh secret list | grep -q "AWS_ACCESS_KEY_ID"; then
    echo -e "${YELLOW}⚠️  GitHub Secrets nicht konfiguriert${NC}"
    echo "Setup: ./setup-github-secrets.sh"
    read -p "Trotzdem fortfahren? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ GitHub Secrets OK${NC}"
fi
echo ""

# Ask for deployment type
echo "❓ Deployment-Typ auswählen:"
echo "   1) Komplettes Deployment (Bootstrap + Infrastructure)"
echo "   2) Nur Infrastructure Update (Bootstrap existiert bereits)"
echo "   3) Nur Frontend Deployment"
echo ""
read -p "Auswahl (1/2/3): " deploy_type

case $deploy_type in
    1)
        SKIP_BOOTSTRAP=false
        DEPLOY_INFRA=true
        DEPLOY_FRONTEND=true
        ;;
    2)
        SKIP_BOOTSTRAP=true
        DEPLOY_INFRA=true
        DEPLOY_FRONTEND=true
        ;;
    3)
        SKIP_BOOTSTRAP=true
        DEPLOY_INFRA=false
        DEPLOY_FRONTEND=true
        ;;
    *)
        echo -e "${RED}❌ Ungültige Auswahl${NC}"
        exit 1
        ;;
esac

# Confirm
echo ""
echo "Zusammenfassung:"
echo "  - Bootstrap: $([ $SKIP_BOOTSTRAP = false ] && echo 'JA' || echo 'NEIN')"
echo "  - Infrastructure: $([ $DEPLOY_INFRA = true ] && echo 'JA' || echo 'NEIN')"
echo "  - Frontend: $([ $DEPLOY_FRONTEND = true ] && echo 'JA' || echo 'NEIN')"
echo ""
read -p "Deployment starten? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Abgebrochen."
    exit 0
fi

START_TIME=$(date +%s)

# ========================================
# Phase 1: Bootstrap (optional)
# ========================================
if [ "$SKIP_BOOTSTRAP" = false ]; then
    echo ""
    echo "=================================================="
    echo "Phase 1: Bootstrap"
    echo "=================================================="
    echo ""

    # Get Account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo "📋 Bitte AWS Account ID eingeben (12 Stellen):"
        read -p "Account ID: " AWS_ACCOUNT_ID
    else
        echo -e "${BLUE}AWS Account ID: $AWS_ACCOUNT_ID${NC}"
    fi

    # Trigger Bootstrap
    echo "🏗️  Triggere Bootstrap Workflow..."
    gh workflow run bootstrap.yml \
      -f aws_account_id="$AWS_ACCOUNT_ID" \
      -f aws_region="eu-central-1" \
      -f project_name="stackvertex"

    sleep 5

    RUN_ID=$(gh run list --workflow=bootstrap.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    echo -e "${BLUE}Bootstrap Run ID: $RUN_ID${NC}"

    echo "👀 Watching Bootstrap..."
    gh run watch $RUN_ID

    STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
    if [ "$STATUS" != "success" ]; then
        echo -e "${RED}❌ Bootstrap failed!${NC}"
        gh run view $RUN_ID --log-failed
        exit 1
    fi

    echo -e "${GREEN}✅ Bootstrap erfolgreich!${NC}"
fi

# ========================================
# Phase 2: Infrastructure Deployment
# ========================================
if [ "$DEPLOY_INFRA" = true ]; then
    echo ""
    echo "=================================================="
    echo "Phase 2: Infrastructure Deployment"
    echo "=================================================="
    echo ""

    echo "🚀 Triggere Deploy Workflow..."
    gh workflow run deploy.yml \
      -f environment=dev \
      -f action=apply

    sleep 5

    RUN_ID=$(gh run list --workflow=deploy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    echo -e "${BLUE}Deploy Run ID: $RUN_ID${NC}"

    echo "👀 Watching Deployment..."
    gh run watch $RUN_ID

    STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
    if [ "$STATUS" != "success" ]; then
        echo -e "${RED}❌ Deployment failed!${NC}"
        gh run view $RUN_ID --log-failed
        exit 1
    fi

    echo -e "${GREEN}✅ Deployment erfolgreich!${NC}"
elif [ "$DEPLOY_FRONTEND" = true ]; then
    # Frontend-only deployment via existing workflow
    echo ""
    echo "=================================================="
    echo "Frontend Deployment"
    echo "=================================================="
    echo ""

    echo "🚀 Triggere Deploy Workflow (Frontend only)..."
    gh workflow run deploy.yml \
      -f environment=dev \
      -f action=apply

    sleep 5

    RUN_ID=$(gh run list --workflow=deploy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    echo -e "${BLUE}Deploy Run ID: $RUN_ID${NC}"

    echo "👀 Watching Deployment..."
    gh run watch $RUN_ID

    STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
    if [ "$STATUS" != "success" ]; then
        echo -e "${RED}❌ Deployment failed!${NC}"
        gh run view $RUN_ID --log-failed
        exit 1
    fi

    echo -e "${GREEN}✅ Frontend Deployment erfolgreich!${NC}"
fi

# ========================================
# Summary
# ========================================
echo ""
echo "=================================================="
echo "Deployment Summary"
echo "=================================================="
echo ""

# Get URLs from Terraform outputs
echo "📊 Deployment URLs:"
aws s3api get-bucket-website --bucket stackvertex-dev-frontend 2>/dev/null && {
    FRONTEND_URL="http://stackvertex-dev-frontend.s3-website.eu-central-1.amazonaws.com"
    echo -e "${GREEN}🌐 Frontend:${NC} $FRONTEND_URL"
} || echo "⚠️  Frontend URL nicht verfügbar"

# Get API Gateway URL
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='stackvertex-dev-http'].ApiId" --output text 2>/dev/null || echo "")
if [ -n "$API_ID" ]; then
    echo -e "${GREEN}🌐 API:${NC} https://${API_ID}.execute-api.eu-central-1.amazonaws.com/"
fi

# Zeit-Info
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
ELAPSED_MIN=$((ELAPSED / 60))

echo ""
echo "⏱️  Deployment-Dauer: ${ELAPSED_MIN} Minuten"
echo ""
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Admin User erstellen: ./create-admin-user.sh"
echo "  2. Frontend testen: $FRONTEND_URL"
echo "  3. API testen: https://${API_ID}.execute-api.eu-central-1.amazonaws.com/"
echo "  4. Logs checken: gh run view $RUN_ID --log"
echo ""
echo -e "${YELLOW}⚠️  WICHTIG: Erstelle zuerst einen Admin User bevor du dich einloggst!${NC}"
echo "   Führe aus: ./create-admin-user.sh"
echo ""
