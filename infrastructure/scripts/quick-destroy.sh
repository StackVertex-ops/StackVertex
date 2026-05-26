#!/bin/bash
#
# StackVertex - Quick Destroy Script
# Für Pluralsight Sandbox (4h Zeit-Limit)
#
# Usage: ./quick-destroy.sh [environment]
# Example: ./quick-destroy.sh dev

set -e

ENV=${1:-dev}
REGION=${AWS_REGION:-us-east-1}

echo "🗑️  StackVertex Quick Destroy - Environment: $ENV"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Confirm
echo -e "${YELLOW}⚠️  WARNUNG: Löscht ALLE StackVertex-$ENV Ressourcen!${NC}"
read -p "Fortfahren? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "Starting destroy..."
echo ""

# 1. Terraform Destroy
echo "1️⃣  Terraform Destroy..."
if [ -d "infrastructure/terraform/environments/$ENV" ]; then
    cd "infrastructure/terraform/environments/$ENV"

    # Try normal destroy
    terraform destroy -auto-approve || {
        echo -e "${YELLOW}⚠️  Terraform destroy failed, trying force-unlock...${NC}"

        # Get lock ID if exists
        LOCK_ID=$(terraform state list 2>&1 | grep -oP 'ID: \K[^"]+' | head -1 || echo "")

        if [ -n "$LOCK_ID" ]; then
            terraform force-unlock -force "$LOCK_ID"
        fi

        # Retry
        terraform destroy -auto-approve || echo -e "${RED}❌ Terraform destroy failed${NC}"
    }

    cd ../../../..
    echo -e "${GREEN}✅ Terraform destroy complete${NC}"
else
    echo -e "${YELLOW}⚠️  Terraform directory not found, skipping${NC}"
fi

echo ""

# 2. Empty & Delete S3 Buckets
echo "2️⃣  Cleaning S3 Buckets..."

BUCKETS=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'stackvertex-$ENV')].Name" --output text 2>/dev/null || echo "")

if [ -n "$BUCKETS" ]; then
    for bucket in $BUCKETS; do
        echo "   Emptying s3://$bucket..."
        aws s3 rm "s3://$bucket" --recursive 2>/dev/null || true

        echo "   Deleting s3://$bucket..."
        aws s3 rb "s3://$bucket" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ S3 Buckets cleaned${NC}"
else
    echo "   No S3 buckets found"
fi

echo ""

# 3. Delete DynamoDB Tables
echo "3️⃣  Deleting DynamoDB Tables..."

TABLES=$(aws dynamodb list-tables --query "TableNames[?contains(@, 'stackvertex-$ENV')]" --output text 2>/dev/null || echo "")

if [ -n "$TABLES" ]; then
    for table in $TABLES; do
        echo "   Deleting table: $table..."
        aws dynamodb delete-table --table-name "$table" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ DynamoDB Tables deleted${NC}"
else
    echo "   No DynamoDB tables found"
fi

echo ""

# 4. Delete Lambda Functions
echo "4️⃣  Deleting Lambda Functions..."

FUNCTIONS=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'stackvertex-$ENV')].FunctionName" --output text 2>/dev/null || echo "")

if [ -n "$FUNCTIONS" ]; then
    for func in $FUNCTIONS; do
        echo "   Deleting function: $func..."
        aws lambda delete-function --function-name "$func" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Lambda Functions deleted${NC}"
else
    echo "   No Lambda functions found"
fi

echo ""

# 5. Delete API Gateways
echo "5️⃣  Deleting API Gateways..."

# HTTP APIs
HTTP_APIS=$(aws apigatewayv2 get-apis --query "Items[?contains(Name, 'stackvertex-$ENV')].ApiId" --output text 2>/dev/null || echo "")

if [ -n "$HTTP_APIS" ]; then
    for api_id in $HTTP_APIS; do
        echo "   Deleting HTTP API: $api_id..."
        aws apigatewayv2 delete-api --api-id "$api_id" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ API Gateways deleted${NC}"
else
    echo "   No API Gateways found"
fi

echo ""

# 6. Stop & Delete ECS Tasks/Cluster
echo "6️⃣  Cleaning ECS..."

CLUSTER="stackvertex-$ENV"
if aws ecs describe-clusters --clusters "$CLUSTER" &>/dev/null; then
    # Stop all tasks
    TASKS=$(aws ecs list-tasks --cluster "$CLUSTER" --query 'taskArns' --output text 2>/dev/null || echo "")
    if [ -n "$TASKS" ]; then
        for task in $TASKS; do
            echo "   Stopping task: $task..."
            aws ecs stop-task --cluster "$CLUSTER" --task "$task" 2>/dev/null || true
        done
    fi

    # Delete cluster
    echo "   Deleting cluster: $CLUSTER..."
    aws ecs delete-cluster --cluster "$CLUSTER" 2>/dev/null || true
    echo -e "${GREEN}✅ ECS cleaned${NC}"
else
    echo "   No ECS cluster found"
fi

echo ""

# 7. Delete CloudWatch Log Groups
echo "7️⃣  Deleting CloudWatch Logs..."

LOG_GROUPS=$(aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'stackvertex-$ENV')].logGroupName" --output text 2>/dev/null || echo "")

if [ -n "$LOG_GROUPS" ]; then
    for log_group in $LOG_GROUPS; do
        echo "   Deleting log group: $log_group..."
        aws logs delete-log-group --log-group-name "$log_group" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ CloudWatch Logs deleted${NC}"
else
    echo "   No log groups found"
fi

echo ""

# 8. Summary
echo "=================================================="
echo -e "${GREEN}✅ Quick Destroy Complete!${NC}"
echo ""
echo "Remaining resources (manual cleanup if needed):"
echo "  - CloudFront Distributions (takes 15-20 min to disable)"
echo "  - Route53 Hosted Zones (\$0.50/month)"
echo "  - IAM Roles (check manually)"
echo ""

# Verify
echo "Verifying remaining resources..."
REMAINING=$(aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=stackvertex Key=Environment,Values=$ENV \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output text 2>/dev/null || echo "")

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✅ No tagged resources remaining${NC}"
else
    echo -e "${YELLOW}⚠️  Some resources still exist:${NC}"
    echo "$REMAINING"
fi

echo ""
echo "Done! 🎉"
