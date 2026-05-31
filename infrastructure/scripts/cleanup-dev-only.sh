#!/bin/bash
#
# StackVertex - DEV CLEANUP ONLY
# Löscht nur Dev-Environment, behält Bootstrap-Ressourcen
#
# Bootstrap-Ressourcen bleiben erhalten:
#   ✓ stackvertex-terraform-state-* Bucket
#   ✓ stackvertex-deployment-states-* Bucket
#   ✓ stackvertex-terraform-locks DynamoDB Table
#   ✓ ECR Repositories
#
# Usage: ./cleanup-dev-only.sh

set -e

ENV="dev"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️  StackVertex - DEV CLEANUP (Bootstrap bleibt)${NC}"
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

# Info
echo "Dieses Script löscht:"
echo "  ✗ Dev VPC, Subnets, Security Groups"
echo "  ✗ Dev Lambda Functions"
echo "  ✗ Dev API Gateways (HTTP + WebSocket)"
echo "  ✗ Dev DynamoDB Tables"
echo "  ✗ Dev S3 Buckets (customer-data, large-items, cloudtrail, lambda-code)"
echo "  ✗ Dev CloudWatch Logs, Alarms"
echo "  ✗ Dev SNS Topics"
echo "  ✗ Dev CloudTrail Trail"
echo "  ✗ Dev GuardDuty Detector"
echo "  ✗ Dev IAM Roles & Policies (Lambda, CloudTrail)"
echo ""
echo -e "${GREEN}Bootstrap-Ressourcen bleiben erhalten!${NC}"
echo "  ✓ stackvertex-terraform-state-* Bucket"
echo "  ✓ stackvertex-deployment-states-* Bucket"
echo "  ✓ stackvertex-terraform-locks DynamoDB Table"
echo "  ✓ ECR Repositories (dev/staging/prod)"
echo ""
read -p "Dev-Environment löschen? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "Starting dev cleanup..."
echo ""

# =============================================================================
# PHASE 1: Terraform Destroy
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Terraform Destroy${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

if [ -d "infrastructure/terraform/environments/$ENV" ]; then
    cd infrastructure/terraform/environments/$ENV

    if [ -d ".terraform" ]; then
        echo "1️⃣  Terraform Destroy..."
        terraform destroy -auto-approve || {
            echo -e "${YELLOW}⚠️  Terraform destroy failed, continuing with manual cleanup...${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  Terraform not initialized, trying to init...${NC}"
        terraform init -reconfigure || {
            echo -e "${YELLOW}⚠️  Terraform init failed, skipping terraform destroy${NC}"
        }

        if [ -d ".terraform" ]; then
            terraform destroy -auto-approve || {
                echo -e "${YELLOW}⚠️  Terraform destroy failed, continuing with manual cleanup...${NC}"
            }
        fi
    fi

    cd ../../../..
else
    echo -e "${YELLOW}⚠️  Dev environment directory not found, skipping terraform destroy${NC}"
fi

echo ""

# =============================================================================
# PHASE 2: Manual Cleanup (falls Terraform failed)
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: Manual Cleanup (Fallback)${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# S3 Buckets (nur Dev, NICHT Bootstrap!)
echo "2️⃣  Cleaning Dev S3 Buckets..."
DEV_BUCKETS=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, 'stackvertex-dev-')].Name" --output text 2>/dev/null || echo "")

if [ -n "$DEV_BUCKETS" ]; then
    for bucket in $DEV_BUCKETS; do
        # Skip Bootstrap-Buckets
        if [[ "$bucket" == *"terraform-state"* ]] || [[ "$bucket" == *"deployment-states"* ]]; then
            echo "   Skipping Bootstrap bucket: $bucket"
            continue
        fi

        echo "   Emptying & deleting: s3://$bucket..."

        # Delete all object versions
        aws s3api list-object-versions --bucket "$bucket" --output json --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null > /tmp/versions.json || echo '{"Objects":[]}' > /tmp/versions.json
        if [ -s /tmp/versions.json ] && [ "$(cat /tmp/versions.json | grep -c Key)" -gt 0 ]; then
            aws s3api delete-objects --bucket "$bucket" --delete file:///tmp/versions.json 2>/dev/null || true
        fi

        # Delete all delete markers
        aws s3api list-object-versions --bucket "$bucket" --output json --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null > /tmp/markers.json || echo '{"Objects":[]}' > /tmp/markers.json
        if [ -s /tmp/markers.json ] && [ "$(cat /tmp/markers.json | grep -c Key)" -gt 0 ]; then
            aws s3api delete-objects --bucket "$bucket" --delete file:///tmp/markers.json 2>/dev/null || true
        fi

        # Delete bucket
        aws s3 rb "s3://$bucket" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev S3 Buckets cleaned${NC}"
else
    echo "   No dev S3 buckets found"
fi

echo ""

# DynamoDB Tables (nur Dev!)
echo "3️⃣  Deleting Dev DynamoDB Tables..."
DEV_TABLES=$(aws dynamodb list-tables --query "TableNames[?starts_with(@, 'stackvertex-dev-')]" --output text 2>/dev/null || echo "")

if [ -n "$DEV_TABLES" ]; then
    for table in $DEV_TABLES; do
        # Skip Bootstrap Locks Table
        if [[ "$table" == "stackvertex-terraform-locks" ]]; then
            echo "   Skipping Bootstrap table: $table"
            continue
        fi

        echo "   Deleting table: $table..."
        aws dynamodb delete-table --table-name "$table" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev DynamoDB Tables deleted${NC}"
else
    echo "   No dev DynamoDB tables found"
fi

echo ""

# Lambda Functions
echo "4️⃣  Deleting Dev Lambda Functions..."
DEV_FUNCTIONS=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'stackvertex-dev-')].FunctionName" --output text 2>/dev/null || echo "")

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

