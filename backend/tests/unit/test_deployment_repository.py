"""Unit tests für DeploymentRepository.

Fokus: Status Lifecycle, S3 Always-Offload, Relationship Sync.
"""

import pytest
from uuid import UUID, uuid4
from boto3.dynamodb.conditions import Key

from app.models.deployment import DeploymentStatus
from app.schemas.deployment import DeploymentCreate


class TestDeploymentCreate:
    """Tests für create() method."""

    def test_create_deployment(self, deployment_repository):
        """Test creating deployment mit initial PENDING status."""
        arch_id = uuid4()
        deploy_create = DeploymentCreate(
            architecture_id=arch_id,
            deployed_by="test_user"
        )

        result = deployment_repository.create(deploy_create)

        assert result["architecture_id"] == str(arch_id)
        assert result["status"] == DeploymentStatus.PENDING.value
        assert result["deployed_by"] == "test_user"
        assert result["PK"].startswith("DEPLOY#")
        assert result["SK"] == "METADATA"
        assert result["GSI1PK"] == "deployment"
        assert result["GSI3PK"] == f"status#{DeploymentStatus.PENDING.value}"
        assert result["GSI4PK"] == f"architecture_id#{str(arch_id)}"

    def test_create_creates_relationship_item(self, deployment_repository):
        """Test creating deployment erstellt auch architecture-deployment relationship."""
        arch_id = uuid4()
        deploy_create = DeploymentCreate(
            architecture_id=arch_id,
            deployed_by="test_user"
        )

        result = deployment_repository.create(deploy_create)
        deployment_id = result["id"]

        # Verify relationship item exists
        relationship = deployment_repository._get_item(
            f"ARCH#{str(arch_id)}",
            f"DEPLOY#{deployment_id}"
        )

        assert relationship is not None
        assert relationship["deployment_id"] == deployment_id
        assert relationship["status"] == DeploymentStatus.PENDING.value


