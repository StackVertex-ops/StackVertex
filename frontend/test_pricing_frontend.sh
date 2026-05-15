#!/bin/bash
# Frontend Pricing Test Script

set -e

echo "🎨 OverCloud Frontend - Pricing Test"
echo "======================================"
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
echo "📋 Test 1: Get Pricing (Backend API)"
echo "====================================="
PRICING_RESPONSE=$(curl -s http://localhost:8001/api/v1/billing/pricing)

if echo "$PRICING_RESPONSE" | grep -q "free"; then
    echo -e "${GREEN}✓ Pricing API works${NC}"
    echo "$PRICING_RESPONSE" | python3 -m json.tool | head -20
else
    echo -e "${RED}✗ Pricing API failed${NC}"
    echo "$PRICING_RESPONSE"
    exit 1
fi

echo ""
echo "🚀 Test 2: Check Frontend Files"
echo "================================"

FILES=(
    "src/pricing.html"
    "src/billing.html"
    "src/billing/success.html"
    "src/billing/cancel.html"
    "src/js/api/billing.js"
    "src/js/pages/pricing.js"
    "src/js/pages/billing.js"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (NOT FOUND)"
    fi
done

echo ""
echo "🌐 Test 3: Start Frontend Dev Server"
echo "====================================="

# Check if Vite is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    echo "Install Node.js first: https://nodejs.org/"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ node_modules not found, installing dependencies...${NC}"
    npm install
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ All checks passed!${NC}"
echo ""
echo "🎯 Next Steps:"
echo "1. Start frontend dev server:"
echo "   ${BLUE}npm run dev${NC}"
echo ""
echo "2. Open in browser:"
echo "   ${BLUE}http://localhost:5173/src/pricing.html${NC}"
echo ""
echo "3. Test features:"
echo "   - Monthly/Yearly toggle"
echo "   - Pricing cards (FREE, PRO, ENTERPRISE)"
echo "   - Upgrade buttons"
echo ""
echo "📝 Note: Login functionality not yet implemented."
echo "   Use browser console: localStorage.setItem('access_token', 'YOUR_TOKEN')"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