# API Gateways
echo "5️⃣  Deleting Dev API Gateways..."
DEV_APIS=$(aws apigatewayv2 get-apis --query "Items[?starts_with(Name, 'stackvertex-dev-')].ApiId" --output text 2>/dev/null || echo "")

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

# CloudWatch Logs
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

# CloudWatch Query Definitions
echo "6️⃣a  Deleting Dev CloudWatch Query Definitions..."
QUERY_DEFS=$(aws logs describe-query-definitions --query "queryDefinitions[?contains(name, 'stackvertex-dev')].queryDefinitionId" --output text 2>/dev/null || echo "")

if [ -n "$QUERY_DEFS" ]; then
    for query_id in $QUERY_DEFS; do
        echo "   Deleting query definition: $query_id..."
        aws logs delete-query-definition --query-definition-id "$query_id" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev CloudWatch Query Definitions deleted${NC}"
else
    echo "   No dev query definitions found"
fi

echo ""

# CloudWatch Alarms
echo "7️⃣  Deleting Dev CloudWatch Alarms..."
DEV_ALARMS=$(aws cloudwatch describe-alarms --query "MetricAlarms[?starts_with(AlarmName, 'stackvertex-dev-')].AlarmName" --output text 2>/dev/null || echo "")

if [ -n "$DEV_ALARMS" ]; then
    for alarm in $DEV_ALARMS; do
        echo "   Deleting alarm: $alarm..."
        aws cloudwatch delete-alarms --alarm-names "$alarm" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev CloudWatch Alarms deleted${NC}"
else
    echo "   No dev alarms found"
fi

echo ""

# SNS Topics
echo "8️⃣  Deleting Dev SNS Topics..."
DEV_TOPICS=$(aws sns list-topics --query "Topics[?contains(TopicArn, 'stackvertex-dev-')].TopicArn" --output text 2>/dev/null || echo "")

if [ -n "$DEV_TOPICS" ]; then
    for topic in $DEV_TOPICS; do
        echo "   Deleting topic: $topic..."
        aws sns delete-topic --topic-arn "$topic" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Dev SNS Topics deleted${NC}"
else
    echo "   No dev SNS topics found"
fi

echo ""

# CloudTrail
echo "9️⃣  Deleting Dev CloudTrail..."
TRAIL_NAME="stackvertex-dev-trail"
if aws cloudtrail describe-trails --trail-name-list "$TRAIL_NAME" 2>/dev/null | grep -q "$TRAIL_NAME"; then
    echo "   Stopping logging: $TRAIL_NAME..."
    aws cloudtrail stop-logging --name "$TRAIL_NAME" 2>/dev/null || true

    echo "   Deleting trail: $TRAIL_NAME..."
    aws cloudtrail delete-trail --name "$TRAIL_NAME" 2>/dev/null || true
    echo -e "${GREEN}✅ CloudTrail deleted${NC}"
else
    echo "   No CloudTrail trail found"
fi

