"""Deployment Manager.

Orchestriert Terraform Deployments.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any
from uuid import UUID

from app.config import settings
from app.core.terraform_generator import TerraformGenerator
from app.models.deployment import DeploymentStatus
from app.repositories.architecture import ArchitectureRepository
from app.repositories.deployment import DeploymentRepository
from app.schemas.deployment import DeploymentCreate
from app.services.background_tasks import task_runner
from app.services.deployment_progress import get_progress_info
from app.services.terraform_executor import TerraformExecutor

logger = logging.getLogger(__name__)

# Import WebSocket manager (lazy to avoid circular imports)
def get_ws_manager():
    """Lazy import of WebSocket manager."""
    from app.services.websocket_manager import ws_manager
    return ws_manager


class DeploymentManager:
    """Manages Terraform Deployments."""

    def __init__(self):
        """Initialisiert Deployment Manager."""
        self.workspace_dir = Path(settings.TERRAFORM_WORKSPACE_DIR)
        self.terraform_generator = TerraformGenerator()

    async def _send_websocket_update(self, deployment_id: UUID):
        """Send WebSocket status update for deployment.

        Args:
            deployment_id: Deployment ID
        """
        try:
            repo = DeploymentRepository()
            item = repo.get(deployment_id)
            if not item:
                return

            progress_info = get_progress_info(item)
            ws_manager = get_ws_manager()

            await ws_manager.send_status_update(
                deployment_id=deployment_id,
                status=item["status"],
                progress_percentage=progress_info["progress_percentage"],
                current_step=progress_info["current_step"],
                elapsed_seconds=progress_info["elapsed_seconds"],
                estimated_remaining_seconds=progress_info.get("estimated_remaining_seconds"),
                error_message=item.get("error_message")
            )
        except Exception as e:
            logger.warning(f"Failed to send WebSocket update: {e}")

    def start_deployment(
        self,
        repo: DeploymentRepository,
        architecture_id: UUID,
        deployed_by: str,
        aws_credentials: dict[str, str] | None = None
    ) -> UUID:
        """Startet ein neues Deployment im Hintergrund.

        Args:
            repo: DeploymentRepository instance
            architecture_id: Architecture ID
            deployed_by: User ID
            aws_credentials: AWS Credentials (access_key_id, secret_access_key, region)

        Returns:
            Deployment ID

        Raises:
            ValueError: Bei Fehlern
        """
        logger.info(f"Starting deployment for architecture {architecture_id}")

        # 1. Load Architecture
        arch_repo = ArchitectureRepository()
        architecture = arch_repo.get(architecture_id)
        if not architecture:
            raise ValueError(f"Architecture {architecture_id} not found")

        # 2. Create Deployment Record (status: PENDING)
        deployment_data = DeploymentCreate(
            architecture_id=architecture_id,
            deployed_by=deployed_by,
        )
        item = repo.create(deployment_data)

        deployment_id = UUID(item["id"])
        logger.info(f"Created deployment {deployment_id}, submitting to background queue")

        # 3. Submit to Background Task Queue
        task_runner.submit_task(
            task_id=deployment_id,
            func=self._execute_deployment,
            deployment_id=deployment_id,
            architecture_json=architecture["architecture_json"],
            aws_credentials=aws_credentials,
        )

        return deployment_id

    def _execute_deployment(
        self,
        deployment_id: UUID,
        architecture_json: dict[str, Any],
        aws_credentials: dict[str, str] | None = None
    ) -> None:
        """Führt Deployment im Hintergrund aus.

        Diese Methode läuft in einem separaten Thread.

        Args:
            deployment_id: Deployment ID
            architecture_json: Architecture JSON
            aws_credentials: AWS Credentials

        Raises:
            Exception: Bei Fehlern
        """
        # Create repository for this thread
        repo = DeploymentRepository()

        try:
            # 1. Generate Terraform Files
            logger.info(f"Generating Terraform for deployment {deployment_id}")
            repo.update_status(deployment_id, DeploymentStatus.GENERATING)

            terraform_project = self.terraform_generator.generate(
                architecture_json,
                validate=False  # Skip validation for now
            )

            # 2. Create Workspace Directory
            deployment_dir = self.workspace_dir / str(deployment_id)
            deployment_dir.mkdir(parents=True, exist_ok=True)

            # 3. Write Terraform Files
            terraform_project.write_to_directory(deployment_dir)

            # Save generated files to DynamoDB
            repo.update_outputs(
                deployment_id,
                generated_files={
                    filename: content
                    for filename, content in terraform_project.files.items()
                }
            )

            # 4. Setup Environment Variables (AWS Credentials)
            env_vars = {}
            if aws_credentials:
                if "access_key_id" in aws_credentials:
                    env_vars["AWS_ACCESS_KEY_ID"] = aws_credentials["access_key_id"]
                if "secret_access_key" in aws_credentials:
                    env_vars["AWS_SECRET_ACCESS_KEY"] = aws_credentials["secret_access_key"]
                if "region" in aws_credentials:
                    env_vars["AWS_DEFAULT_REGION"] = aws_credentials["region"]

            # 5. Initialize Terraform Executor
            executor = TerraformExecutor(
                working_dir=deployment_dir,
                terraform_binary=settings.TERRAFORM_BINARY,
                env_vars=env_vars,
            )

            # 6. Get Terraform Version
            version_result = executor.version()
            if version_result.success:
                terraform_version = version_result.stdout.split("\n")[0]
                repo.update_outputs(deployment_id, terraform_version=terraform_version)

            # 7. Terraform Init
            logger.info(f"Running terraform init for deployment {deployment_id}")
            repo.update_status(deployment_id, DeploymentStatus.INITIALIZING)

            init_result = executor.init(backend_config={"path": str(deployment_dir / "terraform.tfstate")})

            if not init_result.success:
                raise Exception(f"Terraform init failed: {init_result.stderr}")

            # 8. Terraform Validate
            validate_result = executor.validate()
            if not validate_result.success:
                logger.warning(f"Terraform validate failed: {validate_result.stderr}")
                # Continue anyway (validation might fail due to missing vars)

            # 9. Terraform Plan
            logger.info(f"Running terraform plan for deployment {deployment_id}")
            repo.update_status(deployment_id, DeploymentStatus.PLANNING)

            plan_result = executor.plan()

            if not plan_result.success:
                raise Exception(f"Terraform plan failed: {plan_result.stderr}")

            # Save plan output (S3 offload)
            repo.update_outputs(deployment_id, plan_output=plan_result.stdout)

            # 10. Terraform Apply
            logger.info(f"Running terraform apply for deployment {deployment_id}")
            repo.update_status(deployment_id, DeploymentStatus.APPLYING)

            apply_result = executor.apply(auto_approve=True)

            if not apply_result.success:
                raise Exception(f"Terraform apply failed: {apply_result.stderr}")

            # Save apply output (S3 offload)
            repo.update_outputs(deployment_id, apply_output=apply_result.stdout)

            # 11. Get Terraform Outputs
            output_result = executor.output(format="json")

            if output_result.success:
                try:
                    outputs = json.loads(output_result.stdout)
                    repo.update_outputs(deployment_id, terraform_outputs=outputs)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse terraform outputs as JSON")

            # 12. Backup Terraform State File (always to S3)
            state_file_path = deployment_dir / "terraform.tfstate"
            if state_file_path.exists():
                try:
                    state_content = state_file_path.read_text()
                    repo.update_outputs(deployment_id, terraform_state=state_content)
                    logger.info(f"Terraform state backed up to S3 for deployment {deployment_id}")
                except Exception as e:
                    logger.warning(f"Failed to backup terraform state: {e}")

            # 13. Mark Success
            repo.update_status(deployment_id, DeploymentStatus.SUCCESS)

            logger.info(f"Deployment {deployment_id} completed successfully")

        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}", exc_info=True)

            # Mark as failed
            repo.update_status(
                deployment_id,
                DeploymentStatus.FAILED,
                error_message=str(e)
            )

            raise

    def destroy_deployment(
        self,
        repo: DeploymentRepository,
        deployment_id: UUID,
        aws_credentials: dict[str, str] | None = None
    ) -> None:
        """Destroys Infrastructure von einem Deployment.

        Args:
            repo: DeploymentRepository instance
            deployment_id: Deployment ID
            aws_credentials: AWS Credentials

        Raises:
            ValueError: Bei Fehlern
        """
        logger.info(f"Destroying deployment {deployment_id}")

        # Load deployment
        item = repo.get(deployment_id)
        if not item:
            raise ValueError(f"Deployment {deployment_id} not found")

        if item["status"] != DeploymentStatus.SUCCESS.value:
            raise ValueError(f"Can only destroy successful deployments (current: {item['status']})")

        deployment_dir = self.workspace_dir / str(deployment_id)

        # Recreate workspace if needed
        if not deployment_dir.exists():
            logger.info(f"Recreating deployment directory: {deployment_dir}")
            deployment_dir.mkdir(parents=True, exist_ok=True)

            # Restore generated files from DynamoDB
            if item.get("generated_files"):
                for filename, content in item["generated_files"].items():
                    file_path = deployment_dir / filename
                    file_path.write_text(content)
                logger.info(f"Restored {len(item['generated_files'])} Terraform files")

            # Restore state file from S3 (loaded automatically by repo.get())
            if item.get("terraform_state"):
                state_file_path = deployment_dir / "terraform.tfstate"
                state_file_path.write_text(item["terraform_state"])
                logger.info("Restored Terraform state file from S3")
            else:
                logger.warning("No terraform state found in S3")

        try:
            # Setup environment
            env_vars = {}
            if aws_credentials:
                if "access_key_id" in aws_credentials:
                    env_vars["AWS_ACCESS_KEY_ID"] = aws_credentials["access_key_id"]
                if "secret_access_key" in aws_credentials:
                    env_vars["AWS_SECRET_ACCESS_KEY"] = aws_credentials["secret_access_key"]
                if "region" in aws_credentials:
                    env_vars["AWS_DEFAULT_REGION"] = aws_credentials["region"]

            # Initialize executor
            executor = TerraformExecutor(
                working_dir=deployment_dir,
                terraform_binary=settings.TERRAFORM_BINARY,
                env_vars=env_vars,
            )

            # Update status
            repo.update_status(deployment_id, DeploymentStatus.DESTROYING)

            # Run destroy
            destroy_result = executor.destroy(auto_approve=True)

            if not destroy_result.success:
                raise Exception(f"Terraform destroy failed: {destroy_result.stderr}")

            # Mark as destroyed
            repo.update_status(deployment_id, DeploymentStatus.DESTROYED)

            logger.info(f"Deployment {deployment_id} destroyed successfully")

        except Exception as e:
            logger.error(f"Failed to destroy deployment {deployment_id}: {e}", exc_info=True)

            repo.update_status(
                deployment_id,
                DeploymentStatus.FAILED,
                error_message=f"Destroy failed: {str(e)}"
            )

            raise

    def cancel_deployment(
        self,
        repo: DeploymentRepository,
        deployment_id: UUID
    ) -> bool:
        """Cancelt ein laufendes Deployment.

        Args:
            repo: DeploymentRepository instance
            deployment_id: Deployment ID

        Returns:
            True wenn gecancelt, False wenn nicht möglich

        Raises:
            ValueError: Bei Fehlern
        """
        logger.info(f"Cancelling deployment {deployment_id}")

        # Load deployment
        item = repo.get(deployment_id)
        if not item:
            raise ValueError(f"Deployment {deployment_id} not found")

        # Check if deployment is running
        status = DeploymentStatus(item["status"])
        is_running = status in [
            DeploymentStatus.PENDING,
            DeploymentStatus.GENERATING,
            DeploymentStatus.INITIALIZING,
            DeploymentStatus.PLANNING,
            DeploymentStatus.APPLYING,
            DeploymentStatus.DESTROYING,
        ]

        if not is_running:
            raise ValueError(
                f"Cannot cancel deployment in status {status}. "
                f"Only running deployments can be cancelled."
            )

        # Try to cancel background task
        cancelled = task_runner.cancel_task(deployment_id)

        if cancelled:
            # Mark as cancelled
            repo.update_status(
                deployment_id,
                DeploymentStatus.CANCELLED,
                error_message="Deployment cancelled by user"
            )
            logger.info(f"Deployment {deployment_id} cancelled successfully")
            return True
        else:
            logger.warning(
                f"Could not cancel background task for deployment {deployment_id}. "
                f"Task may have already completed or is not cancellable."
            )
            return False

    def retry_deployment(
        self,
        repo: DeploymentRepository,
        deployment_id: UUID,
        aws_credentials: dict[str, str] | None = None
    ) -> UUID:
        """Wiederholt ein fehlgeschlagenes Deployment.

        Args:
            repo: DeploymentRepository instance
            deployment_id: Original Deployment ID
            aws_credentials: Neue/Gleiche AWS Credentials (optional)

        Returns:
            Neue Deployment ID

        Raises:
            ValueError: Bei Fehlern
        """
        logger.info(f"Retrying deployment {deployment_id}")

        # Load original deployment
        original_item = repo.get(deployment_id)
        if not original_item:
            raise ValueError(f"Deployment {deployment_id} not found")

        # Check if deployment can be retried
        status = DeploymentStatus(original_item["status"])
        if status not in [
            DeploymentStatus.FAILED,
            DeploymentStatus.CANCELLED
        ]:
            raise ValueError(
                f"Cannot retry deployment in status {status}. "
                f"Only FAILED or CANCELLED deployments can be retried."
            )

        # Load architecture
        arch_repo = ArchitectureRepository()
        architecture_id = UUID(original_item["architecture_id"])
        architecture = arch_repo.get(architecture_id)
        if not architecture:
            raise ValueError(
                f"Architecture {architecture_id} not found"
            )

        # Start new deployment with same architecture
        logger.info(
            f"Creating new deployment for architecture {architecture_id} "
            f"(retry of {deployment_id})"
        )

        new_deployment_id = self.start_deployment(
            repo=repo,
            architecture_id=architecture_id,
            deployed_by=original_item["deployed_by"],
            aws_credentials=aws_credentials
        )

        logger.info(
            f"Retry deployment created: {new_deployment_id} "
            f"(original: {deployment_id})"
        )

        return new_deployment_id

    def cleanup_deployment(self, deployment_id: UUID) -> None:
        """Bereinigt Deployment Workspace.

        Args:
            deployment_id: Deployment ID
        """
        deployment_dir = self.workspace_dir / str(deployment_id)

        if deployment_dir.exists():
            try:
                shutil.rmtree(deployment_dir)
                logger.info(f"Cleaned up deployment directory: {deployment_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up deployment {deployment_id}: {e}")
