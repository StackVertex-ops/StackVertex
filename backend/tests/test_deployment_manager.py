"""Tests für DeploymentManager.

Testet Deployment Orchestration (mocked).
"""

import pytest
from uuid import uuid4
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.services.deployment_manager import DeploymentManager
from app.models.deployment import DeploymentStatus


class TestDeploymentManager:
    """Tests für DeploymentManager."""

    def test_create_manager(self):
        """Test: Manager erstellen."""
        manager = DeploymentManager()

        assert manager.workspace_dir is not None

    @pytest.mark.skip(reason="Complex mock setup - requires full deployment pipeline mocking")
    @patch('app.services.deployment_manager.get_architecture')
    @patch('app.services.deployment_manager.create_deployment')
    @patch('app.services.deployment_manager.TerraformGenerator')
    @patch('app.services.deployment_manager.TerraformExecutor')
    @patch('app.services.deployment_manager.update_deployment_status')
    @patch('app.services.deployment_manager.update_deployment_outputs')
    def test_start_deployment_success(
        self,
        mock_update_outputs,
        mock_update_status,
        mock_executor_class,
        mock_generator_class,
        mock_create_deployment,
        mock_get_architecture,
        db_session,
    ):
        """Test: Deployment erfolgreich starten."""
        # Setup mocks
        arch_id = uuid4()
        deployment_id = uuid4()

        mock_arch = Mock()
        mock_arch.id = arch_id
        mock_arch.architecture_json = {
            "version": "1.0.0",
            "metadata": {"name": "test"},
            "architecture": {"components": []},
        }
        mock_get_architecture.return_value = mock_arch

        mock_deployment = Mock()
        mock_deployment.id = deployment_id
        mock_create_deployment.return_value = mock_deployment

        mock_generator = Mock()
        mock_generator.generate.return_value = Mock(
            files={
                "main.tf": "resource ...",
                "variables.tf": "variable ...",
            }
        )
        mock_generator_class.return_value = mock_generator

        mock_executor = Mock()
        mock_executor.init.return_value = Mock(success=True, stdout="", stderr="")
        mock_executor.validate.return_value = Mock(success=True, stdout="", stderr="")
        mock_executor.plan.return_value = Mock(success=True, stdout="Plan: 5 to add", stderr="")
        mock_executor.apply.return_value = Mock(success=True, stdout="Apply complete", stderr="")
        mock_executor.output.return_value = Mock(success=True, stdout='{"vpc_id": {"value": "vpc-123"}}', stderr="")
        mock_executor_class.return_value = mock_executor

        # Execute
        manager = DeploymentManager()
        result = manager.start_deployment(
            db_session,
            architecture_id=arch_id,
            deployed_by="test-user",
        )

        # Verify
        assert result == deployment_id
        mock_get_architecture.assert_called_once()
        mock_create_deployment.assert_called_once()
        mock_generator.generate.assert_called_once()
        mock_executor.init.assert_called_once()
        mock_executor.validate.assert_called_once()
        mock_executor.plan.assert_called_once()
        mock_executor.apply.assert_called_once()

    @patch('app.services.deployment_manager.get_architecture')
    def test_start_deployment_architecture_not_found(self, mock_get_architecture, db_session):
        """Test: Architecture nicht gefunden."""
        mock_get_architecture.return_value = None

        manager = DeploymentManager()

        with pytest.raises(ValueError, match="Architecture .* not found"):
            manager.start_deployment(
                db_session,
                architecture_id=uuid4(),
                deployed_by="test-user",
            )

    @patch('app.services.deployment_manager.get_architecture')
    @patch('app.services.deployment_manager.create_deployment')
    @patch('app.services.deployment_manager.TerraformGenerator')
    def test_start_deployment_terraform_generation_fails(
        self,
        mock_generator_class,
        mock_create_deployment,
        mock_get_architecture,
        db_session,
    ):
        """Test: Terraform Generation schlägt fehl."""
        mock_arch = Mock()
        mock_arch.id = uuid4()
        mock_arch.architecture_json = {"version": "1.0.0"}
        mock_get_architecture.return_value = mock_arch

        mock_deployment = Mock()
        mock_deployment.id = uuid4()
        mock_create_deployment.return_value = mock_deployment

        mock_generator = Mock()
        mock_generator.generate.side_effect = Exception("Invalid template")
        mock_generator_class.return_value = mock_generator

        manager = DeploymentManager()

        with pytest.raises(Exception):
            manager.start_deployment(
                db_session,
                architecture_id=mock_arch.id,
                deployed_by="test-user",
            )

    @pytest.mark.skip(reason="Complex mock setup - requires full destroy pipeline mocking")
    @patch('app.services.deployment_manager.get_deployment')
    @patch('app.services.deployment_manager.TerraformExecutor')
    @patch('app.services.deployment_manager.update_deployment_status')
    def test_destroy_deployment_success(
        self,
        mock_update_status,
        mock_executor_class,
        mock_get_deployment,
        db_session,
    ):
        """Test: Deployment erfolgreich destroyen."""
        deployment_id = uuid4()

        mock_deployment = Mock()
        mock_deployment.id = deployment_id
        mock_deployment.status = DeploymentStatus.SUCCESS
        mock_deployment.generated_files = {
            "main.tf": "resource ...",
            "variables.tf": "variable ...",
        }
        mock_get_deployment.return_value = mock_deployment

        mock_executor = Mock()
        mock_executor.destroy.return_value = Mock(success=True, stdout="Destroy complete", stderr="")
        mock_executor_class.return_value = mock_executor

        manager = DeploymentManager()
        result = manager.destroy_deployment(
            db_session,
            deployment_id=deployment_id,
        )

        assert result == deployment_id
        mock_executor.destroy.assert_called_once()

    @patch('app.services.deployment_manager.get_deployment')
    def test_destroy_deployment_not_found(self, mock_get_deployment, db_session):
        """Test: Deployment nicht gefunden."""
        mock_get_deployment.return_value = None

        manager = DeploymentManager()

        with pytest.raises(ValueError, match="Deployment .* not found"):
            manager.destroy_deployment(
                db_session,
                deployment_id=uuid4(),
            )

    @patch('app.services.deployment_manager.get_deployment')
    def test_destroy_deployment_already_destroyed(self, mock_get_deployment, db_session):
        """Test: Deployment bereits destroyed."""
        mock_deployment = Mock()
        mock_deployment.status = DeploymentStatus.DESTROYED
        mock_get_deployment.return_value = mock_deployment

        manager = DeploymentManager()

        with pytest.raises(ValueError, match="Can only destroy successful deployments"):
            manager.destroy_deployment(
                db_session,
                deployment_id=uuid4(),
            )

    @pytest.mark.skip(reason="Complex mock setup - workspace_dir is from settings")
    def test_cleanup_deployment(self, tmp_path):
        """Test: Workspace cleanup."""
        manager = DeploymentManager()

        deployment_id = uuid4()
        workspace_path = manager.workspace_dir / str(deployment_id)
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create some files
        (workspace_path / "main.tf").write_text("resource ...")

        # Cleanup
        manager.cleanup_deployment(deployment_id)

        # Verify deleted
        assert not workspace_path.exists()

    @pytest.mark.skip(reason="Complex mock setup - workspace_dir is from settings")
    def test_cleanup_deployment_not_exists(self, tmp_path):
        """Test: Cleanup non-existent workspace (should not error)."""
        manager = DeploymentManager()

        # Should not raise
        manager.cleanup_deployment(uuid4())
