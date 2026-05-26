"""ECS Task Worker für Terraform Deployments.

Läuft on-demand als ECS Fargate Spot Task.
Führt lange Terraform Deployments (>10 Min) aus.
Stoppt automatisch nach Completion.
"""

import asyncio
import json
import logging
import os
import sys
from uuid import UUID

# Logger konfigurieren (CloudWatch Logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def send_progress_update(
    deployment_id: str,
    message: str,
    progress: int,
    error: bool = False
) -> None:
    """Sendet Progress Update via WebSocket.

    Args:
        deployment_id: Deployment ID
        message: Status Message
        progress: Progress Percentage (0-100)
        error: Is Error Message
    """
    try:
        from app.services.websocket_manager import ws_manager

        # WebSocket API Endpoint aus Environment
        websocket_endpoint = os.environ.get('WEBSOCKET_API_ENDPOINT', '')

        if not websocket_endpoint:
            logger.warning("WEBSOCKET_API_ENDPOINT not set - skipping progress update")
            return

        # TODO: Implement API Gateway Management API for WebSocket postToConnection
        # For now: just log
        logger.info(f"Progress Update: {message} ({progress}%)")

    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")
        # Non-critical - don't fail deployment


async def main():
    """Main Worker Function."""
    # Environment Variables
    deployment_id = os.environ.get('DEPLOYMENT_ID')
    architecture_json = os.environ.get('ARCHITECTURE_JSON')
    user_id = os.environ.get('USER_ID')
    credential_id = os.environ.get('CREDENTIAL_ID')

    # Validierung
    if not all([deployment_id, architecture_json, user_id, credential_id]):
        logger.error("Missing required environment variables")
        logger.error(f"DEPLOYMENT_ID: {deployment_id}")
        logger.error(f"ARCHITECTURE_JSON: {'set' if architecture_json else 'missing'}")
        logger.error(f"USER_ID: {user_id}")
        logger.error(f"CREDENTIAL_ID: {credential_id}")
        sys.exit(1)

    logger.info(f"Starting deployment {deployment_id} for user {user_id}")

    # Parse Architecture JSON
    try:
        architecture = json.loads(architecture_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid ARCHITECTURE_JSON: {e}")
        sys.exit(1)

    # Import Services
    from app.services.deployment_executor import DeploymentExecutor
    from app.repositories.deployment import DeploymentRepository

    try:
        # Deployment Executor initialisieren
        executor = DeploymentExecutor()
        repo = DeploymentRepository()

        # Update Status: in_progress
        await send_progress_update(deployment_id, "Starting deployment...", 5)
        repo.update_status(
            deployment_id=UUID(deployment_id),
            status='in_progress',
            error_message=None
        )

        # Execute Deployment
        logger.info("Executing Terraform deployment...")
        await send_progress_update(deployment_id, "Initializing Terraform...", 10)

        result = await executor.deploy(
            deployment_id=deployment_id,
            architecture_json=architecture,
            credential_id=credential_id,
            org_id=user_id  # TODO: use actual org_id
        )

        # Success
        logger.info("Deployment completed successfully")
        await send_progress_update(deployment_id, "Deployment complete!", 100)

        repo.update_status(
            deployment_id=UUID(deployment_id),
            status='completed',
            error_message=None
        )

        logger.info(f"Deployment {deployment_id} completed successfully")
        sys.exit(0)

    except Exception as e:
        # Failure
        logger.error(f"Deployment failed: {e}", exc_info=True)
        await send_progress_update(
            deployment_id,
            f"Deployment failed: {str(e)}",
            100,
            error=True
        )

        # Update Status
        try:
            repo = DeploymentRepository()
            repo.update_status(
                deployment_id=UUID(deployment_id),
                status='failed',
                error_message=str(e)
            )
        except Exception as update_error:
            logger.error(f"Failed to update deployment status: {update_error}")

        logger.error(f"Deployment {deployment_id} failed")
        sys.exit(1)


if __name__ == '__main__':
    logger.info("ECS Deployment Worker starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")

    # Run async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
