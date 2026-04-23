"""Audit Logger Service.

Zentrale Logging-Funktionen für Audit Trail.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Request

from app.repositories.audit_log import AuditLogRepository

logger = logging.getLogger(__name__)


def log_audit(
    user: str,
    action: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    request: Optional[Request] = None
):
    """Log audit event.

    Args:
        user: User identifier
        action: Action performed
        resource_type: Type of resource
        resource_id: Resource ID (optional)
        details: Additional details (optional)
        success: Whether action succeeded
        error_message: Error message if failed
        request: FastAPI Request object for IP/User-Agent extraction
    """
    try:
        # Extract request metadata
        ip_address = None
        user_agent = None

        if request:
            # Get client IP (handle proxy headers)
            ip_address = request.client.host if request.client else None
            if "x-forwarded-for" in request.headers:
                ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()

            # Get user agent
            user_agent = request.headers.get("user-agent")

        # Create audit log entry via repository
        repo = AuditLogRepository()
        repo.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success,
            error_message=error_message
        )

        logger.info(
            f"Audit: {user} performed {action} on {resource_type} "
            f"{resource_id} - {'success' if success else 'failed'}"
        )

    except Exception as e:
        logger.error(f"Failed to log audit event: {e}", exc_info=True)
        # Don't raise - audit logging failure shouldn't break app


def log_deployment_created(
    user: str,
    deployment_id: UUID,
    architecture_id: UUID,
    request: Optional[Request] = None
):
    """Log deployment creation.

    Args:
        user: User identifier
        deployment_id: Deployment ID
        architecture_id: Architecture ID
        request: Request object
    """
    log_audit(
        user=user,
        action="deploy_start",
        resource_type="deployment",
        resource_id=deployment_id,
        details={"architecture_id": str(architecture_id)},
        request=request
    )


def log_deployment_cancelled(
    user: str,
    deployment_id: UUID,
    request: Optional[Request] = None
):
    """Log deployment cancellation.

    Args:
        user: User identifier
        deployment_id: Deployment ID
        request: Request object
    """
    log_audit(
        user=user,
        action="deploy_cancel",
        resource_type="deployment",
        resource_id=deployment_id,
        request=request
    )


def log_deployment_retried(
    user: str,
    original_deployment_id: UUID,
    new_deployment_id: UUID,
    request: Optional[Request] = None
):
    """Log deployment retry.

    Args:
        user: User identifier
        original_deployment_id: Original deployment ID
        new_deployment_id: New deployment ID
        request: Request object
    """
    log_audit(
        user=user,
        action="deploy_retry",
        resource_type="deployment",
        resource_id=new_deployment_id,
        details={
            "original_deployment_id": str(original_deployment_id)
        },
        request=request
    )


def log_deployment_destroyed(
    user: str,
    deployment_id: UUID,
    request: Optional[Request] = None
):
    """Log deployment destruction.

    Args:
        user: User identifier
        deployment_id: Deployment ID
        request: Request object
    """
    log_audit(
        user=user,
        action="deploy_destroy",
        resource_type="deployment",
        resource_id=deployment_id,
        request=request
    )


def log_architecture_created(
    user: str,
    architecture_id: UUID,
    request: Optional[Request] = None
):
    """Log architecture creation.

    Args:
        user: User identifier
        architecture_id: Architecture ID
        request: Request object
    """
    log_audit(
        user=user,
        action="architecture_create",
        resource_type="architecture",
        resource_id=architecture_id,
        request=request
    )


def log_architecture_updated(
    user: str,
    architecture_id: UUID,
    new_version_id: UUID,
    request: Optional[Request] = None
):
    """Log architecture update.

    Args:
        user: User identifier
        architecture_id: Original architecture ID
        new_version_id: New version ID
        request: Request object
    """
    log_audit(
        user=user,
        action="architecture_update",
        resource_type="architecture",
        resource_id=new_version_id,
        details={"original_id": str(architecture_id)},
        request=request
    )


def log_architecture_deleted(
    user: str,
    architecture_id: UUID,
    request: Optional[Request] = None
):
    """Log architecture deletion.

    Args:
        user: User identifier
        architecture_id: Architecture ID
        request: Request object
    """
    log_audit(
        user=user,
        action="architecture_delete",
        resource_type="architecture",
        resource_id=architecture_id,
        request=request
    )
