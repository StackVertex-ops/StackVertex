#!/bin/bash
#
# StackVertex - Create Admin User (Post-Deployment)
#
# Erstellt einen SuperAdmin User in der deployed DynamoDB
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "👤 StackVertex - Create Admin User"
echo "===================================="
echo ""

# Check if backend directory exists
if [ ! -d "../../backend" ]; then
    echo -e "${RED}❌ Backend directory not found${NC}"
    echo "Run this script from: infrastructure/scripts/"
    exit 1
fi

# Get environment
echo "Environment:"
echo "  1) dev"
echo "  2) staging"
echo "  3) prod"
echo ""
read -p "Select (1/2/3): " env_choice

case $env_choice in
    1) ENV="dev" ;;
    2) ENV="staging" ;;
    3) ENV="prod" ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Environment: $ENV${NC}"
echo ""

# Get admin details
read -p "Admin Email: " ADMIN_EMAIL
read -p "Admin Name [Admin User]: " ADMIN_NAME
ADMIN_NAME=${ADMIN_NAME:-"Admin User"}

# Force flag
read -p "Force creation (even if admin exists)? (yes/no) [no]: " FORCE
FORCE=${FORCE:-"no"}

FORCE_FLAG=""
if [ "$FORCE" = "yes" ]; then
    FORCE_FLAG="--force"
fi

echo ""
echo "=================================================="
echo "Creating Admin User"
echo "=================================================="
echo "Environment: $ENV"
echo "Email:       $ADMIN_EMAIL"
echo "Name:        $ADMIN_NAME"
echo "Force:       $FORCE"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Set environment variable for DynamoDB table
export DYNAMODB_TABLE_NAME="stackvertex-${ENV}-main"
export ENVIRONMENT="$ENV"
export AWS_REGION="eu-central-1"

# Check for ADMIN_CREATION_SECRET
if [ -z "$ADMIN_CREATION_SECRET" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  ADMIN_CREATION_SECRET not set${NC}"
    echo ""
    echo "This secret prevents unauthorized admin creation."
    echo "Set a random 32+ character value and store it securely."
    echo ""
    read -p "Enter ADMIN_CREATION_SECRET: " ADMIN_SECRET
    export ADMIN_CREATION_SECRET="$ADMIN_SECRET"
fi

echo ""
echo "🚀 Creating admin user..."
echo ""

# Navigate to backend
cd ../../backend

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry not installed${NC}"
    echo "Install: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    poetry install --no-root --only main
fi

# Run create_superadmin script
echo "👤 Creating SuperAdmin..."
poetry run python scripts/create_superadmin.py \
    --email "$ADMIN_EMAIL" \
    --name "$ADMIN_NAME" \
    $FORCE_FLAG

echo ""
echo -e "${GREEN}✅ ADMIN USER CREATED!${NC}"
echo ""
echo "=================================================="
echo "Next Steps:"
echo "  1. Copy the password from above"
echo "  2. Store it securely (password manager)"
echo "  3. Login at: https://<your-frontend-url>/login.html"
echo "  4. Change password after first login"
echo "=================================================="
echo ""