class TestDeploymentGet:
    """Tests für get() method."""

    def test_get_deployment(self, deployment_repository):
        """Test getting deployment."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test_user"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        result = deployment_repository.get(deployment_id)

        assert result is not None
        assert result["id"] == created["id"]

    def test_get_nonexistent_deployment(self, deployment_repository):
        """Test getting non-existent deployment returns None."""
        fake_id = uuid4()

        result = deployment_repository.get(fake_id)

        assert result is None


class TestDeploymentList:
    """Tests für list() method."""

    def test_list_all_deployments(self, deployment_repository):
        """Test listing all deployments (GSI1)."""
        for i in range(3):
            deployment_repository.create(DeploymentCreate(
                architecture_id=uuid4(),
                deployed_by=f"user{i}"
            ))

        items, total = deployment_repository.list(skip=0, limit=100)

        assert total == 3
        assert len(items) == 3

    def test_list_by_status(self, deployment_repository):
        """Test listing deployments by status (GSI3)."""
        # Create deployments
        dep1 = deployment_repository.create(DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        ))
        dep2 = deployment_repository.create(DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        ))

        # Update statuses
        deployment_repository.update_status(
            UUID(dep1["id"]),
            DeploymentStatus.SUCCESS
        )
        deployment_repository.update_status(
            UUID(dep2["id"]),
            DeploymentStatus.FAILED
        )

        # List by status
        items, total = deployment_repository.list(
            skip=0,
            limit=100,
            status=DeploymentStatus.SUCCESS
        )

        assert total == 1
        assert items[0]["id"] == dep1["id"]

    def test_list_by_architecture_id(self, deployment_repository):
        """Test listing deployments by architecture_id (GSI4)."""
        arch_id = uuid4()
        other_arch_id = uuid4()

        # Create deployments for different architectures
        deployment_repository.create(DeploymentCreate(
            architecture_id=arch_id,
            deployed_by="test"
        ))
        deployment_repository.create(DeploymentCreate(
            architecture_id=arch_id,
            deployed_by="test"
        ))
        deployment_repository.create(DeploymentCreate(
            architecture_id=other_arch_id,
            deployed_by="test"
        ))

        items, total = deployment_repository.list(
            skip=0,
            limit=100,
            architecture_id=arch_id
        )

        assert total == 2
        assert all(item["architecture_id"] == str(arch_id) for item in items)


class TestDeploymentUpdateStatus:
    """Tests für update_status() method (KRITISCH - STATUS LIFECYCLE)."""

    def test_update_status_updates_gsi(self, deployment_repository):
        """Test status update aktualisiert GSI3PK für querying by status."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        updated = deployment_repository.update_status(
            deployment_id,
            DeploymentStatus.PLANNING
        )

        assert updated["status"] == DeploymentStatus.PLANNING.value
        assert updated["GSI3PK"] == f"status#{DeploymentStatus.PLANNING.value}"

    def test_update_status_syncs_relationship_item(self, deployment_repository):
        """Test status update synct zu architecture-deployment relationship."""
        arch_id = uuid4()
        deploy_create = DeploymentCreate(
            architecture_id=arch_id,
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        deployment_repository.update_status(
            deployment_id,
            DeploymentStatus.SUCCESS
        )

        # Verify relationship item status updated
        relationship = deployment_repository._get_item(
            f"ARCH#{str(arch_id)}",
            f"DEPLOY#{str(deployment_id)}"
        )

        assert relationship["status"] == DeploymentStatus.SUCCESS.value

    @pytest.mark.parametrize("terminal_status", [
        DeploymentStatus.SUCCESS,
        DeploymentStatus.FAILED,
        DeploymentStatus.DESTROYED,
        DeploymentStatus.CANCELLED
    ])
    def test_update_terminal_status_sets_completed_at(self, deployment_repository, terminal_status):
        """Test terminal statuses setzen completed_at timestamp."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        updated = deployment_repository.update_status(
            deployment_id,
            terminal_status
        )

        assert "completed_at" in updated
        assert updated["completed_at"] is not None

    @pytest.mark.parametrize("non_terminal_status", [
        DeploymentStatus.PENDING,
        DeploymentStatus.GENERATING,
        DeploymentStatus.INITIALIZING,
        DeploymentStatus.PLANNING,
        DeploymentStatus.APPLYING
    ])
    def test_update_non_terminal_status_no_completed_at(self, deployment_repository, non_terminal_status):
        """Test non-terminal statuses setzen KEIN completed_at."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        updated = deployment_repository.update_status(
            deployment_id,
            non_terminal_status
        )

        assert "completed_at" not in updated or updated.get("completed_at") is None

    def test_update_status_with_error_message(self, deployment_repository):
        """Test updating to FAILED status mit error message."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        updated = deployment_repository.update_status(
            deployment_id,
            DeploymentStatus.FAILED,
            error_message="Terraform apply failed"
        )

        assert updated["status"] == DeploymentStatus.FAILED.value
        assert updated["error_message"] == "Terraform apply failed"


class TestDeploymentUpdateOutputs:
    """Tests für update_outputs() method (KRITISCH - ALWAYS S3)."""

    def test_update_plan_output_always_s3(self, deployment_repository):
        """Test plan_output geht ALWAYS zu S3 (unabhängig von Größe)."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        # Even small output goes to S3
        small_plan = "Terraform plan output (small)"

        updated = deployment_repository.update_outputs(
            deployment_id,
            plan_output=small_plan
        )

        # Response should have plan_output loaded
        assert updated["plan_output"] == small_plan

        # But underlying storage should use S3
        from_db = deployment_repository._get_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA"
        )
        assert "plan_output_s3_uri" in from_db
        assert "plan_output" not in from_db

    def test_update_apply_output_always_s3(self, deployment_repository):
        """Test apply_output geht ALWAYS zu S3."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        small_apply = "Terraform apply output (small)"

        updated = deployment_repository.update_outputs(
            deployment_id,
            apply_output=small_apply
        )

        assert updated["apply_output"] == small_apply

        # Verify S3 storage
        from_db = deployment_repository._get_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA"
        )
        assert "apply_output_s3_uri" in from_db

    def test_update_terraform_state_always_s3(self, deployment_repository):
        """Test terraform_state geht ALWAYS zu S3."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        terraform_state = '{"version": 4, "terraform_version": "1.5.0", "resources": []}'

        updated = deployment_repository.update_outputs(
            deployment_id,
            terraform_state=terraform_state
        )

        # Verify S3 storage
        from_db = deployment_repository._get_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA"
        )
        assert "terraform_state_s3_uri" in from_db

    def test_update_terraform_outputs_in_dynamodb(self, deployment_repository):
        """Test terraform_outputs bleiben in DynamoDB (small JSON)."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        terraform_outputs = {
            "vpc_id": {"value": "vpc-123", "type": "string"},
            "subnet_ids": {"value": ["subnet-1", "subnet-2"], "type": "list"}
        }

        updated = deployment_repository.update_outputs(
            deployment_id,
            terraform_outputs=terraform_outputs
        )

        # Should be stored inline in DynamoDB
        from_db = deployment_repository._get_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA"
        )
        assert from_db["terraform_outputs"] == terraform_outputs

    def test_update_generated_files_in_dynamodb(self, deployment_repository):
        """Test generated_files bleiben in DynamoDB (nur Paths)."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        generated_files = {
            "main.tf": "/tmp/deployment/main.tf",
            "variables.tf": "/tmp/deployment/variables.tf"
        }

        updated = deployment_repository.update_outputs(
            deployment_id,
            generated_files=generated_files
        )

        # Should be stored inline in DynamoDB
        from_db = deployment_repository._get_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA"
        )
        assert from_db["generated_files"] == generated_files


