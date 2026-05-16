#!/bin/bash

# Manual Auth Testing Script
# Run backend first: poetry run uvicorn app.main:app --reload

set -e

API_URL="http://127.0.0.1:8000/api/v1"
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-${TIMESTAMP}@example.com"
TEST_PASSWORD="SecurePass123!"

echo "========================================"
echo "OverCloud Auth Manual Testing"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Registration
echo -e "${YELLOW}[Test 1] Registering new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"name\": \"Test User Manual\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Registration successful${NC}"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":"[^"]*' | sed -n 2p | cut -d'"' -f4)
    echo "  Email: ${TEST_EMAIL}"
    echo "  Token: ${ACCESS_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Registration failed${NC}"
    echo "$REGISTER_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Get User Profile
echo -e "${YELLOW}[Test 2] Getting user profile...${NC}"
PROFILE_RESPONSE=$(curl -s -X GET "${API_URL}/auth/me" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$PROFILE_RESPONSE" | grep -q "${TEST_EMAIL}"; then
    echo -e "${GREEN}✓ Profile retrieved successfully${NC}"
    echo "  User ID: ${USER_ID}"
else
    echo -e "${RED}✗ Profile retrieval failed${NC}"
    echo "$PROFILE_RESPONSE"
fi
echo ""

# Test 3: Login with Credentials
echo -e "${YELLOW}[Test 3] Logging in with credentials...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${TEST_EMAIL}&password=${TEST_PASSWORD}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Login successful${NC}"
    NEW_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "  New Token: ${NEW_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "$LOGIN_RESPONSE"
fi
echo ""

# Test 4: Wrong Password
echo -e "${YELLOW}[Test 4] Testing wrong password...${NC}"
WRONG_PW_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${TEST_EMAIL}&password=WrongPassword123")

if echo "$WRONG_PW_RESPONSE" | grep -q "Incorrect"; then
    echo -e "${GREEN}✓ Wrong password correctly rejected${NC}"
else
    echo -e "${RED}✗ Wrong password not rejected${NC}"
    echo "$WRONG_PW_RESPONSE"
fi
echo ""

# Test 5: Invalid Token
echo -e "${YELLOW}[Test 5] Testing invalid token...${NC}"
INVALID_TOKEN_RESPONSE=$(curl -s -X GET "${API_URL}/auth/me" \
  -H "Authorization: Bearer invalid-token-here")

if echo "$INVALID_TOKEN_RESPONSE" | grep -q "Could not validate"; then
    echo -e "${GREEN}✓ Invalid token correctly rejected${NC}"
else
    echo -e "${RED}✗ Invalid token not rejected${NC}"
    echo "$INVALID_TOKEN_RESPONSE"
fi
echo ""

# Test 6: Token Refresh
echo -e "${YELLOW}[Test 6] Refreshing token...${NC}"
REFRESH_RESPONSE=$(curl -s -X POST "${API_URL}/auth/refresh" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$REFRESH_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Token refresh successful${NC}"
    REFRESHED_TOKEN=$(echo "$REFRESH_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "  Refreshed Token: ${REFRESHED_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Token refresh failed${NC}"
    echo "$REFRESH_RESPONSE"
fi
echo ""

# Test 7: Logout
echo -e "${YELLOW}[Test 7] Testing logout...${NC}"
LOGOUT_RESPONSE=$(curl -s -X POST "${API_URL}/auth/logout")

if echo "$LOGOUT_RESPONSE" | grep -q "Logged out"; then
    echo -e "${GREEN}✓ Logout successful${NC}"
else
    echo -e "${RED}✗ Logout failed${NC}"
    echo "$LOGOUT_RESPONSE"
fi
echo ""

# Test 8: Duplicate Registration
echo -e "${YELLOW}[Test 8] Testing duplicate email registration...${NC}"
DUP_RESPONSE=$(curl -s -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"name\": \"Test User 2\",
    \"password\": \"AnotherPass123!\"
  }")

if echo "$DUP_RESPONSE" | grep -q "already registered"; then
    echo -e "${GREEN}✓ Duplicate email correctly rejected${NC}"
else
    echo -e "${RED}✗ Duplicate email not rejected${NC}"
    echo "$DUP_RESPONSE"
fi
echo ""

# Test 9: Account Lockout
echo -e "${YELLOW}[Test 9] Testing account lockout (5 failed attempts)...${NC}"
LOCKOUT_EMAIL="lockout-${TIMESTAMP}@example.com"

# First register a user for lockout test
curl -s -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${LOCKOUT_EMAIL}\",
    \"name\": \"Lockout Test User\",
    \"password\": \"${TEST_PASSWORD}\"
  }" > /dev/null

# Try 5 times with wrong password
for i in {1..5}; do
    ATTEMPT_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=${LOCKOUT_EMAIL}&password=WrongPassword${i}")

    if [ $i -lt 5 ]; then
        if echo "$ATTEMPT_RESPONSE" | grep -q "remaining"; then
            echo "  Attempt $i: Failed ($(expr 5 - $i) attempts remaining)"
        fi
    else
        if echo "$ATTEMPT_RESPONSE" | grep -q "locked"; then
            echo -e "${GREEN}✓ Account locked after 5 failed attempts${NC}"
        else
            echo -e "${RED}✗ Account not locked${NC}"
            echo "$ATTEMPT_RESPONSE"
        fi
    fi
done
echo ""

echo "========================================"
echo "All tests completed!"
echo "========================================"
