#!/bin/bash
#
# StackVertex - COMPLETE CLEANUP (inkl. Bootstrap!)
# Löscht ALLES: Dev-Environment + Bootstrap-Ressourcen
#
# WARNUNG: Danach musst du Bootstrap komplett neu ausführen!
#
# Usage: ./cleanup-all.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}🗑️  StackVertex - COMPLETE CLEANUP (ALL + Bootstrap)${NC}"
echo "========================================================"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI nicht installiert${NC}"
    exit 1
fi

# Check AWS Credentials
aws sts get-caller-identity &> /dev/null || {
    echo -e "${RED}❌ AWS Credentials nicht konfiguriert${NC}"
    exit 1
}

echo -e "${GREEN}✅ AWS CLI & Credentials OK${NC}"
echo ""

# WARNUNG
echo -e "${RED}⚠️⚠️⚠️  WARNUNG  ⚠️⚠️⚠️${NC}"
echo ""
echo "Dieses Script löscht:"
echo "  ✗ Dev-Environment (VPC, Lambda, API Gateway, DynamoDB, S3, etc.)"
echo "  ✗ Bootstrap-Ressourcen:"
echo "    - stackvertex-terraform-state-* Bucket"
echo "    - stackvertex-deployment-states-* Bucket"
echo "    - stackvertex-terraform-locks DynamoDB Table"
echo "    - ECR Repositories (dev/staging/prod)"
echo ""
echo -e "${YELLOW}Danach musst du Bootstrap komplett neu ausführen!${NC}"
echo ""
read -p "Wirklich ALLES löschen? Tippe 'DELETE-ALL': " confirm

if [ "$confirm" != "DELETE-ALL" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "Starting complete cleanup..."
echo ""

# =============================================================================
# PHASE 1: Dev-Environment (via Terraform Destroy)
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Dev-Environment${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

if [ -d "infrastructure/terraform/environments/dev" ]; then
    cd infrastructure/terraform/environments/dev

    if [ -d ".terraform" ]; then
        echo "1️⃣  Terraform Destroy (Dev)..."
        terraform destroy -auto-approve || {
            echo -e "${YELLOW}⚠️  Terraform destroy failed, continuing with manual cleanup...${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  Terraform not initialized, skipping terraform destroy${NC}"
    fi

    cd ../../../..
else
    echo -e "${YELLOW}⚠️  Dev environment not found, skipping${NC}"
fi

echo ""

# =============================================================================
# PHASE 2: Manual Cleanup (Dev-Ressourcen)
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: Manual Cleanup (Dev)${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# S3 Buckets (Dev)
echo "2️⃣  Cleaning Dev S3 Buckets..."
DEV_BUCKETS=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'stackvertex-dev')].Name" --output text 2>/dev/null || echo "")

if [ -n "$DEV_BUCKETS" ]; then
    for bucket in $DEV_BUCKETS; do
        echo "   Emptying & deleting: s3://$bucket..."

        # Delete all object versions
        aws s3api list-object-versions --bucket "$bucket" --output json --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
          aws s3api delete-objects --bucket "$bucket" --delete file:///dev/stdin 2>/dev/null || true

        # Delete all delete markers
        aws s3api list-object-versions --bucket "$bucket" --output json --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
          aws s3api delete-objects --bucket "$bucket" --delete file:///dev/stdin 2>/dev/null || true

        # Delete bucket
        aws s3 rb "s3://$bucket" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev S3 Buckets cleaned${NC}"
else
    echo "   No dev S3 buckets found"
fi

echo ""

# DynamoDB Tables (Dev)
echo "3️⃣  Deleting Dev DynamoDB Tables..."
DEV_TABLES=$(aws dynamodb list-tables --query "TableNames[?contains(@, 'stackvertex-dev')]" --output text 2>/dev/null || echo "")

if [ -n "$DEV_TABLES" ]; then
    for table in $DEV_TABLES; do
        echo "   Deleting table: $table..."
        aws dynamodb delete-table --table-name "$table" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev DynamoDB Tables deleted${NC}"
else
    echo "   No dev DynamoDB tables found"
fi

echo ""

# Lambda Functions (Dev)
echo "4️⃣  Deleting Dev Lambda Functions..."
DEV_FUNCTIONS=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'stackvertex-dev')].FunctionName" --output text 2>/dev/null || echo "")

if [ -n "$DEV_FUNCTIONS" ]; then
    for func in $DEV_FUNCTIONS; do
        echo "   Deleting function: $func..."
        aws lambda delete-function --function-name "$func" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev Lambda Functions deleted${NC}"
else
    echo "   No dev Lambda functions found"
fi

echo ""

# API Gateways (Dev)
echo "5️⃣  Deleting Dev API Gateways..."
DEV_APIS=$(aws apigatewayv2 get-apis --query "Items[?contains(Name, 'stackvertex-dev')].ApiId" --output text 2>/dev/null || echo "")

if [ -n "$DEV_APIS" ]; then
    for api_id in $DEV_APIS; do
        echo "   Deleting API: $api_id..."
        aws apigatewayv2 delete-api --api-id "$api_id" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev API Gateways deleted${NC}"