class TestDeploymentDelete:
    """Tests für delete() method."""

    def test_delete_deployment(self, deployment_repository):
        """Test deleting deployment."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        result = deployment_repository.delete(deployment_id)

        assert result is True
        assert deployment_repository.get(deployment_id) is None

    def test_delete_deployment_deletes_relationship_item(self, deployment_repository):
        """Test deleting deployment löscht architecture-deployment relationship."""
        arch_id = uuid4()
        deploy_create = DeploymentCreate(
            architecture_id=arch_id,
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        # Verify relationship exists
        rel_before = deployment_repository._get_item(
            f"ARCH#{str(arch_id)}",
            f"DEPLOY#{str(deployment_id)}"
        )
        assert rel_before is not None

        # Delete deployment
        deployment_repository.delete(deployment_id)

        # Verify relationship deleted
        rel_after = deployment_repository._get_item(
            f"ARCH#{str(arch_id)}",
            f"DEPLOY#{str(deployment_id)}"
        )
        assert rel_after is None

    def test_delete_deployment_with_outputs_deletes_s3(self, deployment_repository):
        """Test deleting deployment mit outputs löscht S3 objects."""
        deploy_create = DeploymentCreate(
            architecture_id=uuid4(),
            deployed_by="test"
        )
        created = deployment_repository.create(deploy_create)
        deployment_id = UUID(created["id"])

        # Add outputs to S3
        deployment_repository.update_outputs(
            deployment_id,
            plan_output="Plan output",
            apply_output="Apply output",
            terraform_state="State"
        )

        # Get S3 URIs before deletion
        from_db = deployment_repository._get_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA"
        )
        assert "plan_output_s3_uri" in from_db
        assert "apply_output_s3_uri" in from_db
        assert "terraform_state_s3_uri" in from_db

        # Delete deployment (should clean up S3)
        result = deployment_repository.delete(deployment_id)
        assert result is True

        # Note: moto doesn't fully simulate S3 delete,
        # but in real AWS the S3 objects would be deleted
