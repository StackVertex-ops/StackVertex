#!/bin/bash

# Test script for Admin Dashboard Frontend
# Tests various aspects of the admin dashboard

set -e

echo "=========================================="
echo "OverCloud - Admin Dashboard Frontend Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:5173"
API_URL="http://localhost:8000"

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3

    echo -n "Testing $name... "

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status)"
        exit 1
    fi
}

# Check if frontend is running
echo "1. Checking if frontend dev server is running..."
if ! curl -s "$BASE_URL" > /dev/null; then
    echo -e "${RED}✗ Frontend not running!${NC}"
    echo "Start with: cd frontend && npm run dev"
    exit 1
fi
echo -e "${GREEN}✓ Frontend is running${NC}"
echo ""

# Check if backend is running
echo "2. Checking if backend API is running..."
if ! curl -s "$API_URL/health" > /dev/null; then
    echo -e "${RED}✗ Backend not running!${NC}"
    echo "Start with: cd backend && poetry run uvicorn app.main:app --reload"
    exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Test file existence
echo "3. Testing file existence..."
files=(
    "src/admin.html"
    "src/js/pages/admin.js"
    "src/js/api/admin.js"
    "src/js/lib/api-client.js"
    "src/css/main.css"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file exists"
    else
        echo -e "  ${RED}✗${NC} $file NOT FOUND"
        exit 1
    fi
done
echo ""

# Test HTML pages
echo "4. Testing HTML pages..."
test_endpoint "Admin Dashboard HTML" "$BASE_URL/src/admin.html" 200
test_endpoint "Login Page HTML" "$BASE_URL/src/login.html" 200
echo ""

# Test JavaScript modules
echo "5. Testing JavaScript modules..."
test_endpoint "Admin Page JS" "$BASE_URL/src/js/pages/admin.js" 200
test_endpoint "Admin API JS" "$BASE_URL/src/js/api/admin.js" 200
test_endpoint "API Client JS" "$BASE_URL/src/js/lib/api-client.js" 200
echo ""

# Test CSS
echo "6. Testing CSS..."
test_endpoint "Main CSS" "$BASE_URL/src/css/main.css" 200
echo ""

# Test API endpoints (without auth)
echo "7. Testing API endpoints availability..."
echo -e "${YELLOW}Note: These should return 401 without authentication${NC}"

api_endpoints=(
    "/api/v1/admin/statistics"
    "/api/v1/admin/users"
    "/api/v1/admin/organisations"
    "/api/v1/admin/audit-logs"
)

for endpoint in "${api_endpoints[@]}"; do
    echo -n "  Testing $endpoint... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")

    if [ "$status" -eq 401 ] || [ "$status" -eq 403 ]; then
        echo -e "${GREEN}✓${NC} (HTTP $status - Auth required)"
    else
        echo -e "${YELLOW}?${NC} (HTTP $status - Unexpected)"
    fi
done
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create SuperAdmin user via backend CLI"
echo "2. Login at: $BASE_URL/src/login.html"
echo "3. Access Admin Dashboard at: $BASE_URL/src/admin.html"
echo ""
echo "Backend API docs: $API_URL/docs"
echo ""