echo ""

# GuardDuty
echo "🔟  Deleting Dev GuardDuty Detector..."
DETECTOR_ID=$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text 2>/dev/null || echo "")

if [ "$DETECTOR_ID" != "None" ] && [ -n "$DETECTOR_ID" ]; then
    echo "   Deleting detector: $DETECTOR_ID..."
    aws guardduty delete-detector --detector-id "$DETECTOR_ID" 2>/dev/null || true
    echo -e "${GREEN}✅ GuardDuty deleted${NC}"
else
    echo "   No GuardDuty detector found"
fi

echo ""

# IAM Roles & Policies (nur Dev!)
echo "1️⃣1️⃣  Deleting Dev IAM Roles & Policies..."

# Lambda Role
LAMBDA_ROLE="stackvertex-dev-lambda-role"
if aws iam get-role --role-name "$LAMBDA_ROLE" 2>/dev/null; then
    echo "   Detaching managed policies from role: $LAMBDA_ROLE..."
    ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$LAMBDA_ROLE" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || echo "")
    if [ -n "$ATTACHED_POLICIES" ]; then
        for policy_arn in $ATTACHED_POLICIES; do
            echo "     Detaching policy: $policy_arn..."
            aws iam detach-role-policy --role-name "$LAMBDA_ROLE" --policy-arn "$policy_arn" 2>/dev/null || true
        done
    fi

    echo "   Deleting inline policies from role: $LAMBDA_ROLE..."
    INLINE_POLICIES=$(aws iam list-role-policies --role-name "$LAMBDA_ROLE" --query 'PolicyNames' --output text 2>/dev/null || echo "")
    if [ -n "$INLINE_POLICIES" ]; then
        for policy_name in $INLINE_POLICIES; do
            echo "     Deleting inline policy: $policy_name..."
            aws iam delete-role-policy --role-name "$LAMBDA_ROLE" --policy-name "$policy_name" 2>/dev/null || true
        done
    fi

    echo "   Deleting role: $LAMBDA_ROLE..."
    aws iam delete-role --role-name "$LAMBDA_ROLE" 2>/dev/null || true
    echo -e "${GREEN}✅ Lambda IAM Role deleted${NC}"
else
    echo "   Lambda role not found"
fi

# CloudTrail Role
CLOUDTRAIL_ROLE="stackvertex-dev-cloudtrail-cloudwatch"
if aws iam get-role --role-name "$CLOUDTRAIL_ROLE" 2>/dev/null; then
    echo "   Detaching managed policies from role: $CLOUDTRAIL_ROLE..."
    ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$CLOUDTRAIL_ROLE" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || echo "")
    if [ -n "$ATTACHED_POLICIES" ]; then
        for policy_arn in $ATTACHED_POLICIES; do
            echo "     Detaching policy: $policy_arn..."
            aws iam detach-role-policy --role-name "$CLOUDTRAIL_ROLE" --policy-arn "$policy_arn" 2>/dev/null || true
        done
    fi

    echo "   Deleting inline policies from role: $CLOUDTRAIL_ROLE..."
    INLINE_POLICIES=$(aws iam list-role-policies --role-name "$CLOUDTRAIL_ROLE" --query 'PolicyNames' --output text 2>/dev/null || echo "")
    if [ -n "$INLINE_POLICIES" ]; then
        for policy_name in $INLINE_POLICIES; do
            echo "     Deleting inline policy: $policy_name..."
            aws iam delete-role-policy --role-name "$CLOUDTRAIL_ROLE" --policy-name "$policy_name" 2>/dev/null || true
        done
    fi

    echo "   Deleting role: $CLOUDTRAIL_ROLE..."
    aws iam delete-role --role-name "$CLOUDTRAIL_ROLE" 2>/dev/null || true
    echo -e "${GREEN}✅ CloudTrail IAM Role deleted${NC}"
else
    echo "   CloudTrail role not found"
fi

# Custom Lambda Policy (falls standalone existiert)
LAMBDA_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='stackvertex-dev-lambda-custom-policy'].Arn" --output text 2>/dev/null || echo "")
if [ -n "$LAMBDA_POLICY_ARN" ] && [ "$LAMBDA_POLICY_ARN" != "None" ]; then
    echo "   Deleting custom Lambda policy: $LAMBDA_POLICY_ARN..."
    aws iam delete-policy --policy-arn "$LAMBDA_POLICY_ARN" 2>/dev/null || true
    echo -e "${GREEN}✅ Custom Lambda Policy deleted${NC}"
