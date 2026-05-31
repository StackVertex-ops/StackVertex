"""DynamoDB Client Setup.

Provides configured DynamoDB resource and table for the application.
"""


import os
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

from app.config import settings


def get_dynamodb_resource(
    region_name: str | None = None,
    endpoint_url: str | None = None
) -> DynamoDBServiceResource:
    """Get configured DynamoDB resource.

    Args:
        region_name: AWS region (defaults to Lambda runtime AWS_REGION or settings.AWS_REGION)
        endpoint_url: Custom endpoint URL (for DynamoDB Local testing)

    Returns:
        DynamoDB service resource
    """
    # Priority: 1. Explicit param, 2. Lambda runtime env var, 3. Settings default
    region = region_name or os.environ.get("AWS_REGION") or settings.AWS_REGION

    kwargs = {
        "region_name": region,
    }

    # Use custom endpoint if provided (for DynamoDB Local)
    if endpoint_url or settings.DYNAMODB_ENDPOINT_URL:
        kwargs["endpoint_url"] = endpoint_url or settings.DYNAMODB_ENDPOINT_URL

    # Add credentials if configured (for local dev)
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    return boto3.resource("dynamodb", **kwargs)


def get_dynamodb_table() -> Table:
    """Get DynamoDB table instance (FastAPI Dependency).

    Returns:
        DynamoDB Table resource
    """
    resource = get_dynamodb_resource()
    return resource.Table(settings.DYNAMODB_TABLE_NAME)
