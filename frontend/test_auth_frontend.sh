#!/bin/bash
# Frontend Auth Test Script

set -e

echo "🔐 OverCloud Frontend - Auth Test"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo -n "Checking backend... "
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
    echo "Start backend with: cd backend && poetry run uvicorn app.main:app --reload --port 8001"
    exit 1
fi

echo ""
echo "🚀 Test 1: Check Auth Files"
echo "============================"

FILES=(
    "src/login.html"
    "src/register.html"
    "src/js/api/auth.js"
    "src/js/lib/auth.js"
    "src/js/pages/login.js"
    "src/js/pages/register.js"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (NOT FOUND)"
    fi
done

echo ""
echo "📋 Test 2: Test Registration (Backend API)"
echo "==========================================="

# Generate random email
RANDOM_EMAIL="test-$(date +%s)@example.com"

REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$RANDOM_EMAIL\",
    \"name\": \"Test User\",
    \"password\": \"Test1234!\"
  }")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Registration works${NC}"
    ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "  Email: $RANDOM_EMAIL"
    echo "  Token: ${ACCESS_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Registration failed${NC}"
    echo "$REGISTER_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo ""
echo "📋 Test 3: Test Login (Backend API)"
echo "===================================="

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$RANDOM_EMAIL&password=Test1234!")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Login works${NC}"
    LOGIN_TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "  Token: ${LOGIN_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo ""
echo "📋 Test 4: Get Current User (Backend API)"
echo "=========================================="

ME_RESPONSE=$(curl -s http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ME_RESPONSE" | grep -q "email"; then
    echo -e "${GREEN}✓ Get current user works${NC}"
    echo "$ME_RESPONSE" | python3 -m json.tool | head -15
else
    echo -e "${RED}✗ Get current user failed${NC}"
    echo "$ME_RESPONSE"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ All Auth tests passed!${NC}"
echo ""
echo "🎯 Next Steps:"
echo "1. Start frontend dev server:"
echo "   ${BLUE}npm run dev${NC}"
echo ""
echo "2. Open in browser:"
echo "   ${BLUE}http://localhost:5173/src/register.html${NC}"
echo "   ${BLUE}http://localhost:5173/src/login.html${NC}"
echo ""
echo "3. Test complete flow:"
echo "   a) Register new account"
echo "   b) Login with account"
echo "   c) Go to Pricing page"
echo "   d) Try to upgrade (should redirect to Stripe)"
echo "   e) Go to Billing page"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