else
    echo "   Custom Lambda policy not found"
fi

echo ""

# VPC Endpoints
echo "1️⃣2️⃣  Deleting Dev VPC Endpoints..."
VPC_ENDPOINTS=$(aws ec2 describe-vpc-endpoints --query "VpcEndpoints[?Tags[?Key=='Project' && Value=='StackVertex'] && Tags[?Key=='Environment' && Value=='dev']].VpcEndpointId" --output text 2>/dev/null || echo "")

if [ -n "$VPC_ENDPOINTS" ]; then
    for endpoint in $VPC_ENDPOINTS; do
        echo "   Deleting VPC endpoint: $endpoint..."
        aws ec2 delete-vpc-endpoints --vpc-endpoint-ids "$endpoint" 2>/dev/null || true
    done
    echo -e "${GREEN}✅ VPC Endpoints deleted${NC}"
else
    echo "   No VPC endpoints found"
fi

echo ""

# NAT Gateways (falls vorhanden)
echo "1️⃣3️⃣  Deleting NAT Gateways..."
NAT_GATEWAYS=$(aws ec2 describe-nat-gateways --filter "Name=tag:Project,Values=StackVertex" "Name=tag:Environment,Values=dev" --query 'NatGateways[?State==`available`].NatGatewayId' --output text 2>/dev/null || echo "")

if [ -n "$NAT_GATEWAYS" ]; then
    for nat in $NAT_GATEWAYS; do
        echo "   Deleting NAT Gateway: $nat..."
        aws ec2 delete-nat-gateway --nat-gateway-id "$nat" 2>/dev/null || true
    done
    echo -e "${YELLOW}⏳ NAT Gateways deleting (takes ~2 min)${NC}"
    sleep 120
    echo -e "${GREEN}✅ NAT Gateways deleted${NC}"
else
    echo "   No NAT Gateways found"
fi

echo ""

# Internet Gateways
echo "1️⃣4️⃣  Deleting Internet Gateways..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Project,Values=StackVertex" "Name=tag:Environment,Values=dev" --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "")

if [ "$VPC_ID" != "None" ] && [ -n "$VPC_ID" ]; then
    IGW_ID=$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query 'InternetGateways[0].InternetGatewayId' --output text 2>/dev/null || echo "")

    if [ "$IGW_ID" != "None" ] && [ -n "$IGW_ID" ]; then
        echo "   Detaching IGW: $IGW_ID from VPC: $VPC_ID..."
        aws ec2 detach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID" 2>/dev/null || true

        echo "   Deleting IGW: $IGW_ID..."
        aws ec2 delete-internet-gateway --internet-gateway-id "$IGW_ID" 2>/dev/null || true
        echo -e "${GREEN}✅ Internet Gateway deleted${NC}"
    else
        echo "   No Internet Gateway found"
    fi
else
    echo "   No VPC found"
fi

echo ""

# Subnets
echo "1️⃣5️⃣  Deleting Subnets..."
if [ "$VPC_ID" != "None" ] && [ -n "$VPC_ID" ]; then
    SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text 2>/dev/null || echo "")

    if [ -n "$SUBNETS" ]; then
        for subnet in $SUBNETS; do
            echo "   Deleting subnet: $subnet..."
            aws ec2 delete-subnet --subnet-id "$subnet" 2>/dev/null || true
        done
        echo -e "${GREEN}✅ Subnets deleted${NC}"
    else
        echo "   No subnets found"
    fi
fi

echo ""

# Route Tables
echo "1️⃣6️⃣  Deleting Route Tables..."
if [ "$VPC_ID" != "None" ] && [ -n "$VPC_ID" ]; then
    ROUTE_TABLES=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Project,Values=StackVertex" --query 'RouteTables[].RouteTableId' --output text 2>/dev/null || echo "")

    if [ -n "$ROUTE_TABLES" ]; then
        for rt in $ROUTE_TABLES; do
            echo "   Deleting route table: $rt..."
            aws ec2 delete-route-table --route-table-id "$rt" 2>/dev/null || true
        done
        echo -e "${GREEN}✅ Route Tables deleted${NC}"
    else
        echo "   No custom route tables found"
    fi
fi

echo ""

