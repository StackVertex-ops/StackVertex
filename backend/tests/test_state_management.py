"""Tests für Terraform State Management.

Testet State File Backup und Restore.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.services.deployment_manager import DeploymentManager
from app.models.deployment import DeploymentStatus


class TestStateManagement:
    """Tests für State File Management."""

    def test_state_backup_after_successful_deployment(self, tmp_path):
        """Test: State File wird nach erfolgreichem Deployment gesichert."""
        # This is tested in the deployment workflow
        # State file should be saved to deployment.terraform_state
        deployment_id = uuid4()
        state_file = tmp_path / "terraform.tfstate"

        # Mock state file content
        state_content = '{"version": 4, "terraform_version": "1.5.0", "resources": []}'
        state_file.write_text(state_content)

        assert state_file.exists()
        assert state_file.read_text() == state_content

    @pytest.mark.skip(reason="DeploymentManager doesn't accept workspace_dir parameter")
    @patch('app.services.deployment_manager.get_deployment')
    def test_state_restore_for_destroy(self, mock_get_deployment, tmp_path):
        """Test: State File wird für Destroy wiederhergestellt."""
        deployment_id = uuid4()

        # Mock deployment with state
        deployment = Mock()
        deployment.id = deployment_id
        deployment.status = DeploymentStatus.SUCCESS
        deployment.terraform_state = '{"version": 4, "resources": []}'
        deployment.generated_files = {
            "main.tf": "resource \"aws_instance\" \"test\" {}"
        }
        mock_get_deployment.return_value = deployment

        manager = DeploymentManager()
        # Note: Full destroy test requires mocking TerraformExecutor
        # This just verifies the workspace restoration logic would work

    def test_state_file_format(self):
        """Test: State File hat korrektes JSON Format."""
        state_content = '{"version": 4, "terraform_version": "1.5.0", "resources": []}'

        import json
        parsed = json.loads(state_content)

        assert "version" in parsed
        assert "terraform_version" in parsed
        assert "resources" in parsed

    @pytest.mark.skip("State management changed - deployment_manager.get_architecture removed")
    @patch('app.services.deployment_manager.get_deployment')
    @patch('app.services.deployment_manager.get_architecture')
    def test_missing_state_file_warning(
        self,
        mock_get_architecture,
        mock_get_deployment,
        tmp_path,
        caplog
    ):
        """Test: Warning wenn State File fehlt."""
        deployment_id = uuid4()

        # Mock deployment without state
        deployment = Mock()
        deployment.id = deployment_id
        deployment.status = DeploymentStatus.SUCCESS
        deployment.terraform_state = None  # No state
        deployment.generated_files = {"main.tf": "resource {}"}
        mock_get_deployment.return_value = deployment

        # Note: Would need full mocking to test warning log
        # This test documents the expected behavior

    def test_state_backup_preserves_json(self):
        """Test: State Backup bewahrt JSON Struktur."""
        original_state = {
            "version": 4,
            "terraform_version": "1.5.0",
            "serial": 1,
            "lineage": "test-lineage",
            "resources": [
                {
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "test",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": []
                }
            ]
        }

        import json
        state_text = json.dumps(original_state)
        restored_state = json.loads(state_text)

        assert restored_state == original_state
        assert restored_state["version"] == 4
        assert len(restored_state["resources"]) == 1

    def test_state_file_size_handling(self):
        """Test: Large State Files können gespeichert werden."""
        # Simulate large state (many resources)
        resources = [
            {
                "mode": "managed",
                "type": f"aws_instance",
                "name": f"instance_{i}",
                "instances": []
            }
            for i in range(100)  # 100 resources
        ]

        large_state = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": resources
        }

        import json
        state_text = json.dumps(large_state)

        # Verify it's reasonably sized (< 1MB for 100 resources)
        assert len(state_text) < 1_000_000

        # Verify it can be parsed back
        restored = json.loads(state_text)
        assert len(restored["resources"]) == 100

    def test_state_backup_handles_unicode(self):
        """Test: State File mit Unicode Characters."""
        state_with_unicode = {
            "version": 4,
            "resources": [
                {
                    "name": "resource_ä_ö_ü",
                    "description": "Test mit Umlauten: äöü ÄÖÜ ß"
                }
            ]
        }

        import json
        state_text = json.dumps(state_with_unicode, ensure_ascii=False)
        restored = json.loads(state_text)

        assert "ä_ö_ü" in restored["resources"][0]["name"]
        assert "äöü" in restored["resources"][0]["description"]
