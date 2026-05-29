#!/bin/bash
#
# StackVertex - Pluralsight Destroy (via GitHub Actions oder Terraform)
#
# Usage: ./destroy-pluralsight.sh [method]
#   method: actions (default) | terraform | quick
#
# Methoden:
#   actions    - Via GitHub Actions Workflow (empfohlen)
#   terraform  - Via lokales Terraform destroy
#   quick      - Via quick-destroy.sh Script (schnellste)

set -e

METHOD=${1:-actions}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🗑️  StackVertex - Pluralsight Destroy"
echo "========================================"
echo ""
echo "Methode: $METHOD"
echo ""

# Confirmation
echo -e "${YELLOW}⚠️  WARNUNG: Löscht ALLE StackVertex-Dev Ressourcen!${NC}"
read -p "Fortfahren? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""

case $METHOD in
    actions)
        echo "=================================================="
        echo "Destroy via GitHub Actions"
        echo "=================================================="
        echo ""

        # Check gh CLI
        if ! command -v gh &> /dev/null; then
            echo -e "${RED}❌ GitHub CLI nicht installiert${NC}"
            echo "Fallback: Nutze 'terraform' Methode"
            echo "./destroy-pluralsight.sh terraform"
            exit 1
        fi

        # Trigger destroy workflow
        echo "🚀 Triggere Destroy Workflow..."
        gh workflow run destroy.yml \
          -f environment=dev \
          -f confirm_destroy=DESTROY \
          -f skip_approval=true

        echo "⏳ Warte auf Workflow Start..."
        sleep 5

        # Get latest run
        RUN_ID=$(gh run list --workflow=destroy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
        echo -e "${BLUE}Run ID: $RUN_ID${NC}"

        # Watch destroy
        echo "👀 Watching destroy workflow (dauert ~15-20 min)..."
        gh run watch $RUN_ID

        # Check status
        STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
        if [ "$STATUS" != "success" ]; then
            echo -e "${RED}❌ Destroy failed!${NC}"
            echo "Logs:"
            gh run view $RUN_ID --log
            echo ""
            echo "Fallback: Nutze quick-destroy.sh"
            exit 1
        fi

        echo -e "${GREEN}✅ Destroy erfolgreich!${NC}"
        ;;

    terraform)
        echo "=================================================="
        echo "Destroy via Terraform"
        echo "=================================================="
        echo ""

        cd ../terraform/environments/dev

        # Check if terraform initialized
        if [ ! -d ".terraform" ]; then
            echo "Terraform initialisieren..."
            terraform init
        fi

        # Destroy
        echo "🗑️  Terraform Destroy..."
        terraform destroy -auto-approve || {
            echo -e "${YELLOW}⚠️  Terraform destroy fehlgeschlagen, versuche force-unlock...${NC}"

            LOCK_ID=$(terraform state list 2>&1 | grep -oP 'ID: \K[^"]+' | head -1 || echo "")

            if [ -n "$LOCK_ID" ]; then
                terraform force-unlock -force "$LOCK_ID"
            fi

            terraform destroy -auto-approve
        }

        echo -e "${GREEN}✅ Terraform Destroy erfolgreich!${NC}"
        ;;

    quick)
        echo "=================================================="
        echo "Quick Destroy (Script)"
        echo "=================================================="
        echo ""

        # Use quick-destroy.sh
        ./quick-destroy.sh dev

        echo -e "${GREEN}✅ Quick Destroy erfolgreich!${NC}"
        ;;

    *)
        echo -e "${RED}❌ Unbekannte Methode: $METHOD${NC}"
        echo "Verfügbare Methoden: actions | terraform | quick"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "Verify Cleanup"
echo "=================================================="
echo ""

# Check für übrige Ressourcen
echo "🔍 Prüfe auf übrige Ressourcen..."
REMAINING=$(aws resourcegroupstaggingapi get-resources \
  --tag-filters \
    Key=Project,Values=StackVertex \
    Key=Environment,Values=dev \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output text 2>/dev/null || echo "")

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✅ Keine tagged Ressourcen übrig${NC}"
else
    echo -e "${YELLOW}⚠️  Einige Ressourcen existieren noch:${NC}"
    echo "$REMAINING"
    echo ""
    echo "Manuelles Cleanup eventuell nötig (siehe DESTROY.md)"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ DESTROY COMPLETE!${NC}"
echo "=================================================="
echo ""
echo "Pluralsight Session kann beendet werden."
echo ""
