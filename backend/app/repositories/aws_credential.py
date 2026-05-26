"""Repository für AWS Credentials (Kunden-Accounts).

Speichert AWS Credentials sicher in AWS Secrets Manager.
Unterstützt AssumeRole (bevorzugt) und Access Keys (Fallback).
"""

import json
import logging
from datetime import datetime
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AWSCredentialRepository(BaseRepository):
    """Repository für AWS Credentials der Kunden."""

    def __init__(self, table=None, s3_storage=None):
        super().__init__(table, s3_storage)
        self.secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)

    def create(
        self,
        org_id: UUID,
        credential_type: str,
        name: str = "Default",
        role_arn: str | None = None,
        external_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str = "us-east-1"
    ) -> dict:
        """Erstellt neue AWS Credentials (encrypted in Secrets Manager).

        Args:
            org_id: Organisation ID
            credential_type: "assume_role" oder "access_key"
            name: Display Name für Credentials
            role_arn: ARN der IAM Role (für assume_role)
            external_id: External ID für AssumeRole (optional, aber empfohlen)
            access_key_id: AWS Access Key ID (für access_key)
            secret_access_key: AWS Secret Access Key (für access_key)
            region: AWS Region

        Returns:
            Credential Metadata (ohne sensitive Daten)

        Raises:
            ValueError: Bei ungültigen Parametern
        """
        # Validierung
        if credential_type not in ["assume_role", "access_key"]:
            raise ValueError("credential_type muss 'assume_role' oder 'access_key' sein")

        if credential_type == "assume_role" and not role_arn:
            raise ValueError("role_arn ist required für assume_role")

        if credential_type == "access_key":
            if not access_key_id or not secret_access_key:
                raise ValueError("access_key_id und secret_access_key sind required für access_key")

        credential_id = str(uuid4())

        # Speichere sensitive Daten in Secrets Manager
        secret_arn = self._store_in_secrets_manager(
            credential_id=credential_id,
            credential_type=credential_type,
            role_arn=role_arn,
            external_id=external_id,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key
        )

        # Speichere Metadata in DynamoDB
        item = {
            "PK": f"ORG#{org_id}",
            "SK": f"AWS_CREDENTIAL#{credential_id}",
            "id": credential_id,
            "org_id": str(org_id),
            "name": name,
            "credential_type": credential_type,
            "region": region,
            "secret_arn": secret_arn,
            "status": "active",
            "last_verified": None,
            # GSI für direkten Credential Lookup
            "GSI1PK": f"AWS_CREDENTIAL#{credential_id}",
            "GSI1SK": "METADATA"
        }

        self._put_item(item)
        logger.info(f"AWS Credential erstellt: {credential_id} (Typ: {credential_type})")

        return item

    def _store_in_secrets_manager(
        self,
        credential_id: str,
        credential_type: str,
        role_arn: str | None = None,
        external_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None
    ) -> str:
        """Speichert sensitive Credentials in AWS Secrets Manager.

        Args:
            credential_id: Unique Credential ID
            credential_type: "assume_role" oder "access_key"
            role_arn: IAM Role ARN (optional)
            external_id: External ID (optional)
            access_key_id: Access Key ID (optional)
            secret_access_key: Secret Access Key (optional)

        Returns:
            Secret ARN

        Raises:
            Exception: Wenn Secret nicht erstellt werden kann
        """
        secret_value = {
            "credential_type": credential_type
        }

        if credential_type == "assume_role":
            secret_value["role_arn"] = role_arn
            if external_id:
                secret_value["external_id"] = external_id
        elif credential_type == "access_key":
            secret_value["access_key_id"] = access_key_id
            secret_value["secret_access_key"] = secret_access_key

        secret_name = f"stackvertex/aws-credentials/{credential_id}"

        try:
            response = self.secrets_client.create_secret(
                Name=secret_name,
                Description=f"AWS Credentials für StackVertex Deployment {credential_id}",
                SecretString=json.dumps(secret_value),
                KmsKeyId=f"alias/stackvertex-secrets-{settings.ENV}",
                Tags=[
                    {"Key": "ManagedBy", "Value": "StackVertex"},
                    {"Key": "CredentialId", "Value": credential_id}
                ]
            )
            logger.info(f"Secret erstellt: {secret_name}")
            return response['ARN']

        except ClientError as e:
            logger.error(f"Fehler beim Erstellen des Secrets: {e}")
            raise

    def get_credentials(self, credential_id: str) -> dict:
        """Holt vollständige Credentials (inkl. sensitive Daten) aus Secrets Manager.

        Args:
            credential_id: Credential ID

        Returns:
            Credential dict mit allen Daten

        Raises:
            ValueError: Wenn Credential nicht existiert
        """
        # Hole Metadata aus DynamoDB (via GSI)
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :pk AND GSI1SK = :sk",
            ExpressionAttributeValues={
                ":pk": f"AWS_CREDENTIAL#{credential_id}",
                ":sk": "METADATA"
            }
        )

        items = response.get('Items', [])
        if not items:
            raise ValueError(f"Credential {credential_id} nicht gefunden")

        credential = items[0]

        # Hole sensitive Daten aus Secrets Manager
        try:
            secret_response = self.secrets_client.get_secret_value(
                SecretId=credential["secret_arn"]
            )
            secret_data = json.loads(secret_response['SecretString'])

            # Merge Metadata + Secrets
            return {
                **credential,
                **secret_data
            }

        except ClientError as e:
            logger.error(f"Fehler beim Abrufen des Secrets: {e}")
            raise

    def verify_credentials(self, credential_id: str) -> bool:
        """Verifiziert AWS Credentials durch Test-Connection.

        Args:
            credential_id: Credential ID

        Returns:
            True wenn Credentials gültig, False sonst
        """
        creds = self.get_credentials(credential_id)

        try:
            if creds["credential_type"] == "assume_role":
                # Test AssumeRole
                sts = boto3.client('sts', region_name=creds["region"])

                assume_role_params = {
                    "RoleArn": creds["role_arn"],
                    "RoleSessionName": "stackvertex-verification",
                    "DurationSeconds": 900
                }

                # External ID falls vorhanden
                if creds.get("external_id"):
                    assume_role_params["ExternalId"] = creds["external_id"]

                sts.assume_role(**assume_role_params)

            elif creds["credential_type"] == "access_key":
                # Test Access Keys
                sts = boto3.client(
                    'sts',
                    region_name=creds["region"],
                    aws_access_key_id=creds["access_key_id"],
                    aws_secret_access_key=creds["secret_access_key"]
                )
                sts.get_caller_identity()

            # Update last_verified timestamp
            self.table.update_item(
                Key={
                    "PK": f"ORG#{creds['org_id']}",
                    "SK": f"AWS_CREDENTIAL#{credential_id}"
                },
                UpdateExpression="SET last_verified = :now, #status = :status",
                ExpressionAttributeNames={
                    "#status": "status"
                },
                ExpressionAttributeValues={
                    ":now": datetime.utcnow().isoformat(),
                    ":status": "verified"
                }
            )

            logger.info(f"Credentials {credential_id} erfolgreich verifiziert")
            return True

        except ClientError as e:
            logger.error(f"Credential Verification fehlgeschlagen: {e}")

            # Markiere als failed
            self.table.update_item(
                Key={
                    "PK": f"ORG#{creds['org_id']}",
                    "SK": f"AWS_CREDENTIAL#{credential_id}"
                },
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={
                    "#status": "status"
                },
                ExpressionAttributeValues={
                    ":status": "failed"
                }
            )

            return False

    def list_by_org(self, org_id: UUID) -> list[dict]:
        """Listet alle Credentials einer Organisation.

        Args:
            org_id: Organisation ID

        Returns:
            Liste von Credential Metadata (ohne sensitive Daten)
        """
        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"ORG#{org_id}",
                ":sk_prefix": "AWS_CREDENTIAL#"
            }
        )

        return response.get('Items', [])

    def delete(self, credential_id: str) -> bool:
        """Löscht Credentials (DynamoDB + Secrets Manager).

        Args:
            credential_id: Credential ID

        Returns:
            True wenn erfolgreich gelöscht
        """
        # Hole Credential für secret_arn
        creds = self.get_credentials(credential_id)

        # Lösche Secret (mit Recovery Window)
        try:
            self.secrets_client.delete_secret(
                SecretId=creds["secret_arn"],
                RecoveryWindowInDays=7  # Wiederherstellbar für 7 Tage
            )
            logger.info(f"Secret gelöscht: {creds['secret_arn']}")
        except ClientError as e:
            logger.error(f"Fehler beim Löschen des Secrets: {e}")

        # Lösche DynamoDB Item
        self.table.delete_item(
            Key={
                "PK": f"ORG#{creds['org_id']}",
                "SK": f"AWS_CREDENTIAL#{credential_id}"
            }
        )

        logger.info(f"Credential gelöscht: {credential_id}")
        return True
