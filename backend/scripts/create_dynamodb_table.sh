#!/bin/bash
# Create DynamoDB table with all GSIs for local testing

set -e

ENDPOINT="http://localhost:8000"
TABLE_NAME="overcloud-dev-main"
REGION="us-east-1"

# Set fake credentials for DynamoDB Local (it doesn't validate them)
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-fakeAccessKey}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-fakeSecretKey}

echo "📦 Creating DynamoDB table: $TABLE_NAME"

# Create table with GSIs
aws dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
        AttributeName=GSI1PK,AttributeType=S \
        AttributeName=GSI1SK,AttributeType=S \
        AttributeName=GSI2PK,AttributeType=S \
        AttributeName=GSI2SK,AttributeType=S \
        AttributeName=GSI3PK,AttributeType=S \
        AttributeName=GSI3SK,AttributeType=S \
        AttributeName=GSI4PK,AttributeType=S \
        AttributeName=GSI4SK,AttributeType=S \
        AttributeName=GSI5PK,AttributeType=S \
        AttributeName=GSI5SK,AttributeType=S \
        AttributeName=GSI6PK,AttributeType=S \
        AttributeName=GSI6SK,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"GSI1\",
                \"KeySchema\": [
                    {\"AttributeName\": \"GSI1PK\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"GSI1SK\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"GSI2\",
                \"KeySchema\": [
                    {\"AttributeName\": \"GSI2PK\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"GSI2SK\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"GSI3\",
                \"KeySchema\": [
                    {\"AttributeName\": \"GSI3PK\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"GSI3SK\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"GSI4\",
                \"KeySchema\": [
                    {\"AttributeName\": \"GSI4PK\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"GSI4SK\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"GSI5\",
                \"KeySchema\": [
                    {\"AttributeName\": \"GSI5PK\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"GSI5SK\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"GSI6\",
                \"KeySchema\": [
                    {\"AttributeName\": \"GSI6PK\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"GSI6SK\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url $ENDPOINT \
    --region $REGION \
    --no-cli-pager

echo "✅ Table created successfully!"
echo ""
echo "Verify with:"
echo "  aws dynamodb describe-table --table-name $TABLE_NAME --endpoint-url $ENDPOINT --region $REGION"
echo ""
echo "Next: Set environment variables and start the backend"
echo "  export DYNAMODB_TABLE_NAME=$TABLE_NAME"
echo "  export DYNAMODB_ENDPOINT_URL=$ENDPOINT"
echo "  poetry run uvicorn app.main:app --reload"
