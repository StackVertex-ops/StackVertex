"""Repository layer for DynamoDB data access.

Provides clean abstraction over DynamoDB operations with automatic
S3 offload for large items.
"""

from app.repositories.base import BaseRepository

__all__ = ["BaseRepository"]
