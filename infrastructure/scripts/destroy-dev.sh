#!/bin/bash
#
# StackVertex - Dev Environment Destroy
#
# Komplett-Löschung der Dev-Umgebung
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🗑️  StackVertex - Dev Environment Destroy"
echo "=========================================="
echo ""

# Methode auswählen
echo "❓ Destroy-Methode auswählen:"
echo "   1) GitHub Actions (empfohlen, sauber)"
echo "   2) Cleanup Script (schnell, AWS CLI direkt)"
echo "   3) Terraform Destroy (manuell)"
echo ""
read -p "Auswahl (1/2/3): " method

case $method in
    1) METHOD="actions" ;;
    2) METHOD="cleanup" ;;
    3) METHOD="terraform" ;;
    *)
        echo -e "${RED}❌ Ungültige Auswahl${NC}"
        exit 1
        ;;
esac

# ========================================
# Confirmation
# ========================================
echo ""
echo -e "${YELLOW}⚠️  WARNUNG: Löscht ALLE StackVertex-Dev Ressourcen!${NC}"
echo ""
echo "Betroffen:"
echo "  - VPC, Subnets, Security Groups"
echo "  - Lambda Functions"
echo "  - API Gateway"
echo "  - DynamoDB Tables"
echo "  - S3 Buckets (inkl. Frontend)"
echo "  - CloudWatch Logs"
echo "  - IAM Roles"
echo ""
read -p "Wirklich löschen? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "=================================================="
echo "Destroy Methode: $METHOD"
echo "=================================================="
echo ""

START_TIME=$(date +%s)

# ========================================
# Method 1: GitHub Actions
# ========================================
if [ "$METHOD" = "actions" ]; then
    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}❌ GitHub CLI nicht installiert${NC}"
        echo "Fallback: Nutze 'cleanup' Methode"
        METHOD="cleanup"
    else
        # Trigger Destroy Workflow
        echo "🚀 Triggere Destroy Workflow..."

        # Check if destroy workflow exists
        if ! gh workflow list | grep -q "destroy.yml"; then
            echo -e "${YELLOW}⚠️  Destroy Workflow existiert nicht${NC}"
            echo "Fallback: Nutze 'cleanup' Methode"
            METHOD="cleanup"
        else
            gh workflow run destroy.yml \
              -f environment=dev \
              -f confirm_destroy=DESTROY \
              -f skip_approval=true

            sleep 5

            RUN_ID=$(gh run list --workflow=destroy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
            echo -e "${BLUE}Destroy Run ID: $RUN_ID${NC}"

            echo "👀 Watching Destroy..."
            gh run watch $RUN_ID || {
                echo -e "${YELLOW}⚠️  Workflow fehlgeschlagen${NC}"
                echo "Fallback: Nutze 'cleanup' Methode"
                METHOD="cleanup"
            }

            if [ "$METHOD" = "actions" ]; then
                STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
                if [ "$STATUS" != "success" ]; then
                    echo -e "${RED}❌ Destroy failed!${NC}"
                    gh run view $RUN_ID --log-failed
                    echo ""
                    echo "Versuche Cleanup Script..."
                    METHOD="cleanup"
                else
                    echo -e "${GREEN}✅ Destroy via Actions erfolgreich!${NC}"
                fi
            fi
        fi
    fi
fi

# ========================================
# Method 2: Cleanup Script
# ========================================
if [ "$METHOD" = "cleanup" ]; then
    echo "🧹 Nutze Cleanup Script..."
    echo ""

    # Use cleanup-dev-only.sh
    if [ -f "./cleanup-dev-only.sh" ]; then
        ./cleanup-dev-only.sh
    else
        echo -e "${RED}❌ cleanup-dev-only.sh nicht gefunden${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Cleanup Script erfolgreich!${NC}"
fi

# ========================================
# Method 3: Terraform Destroy
# ========================================
if [ "$METHOD" = "terraform" ]; then
    echo "🔨 Terraform Destroy..."
    echo ""

    cd ../terraform/environments/dev

    # Check if initialized
    if [ ! -d ".terraform" ]; then
        echo "Terraform initialisieren..."
        terraform init
    fi

    # Destroy
    echo "🗑️  Terraform Destroy..."
    terraform destroy -auto-approve || {
        echo -e "${YELLOW}⚠️  Terraform destroy fehlgeschlagen${NC}"
        echo "Manuelles Cleanup nötig oder cleanup-dev-only.sh nutzen"
        exit 1
    }

    echo -e "${GREEN}✅ Terraform Destroy erfolgreich!${NC}"
fi

# ========================================
# Verify Cleanup
# ========================================
echo ""
echo "=================================================="
echo "Verify Cleanup"
echo "=================================================="
echo ""

echo "🔍 Prüfe übrige Ressourcen..."

# Check S3 Buckets
BUCKETS=$(aws s3 ls | grep stackvertex-dev || echo "")
if [ -n "$BUCKETS" ]; then
    echo -e "${YELLOW}⚠️  Übrige S3 Buckets:${NC}"
    echo "$BUCKETS"
else
    echo -e "${GREEN}✅ Keine S3 Buckets übrig${NC}"
fi

# Check Lambda Functions
LAMBDAS=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'stackvertex-dev')].FunctionName" --output text || echo "")
if [ -n "$LAMBDAS" ]; then
    echo -e "${YELLOW}⚠️  Übrige Lambda Functions:${NC}"
    echo "$LAMBDAS"
else
    echo -e "${GREEN}✅ Keine Lambda Functions übrig${NC}"
fi

# Check DynamoDB Tables
TABLES=$(aws dynamodb list-tables --query "TableNames[?starts_with(@, 'stackvertex-dev')]" --output text || echo "")
if [ -n "$TABLES" ]; then
    echo -e "${YELLOW}⚠️  Übrige DynamoDB Tables:${NC}"
    echo "$TABLES"
else
    echo -e "${GREEN}✅ Keine DynamoDB Tables übrig${NC}"
fi

# Check API Gateways
APIS=$(aws apigatewayv2 get-apis --query "Items[?starts_with(Name, 'stackvertex-dev')].Name" --output text || echo "")
if [ -n "$APIS" ]; then
    echo -e "${YELLOW}⚠️  Übrige API Gateways:${NC}"
    echo "$APIS"
else
    echo -e "${GREEN}✅ Keine API Gateways übrig${NC}"
fi

# Zeit-Info
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
ELAPSED_MIN=$((ELAPSED / 60))

echo ""
echo "⏱️  Destroy-Dauer: ${ELAPSED_MIN} Minuten"
echo ""
echo "=================================================="
echo -e "${GREEN}✅ DESTROY COMPLETE!${NC}"
echo "=================================================="
echo ""
