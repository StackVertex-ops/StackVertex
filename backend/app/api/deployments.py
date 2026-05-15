"""Deployment API Endpoints.

REST API für Deployment Management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.repositories.deployment import DeploymentRepository
from app.models.deployment import DeploymentStatus
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentResponse,
    DeploymentListResponse,
    DeploymentStatusResponse,
)
from app.services.deployment_manager import DeploymentManager
from app.services.deployment_progress import get_progress_info

logger = logging.getLogger(__name__)

router = APIRouter()
deployment_manager = DeploymentManager()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# Dependency injection for DeploymentRepository
def get_deployment_repo() -> DeploymentRepository:
    """Get DeploymentRepository instance."""
    return DeploymentRepository()


@router.post(
    "/architectures/{architecture_id}/deploy",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy Architecture",
    description="Startet Deployment einer Architecture mit Terraform",
    responses={
        201: {"description": "Deployment started"},
        404: {"description": "Architecture not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Deployment failed"},
    },
)
@limiter.limit("1000/minute" if settings.TESTING else "10/minute")
async def deploy_architecture(
    request: Request,
    architecture_id: UUID,
    deployment_data: DeploymentCreate,
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> DeploymentResponse:
    """Deployed eine Architecture.

    Args:
        architecture_id: Architecture ID
        deployment_data: Deployment Configuration
        repo: DeploymentRepository

    Returns:
        DeploymentResponse

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # Start deployment (DeploymentManager will be updated to use repo later)
        deployment_id = deployment_manager.start_deployment(
            repo,
            architecture_id=architecture_id,
            deployed_by=deployment_data.deployed_by,
            aws_credentials=deployment_data.aws_credentials,
        )

        # Load deployment
        item = repo.get(deployment_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Deployment created but not found"
            )

        logger.info(f"Deployment {deployment_id} started")
        return DeploymentResponse(**item)

    except ValueError as e:
        logger.error(f"Deployment validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}",
        )


