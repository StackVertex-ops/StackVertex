#!/bin/bash
#
# StackVertex - Pluralsight Deployment via GitHub Actions
#
# Usage: ./deploy-pluralsight-actions.sh
#
# Führt komplettes Deployment über GitHub Actions durch:
# 1. Bootstrap
# 2. Infrastructure Deploy
# 3. Monitoring

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🚀 StackVertex - Pluralsight Deployment (GitHub Actions)"
echo "=========================================================="
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
    echo "Bitte zuerst: gh auth login"
    exit 1
fi

# Timer
START_TIME=$(date +%s)
DESTROY_TIME=$((START_TIME + 12600)) # 3.5 Stunden
echo -e "${BLUE}⏰ Start: $(date '+%H:%M:%S')${NC}"
echo -e "${YELLOW}⚠️  Destroy spätestens um: $(date -r $DESTROY_TIME '+%H:%M:%S')${NC}"
echo ""

# Check Secrets
echo "🔍 Prüfe GitHub Secrets..."
if ! gh secret list | grep -q "AWS_ACCESS_KEY_ID"; then
    echo -e "${RED}❌ GitHub Secrets nicht konfiguriert${NC}"
    echo "Bitte zuerst: ./setup-github-secrets.sh ausführen"
    exit 1
fi
echo -e "${GREEN}✅ GitHub Secrets OK${NC}"
echo ""

# Check if Bootstrap needed
echo "🔍 Prüfe ob Bootstrap nötig ist..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}❌ AWS Credentials ungültig${NC}"
    echo "Bitte zuerst AWS Credentials konfigurieren"
    exit 1
fi

BUCKET_NAME="stackvertex-dev-terraform-state-${ACCOUNT_ID}"
if aws s3 ls "s3://$BUCKET_NAME" &>/dev/null; then
    echo -e "${GREEN}✅ Bootstrap bereits durchgeführt (Bucket existiert)${NC}"
    SKIP_BOOTSTRAP=true
else
    echo -e "${YELLOW}⚠️  Bootstrap noch nicht durchgeführt${NC}"
    SKIP_BOOTSTRAP=false
fi

# Confirm
echo ""
read -p "Deployment starten? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Abgebrochen."
    exit 0
fi

if [ "$SKIP_BOOTSTRAP" = false ]; then
    echo ""
    echo "=================================================="
    echo "Phase 1: Bootstrap"
    echo "=================================================="
    echo ""
else
    echo ""
    echo "=================================================="
    echo "Phase 1: Bootstrap (übersprungen - bereits vorhanden)"
    echo "=================================================="
    echo ""
fi

if [ "$SKIP_BOOTSTRAP" = false ]; then
    # Bootstrap
    echo "🏗️  Triggere Bootstrap Workflow..."
    gh workflow run bootstrap.yml \
      -f aws_account_id="$ACCOUNT_ID" \
      -f aws_region="eu-central-1" \
      -f project_name="stackvertex"

    echo "⏳ Warte auf Workflow Start..."
    sleep 5

    # Get latest run
    RUN_ID=$(gh run list --workflow=bootstrap.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    echo -e "${BLUE}Run ID: $RUN_ID${NC}"

    # Watch bootstrap
    echo "👀 Watching bootstrap workflow..."
    gh run watch $RUN_ID

    # Check status
    STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
    if [ "$STATUS" != "success" ]; then
        echo -e "${RED}❌ Bootstrap failed!${NC}"
        echo "Logs:"
        gh run view $RUN_ID --log
        exit 1
    fi

    echo -e "${GREEN}✅ Bootstrap erfolgreich!${NC}"
    echo ""
fi

echo "=================================================="
echo "Phase 2: Infrastructure Deployment"
echo "=================================================="
echo ""

# Deploy
echo "🚀 Triggere Deploy Workflow..."
gh workflow run deploy.yml \
  -f environment=dev \
  -f action=apply

echo "⏳ Warte auf Workflow Start..."
sleep 5

# Get latest run
RUN_ID=$(gh run list --workflow=deploy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo -e "${BLUE}Run ID: $RUN_ID${NC}"

# Watch deployment
echo "👀 Watching deployment workflow (dauert ~20-30 min)..."
gh run watch $RUN_ID

# Check status
STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
if [ "$STATUS" != "success" ]; then
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo "Logs:"
    gh run view $RUN_ID --log
    exit 1
fi

echo -e "${GREEN}✅ Deployment erfolgreich!${NC}"
echo ""

echo "=================================================="
echo "Deployment Summary"
echo "=================================================="

# Get outputs from workflow logs
echo "📊 Terraform Outputs:"
gh run view $RUN_ID --log | grep -A 20 "Terraform Output" || echo "Outputs in Workflow Logs checken"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "=================================================="

# Zeit-Info
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
ELAPSED_MIN=$((ELAPSED / 60))
REMAINING=$((DESTROY_TIME - END_TIME))
REMAINING_MIN=$((REMAINING / 60))

echo ""
echo "⏱️  Deployment-Dauer: ${ELAPSED_MIN} Minuten"
echo "⏰ Verbleibende Zeit: ${REMAINING_MIN} Minuten"
echo ""
echo -e "${YELLOW}⚠️  Denk dran: Destroy spätestens um $(date -r $DESTROY_TIME '+%H:%M')!${NC}"
echo ""
echo "Nächste Schritte:"
echo "1. GitHub → Actions → Workflow Logs checken für Outputs"
echo "2. Testing durchführen"
echo "3. Destroy: ./destroy-pluralsight.sh"
echo ""
