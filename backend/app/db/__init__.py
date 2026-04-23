"""Database connection modules.

Provides DynamoDB and S3 clients for data persistence.
"""

from app.db.dynamodb import get_dynamodb_table, get_dynamodb_resource
from app.db.s3_storage import S3Storage

__all__ = [
    "get_dynamodb_table",
    "get_dynamodb_resource",
    "S3Storage",
]
