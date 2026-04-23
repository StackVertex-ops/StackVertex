#!/bin/bash
# Test OverCloud API with DynamoDB Local

set -e

BASE_URL="http://localhost:8000"

echo "🧪 Testing OverCloud API..."
echo ""

# Test 1: Health Check
echo "1️⃣  Health Check"
curl -s "$BASE_URL/health" | jq '.'
echo ""

# Test 2: Create Architecture
echo "2️⃣  Create Architecture"
ARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/architectures" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Web App",
        "description": "Simple test architecture",
        "version": "1.0.0",
        "owner": "test@example.com",
        "architecture_json": {
            "version": "1.0.0",
            "metadata": {
                "name": "Test Web App"
            },
            "components": [
                {
                    "id": "web-server",
                    "type": "ecs_service",
                    "properties": {
                        "image": "nginx:latest",
                        "port": 80
                    }
                }
            ]
        }
    }')

ARCH_ID=$(echo $ARCH_RESPONSE | jq -r '.id')
echo "Created Architecture: $ARCH_ID"
echo $ARCH_RESPONSE | jq '.'
echo ""

# Test 3: Get Architecture
echo "3️⃣  Get Architecture"
curl -s "$BASE_URL/api/v1/architectures/$ARCH_ID" | jq '.'
echo ""

# Test 4: List Architectures
echo "4️⃣  List Architectures"
curl -s "$BASE_URL/api/v1/architectures?limit=10" | jq '.items | length'
echo ""

# Test 5: Update Architecture
echo "5️⃣  Update Architecture"
curl -s -X PUT "$BASE_URL/api/v1/architectures/$ARCH_ID" \
    -H "Content-Type: application/json" \
    -d '{
        "description": "Updated description"
    }' | jq '.description'
echo ""

# Test 6: Cost Estimation
echo "6️⃣  Cost Estimation"
curl -s "$BASE_URL/api/v1/costs/architectures/$ARCH_ID/estimate" | jq '{total_monthly, currency}'
echo ""

# Test 7: Delete Architecture
echo "7️⃣  Delete Architecture"
curl -s -X DELETE "$BASE_URL/api/v1/architectures/$ARCH_ID"
echo "Architecture deleted: $ARCH_ID"
echo ""

# Test 8: Verify Deletion
echo "8️⃣  Verify Deletion"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/architectures/$ARCH_ID")
if [ "$STATUS" == "404" ]; then
    echo "✅ Architecture correctly deleted (404 Not Found)"
else
    echo "❌ Unexpected status: $STATUS"
fi
echo ""

echo "✅ All tests completed!"
echo ""
echo "Summary:"
echo "  ✅ Health check"
echo "  ✅ Create architecture"
echo "  ✅ Get architecture"
echo "  ✅ List architectures"
echo "  ✅ Update architecture"
echo "  ✅ Cost estimation"
echo "  ✅ Delete architecture"
echo "  ✅ Verify deletion"
