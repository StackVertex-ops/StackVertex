#!/bin/bash
# Start DynamoDB Local für Testing

set -e

echo "🚀 Starting DynamoDB Local..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Stop existing container if running
docker stop dynamodb-local 2>/dev/null || true
docker rm dynamodb-local 2>/dev/null || true

# Start DynamoDB Local
docker run -d \
    --name dynamodb-local \
    -p 8000:8000 \
    amazon/dynamodb-local \
    -jar DynamoDBLocal.jar -sharedDb -inMemory

echo "✅ DynamoDB Local started on port 8000"
echo ""
echo "To stop: docker stop dynamodb-local"
echo "To view logs: docker logs -f dynamodb-local"
echo ""
echo "Next: Run ./create_dynamodb_table.sh to create the table"
