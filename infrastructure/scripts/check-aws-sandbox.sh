#!/bin/bash
#
# AWS Sandbox Capability Check
# Prüft welche AWS Services in deinem Pluralsight Sandbox verfügbar sind
#

set -e

echo "🔍 AWS Sandbox Capability Check"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI nicht installiert${NC}"
    exit 1
fi

echo "✅ AWS CLI installiert"
echo ""

# Check AWS Credentials
echo "1. AWS Account Info:"
echo "   -------------------"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "ERROR")
AWS_USER_ARN=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null || echo "ERROR")

if [ "$AWS_ACCOUNT_ID" = "ERROR" ]; then
    echo -e "   ${RED}❌ AWS Credentials nicht konfiguriert${NC}"
    echo ""
    echo "   Bitte zuerst AWS credentials aus Pluralsight Sandbox kopieren:"
    echo "   export AWS_ACCESS_KEY_ID=..."
    echo "   export AWS_SECRET_ACCESS_KEY=..."
    echo "   export AWS_SESSION_TOKEN=..."
    exit 1
fi

echo -e "   ${GREEN}✅ Account ID: $AWS_ACCOUNT_ID${NC}"
echo "   User/Role: $AWS_USER_ARN"
echo ""

# Check Region
AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}
echo "2. Region: $AWS_REGION"
echo ""

# Function to test service access
test_service() {
    local service_name=$1
    local test_command=$2

    echo -n "   Testing $service_name... "

    if eval "$test_command" &>/dev/null; then
        echo -e "${GREEN}✅ Available${NC}"
        return 0
    else
        echo -e "${RED}❌ Not available / No permission${NC}"
        return 1
    fi
}

echo "3. Service Availability:"
echo "   ---------------------"

# S3
test_service "S3              " "aws s3 ls"
S3_OK=$?

# DynamoDB
test_service "DynamoDB        " "aws dynamodb list-tables"
DYNAMODB_OK=$?

# ECR
test_service "ECR             " "aws ecr describe-repositories"
ECR_OK=$?

# Lambda
test_service "Lambda          " "aws lambda list-functions"
LAMBDA_OK=$?

# ECS
test_service "ECS             " "aws ecs list-clusters"
ECS_OK=$?

# CloudFront
test_service "CloudFront      " "aws cloudfront list-distributions"
CLOUDFRONT_OK=$?

# Secrets Manager
test_service "Secrets Manager " "aws secretsmanager list-secrets"
SECRETS_OK=$?

# IAM
test_service "IAM             " "aws iam list-roles --max-items 1"
IAM_OK=$?

# VPC
test_service "VPC             " "aws ec2 describe-vpcs"
VPC_OK=$?

# CloudWatch
test_service "CloudWatch      " "aws logs describe-log-groups --max-items 1"
CLOUDWATCH_OK=$?

echo ""
echo "4. Recommended Deployment Strategy:"
echo "   ---------------------------------"

if [ $S3_OK -eq 0 ] && [ $DYNAMODB_OK -eq 0 ] && [ $LAMBDA_OK -eq 0 ]; then
    echo -e "   ${GREEN}✅ MINIMAL DEPLOYMENT möglich:${NC}"
    echo "      - S3 für Terraform State ✅"
    echo "      - DynamoDB für State Locking ✅"
    echo "      - Lambda für Backend ✅"
    echo ""

    if [ $ECR_OK -ne 0 ]; then
        echo -e "   ${YELLOW}⚠️  ECR nicht verfügbar → Verwende Lambda ZIP Deployment${NC}"
    fi

    if [ $CLOUDFRONT_OK -ne 0 ]; then
        echo -e "   ${YELLOW}⚠️  CloudFront nicht verfügbar → Frontend nur via S3${NC}"
    fi

    if [ $SECRETS_OK -ne 0 ]; then
        echo -e "   ${YELLOW}⚠️  Secrets Manager nicht verfügbar → Secrets via Environment Variables${NC}"
    fi

    echo ""
    echo -e "   ${GREEN}👉 Du kannst den Deployment-Flow TESTEN!${NC}"
    echo ""
    echo "   Empfohlene Schritte:"
    echo "   1. ./bootstrap-backend.sh (S3 + DynamoDB Setup)"
    echo "   2. cd ../terraform/environments/dev-lean"
    echo "   3. terraform init"
    echo "   4. terraform plan"
    echo "   5. terraform apply (nur wenn du bereit bist)"
    echo ""
    echo "   ⏰ Zeit-Budget: 4 Stunden → Plane 3h für Tests, 1h Buffer"

else
    echo -e "   ${RED}❌ DEPLOYMENT NICHT EMPFOHLEN${NC}"
    echo "      Benötigte Services fehlen:"
    [ $S3_OK -ne 0 ] && echo "      - S3 ❌"
    [ $DYNAMODB_OK -ne 0 ] && echo "      - DynamoDB ❌"
    [ $LAMBDA_OK -ne 0 ] && echo "      - Lambda ❌"
fi

echo ""
echo "5. Nächste Schritte:"
echo "   -----------------"
echo "   - Falls Services fehlen: Prüfe Pluralsight Sandbox Permissions"
echo "   - Falls alles ✅: Starte mit ./bootstrap-backend.sh"
echo "   - Falls ECR fehlt: Verwende Lambda ZIP statt Docker"
echo ""
echo "================================"
echo "Check abgeschlossen!"