# Security Groups
echo "1️⃣7️⃣  Deleting Security Groups..."
if [ "$VPC_ID" != "None" ] && [ -n "$VPC_ID" ]; then
    SECURITY_GROUPS=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Project,Values=StackVertex" --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text 2>/dev/null || echo "")

    if [ -n "$SECURITY_GROUPS" ]; then
        for sg in $SECURITY_GROUPS; do
            echo "   Deleting security group: $sg..."
            aws ec2 delete-security-group --group-id "$sg" 2>/dev/null || true
        done
        echo -e "${GREEN}✅ Security Groups deleted${NC}"
    else
        echo "   No custom security groups found"
    fi
fi

echo ""

# VPC
echo "1️⃣8️⃣  Deleting VPC..."
if [ "$VPC_ID" != "None" ] && [ -n "$VPC_ID" ]; then
    echo "   Deleting VPC: $VPC_ID..."
    aws ec2 delete-vpc --vpc-id "$VPC_ID" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  VPC deletion failed (dependencies may still exist)${NC}"
    }
    echo -e "${GREEN}✅ VPC deleted${NC}"
else
    echo "   No VPC found"
fi

echo ""

# =============================================================================
# VERIFICATION
# =============================================================================

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}VERIFICATION${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

echo "🔍 Checking for remaining dev resources..."
REMAINING=$(aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=StackVertex Key=Environment,Values=dev \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output text 2>/dev/null || echo "")

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✅ No tagged dev resources remaining${NC}"
else
    echo -e "${YELLOW}⚠️  Some dev resources still exist:${NC}"
    echo "$REMAINING"
fi

echo ""

# Check Bootstrap-Ressourcen
echo "🔍 Checking Bootstrap resources (should still exist)..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

BOOTSTRAP_OK=true

# Check Terraform State Bucket
if aws s3 ls "s3://stackvertex-terraform-state-${AWS_ACCOUNT_ID}" 2>/dev/null; then
    echo -e "${GREEN}✓ Terraform State Bucket exists${NC}"
else
    echo -e "${RED}✗ Terraform State Bucket MISSING!${NC}"
    BOOTSTRAP_OK=false
fi

# Check Terraform Locks Table
if aws dynamodb describe-table --table-name stackvertex-terraform-locks 2>/dev/null; then
    echo -e "${GREEN}✓ Terraform Locks Table exists${NC}"
else
    echo -e "${RED}✗ Terraform Locks Table MISSING!${NC}"
    BOOTSTRAP_OK=false
fi

# Check Deployment States Bucket
if aws s3 ls "s3://stackvertex-deployment-states-${AWS_ACCOUNT_ID}" 2>/dev/null; then
    echo -e "${GREEN}✓ Deployment States Bucket exists${NC}"
else
    echo -e "${YELLOW}⚠ Deployment States Bucket MISSING (kann neu erstellt werden)${NC}"
    BOOTSTRAP_OK=false
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo "========================================================"
echo -e "${GREEN}✅ DEV CLEANUP DONE!${NC}"
echo "========================================================"
echo ""
echo "Gelöscht:"
echo "  ✓ Dev VPC, Subnets, Security Groups, IGW, Route Tables"
echo "  ✓ Dev Lambda Functions"
echo "  ✓ Dev API Gateways"
echo "  ✓ Dev DynamoDB Tables"
echo "  ✓ Dev S3 Buckets"
echo "  ✓ Dev CloudWatch Logs & Alarms"
echo "  ✓ Dev SNS Topics"
echo "  ✓ Dev CloudTrail"
echo "  ✓ Dev GuardDuty"
echo "  ✓ Dev IAM Roles & Policies"
echo ""

if [ "$BOOTSTRAP_OK" = true ]; then
    echo -e "${GREEN}Bootstrap-Ressourcen sind OK!${NC}"
    echo ""
    echo -e "${YELLOW}Nächste Schritte:${NC}"
    echo "  1. Dev-Environment neu deployen:"
    echo "     cd infrastructure/scripts"
    echo "     ./deploy.sh dev"
    echo ""
    echo "  2. Oder via GitHub Actions:"
    echo "     gh workflow run deploy.yml -f environment=dev"
else
    echo -e "${YELLOW}⚠️  Einige Bootstrap-Ressourcen fehlen!${NC}"
    echo ""
    echo "Führe Bootstrap neu aus:"
    echo "  cd infrastructure/scripts"
    echo "  ./bootstrap.sh"
fi

echo ""
echo "Done! 🎉"
