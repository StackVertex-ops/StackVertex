"""S3 Storage Helper.

Handles upload/download of large items that exceed DynamoDB's 400KB item size limit.
"""

import boto3
from typing import Optional
from mypy_boto3_s3 import S3Client

from app.config import settings


class S3Storage:
    """S3 storage for large items (> 300KB).

    Handles transparent storage and retrieval of items that exceed
    DynamoDB's 400KB limit or our 300KB threshold.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """Initialize S3 storage.

        Args:
            bucket_name: S3 bucket name (defaults to settings.S3_LARGE_ITEMS_BUCKET)
            region_name: AWS region (defaults to settings.AWS_REGION)
        """
        self.bucket_name = bucket_name or settings.S3_LARGE_ITEMS_BUCKET
        self.region_name = region_name or settings.AWS_REGION

        kwargs = {"region_name": self.region_name}

        # Add credentials if configured (for local dev)
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        self.client: S3Client = boto3.client("s3", **kwargs)

    def upload(self, key: str, data: str) -> str:
        """Upload data to S3.

        Args:
            key: S3 object key (path within bucket)
            data: String data to upload

        Returns:
            S3 URI (s3://bucket/key)

        Raises:
            Exception: If upload fails
        """
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data.encode("utf-8"),
            ServerSideEncryption="AES256",
            ContentType="application/json",
        )

        return f"s3://{self.bucket_name}/{key}"

    def download(self, s3_uri: str) -> str:
        """Download data from S3.

        Args:
            s3_uri: S3 URI (s3://bucket/key)

        Returns:
            Downloaded data as string

        Raises:
            ValueError: If S3 URI is invalid
            Exception: If download fails
        """
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")

        # Parse S3 URI
        parts = s3_uri[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")

        bucket, key = parts

        # Download object
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode("utf-8")

    def delete(self, s3_uri: str) -> bool:
        """Delete object from S3.

        Args:
            s3_uri: S3 URI (s3://bucket/key)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If S3 URI is invalid
        """
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")

        # Parse S3 URI
        parts = s3_uri[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")

        bucket, key = parts

        # Delete object
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def exists(self, s3_uri: str) -> bool:
        """Check if object exists in S3.

        Args:
            s3_uri: S3 URI (s3://bucket/key)

        Returns:
            True if object exists
        """
        if not s3_uri.startswith("s3://"):
            return False

        parts = s3_uri[5:].split("/", 1)
        if len(parts) != 2:
            return False

        bucket, key = parts

        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False
