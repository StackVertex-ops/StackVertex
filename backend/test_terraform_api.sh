#!/bin/bash
# Test-Skript für Terraform Generator V2 API Endpoint

set -e

# Konfiguration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ENDPOINT="/api/v1/terraform/generate-from-json"

# Farben für Output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Terraform Generator V2 API Test"
echo "========================================"
echo "API Base URL: $API_BASE_URL"
echo "Endpoint: $ENDPOINT"
echo ""

# Test Architecture JSON
cat > /tmp/test_architecture.json <<'EOF'
{
  "metadata": {
    "name": "api-test-infrastructure",
    "provider": "aws",
    "region": "eu-central-1"
  },
  "components": {
    "vpc-1": {
      "name": "test-vpc",
      "type": "vpc",
      "config": {
        "cidr": "10.0.0.0/16",
        "enableDns": true,
        "needsIGW": true
      }
    },
    "subnet-1": {
      "name": "public-subnet",
      "type": "subnet",
      "config": {
        "vpc": "vpc-1",
        "cidr": "10.0.1.0/24",
        "az": "eu-central-1a",
        "subnetType": "public"
      }
    },
    "sg-1": {
      "name": "api-sg",
      "type": "security_group",
      "config": {
        "vpc": "vpc-1",
        "description": "Security group for API servers",
        "ingressRules": [
          {
            "description": "Allow HTTPS",
            "fromPort": 443,
            "toPort": 443,
            "protocol": "tcp",
            "cidrBlocks": ["0.0.0.0/0"]
          }
        ]
      }
    },
    "s3-1": {
      "name": "api-storage",
      "type": "s3",
      "config": {
        "versioning": true
      }
    },
    "dynamodb-1": {
      "name": "api-data",
      "type": "dynamodb",
      "config": {
        "billingMode": "PAY_PER_REQUEST",
        "hashKey": "id",
        "hashKeyType": "S",
        "pointInTimeRecovery": true
      }
    }
  },
  "connections": [
    {"from": "vpc-1", "to": "subnet-1"},
    {"from": "vpc-1", "to": "sg-1"}
  ]
}
EOF

echo -e "${YELLOW}Sende Request an API...${NC}"
echo ""

# API Request
RESPONSE=$(curl -s -X POST "$API_BASE_URL$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d @/tmp/test_architecture.json \
  -w "\nHTTP_STATUS:%{http_code}")

# Extract HTTP Status
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
  echo -e "${GREEN}✅ API Request erfolgreich!${NC}"
  echo ""

  # Parse Response (mit jq wenn verfügbar)
  if command -v jq &> /dev/null; then
    echo "Response (formatiert):"
    echo "$BODY" | jq '.'
    echo ""

    # Extract Terraform files
    echo -e "${YELLOW}Generierte Terraform Files:${NC}"
    echo "$BODY" | jq -r '.terraform_files | keys[]' | while read filename; do
      echo "  - $filename"
    done
    echo ""

    # Extract main.tf (als Beispiel)
    echo -e "${YELLOW}main.tf (Auszug):${NC}"
    echo "$BODY" | jq -r '.terraform_files["main.tf"]' | head -20
    echo "  [...]"
    echo ""

    # Extract statistics
    echo -e "${YELLOW}Statistik:${NC}"
    echo "  Project Name: $(echo "$BODY" | jq -r '.project_name')"
    echo "  File Count: $(echo "$BODY" | jq -r '.file_count')"
    echo "  Component Count: $(echo "$BODY" | jq -r '.component_count')"
    echo "  Generated At: $(echo "$BODY" | jq -r '.generated_at')"

  else
    echo "Response (raw):"
    echo "$BODY"
    echo ""
    echo -e "${YELLOW}Tipp: Installiere 'jq' für formatierte Ausgabe${NC}"
  fi

  echo ""
  echo -e "${GREEN}✅ Test erfolgreich abgeschlossen!${NC}"
  exit 0

else
  echo -e "${RED}❌ API Request fehlgeschlagen!${NC}"
  echo ""
  echo "Response Body:"
  echo "$BODY"
  exit 1
fi
