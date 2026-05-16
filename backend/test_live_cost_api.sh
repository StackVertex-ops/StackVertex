#!/bin/bash
# Test Script für Live Cost Calculation API
# Testet den /costs/calculate-live Endpoint

API_URL="http://localhost:8000/api/v1/costs/calculate-live"

echo "=========================================="
echo "Live Cost Calculation API Tests"
echo "=========================================="
echo ""

# Test 1: Static Website
echo "Test 1: Static Website Blueprint"
echo "------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "static-website",
    "configuration": {
      "storage_gb": 50,
      "traffic_gb": 1000,
      "monthly_requests": 1000000,
      "domain_name": "example.com"
    }
  }' | jq .

echo ""
echo ""

# Test 2: Three-Tier Web App
echo "Test 2: Three-Tier Web App Blueprint"
echo "------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "three-tier-web",
    "configuration": {
      "ec2_instance_type": "t3.small",
      "min_instances": 2,
      "rds_instance_class": "db.t3.micro",
      "rds_engine": "postgres",
      "rds_allocated_storage": 20,
      "rds_multi_az": false
    }
  }' | jq .

echo ""
echo ""

# Test 3: Serverless API
echo "Test 3: Serverless API Blueprint"
echo "------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "serverless-api",
    "configuration": {
      "lambda_invocations_per_month": 1000000,
      "lambda_memory_mb": 512,
      "lambda_avg_duration_ms": 200,
      "api_requests_per_month": 1000000
    }
  }' | jq .

echo ""
echo ""

# Test 4: Invalid Blueprint
echo "Test 4: Invalid Blueprint (Error Handling)"
echo "------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "unknown-blueprint",
    "configuration": {}
  }' | jq .

echo ""
echo ""

# Test 5: Invalid Instance Type (Error Handling)
echo "Test 5: Invalid EC2 Instance Type (Error Handling)"
echo "------------------------------------------"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint_id": "three-tier-web",
    "configuration": {
      "ec2_instance_type": "invalid.type",
      "min_instances": 2
    }
  }' | jq .

echo ""
echo "=========================================="
echo "Tests abgeschlossen!"
echo "=========================================="
