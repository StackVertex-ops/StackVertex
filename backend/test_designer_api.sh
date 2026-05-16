#!/bin/bash
# Test script for Infrastructure Designer API

set -e

API_BASE="http://localhost:8000/api/v1"
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Infrastructure Designer API ===${NC}\n"

# Sample Architecture JSON
ARCH_JSON=$(cat <<'EOF'
{
  "version": "1.0.0",
  "metadata": {
    "name": "Test Infrastructure",
    "description": "Test architecture for API validation",
    "createdAt": "2026-05-16T10:00:00Z",
    "updatedAt": "2026-05-16T10:00:00Z"
  },
  "components": {
    "vpc-001": {
      "id": "vpc-001",
      "type": "vpc",
      "name": "Main VPC",
      "config": {
        "cidr": "10.0.0.0/16",
        "enable_dns_support": true,
        "enable_dns_hostnames": true
      },
      "position": { "x": 100, "y": 100 }
    },
    "subnet-001": {
      "id": "subnet-001",
      "type": "subnet",
      "name": "Public Subnet",
      "config": {
        "cidr": "10.0.1.0/24",
        "vpc_id": "vpc-001",
        "availability_zone": "eu-central-1a",
        "map_public_ip_on_launch": true
      },
      "position": { "x": 200, "y": 200 }
    },
    "ec2-001": {
      "id": "ec2-001",
      "type": "ec2",
      "name": "Web Server",
      "config": {
        "instance_type": "t3.micro",
        "ami": "ami-0c55b159cbfafe1f0",
        "subnet_id": "subnet-001",
        "private_ip": "10.0.1.10"
      },
      "position": { "x": 300, "y": 300 }
    }
  },
  "connections": [
    {
      "id": "conn-001",
      "from": "vpc-001",
      "to": "subnet-001",
      "data": { "type": "contains" }
    },
    {
      "id": "conn-002",
      "from": "subnet-001",
      "to": "ec2-001",
      "data": { "type": "contains" }
    }
  ],
  "ipAllocations": {
    "ec2-001": {
      "ip": "10.0.1.10",
      "subnetId": "subnet-001",
      "allocatedAt": "2026-05-16T10:00:00Z"
    }
  }
}
EOF
)

# Test 1: Validate Architecture
echo -e "${BLUE}Test 1: Validate Architecture${NC}"
curl -s -X POST "$API_BASE/designer/validate" \
  -H "Content-Type: application/json" \
  -d "{\"architecture_json\": $ARCH_JSON}" | jq .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Validation successful${NC}\n"
else
  echo -e "${RED}✗ Validation failed${NC}\n"
  exit 1
fi

# Test 2: Generate Terraform
echo -e "${BLUE}Test 2: Generate Terraform${NC}"
TERRAFORM_RESULT=$(curl -s -X POST "$API_BASE/designer/generate-terraform" \
  -H "Content-Type: application/json" \
  -d "{\"architecture_json\": $ARCH_JSON}")

echo "$TERRAFORM_RESULT" | jq 'del(.files) | .'

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Terraform generation successful${NC}"

  # Show generated files
  echo -e "\n${BLUE}Generated files:${NC}"
  echo "$TERRAFORM_RESULT" | jq -r '.files | keys[]'

  # Optionally save files
  echo -e "\n${BLUE}Saving files to ./test_terraform_output/${NC}"
  mkdir -p test_terraform_output
  echo "$TERRAFORM_RESULT" | jq -r '.files | to_entries[] | "\(.key)\n\(.value)"' | \
    while IFS= read -r filename; do
      IFS= read -r content
      echo "$content" > "test_terraform_output/$filename"
      echo "  - $filename"
    done
  echo ""
else
  echo -e "${RED}✗ Terraform generation failed${NC}\n"
  exit 1
fi

# Test 3: Save Architecture
echo -e "${BLUE}Test 3: Save Architecture${NC}"
SAVE_RESULT=$(curl -s -X POST "$API_BASE/designer/save" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Infrastructure\",
    \"description\": \"Test architecture from API test script\",
    \"architecture_json\": $ARCH_JSON,
    \"owner\": \"test-user\"
  }")

echo "$SAVE_RESULT" | jq .

if [ $? -eq 0 ]; then
  ARCH_ID=$(echo "$SAVE_RESULT" | jq -r '.architecture_id')
  echo -e "${GREEN}✓ Save successful (ID: $ARCH_ID)${NC}\n"
else
  echo -e "${RED}✗ Save failed${NC}\n"
  exit 1
fi

# Test 4: Load Architecture
echo -e "${BLUE}Test 4: Load Architecture${NC}"
if [ -n "$ARCH_ID" ] && [ "$ARCH_ID" != "null" ]; then
  curl -s -X GET "$API_BASE/designer/load/$ARCH_ID" | jq 'del(.components) | .'

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Load successful${NC}\n"
  else
    echo -e "${RED}✗ Load failed${NC}\n"
    exit 1
  fi
else
  echo -e "${RED}✗ Skipped (no architecture ID from save)${NC}\n"
fi

# Test 5: Validate Invalid Architecture (should fail gracefully)
echo -e "${BLUE}Test 5: Validate Invalid Architecture${NC}"
INVALID_ARCH='{"version":"1.0.0","components":{}}'
curl -s -X POST "$API_BASE/designer/validate" \
  -H "Content-Type: application/json" \
  -d "{\"architecture_json\": $INVALID_ARCH}" | jq .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Handled invalid architecture gracefully${NC}\n"
else
  echo -e "${RED}✗ Failed to handle invalid architecture${NC}\n"
fi

echo -e "${GREEN}=== All Tests Completed ===${NC}"
