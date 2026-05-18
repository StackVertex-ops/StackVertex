"""AWS Session Management für Kunden-Accounts.

Erstellt boto3 Sessions via AssumeRole oder Access Keys.
"""

import logging

import boto3
from botocore.exceptions import ClientError

from app.repositories.aws_credential import AWSCredentialRepository

logger = logging.getLogger(__name__)


class AWSSessionManager:
    """Managed AWS Sessions für Kunden-Accounts."""

    def __init__(self, credential_repo: AWSCredentialRepository | None = None):
        """Initialisiert Session Manager.

        Args:
            credential_repo: Repository für Credentials (erstellt Default wenn None)
        """
        self.credential_repo = credential_repo or AWSCredentialRepository()

    def get_session(self, credential_id: str) -> boto3.Session:
        """Erstellt boto3 Session für Kunden-Account.

        Args:
            credential_id: ID der zu verwendenden Credentials

        Returns:
            boto3.Session für Kunden-Account

        Raises:
            ValueError: Bei ungültigen Credentials
            ClientError: Bei AWS API Fehlern
        """
        creds = self.credential_repo.get_credentials(credential_id)

        if creds["credential_type"] == "assume_role":
            return self._assume_role_session(
                role_arn=creds["role_arn"],
                external_id=creds.get("external_id"),
                region=creds["region"],
                session_name=f"overcloud-deployment-{credential_id[:8]}"
            )
        elif creds["credential_type"] == "access_key":
            return self._access_key_session(
                access_key_id=creds["access_key_id"],
                secret_access_key=creds["secret_access_key"],
                region=creds["region"]
            )
        else:
            raise ValueError(f"Unbekannter Credential Type: {creds['credential_type']}")

    def _assume_role_session(
        self,
        role_arn: str,
        region: str,
        session_name: str = "overcloud-deployment",
        external_id: str | None = None,
        duration_seconds: int = 3600
    ) -> boto3.Session:
        """Erstellt Session via AssumeRole.

        Args:
            role_arn: ARN der zu assumenden Role
            region: AWS Region
            session_name: Session Name (für CloudTrail)
            external_id: External ID (optional)
            duration_seconds: Session Dauer in Sekunden (default 1h)

        Returns:
            boto3.Session mit temporären Credentials

        Raises:
            ClientError: Bei AssumeRole Fehler
        """
        sts = boto3.client('sts', region_name=region)

        assume_role_params = {
            "RoleArn": role_arn,
            "RoleSessionName": session_name,
            "DurationSeconds": duration_seconds
        }

        # External ID falls vorhanden (empfohlen für Security)
        if external_id:
            assume_role_params["ExternalId"] = external_id

        try:
            response = sts.assume_role(**assume_role_params)
            credentials = response['Credentials']

            logger.info(
                f"AssumeRole erfolgreich: {role_arn} "
                f"(Session: {session_name}, ExpiresAt: {credentials['Expiration']})"
            )

            return boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )

        except ClientError as e:
            logger.error(f"AssumeRole fehlgeschlagen für {role_arn}: {e}")
            raise

    def _access_key_session(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str
    ) -> boto3.Session:
        """Erstellt Session via Access Keys.

        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            region: AWS Region

        Returns:
            boto3.Session mit permanenten Credentials
        """
        logger.info(f"Session erstellt via Access Keys (Region: {region})")

        return boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )

    def get_caller_identity(self, session: boto3.Session) -> dict:
        """Holt Caller Identity für Session (Account ID, User ARN, etc.).

        Args:
            session: boto3 Session

        Returns:
            Dict mit Account, UserId, Arn

        Raises:
            ClientError: Bei API Fehler
        """
        sts = session.client('sts')

        try:
            identity = sts.get_caller_identity()
            logger.info(
                f"Caller Identity: Account={identity['Account']}, "
                f"UserId={identity['UserId']}, Arn={identity['Arn']}"
            )
            return identity

        except ClientError as e:
            logger.error(f"Fehler beim Abrufen der Caller Identity: {e}")
            raise

    def test_permissions(self, session: boto3.Session, service: str = "ec2") -> bool:
        """Testet ob Session Permissions für einen Service hat.

        Args:
            session: boto3 Session
            service: AWS Service Name (default: ec2)

        Returns:
            True wenn Permissions vorhanden, False sonst
        """
        try:
            if service == "ec2":
                ec2 = session.client('ec2')
                # Simple Read Operation
                ec2.describe_regions(DryRun=False)
            elif service == "s3":
                s3 = session.client('s3')
                s3.list_buckets()
            elif service == "ecr":
                ecr = session.client('ecr')
                ecr.describe_repositories(maxResults=1)
            else:
                logger.warning(f"Unbekannter Service für Permission Test: {service}")
                return False

            logger.info(f"Permission Test für {service} erfolgreich")
            return True

        except ClientError as e:
            logger.warning(f"Permission Test für {service} fehlgeschlagen: {e}")
            return False
