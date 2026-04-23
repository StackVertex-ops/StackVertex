"""Deployment Repository - DynamoDB Data Access.

Handles CRUD operations for Deployment entities with automatic
S3 offload for large outputs (terraform_state, plan/apply outputs).
"""

from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

from app.repositories.base import BaseRepository
from app.schemas.deployment import DeploymentCreate
from app.models.deployment import DeploymentStatus


class DeploymentRepository(BaseRepository):
    """Repository for Deployment entities.

    DynamoDB Structure:
        Main Item:
            PK: DEPLOY#{deployment_id}
            SK: METADATA
            Attributes: id, architecture_id, status, terraform_version, generated_files,
                       plan_output_s3_uri, apply_output_s3_uri, terraform_state_s3_uri,
                       terraform_outputs, error_message, timestamps, deployed_by, workspace_path
            GSI1: entity_type + created_at (list all)
            GSI3: status#{status} + created_at (list by status)
            GSI4: architecture_id#{architecture_id} + created_at (list by architecture)

        Relationship Item:
            PK: ARCH#{architecture_id}
            SK: DEPLOY#{deployment_id}
            Attributes: deployment_id, status, created_at
    """

    def create(self, deployment: DeploymentCreate) -> Dict[str, Any]:
        """Create new deployment.

        Args:
            deployment: Deployment data

        Returns:
            Created deployment item

        Raises:
            Exception: If creation fails
        """
        deployment_id = str(uuid4())
        arch_id_str = str(deployment.architecture_id)
        now = datetime.utcnow().isoformat()

        # Main deployment item
        item: Dict[str, Any] = {
            "PK": f"DEPLOY#{deployment_id}",
            "SK": "METADATA",
            "id": deployment_id,
            "architecture_id": arch_id_str,
            "status": DeploymentStatus.PENDING.value,
            "deployed_by": deployment.deployed_by,
            "started_at": now,
            "entity_type": "deployment",
            # GSI attributes
            "GSI1PK": "deployment",
            "GSI1SK": now,
            "GSI3PK": f"status#{DeploymentStatus.PENDING.value}",
            "GSI3SK": now,
            "GSI4PK": f"architecture_id#{arch_id_str}",
            "GSI4SK": now,
        }

        # Store main item
        created = self._put_item(item)

        # Create architecture-deployment relationship item
        relationship_item = {
            "PK": f"ARCH#{arch_id_str}",
            "SK": f"DEPLOY#{deployment_id}",
            "deployment_id": deployment_id,
            "status": DeploymentStatus.PENDING.value,
            "entity_type": "arch_deployment",
        }
        self._put_item(relationship_item)

        return created

    def get(self, deployment_id: UUID) -> Optional[Dict[str, Any]]:
        """Get deployment by ID.

        Args:
            deployment_id: Deployment UUID

        Returns:
            Deployment item or None if not found
        """
        item = self._get_item(f"DEPLOY#{str(deployment_id)}", "METADATA")

        if not item:
            return None

        # Load large outputs from S3 if needed
        if "plan_output_s3_uri" in item:
            item["plan_output"] = self._load_large_item(item["plan_output_s3_uri"])
            del item["plan_output_s3_uri"]

        if "apply_output_s3_uri" in item:
            item["apply_output"] = self._load_large_item(item["apply_output_s3_uri"])
            del item["apply_output_s3_uri"]

        if "terraform_state_s3_uri" in item:
            item["terraform_state"] = self._load_large_item(item["terraform_state_s3_uri"])
            del item["terraform_state_s3_uri"]

        return item

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        architecture_id: Optional[UUID] = None,
        status: Optional[DeploymentStatus] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List deployments with pagination and filtering.

        Args:
            skip: Number of items to skip
            limit: Maximum items to return
            architecture_id: Optional filter by architecture
            status: Optional filter by status

        Returns:
            Tuple of (items list, total count)
        """
        if architecture_id:
            # Query GSI4 (by architecture)
            items, _ = self._query(
                key_condition=Key("GSI4PK").eq(f"architecture_id#{str(architecture_id)}"),
                index_name="GSI4",
                scan_index_forward=False  # DESC order (newest first)
            )
            # Apply status filter if provided
            if status:
                items = [item for item in items if item.get("status") == status.value]
        elif status:
            # Query GSI3 (by status)
            items, _ = self._query(
                key_condition=Key("GSI3PK").eq(f"status#{status.value}"),
                index_name="GSI3",
                scan_index_forward=False  # DESC order (newest first)
            )
        else:
            # Query GSI1 (all deployments)
            items, _ = self._query(
                key_condition=Key("GSI1PK").eq("deployment"),
                index_name="GSI1",
                scan_index_forward=False  # DESC order (newest first)
            )

        # Get total count before pagination
        total = len(items)

        # Apply skip/limit
        paginated_items = items[skip : skip + limit]

        # Load large outputs from S3 if needed (but only for listed items, not full data)
        # For list responses, we typically don't load large outputs to save bandwidth
        # If needed, caller should use get() for individual items

        return paginated_items, total

    def update_status(
        self,
        deployment_id: UUID,
        status: DeploymentStatus,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update deployment status.

        Args:
            deployment_id: Deployment UUID
            status: New status
            error_message: Optional error message (for FAILED status)

        Returns:
            Updated deployment or None if not found

        Raises:
            Exception: If update fails
        """
        # Get existing item to update GSI attributes
        existing = self._get_item(f"DEPLOY#{str(deployment_id)}", "METADATA")
        if not existing:
            return None

        # Prepare updates
        updates: Dict[str, Any] = {
            "status": status.value,
            "GSI3PK": f"status#{status.value}",
        }

        # Set completed_at for terminal states
        if status in [
            DeploymentStatus.SUCCESS,
            DeploymentStatus.FAILED,
            DeploymentStatus.DESTROYED,
            DeploymentStatus.CANCELLED
        ]:
            updates["completed_at"] = datetime.utcnow().isoformat()

        # Add error message if provided
        if error_message:
            updates["error_message"] = error_message

        # Update main item
        updated = self._update_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA",
            updates
        )

        # Update relationship item status
        arch_id = existing.get("architecture_id")
        if arch_id:
            self._update_item(
                f"ARCH#{arch_id}",
                f"DEPLOY#{str(deployment_id)}",
                {"status": status.value}
            )

        return updated

    def update_outputs(
        self,
        deployment_id: UUID,
        plan_output: Optional[str] = None,
        apply_output: Optional[str] = None,
        terraform_outputs: Optional[Dict[str, Any]] = None,
        generated_files: Optional[Dict[str, str]] = None,
        terraform_state: Optional[str] = None,
        terraform_version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update deployment outputs (always stored in S3 for large items).

        Args:
            deployment_id: Deployment UUID
            plan_output: Terraform plan output (stored in S3)
            apply_output: Terraform apply output (stored in S3)
            terraform_outputs: Terraform output values (JSON, stored in DynamoDB)
            generated_files: Generated Terraform files (JSON, stored in DynamoDB)
            terraform_state: Terraform state file (always stored in S3)
            terraform_version: Terraform version used

        Returns:
            Updated deployment or None if not found

        Raises:
            Exception: If update fails
        """
        updates: Dict[str, Any] = {}

        # Store plan_output in S3 (always)
        if plan_output is not None:
            s3_uri = self._store_large_item(
                plan_output,
                f"deployments/{str(deployment_id)}/plan_output.txt"
            )
            updates["plan_output_s3_uri"] = s3_uri

        # Store apply_output in S3 (always)
        if apply_output is not None:
            s3_uri = self._store_large_item(
                apply_output,
                f"deployments/{str(deployment_id)}/apply_output.txt"
            )
            updates["apply_output_s3_uri"] = s3_uri

        # Store terraform_state in S3 (always, can be large)
        if terraform_state is not None:
            s3_uri = self._store_large_item(
                terraform_state,
                f"deployments/{str(deployment_id)}/terraform.tfstate"
            )
            updates["terraform_state_s3_uri"] = s3_uri

        # Store terraform_outputs in DynamoDB (typically small JSON)
        if terraform_outputs is not None:
            updates["terraform_outputs"] = terraform_outputs

        # Store generated_files in DynamoDB (file paths/names, not contents)
        if generated_files is not None:
            updates["generated_files"] = generated_files

        # Store terraform_version
        if terraform_version is not None:
            updates["terraform_version"] = terraform_version

        if not updates:
            # No updates provided
            return self.get(deployment_id)

        # Perform update
        updated = self._update_item(
            f"DEPLOY#{str(deployment_id)}",
            "METADATA",
            updates
        )

        # Load large items for response
        if "plan_output_s3_uri" in updated:
            updated["plan_output"] = self._load_large_item(updated["plan_output_s3_uri"])
            del updated["plan_output_s3_uri"]

        if "apply_output_s3_uri" in updated:
            updated["apply_output"] = self._load_large_item(updated["apply_output_s3_uri"])
            del updated["apply_output_s3_uri"]

        if "terraform_state_s3_uri" in updated:
            updated["terraform_state"] = self._load_large_item(updated["terraform_state_s3_uri"])
            del updated["terraform_state_s3_uri"]

        return updated

    def delete(self, deployment_id: UUID) -> bool:
        """Delete deployment and related items.

        Args:
            deployment_id: Deployment UUID

        Returns:
            True if deleted successfully

        Note:
            Also deletes:
            - Architecture-Deployment relationship item
            - S3 objects (plan/apply outputs, terraform state)
        """
        deployment_id_str = str(deployment_id)

        # Get deployment to check for S3 objects and architecture_id
        deployment = self._get_item(f"DEPLOY#{deployment_id_str}", "METADATA")
        if not deployment:
            return False

        # Delete S3 objects
        if "plan_output_s3_uri" in deployment:
            self._delete_large_item(deployment["plan_output_s3_uri"])

        if "apply_output_s3_uri" in deployment:
            self._delete_large_item(deployment["apply_output_s3_uri"])

        if "terraform_state_s3_uri" in deployment:
            self._delete_large_item(deployment["terraform_state_s3_uri"])

        # Delete main deployment item
        success = self._delete_item(f"DEPLOY#{deployment_id_str}", "METADATA")

        if not success:
            return False

        # Delete relationship item
        arch_id = deployment.get("architecture_id")
        if arch_id:
            self._delete_item(f"ARCH#{arch_id}", f"DEPLOY#{deployment_id_str}")

        return True
