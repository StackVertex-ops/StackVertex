"""Unit Tests für AWS Session Manager."""

import pytest
from unittest.mock import Mock, patch

from app.services.aws_session import AWSSessionManager


@pytest.fixture
def mock_credential_repo():
    """Mock Credential Repository."""
    repo = Mock()
    return repo


@pytest.fixture
def session_manager(mock_credential_repo):
    """AWS Session Manager mit Mock Repo."""
    return AWSSessionManager(credential_repo=mock_credential_repo)


class TestAWSSessionManager:
    """Tests für AWS Session Manager."""

    @patch('boto3.client')
    def test_get_session_assume_role(self, mock_boto_client, session_manager, mock_credential_repo):
        """Test: Session via AssumeRole."""
        # Mock STS assume_role
        mock_sts = Mock()
        mock_sts.assume_role = Mock(return_value={
            "Credentials": {
                "AccessKeyId": "ASIATESTACCESSKEY",
                "SecretAccessKey": "testsecretkey",
                "SessionToken": "testtoken",
                "Expiration": "2026-05-17T12:00:00Z"
            }
        })
        mock_boto_client.return_value = mock_sts

        # Mock get_credentials
        mock_credential_repo.get_credentials = Mock(return_value={
            "credential_type": "assume_role",
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "external_id": "test-external-id",
            "region": "us-east-1"
        })

        session = session_manager.get_session("cred_123")

        assert session is not None
        assert session.region_name == "us-east-1"
        assert mock_sts.assume_role.called

        # Verify External ID was passed
        call_args = mock_sts.assume_role.call_args[1]
        assert call_args['ExternalId'] == "test-external-id"

    @patch('boto3.Session')
    def test_get_session_access_key(self, mock_session_class, session_manager, mock_credential_repo):
        """Test: Session via Access Keys."""
        # Mock get_credentials
        mock_credential_repo.get_credentials = Mock(return_value={
            "credential_type": "access_key",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-west-2"
        })

        session = session_manager.get_session("cred_123")

        assert mock_session_class.called
        call_args = mock_session_class.call_args[1]

        assert call_args['aws_access_key_id'] == "AKIAIOSFODNN7EXAMPLE"
        assert call_args['region_name'] == "us-west-2"

    def test_get_session_invalid_type(self, session_manager, mock_credential_repo):
        """Test: Ungültiger Credential Type."""
        mock_credential_repo.get_credentials = Mock(return_value={
            "credential_type": "invalid"
        })

        with pytest.raises(ValueError, match="Unbekannter Credential Type"):
            session_manager.get_session("cred_123")

    @patch('boto3.Session')
    def test_get_caller_identity(self, mock_session_class, session_manager):
        """Test: Caller Identity abrufen."""
        # Mock Session
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity = Mock(return_value={
            "Account": "123456789012",
            "UserId": "AIDAI23EXAMPLE",
            "Arn": "arn:aws:iam::123456789012:user/test"
        })
        mock_session.client = Mock(return_value=mock_sts_client)

        identity = session_manager.get_caller_identity(mock_session)

        assert identity['Account'] == "123456789012"
        assert identity['UserId'] == "AIDAI23EXAMPLE"

    @patch('boto3.Session')
    def test_test_permissions_ec2(self, mock_session_class, session_manager):
        """Test: EC2 Permissions testen."""
        # Mock Session
        mock_session = Mock()
        mock_ec2_client = Mock()
        mock_ec2_client.describe_regions = Mock(return_value={"Regions": []})
        mock_session.client = Mock(return_value=mock_ec2_client)

        result = session_manager.test_permissions(mock_session, "ec2")

        assert result is True
        assert mock_ec2_client.describe_regions.called

    @patch('boto3.Session')
    def test_test_permissions_s3(self, mock_session_class, session_manager):
        """Test: S3 Permissions testen."""
        # Mock Session
        mock_session = Mock()
        mock_s3_client = Mock()
        mock_s3_client.list_buckets = Mock(return_value={"Buckets": []})
        mock_session.client = Mock(return_value=mock_s3_client)

        result = session_manager.test_permissions(mock_session, "s3")

        assert result is True
        assert mock_s3_client.list_buckets.called
