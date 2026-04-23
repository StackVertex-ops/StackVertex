"""Tests für TerraformExecutor.

Testet Terraform CLI Wrapper (mocked).
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.services.terraform_executor import TerraformExecutor, ExecutionResult


class TestTerraformExecutor:
    """Tests für TerraformExecutor."""

    def test_create_executor(self, tmp_path):
        """Test: Executor erstellen."""
        executor = TerraformExecutor(working_dir=tmp_path)

        assert executor.working_dir == tmp_path
        assert executor.terraform_binary == "terraform"

    def test_create_executor_with_env_vars(self, tmp_path):
        """Test: Executor mit Environment Variables."""
        env_vars = {"AWS_ACCESS_KEY_ID": "test123"}

        executor = TerraformExecutor(
            working_dir=tmp_path,
            env_vars=env_vars
        )

        assert executor.env_vars == env_vars

    @patch('subprocess.run')
    def test_init_success(self, mock_run, tmp_path):
        """Test: Terraform init erfolgreich."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Terraform initialized",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.init()

        assert result.success is True
        assert "Terraform initialized" in result.stdout
        assert result.exit_code == 0

    @patch('subprocess.run')
    def test_init_with_backend_config(self, mock_run, tmp_path):
        """Test: Init mit Backend Config."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.init(backend_config={"path": "/tmp/state"})

        assert result.success is True

        # Verify backend config was passed
        call_args = mock_run.call_args[0][0]
        assert any("-backend-config=" in arg for arg in call_args)

    @patch('subprocess.run')
    def test_validate(self, mock_run, tmp_path):
        """Test: Terraform validate."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success! The configuration is valid.",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.validate()

        assert result.success is True
        assert "valid" in result.stdout

    @patch('subprocess.run')
    def test_plan(self, mock_run, tmp_path):
        """Test: Terraform plan."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Plan: 5 to add, 0 to change, 0 to destroy.",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.plan()

        assert result.success is True
        assert "Plan:" in result.stdout

    @patch('subprocess.run')
    def test_apply(self, mock_run, tmp_path):
        """Test: Terraform apply."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Apply complete! Resources: 5 added, 0 changed, 0 destroyed.",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.apply(auto_approve=True)

        assert result.success is True
        assert "Apply complete" in result.stdout

    @patch('subprocess.run')
    def test_destroy(self, mock_run, tmp_path):
        """Test: Terraform destroy."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Destroy complete! Resources: 5 destroyed.",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.destroy(auto_approve=True)

        assert result.success is True
        assert "Destroy complete" in result.stdout

    @patch('subprocess.run')
    def test_output(self, mock_run, tmp_path):
        """Test: Terraform output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"vpc_id": {"value": "vpc-123"}}',
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.output(format="json")

        assert result.success is True
        assert "vpc_id" in result.stdout

    @patch('subprocess.run')
    def test_version(self, mock_run, tmp_path):
        """Test: Terraform version."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Terraform v1.5.0",
            stderr=""
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.version()

        assert result.success is True
        assert "Terraform" in result.stdout

    @patch('subprocess.run')
    def test_command_failure(self, mock_run, tmp_path):
        """Test: Command schlägt fehl."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Configuration is invalid"
        )

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.validate()

        assert result.success is False
        assert result.exit_code == 1
        assert "invalid" in result.stderr

    @patch('subprocess.run')
    def test_command_timeout(self, mock_run, tmp_path):
        """Test: Command timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("terraform", 10)

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.init()

        assert result.success is False
        assert "timed out" in result.stderr
        assert result.exit_code == -1

    @patch('subprocess.run')
    def test_terraform_not_found(self, mock_run, tmp_path):
        """Test: Terraform binary nicht gefunden."""
        mock_run.side_effect = FileNotFoundError()

        executor = TerraformExecutor(working_dir=tmp_path)
        result = executor.init()

        assert result.success is False
        assert "not found" in result.stderr
        assert result.exit_code == -1

    @patch('subprocess.run')
    def test_env_vars_passed_to_subprocess(self, mock_run, tmp_path):
        """Test: Environment Variables werden an subprocess übergeben."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env_vars = {
            "AWS_ACCESS_KEY_ID": "test123",
            "AWS_SECRET_ACCESS_KEY": "secret",
        }

        executor = TerraformExecutor(working_dir=tmp_path, env_vars=env_vars)
        executor.init()

        # Verify env vars were passed
        call_kwargs = mock_run.call_args[1]
        assert "env" in call_kwargs
        assert "AWS_ACCESS_KEY_ID" in call_kwargs["env"]
        assert call_kwargs["env"]["AWS_ACCESS_KEY_ID"] == "test123"
