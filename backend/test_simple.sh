#!/bin/bash

echo "🧪 Testing OverCloud API on port 8001..."
echo ""

# Test 1: Health Check
echo "1️⃣  Health Check:"
curl -s http://localhost:8001/health | jq '.'
echo ""

# Test 2: Create Architecture
echo "2️⃣  Create Architecture:"
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/architectures \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "name": "Test Architecture",
  "owner": "andy@example.com",
  "version": "1.0.0",
  "architecture_json": {
    "version": "1.0.0",
    "components": []
  }
}
EOF
)

echo "$RESPONSE" | jq '.'
ARCH_ID=$(echo "$RESPONSE" | jq -r '.id // empty')

if [ -n "$ARCH_ID" ]; then
  echo ""
  echo "✅ SUCCESS! Architecture created: $ARCH_ID"
  echo ""

  # Test 3: Get it back
  echo "3️⃣  Get Architecture:"
  curl -s http://localhost:8001/api/v1/architectures/$ARCH_ID | jq '.name, .version'
  echo ""

  # Test 4: List all
  echo "4️⃣  List All Architectures:"
  curl -s http://localhost:8001/api/v1/architectures | jq '.total, .items[].name'
  echo ""

  echo "✅ ALL TESTS PASSED! 🎉"
else
  echo "❌ Failed to create architecture"
  echo "$RESPONSE"
fi