@router.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Deployment Status",
    description="Holt Deployment Status mit Progress Tracking",
    responses={
        200: {"description": "Deployment found"},
        404: {"description": "Deployment not found"},
    },
)
async def get_deployment_status(
    deployment_id: UUID,
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> DeploymentStatusResponse:
    """Holt Deployment Details mit Progress Informationen.

    Args:
        deployment_id: Deployment ID
        repo: DeploymentRepository

    Returns:
        DeploymentStatusResponse mit progress_percentage, current_step, elapsed_seconds

    Raises:
        HTTPException: 404 wenn nicht gefunden
    """
    item = repo.get(deployment_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    # Calculate progress information (get_progress_info expects dict-like object)
    progress_info = get_progress_info(item)

    # Build response
    return DeploymentStatusResponse(
        id=item["id"],
        architecture_id=item["architecture_id"],
        status=DeploymentStatus(item["status"]),
        deployed_by=item["deployed_by"],
        terraform_version=item.get("terraform_version"),
        error_message=item.get("error_message"),
        started_at=item.get("started_at"),
        completed_at=item.get("completed_at"),
        **progress_info
    )


@router.get(
    "/deployments",
    response_model=DeploymentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Deployments",
    description="Listet Deployments mit Filtering",
    responses={
        200: {"description": "Deployments listed"},
    },
)
async def list_deployments(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(100, ge=1, le=1000, description="Limit"),
    architecture_id: Optional[UUID] = Query(None, description="Filter by Architecture"),
    status_filter: Optional[DeploymentStatus] = Query(None, description="Filter by Status", alias="status"),
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> DeploymentListResponse:
    """Listet Deployments.

    Args:
        skip: Offset
        limit: Limit
        architecture_id: Filter by Architecture (optional)
        status_filter: Filter by Status (optional)
        repo: DeploymentRepository

    Returns:
        DeploymentListResponse
    """
    items, total = repo.list(
        skip=skip,
        limit=limit,
        architecture_id=architecture_id,
        status=status_filter,
    )

    return DeploymentListResponse(
        items=[DeploymentResponse(**item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.delete(
    "/deployments/{deployment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Destroy Deployment",
    description="Destroys Infrastructure und löscht Deployment",
    responses={
        204: {"description": "Deployment destroyed"},
        404: {"description": "Deployment not found"},
        500: {"description": "Destroy failed"},
    },
)
async def destroy_deployment_endpoint(
    deployment_id: UUID,
    aws_credentials: Optional[dict] = Body(None, description="AWS Credentials"),
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> None:
    """Destroys Infrastructure.

    Args:
        deployment_id: Deployment ID
        aws_credentials: AWS Credentials (optional)
        repo: DeploymentRepository

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # Destroy infrastructure
        deployment_manager.destroy_deployment(
            repo,
            deployment_id=deployment_id,
            aws_credentials=aws_credentials,
        )

        logger.info(f"Deployment {deployment_id} destroyed")
        return None

    except ValueError as e:
        logger.error(f"Destroy validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Destroy failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Destroy failed: {str(e)}",
        )


@router.get(
    "/deployments/{deployment_id}/logs",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get Deployment Logs",
    description="Holt Deployment Logs (plan + apply output)",
    responses={
        200: {"description": "Logs retrieved"},
        404: {"description": "Deployment not found"},
    },
)
async def get_deployment_logs(
    deployment_id: UUID,
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> dict:
    """Holt Deployment Logs.

    Args:
        deployment_id: Deployment ID
        repo: DeploymentRepository

    Returns:
        Dict mit plan_output und apply_output

    Raises:
        HTTPException: 404 wenn nicht gefunden
    """
    item = repo.get(deployment_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    return {
        "deployment_id": str(deployment_id),
        "plan_output": item.get("plan_output"),
        "apply_output": item.get("apply_output"),
        "error_message": item.get("error_message"),
    }


@router.post(
    "/deployments/{deployment_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel Deployment",
    description="Cancelt ein laufendes Deployment",
    responses={
        200: {"description": "Deployment cancelled"},
        404: {"description": "Deployment not found"},
        400: {"description": "Deployment cannot be cancelled"},
    },
)
async def cancel_deployment_endpoint(
    deployment_id: UUID,
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> dict:
    """Cancelt ein laufendes Deployment.

    Args:
        deployment_id: Deployment ID
        repo: DeploymentRepository

    Returns:
        Success message

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        cancelled = deployment_manager.cancel_deployment(repo, deployment_id)

        if cancelled:
            logger.info(f"Deployment {deployment_id} cancelled via API")
            return {
                "deployment_id": str(deployment_id),
                "status": "cancelled",
                "message": "Deployment cancelled successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment could not be cancelled (may have already completed)"
            )

    except ValueError as e:
        logger.error(f"Cancel deployment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Cancel failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cancel failed: {str(e)}",
        )


@router.post(
    "/deployments/{deployment_id}/retry",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Retry Deployment",
    description="Wiederholt ein fehlgeschlagenes Deployment",
    responses={
        201: {"description": "New deployment created"},
        404: {"description": "Deployment not found"},
        400: {"description": "Deployment cannot be retried"},
    },
)
async def retry_deployment_endpoint(
    deployment_id: UUID,
    aws_credentials: Optional[dict] = Body(None, description="AWS Credentials (optional)"),
    repo: DeploymentRepository = Depends(get_deployment_repo),
) -> DeploymentResponse:
    """Wiederholt ein fehlgeschlagenes Deployment.

    Args:
        deployment_id: Original Deployment ID
        aws_credentials: Neue AWS Credentials (optional)
        repo: DeploymentRepository

    Returns:
        Neues Deployment

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        new_deployment_id = deployment_manager.retry_deployment(
            repo,
            deployment_id=deployment_id,
            aws_credentials=aws_credentials
        )

        # Load new deployment
        new_item = repo.get(new_deployment_id)

        if not new_item:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Retry deployment created but not found"
            )

        logger.info(
            f"Deployment {deployment_id} retried successfully, "
            f"new deployment: {new_deployment_id}"
        )

        return DeploymentResponse(**new_item)

    except ValueError as e:
        logger.error(f"Retry deployment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Retry failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry failed: {str(e)}",
        )
