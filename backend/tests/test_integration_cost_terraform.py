"""Integration Tests - Cost + Terraform.

Testet Integration zwischen Cost Estimation und Terraform Generation.
"""

import pytest


class TestCostTerraformIntegration:
    """Cost + Terraform Integration Tests."""

    def test_cost_matches_terraform_resources(self, sample_architecture_simple_web):
        """Test: Cost Estimation berücksichtigt alle Terraform Resources.

        Flow:
        1. Generate Terraform from architecture
        2. Estimate cost
        3. Verify alle Terraform Resources sind im Cost Breakdown
        """
        from app.core.terraform_generator import TerraformGenerator
        from app.services.cost_estimator import CostEstimator

        # 1. Generate Terraform
        generator = TerraformGenerator()
        terraform_project = generator.generate(sample_architecture_simple_web)

        # Count resources in Terraform
        terraform_resources = []
        for filename, content in terraform_project.files.items():
            if filename.endswith(".tf") and "resource" in content:
                # Simple count (not perfect, but good enough)
                terraform_resources.append(filename)

        # 2. Estimate cost
        estimator = CostEstimator()
        cost_estimate = estimator.estimate_architecture_cost(sample_architecture_simple_web)

        # 3. Verify coverage
        # Not all Terraform resources cost money (e.g., VPC is free)
        # But all billable components should be in cost breakdown
        assert len(cost_estimate.components) > 0

        # Check that EC2/RDS/Lambda instances are counted
        component_types = [c.component_type for c in cost_estimate.components]
        architecture_types = [c["type"] for c in sample_architecture_simple_web["architecture"]["components"]]

        for comp_type in architecture_types:
            if comp_type in ["ec2", "rds", "lambda"]:
                assert comp_type in component_types

    def test_terraform_generation_before_deployment(self, sample_architecture_simple_web):
        """Test: Terraform muss erfolgreich generiert werden vor Deployment.

        Flow:
        1. Generate Terraform
        2. Verify valid HCL
        3. Only then should deployment proceed
        """
        from app.core.terraform_generator import TerraformGenerator

        # 1. Generate Terraform
        generator = TerraformGenerator()
        terraform_project = generator.generate(sample_architecture_simple_web, validate=False)

        # 2. Verify files generated
        assert "provider.tf" in terraform_project.files
        assert "variables.tf" in terraform_project.files

        # If generation succeeds, deployment can proceed
        assert terraform_project is not None

    def test_cost_estimation_independent_of_terraform(self, sample_architecture_simple_web):
        """Test: Cost Estimation funktioniert unabhängig von Terraform.

        Flow:
        1. Estimate cost (without generating Terraform)
        2. Verify cost is calculated
        """
        from app.services.cost_estimator import CostEstimator

        # 1. Estimate cost
        estimator = CostEstimator()
        cost_estimate = estimator.estimate_architecture_cost(sample_architecture_simple_web)

        # 2. Verify cost calculated
        assert cost_estimate.total_monthly_cost > 0
        assert len(cost_estimate.components) > 0

    def test_terraform_variables_from_architecture(self, sample_architecture_simple_web):
        """Test: Terraform Variables werden aus Architecture Metadata generiert.

        Flow:
        1. Generate Terraform
        2. Verify variables.tf contains region, owner, etc.
        """
        from app.core.terraform_generator import TerraformGenerator

        # 1. Generate Terraform
        generator = TerraformGenerator()
        terraform_project = generator.generate(sample_architecture_simple_web, validate=False)

        # 2. Verify variables
        variables_tf = terraform_project.files.get("variables.tf", "")

        # Should contain region variable
        assert "variable" in variables_tf
        assert "region" in variables_tf

    def test_cost_changes_with_instance_type(self, sample_architecture_simple_web):
        """Test: Cost ändert sich bei Instance Type Änderung.

        Flow:
        1. Estimate cost für t3.micro
        2. Change to t3.large
        3. Estimate cost again
        4. Verify cost increased
        """
        from app.services.cost_estimator import CostEstimator
        from copy import deepcopy

        estimator = CostEstimator()

        # 1. Estimate cost für t3.micro
        cost_micro = estimator.estimate_architecture_cost(sample_architecture_simple_web)

        # 2. Change to t3.large
        arch_large = deepcopy(sample_architecture_simple_web)
        for component in arch_large["architecture"]["components"]:
            if component["type"] == "ec2" and "instance_type" in component["properties"]:
                component["properties"]["instance_type"] = "t3.large"

        # 3. Estimate cost again
        cost_large = estimator.estimate_architecture_cost(arch_large)

        # 4. Verify cost increased
        assert cost_large.total_monthly_cost > cost_micro.total_monthly_cost

    def test_terraform_plan_output_format(self):
        """Test: Terraform Plan Output hat erwartetes Format.

        Flow:
        1. Mock Terraform Executor
        2. Run plan
        3. Verify output format
        """
        from app.services.terraform_executor import TerraformExecutor, ExecutionResult
        from unittest.mock import patch, Mock
        from pathlib import Path

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Plan: 5 to add, 0 to change, 0 to destroy.",
                stderr="",
            )

            executor = TerraformExecutor(working_dir=Path("/tmp"))
            result = executor.plan()

            assert result.success is True
            assert "Plan:" in result.stdout
            assert result.exit_code == 0

    @pytest.mark.skip(reason="Requires actual Terraform binary")
    def test_terraform_validate_generated_code(self, sample_architecture_simple_web, tmp_path):
        """Test: Generated Terraform Code passes terraform validate.

        Flow:
        1. Generate Terraform
        2. Write files to temp directory
        3. Run terraform validate
        4. Verify success
        """
        from app.core.terraform_generator import TerraformGenerator
        from app.services.terraform_executor import TerraformExecutor

        # 1. Generate Terraform
        generator = TerraformGenerator()
        terraform_project = generator.generate(sample_architecture_simple_web, validate=False)

        # 2. Write files
        for filename, content in terraform_project.files.items():
            (tmp_path / filename).write_text(content)

        # 3. Run terraform validate
        executor = TerraformExecutor(working_dir=tmp_path)
        init_result = executor.init()
        assert init_result.success

        validate_result = executor.validate()

        # 4. Verify success
        assert validate_result.success

    def test_cost_breakdown_has_all_components(self, sample_architecture_simple_web):
        """Test: Cost Breakdown hat alle Components.

        Flow:
        1. Count components in architecture
        2. Estimate cost
        3. Verify alle Components im Breakdown (außer kostenlose wie VPC)
        """
        from app.services.cost_estimator import CostEstimator

        # 1. Count billable components
        billable_types = ["ec2", "rds", "lambda", "s3"]
        arch_components = [
            c for c in sample_architecture_simple_web["architecture"]["components"]
            if c["type"] in billable_types
        ]

        # 2. Estimate cost
        estimator = CostEstimator()
        cost_estimate = estimator.estimate_architecture_cost(sample_architecture_simple_web)

        # 3. Verify all billable components in breakdown
        cost_component_ids = [c.component_id for c in cost_estimate.components]

        for component in arch_components:
            assert component["id"] in cost_component_ids