else
    echo "   No dev API Gateways found"
fi

echo ""

# CloudWatch Log Groups (Dev)
echo "6️⃣  Deleting Dev CloudWatch Logs..."
DEV_LOGS=$(aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'stackvertex-dev')].logGroupName" --output text 2>/dev/null || echo "")

if [ -n "$DEV_LOGS" ]; then
    for log_group in $DEV_LOGS; do
        echo "   Deleting log group: $log_group..."
        aws logs delete-log-group --log-group-name "$log_group" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev CloudWatch Logs deleted${NC}"
else
    echo "   No dev log groups found"
fi

echo ""

# =============================================================================
# PHASE 3: Bootstrap-Ressourcen
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 3: Bootstrap-Ressourcen${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# Get Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Terraform State Bucket
echo "7️⃣  Deleting Terraform State Bucket..."
STATE_BUCKET="stackvertex-terraform-state-${AWS_ACCOUNT_ID}"
if aws s3 ls "s3://$STATE_BUCKET" 2>/dev/null; then
    echo "   Emptying: s3://$STATE_BUCKET..."

    # Delete all versions
    aws s3api list-object-versions --bucket "$STATE_BUCKET" --output json --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
      aws s3api delete-objects --bucket "$STATE_BUCKET" --delete file:///dev/stdin 2>/dev/null || true

    # Delete all delete markers
    aws s3api list-object-versions --bucket "$STATE_BUCKET" --output json --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
      aws s3api delete-objects --bucket "$STATE_BUCKET" --delete file:///dev/stdin 2>/dev/null || true

    echo "   Deleting: s3://$STATE_BUCKET..."
    aws s3 rb "s3://$STATE_BUCKET" 2>/dev/null || true
    echo -e "${GREEN}✅ Terraform State Bucket deleted${NC}"
else
    echo "   Bucket not found: $STATE_BUCKET"
fi

echo ""

# Deployment States Bucket
echo "8️⃣  Deleting Deployment States Bucket..."
DEPLOY_BUCKET="stackvertex-deployment-states-${AWS_ACCOUNT_ID}"
if aws s3 ls "s3://$DEPLOY_BUCKET" 2>/dev/null; then
    echo "   Emptying: s3://$DEPLOY_BUCKET..."
    aws s3 rm "s3://$DEPLOY_BUCKET" --recursive 2>/dev/null || true

    echo "   Deleting: s3://$DEPLOY_BUCKET..."
    aws s3 rb "s3://$DEPLOY_BUCKET" 2>/dev/null || true
    echo -e "${GREEN}✅ Deployment States Bucket deleted${NC}"
else
    echo "   Bucket not found: $DEPLOY_BUCKET"
fi

echo ""

# Terraform Locks Table
echo "9️⃣  Deleting Terraform Locks Table..."
LOCKS_TABLE="stackvertex-terraform-locks"
if aws dynamodb describe-table --table-name "$LOCKS_TABLE" 2>/dev/null; then
    aws dynamodb delete-table --table-name "$LOCKS_TABLE" 2>/dev/null || true
    echo -e "${GREEN}✅ Terraform Locks Table deleted${NC}"
else
    echo "   Table not found: $LOCKS_TABLE"
fi

echo ""

# ECR Repositories
echo "🔟  Deleting ECR Repositories..."
for env in dev staging prod; do
    REPO_NAME="stackvertex-${env}-lambda"
    if aws ecr describe-repositories --repository-names "$REPO_NAME" 2>/dev/null; then
        echo "   Deleting ECR: $REPO_NAME..."
        aws ecr delete-repository --repository-name "$REPO_NAME" --force 2>/dev/null || true
    fi
done
echo -e "${GREEN}✅ ECR Repositories deleted${NC}"

echo ""

# =============================================================================
# VERIFICATION
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}VERIFICATION${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

echo "🔍 Checking for remaining resources..."
REMAINING=$(aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=StackVertex \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output text 2>/dev/null || echo "")

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✅ No tagged resources remaining${NC}"
else
    echo -e "${YELLOW}⚠️  Some resources still exist:${NC}"
    echo "$REMAINING"
    echo ""
    echo "Manual cleanup eventuell nötig (VPC, Security Groups, etc.)"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo "========================================================"
echo -e "${GREEN}✅ COMPLETE CLEANUP DONE!${NC}"
echo "========================================================"
echo ""
echo "Gelöscht:"
echo "  ✓ Dev-Environment (VPC, Lambda, API Gateway, DynamoDB, etc.)"
echo "  ✓ Terraform State Bucket"
echo "  ✓ Deployment States Bucket"
echo "  ✓ Terraform Locks Table"
echo "  ✓ ECR Repositories"
echo ""
echo -e "${YELLOW}Nächste Schritte:${NC}"
echo "  1. Bootstrap neu ausführen:"
echo "     cd infrastructure/scripts"
echo "     ./bootstrap.sh"
echo ""
echo "  2. Dann Dev-Environment deployen:"
echo "     ./deploy.sh dev"
echo ""
echo "Done! 🎉"
