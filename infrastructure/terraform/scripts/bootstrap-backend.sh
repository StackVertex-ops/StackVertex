#!/bin/bash
# Terraform Backend Bootstrap Script
# Erstellt S3 Bucket für Terraform State und generiert backend.tf

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script usage
usage() {
    echo "Usage: $0 <environment> [region]"
    echo ""
    echo "Arguments:"
    echo "  environment  Environment name (dev, staging, prod)"
    echo "  region       AWS region (default: eu-central-1)"
    echo ""
    echo "Examples:"
    echo "  $0 dev"
    echo "  $0 staging eu-central-1"
    echo "  $0 prod"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

ENVIRONMENT=$1
REGION=${2:-eu-central-1}
PROJECT_NAME="overcloud"
BUCKET_NAME="${PROJECT_NAME}-${ENVIRONMENT}-terraform-state"
DYNAMODB_TABLE="${PROJECT_NAME}-${ENVIRONMENT}-terraform-lock"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Environment must be dev, staging, or prod${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Terraform Backend Bootstrap${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment:      $ENVIRONMENT"
echo "Region:           $REGION"
echo "Bucket:           $BUCKET_NAME"
echo "DynamoDB Table:   $DYNAMODB_TABLE"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: $AWS_ACCOUNT_ID${NC}"
echo ""

# Create S3 Bucket
echo -e "${YELLOW}Creating S3 bucket for Terraform state...${NC}"
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Bucket already exists: $BUCKET_NAME${NC}"
else
    # Create bucket (region-specific)
    if [ "$REGION" == "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    echo -e "${GREEN}✓ Bucket created: $BUCKET_NAME${NC}"
fi

# Enable versioning
echo -e "${YELLOW}Enabling versioning...${NC}"
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled
echo -e "${GREEN}✓ Versioning enabled${NC}"

# Enable encryption
echo -e "${YELLOW}Enabling encryption...${NC}"
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'
echo -e "${GREEN}✓ Encryption enabled (AES256)${NC}"

# Block public access
echo -e "${YELLOW}Blocking public access...${NC}"
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        BlockPublicAcls=true,\
IgnorePublicAcls=true,\
BlockPublicPolicy=true,\
RestrictPublicBuckets=true
echo -e "${GREEN}✓ Public access blocked${NC}"

# Enable logging (optional, to separate logging bucket)
# echo -e "${YELLOW}Configuring access logging...${NC}"
# aws s3api put-bucket-logging \
#     --bucket "$BUCKET_NAME" \
#     --bucket-logging-status '{
#         "LoggingEnabled": {
#             "TargetBucket": "'${PROJECT_NAME}'-logs",
#             "TargetPrefix": "s3-access-logs/'$BUCKET_NAME'/"
#         }
#     }'
# echo -e "${GREEN}✓ Logging configured${NC}"

# Create DynamoDB table for state locking
echo -e "${YELLOW}Creating DynamoDB table for state locking...${NC}"
if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$REGION" &>/dev/null; then
    echo -e "${YELLOW}⚠ DynamoDB table already exists: $DYNAMODB_TABLE${NC}"
else
    aws dynamodb create-table \
        --table-name "$DYNAMODB_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT" \
        > /dev/null

    echo -e "${YELLOW}Waiting for table to be active...${NC}"
    aws dynamodb wait table-exists --table-name "$DYNAMODB_TABLE" --region "$REGION"
    echo -e "${GREEN}✓ DynamoDB table created: $DYNAMODB_TABLE${NC}"
fi

# Generate backend.tf
BACKEND_FILE="../environments/${ENVIRONMENT}/backend.tf"
echo -e "${YELLOW}Generating backend.tf...${NC}"

cat > "$BACKEND_FILE" <<EOF
# Auto-generated by bootstrap-backend.sh
# DO NOT EDIT - Regenerate with: ./scripts/bootstrap-backend.sh $ENVIRONMENT

terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "terraform.tfstate"
    region         = "$REGION"
    encrypt        = true
    dynamodb_table = "$DYNAMODB_TABLE"

    # Additional security
    skip_credentials_validation = false
    skip_metadata_api_check     = false
    force_path_style            = false
  }
}
EOF

echo -e "${GREEN}✓ backend.tf created: $BACKEND_FILE${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Bootstrap Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Initialize Terraform backend:"
echo -e "   ${YELLOW}cd ../environments/$ENVIRONMENT${NC}"
echo -e "   ${YELLOW}terraform init${NC}"
echo ""
echo "2. Create terraform.tfvars:"
echo -e "   ${YELLOW}cp terraform.tfvars.example terraform.tfvars${NC}"
echo -e "   ${YELLOW}# Edit terraform.tfvars with your values${NC}"
echo ""
echo "3. Deploy infrastructure:"
echo -e "   ${YELLOW}terraform plan${NC}"
echo -e "   ${YELLOW}terraform apply${NC}"
echo ""
echo "Resources created:"
echo "  • S3 Bucket:       $BUCKET_NAME"
echo "  • DynamoDB Table:  $DYNAMODB_TABLE"
echo "  • Backend Config:  $BACKEND_FILE"
echo ""

# Optionally test Terraform init
read -p "Test Terraform init now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Testing terraform init...${NC}"
    cd "../environments/$ENVIRONMENT"
    terraform init
    echo -e "${GREEN}✓ Terraform init successful!${NC}"
fi
