"""Tests für Deployment Retry Funktionalität.

Testet Retry Logic für fehlgeschlagene Deployments.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch

from app.models.deployment import DeploymentStatus
from app.services.deployment_manager import DeploymentManager


class TestDeploymentRetry:
    """Tests für Deployment Retry."""

    @patch('app.services.deployment_manager.get_deployment')
    @patch('app.services.deployment_manager.get_architecture')
    @patch('app.services.deployment_manager.task_runner')
    @patch('app.services.deployment_manager.create_deployment')
    def test_retry_failed_deployment(
        self,
        mock_create_deployment,
        mock_task_runner,
        mock_get_architecture,
        mock_get_deployment,
        db_session
    ):
        """Test: Retry eines FAILED Deployments."""
        original_deployment_id = uuid4()
        new_deployment_id = uuid4()
        architecture_id = uuid4()

        # Mock original deployment (FAILED)
        original_deployment = Mock()
        original_deployment.id = original_deployment_id
        original_deployment.architecture_id = architecture_id
        original_deployment.status = DeploymentStatus.FAILED
        original_deployment.deployed_by = "test-user"
        mock_get_deployment.return_value = original_deployment

        # Mock architecture
        architecture = Mock()
        architecture.id = architecture_id
        architecture.architecture_json = {"version": "1.0.0"}
        mock_get_architecture.return_value = architecture

        # Mock new deployment creation
        new_deployment = Mock()
        new_deployment.id = new_deployment_id
        mock_create_deployment.return_value = new_deployment

        # Execute retry
        manager = DeploymentManager()
        result = manager.retry_deployment(
            db_session,
            deployment_id=original_deployment_id
        )

        # Verify new deployment created
        assert result == new_deployment_id
        mock_create_deployment.assert_called_once()
        mock_task_runner.submit_task.assert_called_once()

    @patch('app.services.deployment_manager.get_deployment')
    def test_retry_cancelled_deployment(
        self,
        mock_get_deployment,
        db_session
    ):
        """Test: Retry eines CANCELLED Deployments."""
        deployment_id = uuid4()

        # Mock cancelled deployment
        deployment = Mock()
        deployment.id = deployment_id
        deployment.status = DeploymentStatus.CANCELLED
        deployment.architecture_id = uuid4()
        mock_get_deployment.return_value = deployment

        manager = DeploymentManager()

        # Should allow retry of CANCELLED deployments
        # (will fail later due to missing architecture, but validation passes)
        try:
            manager.retry_deployment(db_session, deployment_id)
        except ValueError as e:
            # Expected if architecture not found
            assert "not found" in str(e)

    @patch('app.services.deployment_manager.get_deployment')
    def test_retry_success_deployment_fails(
        self,
        mock_get_deployment,
        db_session
    ):
        """Test: Retry eines SUCCESS Deployments sollte fehlschlagen."""
        deployment_id = uuid4()

        # Mock successful deployment
        deployment = Mock()
        deployment.id = deployment_id
        deployment.status = DeploymentStatus.SUCCESS
        mock_get_deployment.return_value = deployment

        manager = DeploymentManager()

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot retry deployment in status"):
            manager.retry_deployment(db_session, deployment_id)

    @patch('app.services.deployment_manager.get_deployment')
    def test_retry_running_deployment_fails(
        self,
        mock_get_deployment,
        db_session
    ):
        """Test: Retry eines laufenden Deployments sollte fehlschlagen."""
        deployment_id = uuid4()

        # Mock running deployment
        deployment = Mock()
        deployment.id = deployment_id
        deployment.status = DeploymentStatus.APPLYING
        mock_get_deployment.return_value = deployment

        manager = DeploymentManager()

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot retry deployment"):
            manager.retry_deployment(db_session, deployment_id)

    @patch('app.services.deployment_manager.get_deployment')
    def test_retry_nonexistent_deployment(
        self,
        mock_get_deployment,
        db_session
    ):
        """Test: Retry eines nicht-existenten Deployments."""
        deployment_id = uuid4()

        mock_get_deployment.return_value = None

        manager = DeploymentManager()

        # Should raise ValueError
        with pytest.raises(ValueError, match="not found"):
            manager.retry_deployment(db_session, deployment_id)

    @patch('app.services.deployment_manager.get_deployment')
    @patch('app.services.deployment_manager.get_architecture')
    @patch('app.services.deployment_manager.task_runner')
    @patch('app.services.deployment_manager.create_deployment')
    def test_retry_with_new_credentials(
        self,
        mock_create_deployment,
        mock_task_runner,
        mock_get_architecture,
        mock_get_deployment,
        db_session
    ):
        """Test: Retry mit neuen AWS Credentials."""
        deployment_id = uuid4()
        new_deployment_id = uuid4()

        # Mock failed deployment
        deployment = Mock()
        deployment.id = deployment_id
        deployment.architecture_id = uuid4()
        deployment.status = DeploymentStatus.FAILED
        deployment.deployed_by = "test-user"
        mock_get_deployment.return_value = deployment

        # Mock architecture
        architecture = Mock()
        architecture.id = deployment.architecture_id
        architecture.architecture_json = {"version": "1.0.0"}
        mock_get_architecture.return_value = architecture

        # Mock new deployment
        new_deployment = Mock()
        new_deployment.id = new_deployment_id
        mock_create_deployment.return_value = new_deployment

        # New credentials
        new_credentials = {
            "access_key_id": "NEW_KEY",
            "secret_access_key": "NEW_SECRET"
        }

        # Execute retry
        manager = DeploymentManager()
        result = manager.retry_deployment(
            db_session,
            deployment_id=deployment_id,
            aws_credentials=new_credentials
        )

        # Verify credentials passed to background task
        task_call_kwargs = mock_task_runner.submit_task.call_args[1]
        assert task_call_kwargs["aws_credentials"] == new_credentials
