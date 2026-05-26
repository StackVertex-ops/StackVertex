"""AWS Secrets Manager Integration.

Handles encryption/decryption of sensitive data (AWS credentials, API keys, etc.)
"""

import logging

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages sensitive data using AWS Secrets Manager."""

    def __init__(self, client=None):
        """Initialize Secrets Manager client.

        Args:
            client: Optional boto3 secretsmanager client (for testing)
        """
        self.client = client or boto3.client(
            "secretsmanager",
            region_name=settings.AWS_REGION
        )

    def store_aws_role_arn(self, org_id: str, aws_role_arn: str) -> str:
        """Store AWS Role ARN encrypted in Secrets Manager.

        Args:
            org_id: Organisation UUID
            aws_role_arn: IAM Role ARN to encrypt

        Returns:
            Secret name (reference to stored secret)

        Raises:
            ClientError: If AWS API call fails
        """
        secret_name = f"stackvertex/org/{org_id}/aws_role_arn"

        try:
            # Try to update existing secret
            self.client.put_secret_value(
                SecretId=secret_name,
                SecretString=aws_role_arn
            )
            logger.info(f"Updated AWS Role ARN for org {org_id}")

        except self.client.exceptions.ResourceNotFoundException:
            # Create new secret
            self.client.create_secret(
                Name=secret_name,
                Description=f"AWS Role ARN for StackVertex Organisation {org_id}",
                SecretString=aws_role_arn,
                Tags=[
                    {"Key": "organisation_id", "Value": org_id},
                    {"Key": "managed_by", "Value": "stackvertex"},
                ]
            )
            logger.info(f"Created AWS Role ARN secret for org {org_id}")

        return secret_name

    def retrieve_aws_role_arn(self, secret_name: str) -> str | None:
        """Retrieve AWS Role ARN from Secrets Manager.

        Args:
            secret_name: Secret name (reference)

        Returns:
            Decrypted AWS Role ARN or None if not found
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response["SecretString"]

        except self.client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret {secret_name} not found")
            return None

        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {e}")
            return None

    def delete_aws_role_arn(self, secret_name: str, force_delete: bool = False) -> bool:
        """Delete AWS Role ARN from Secrets Manager.

        Args:
            secret_name: Secret name
            force_delete: If True, delete immediately without recovery window

        Returns:
            True if deleted successfully
        """
        try:
            if force_delete:
                self.client.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
            else:
                # Default: 30-day recovery window
                self.client.delete_secret(
                    SecretId=secret_name,
                    RecoveryWindowInDays=30
                )

            logger.info(f"Deleted secret {secret_name}")
            return True

        except self.client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret {secret_name} not found (already deleted?)")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete secret: {e}")
            return False


# Singleton instance
def get_secrets_manager() -> SecretsManager:
    """Get SecretsManager instance (FastAPI dependency)."""
    return SecretsManager()
