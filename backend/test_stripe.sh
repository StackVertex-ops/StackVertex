#!/bin/bash
# Stripe Payment Test Script

set -e

echo "🚀 Stripe Payment Integration Test"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo -n "Checking backend... "
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
    echo "Start backend with: poetry run uvicorn app.main:app --reload --port 8001"
    exit 1
fi

echo ""
echo "📋 Step 1: Get Pricing"
echo "======================="
curl -s http://localhost:8001/api/v1/billing/pricing | python3 -m json.tool
echo ""

echo "👤 Step 2: Register Test User"
echo "============================="
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "stripe-test@example.com",
    "name": "Stripe Test User",
    "password": "Test1234!"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ User registered${NC}"
    ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    ORG_ID=$(echo $REGISTER_RESPONSE | python3 -c "import sys, json; user=json.load(sys.stdin)['user']; orgs=user.get('organisations', []); print(orgs[0]['organisation_id'] if orgs else 'ERROR')")

    echo "  Token: ${ACCESS_TOKEN:0:20}..."
    echo "  Org ID: $ORG_ID"
else
    # User already exists, try login
    echo "User exists, trying login..."
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=stripe-test@example.com&password=Test1234!")

    ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

    # Get org ID
    ME_RESPONSE=$(curl -s http://localhost:8001/api/v1/auth/me \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    ORG_ID=$(echo $ME_RESPONSE | python3 -c "import sys, json; user=json.load(sys.stdin); orgs=user.get('organisations', []); print(orgs[0]['organisation_id'] if orgs else 'ERROR')")

    echo -e "${GREEN}✓ Logged in${NC}"
    echo "  Token: ${ACCESS_TOKEN:0:20}..."
    echo "  Org ID: $ORG_ID"
fi

echo ""
echo "💳 Step 3: Create Checkout Session (PRO - Monthly)"
echo "==================================================="
CHECKOUT_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/v1/billing/${ORG_ID}/checkout" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "pro",
    "interval": "monthly",
    "auto_renewal": false,
    "success_url": "http://localhost:5173/billing/success",
    "cancel_url": "http://localhost:5173/billing/cancel"
  }')

if echo "$CHECKOUT_RESPONSE" | grep -q "checkout_url"; then
    CHECKOUT_URL=$(echo $CHECKOUT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['checkout_url'])")
    echo -e "${GREEN}✓ Checkout session created${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}🔗 Checkout URL:${NC}"
    echo "$CHECKOUT_URL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📝 Test Card (Success):"
    echo "   Number:  4242 4242 4242 4242"
    echo "   Expiry:  12/34"
    echo "   CVC:     123"
    echo "   ZIP:     12345"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Open URL in browser"
    echo "2. Complete payment with test card"
    echo "3. Watch webhook in Stripe CLI (stripe listen)"
    echo "4. Check subscription status"
    echo ""

    # Open URL in browser (macOS)
    echo "Opening in browser..."
    open "$CHECKOUT_URL"

    echo ""
    echo "⏳ After payment, check subscription:"
    echo "   curl http://localhost:8001/api/v1/billing/${ORG_ID}/subscription \\"
    echo "     -H \"Authorization: Bearer $ACCESS_TOKEN\" | python3 -m json.tool"

else
    echo -e "${RED}✗ Failed to create checkout session${NC}"
    echo "$CHECKOUT_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo ""
echo "✅ Test completed successfully!"
echo ""
echo "💡 Tip: Keep 'stripe listen' running to see webhook events!"
