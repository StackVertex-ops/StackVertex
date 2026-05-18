"""Unit Tests für AWS Credential Repository."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from app.repositories.aws_credential import AWSCredentialRepository


@pytest.fixture
def mock_table():
    """Mock DynamoDB Table."""
    table = Mock()
    table.put_item = Mock()
    table.query = Mock()
    table.update_item = Mock()
    table.delete_item = Mock()
    return table


@pytest.fixture
def mock_secrets_client():
    """Mock AWS Secrets Manager Client."""
    client = Mock()
    client.create_secret = Mock(return_value={"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"})
    client.get_secret_value = Mock()
    client.delete_secret = Mock()
    return client


@pytest.fixture
def credential_repo(mock_table, mock_secrets_client):
    """AWSCredentialRepository mit Mocks."""
    repo = AWSCredentialRepository(table=mock_table)
    repo.secrets_client = mock_secrets_client
    return repo


class TestAWSCredentialRepository:
    """Tests für AWS Credential Repository."""

    def test_create_assume_role_credential(self, credential_repo, mock_table, mock_secrets_client):
        """Test: AssumeRole Credential erstellen."""
        org_id = uuid4()
        role_arn = "arn:aws:iam::123456789012:role/TestRole"
        external_id = "test-external-id"

        credential = credential_repo.create(
            org_id=org_id,
            credential_type="assume_role",
            name="Test Role",
            role_arn=role_arn,
            external_id=external_id,
            region="us-east-1"
        )

        # Verify DynamoDB put_item called
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]['Item']

        assert call_args['org_id'] == str(org_id)
        assert call_args['name'] == "Test Role"
        assert call_args['credential_type'] == "assume_role"
        assert call_args['region'] == "us-east-1"
        assert call_args['status'] == "active"

        # Verify Secrets Manager create_secret called
        assert mock_secrets_client.create_secret.called

    def test_create_access_key_credential(self, credential_repo, mock_table, mock_secrets_client):
        """Test: Access Key Credential erstellen."""
        org_id = uuid4()
        access_key_id = "AKIAIOSFODNN7EXAMPLE"
        secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

        credential = credential_repo.create(
            org_id=org_id,
            credential_type="access_key",
            name="Test Access Key",
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region="us-east-1"
        )

        # Verify Secrets Manager called with correct data
        assert mock_secrets_client.create_secret.called
        call_args = mock_secrets_client.create_secret.call_args[1]

        assert "access_key_id" in call_args['SecretString']
        assert "secret_access_key" in call_args['SecretString']

    def test_create_invalid_credential_type(self, credential_repo):
        """Test: Ungültiger Credential Type."""
        with pytest.raises(ValueError, match="credential_type muss"):
            credential_repo.create(
                org_id=uuid4(),
                credential_type="invalid",
                name="Test"
            )

    def test_create_assume_role_without_role_arn(self, credential_repo):
        """Test: AssumeRole ohne role_arn."""
        with pytest.raises(ValueError, match="role_arn ist required"):
            credential_repo.create(
                org_id=uuid4(),
                credential_type="assume_role",
                name="Test"
            )

    def test_create_access_key_without_keys(self, credential_repo):
        """Test: Access Key ohne credentials."""
        with pytest.raises(ValueError, match="access_key_id und secret_access_key sind required"):
            credential_repo.create(
                org_id=uuid4(),
                credential_type="access_key",
                name="Test"
            )

    @patch('boto3.client')
    def test_verify_credentials_assume_role_success(self, mock_boto_client, credential_repo, mock_table):
        """Test: Credential Verification (AssumeRole) erfolgreich."""
        # Mock STS assume_role
        mock_sts = Mock()
        mock_sts.assume_role = Mock(return_value={
            "Credentials": {
                "AccessKeyId": "ASIATESTACCESSKEY",
                "SecretAccessKey": "testsecretkey",
                "SessionToken": "testtoken"
            }
        })
        mock_boto_client.return_value = mock_sts

        # Mock get_credentials
        credential_repo.get_credentials = Mock(return_value={
            "id": "cred_123",
            "org_id": str(uuid4()),
            "credential_type": "assume_role",
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "region": "us-east-1"
        })

        result = credential_repo.verify_credentials("cred_123")

        assert result is True
        assert mock_table.update_item.called

    @patch('boto3.client')
    def test_verify_credentials_access_key_success(self, mock_boto_client, credential_repo, mock_table):
        """Test: Credential Verification (Access Key) erfolgreich."""
        # Mock STS get_caller_identity
        mock_sts = Mock()
        mock_sts.get_caller_identity = Mock(return_value={
            "Account": "123456789012",
            "UserId": "AIDAI23EXAMPLE",
            "Arn": "arn:aws:iam::123456789012:user/test"
        })
        mock_boto_client.return_value = mock_sts

        # Mock get_credentials
        credential_repo.get_credentials = Mock(return_value={
            "id": "cred_123",
            "org_id": str(uuid4()),
            "credential_type": "access_key",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-east-1"
        })

        result = credential_repo.verify_credentials("cred_123")

        assert result is True
        assert mock_table.update_item.called

    def test_list_by_org(self, credential_repo, mock_table):
        """Test: Credentials einer Organisation auflisten."""
        org_id = uuid4()

        mock_table.query.return_value = {
            'Items': [
                {"id": "cred_1", "name": "Credential 1"},
                {"id": "cred_2", "name": "Credential 2"}
            ]
        }

        credentials = credential_repo.list_by_org(org_id)

        assert len(credentials) == 2
        assert mock_table.query.called

    def test_delete_credential(self, credential_repo, mock_table, mock_secrets_client):
        """Test: Credential löschen."""
        # Mock get_credentials
        credential_repo.get_credentials = Mock(return_value={
            "id": "cred_123",
            "org_id": str(uuid4()),
            "secret_arn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"
        })

        result = credential_repo.delete("cred_123")

        assert result is True
        assert mock_secrets_client.delete_secret.called
        assert mock_table.delete_item.called
