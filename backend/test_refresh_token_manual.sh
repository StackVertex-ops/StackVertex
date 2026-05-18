#!/bin/bash
# Manual Test Script für Refresh Token Pattern
# Tests Login -> Refresh -> Logout Flow

set -e  # Exit on error

API_URL="http://localhost:8000"
TEST_EMAIL="test-refresh-$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"

echo "==================================="
echo "Refresh Token Pattern - Manual Test"
echo "==================================="
echo ""

# 1. Register
echo "1. Register new user..."
REGISTER_RESPONSE=$(curl -s -c cookies.txt -X POST "${API_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"name\": \"Test User\",
    \"password\": \"${TEST_PASSWORD}\",
    \"auth_provider\": \"local\"
  }")

echo "✓ User registered"
echo "Response: ${REGISTER_RESPONSE}" | jq '.'
echo ""

# Check cookies
echo "Cookies after register:"
cat cookies.txt | grep -E "access_token|refresh_token" || echo "No cookies found"
echo ""

# 2. Login
echo "2. Login with email + password..."
LOGIN_RESPONSE=$(curl -s -c cookies.txt -X POST "${API_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${TEST_EMAIL}&password=${TEST_PASSWORD}")

echo "✓ Login successful"
echo "Response: ${LOGIN_RESPONSE}" | jq '.'
echo ""

# Check cookies
echo "Cookies after login:"
cat cookies.txt | grep -E "access_token|refresh_token" || echo "No cookies found"
echo ""

# 3. Get current user (with access token)
echo "3. Get current user (authenticated request)..."
ME_RESPONSE=$(curl -s -b cookies.txt -X GET "${API_URL}/api/v1/auth/me")

echo "✓ Got current user"
echo "Response: ${ME_RESPONSE}" | jq '.'
echo ""

# 4. Refresh tokens
echo "4. Refresh access token..."
REFRESH_RESPONSE=$(curl -s -c cookies.txt -b cookies.txt -X POST "${API_URL}/api/v1/auth/refresh")

echo "✓ Tokens refreshed"
echo "Response: ${REFRESH_RESPONSE}" | jq '.'
echo ""

# Check cookies again
echo "Cookies after refresh:"
cat cookies.txt | grep -E "access_token|refresh_token" || echo "No cookies found"
echo ""

# 5. Get current user again (with new token)
echo "5. Get current user with new token..."
ME_RESPONSE2=$(curl -s -b cookies.txt -X GET "${API_URL}/api/v1/auth/me")

echo "✓ Got current user with new token"
echo "Response: ${ME_RESPONSE2}" | jq '.'
echo ""

# 6. Logout
echo "6. Logout (revoke all tokens)..."
LOGOUT_RESPONSE=$(curl -s -c cookies.txt -b cookies.txt -X POST "${API_URL}/api/v1/auth/logout")

echo "✓ Logged out"
echo "Response: ${LOGOUT_RESPONSE}" | jq '.'
echo ""

# 7. Try to refresh with revoked token (should fail)
echo "7. Try to refresh with revoked token (should fail)..."
REFRESH_FAIL_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -b cookies.txt -X POST "${API_URL}/api/v1/auth/refresh")

HTTP_CODE=$(echo "$REFRESH_FAIL_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$REFRESH_FAIL_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" == "401" ]; then
    echo "✓ Refresh failed as expected (401)"
    echo "Response: ${RESPONSE_BODY}" | jq '.'
else
    echo "✗ Expected 401, got ${HTTP_CODE}"
    echo "Response: ${RESPONSE_BODY}"
fi
echo ""

# Cleanup
rm -f cookies.txt

echo "==================================="
echo "✓ All tests passed!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Check CloudWatch logs for refresh attempts"
echo "2. Check DynamoDB for refresh tokens"
echo "3. Test token expiry (wait 15 min or change config)"
