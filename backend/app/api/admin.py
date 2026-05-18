"""Admin API Endpoints - SuperAdmin only.

System-level administration endpoints für:
- User Management (alle User, Status ändern, SystemRole ändern)
- Organisation Management (alle Orgs, Mitglieder, Architectures)
- Audit Logs (mit erweiterten Filters)
- User Impersonation (für Support-Cases)
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from app.api.auth import (
    get_current_superadmin,
    get_current_support,
    get_current_auditor,
    get_user_repository,
    create_access_token,
)
from app.db.dynamodb import get_dynamodb_table
from app.models.user import SystemRole, UserStatus
from app.repositories.user import UserRepository
from app.repositories.organisation import OrganisationRepository
from app.repositories.architecture import ArchitectureRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.user import UserResponse
from app.schemas.organisation import OrganisationResponse
from app.services.audit_logger import log_audit
from app.utils.password import generate_secure_password

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


def get_organisation_repository(table=Depends(get_dynamodb_table)) -> OrganisationRepository:
    """Get OrganisationRepository instance."""
    return OrganisationRepository(table=table)


def get_architecture_repository(table=Depends(get_dynamodb_table)) -> ArchitectureRepository:
    """Get ArchitectureRepository instance."""
    return ArchitectureRepository(table=table, s3_storage=None)


def get_audit_log_repository(table=Depends(get_dynamodb_table)) -> AuditLogRepository:
    """Get AuditLogRepository instance."""
    return AuditLogRepository(table=table, s3_storage=None)


# ============================================================================
# Request/Response Schemas
# ============================================================================


class UserStatusUpdateRequest(BaseModel):
    """Request body for updating user status."""

    status: UserStatus = Field(..., description="New user status")
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for status change (required for audit)")


class SystemRoleUpdateRequest(BaseModel):
    """Request body for updating system role."""

    system_role: SystemRole = Field(..., description="New system role")
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for role change (required for audit)")


class ImpersonationResponse(BaseModel):
    """Response for user impersonation."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    impersonated_user_email: str
    impersonated_user_id: str
    warning: str = "This token expires in 15 minutes. All actions are logged."


class AdminUserDetailResponse(UserResponse):
    """Extended User Response für Admins (enthält mehr Details)."""

    password_hash: str = Field(..., description="Password hash (for verification, never exposed to client)")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    last_login_ip: Optional[str] = Field(None, description="Last login IP address")


class PasswordResetResponse(BaseModel):
    """Response for password reset."""

    user_id: str
    email: str
    new_password: str
    message: str


class StatisticsResponse(BaseModel):
    """Response for platform statistics."""

    users: dict
    organisations: dict
    architectures: dict
    timestamp: str


# ============================================================================
# User Management (SuperAdmin only)
# ============================================================================


@router.get("/admin/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """List ALL users across ALL organisations.

    SuperAdmin only. Logs access to audit trail.

    Args:
        skip: Pagination offset
        limit: Max items to return
        current_admin: Current SuperAdmin user
        user_repo: UserRepository

    Returns:
        List of users
    """
    # Log admin action (audit trail)
    log_audit(
        user=current_admin["email"],
        action="admin.list_users",
        resource_type="user",
        details={"skip": skip, "limit": limit}
    )

    users, total = user_repo.list(skip=skip, limit=limit)

    logger.info(
        f"SuperAdmin {current_admin['email']} listed {len(users)} users (total: {total})",
        extra={"admin_id": current_admin["id"], "total": total}
    )

    return [UserResponse(**user) for user in users]


@router.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user_as_admin(
    user_id: UUID,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Get ANY user's details.

    SuperAdmin only. Logs access to audit trail.

    Args:
        user_id: User ID
        current_admin: Current SuperAdmin user
        user_repo: UserRepository

    Returns:
        User details

    Raises:
        HTTPException: 404 if user not found
    """
    # Log admin action
    log_audit(
        user=current_admin["email"],
        action="admin.view_user",
        resource_type="user",
        resource_id=user_id,
        details={"reason": "admin access"}
    )

    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(
        f"SuperAdmin {current_admin['email']} viewed user {user_id}",
        extra={"admin_id": current_admin["id"], "viewed_user_id": str(user_id)}
    )

    return UserResponse(**user)


@router.patch("/admin/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: UUID,
    request: UserStatusUpdateRequest,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Activate/Deactivate/Suspend user account.

    SuperAdmin only. Requires reason for audit trail.

    Args:
        user_id: User ID
        request: Status update request with reason
        current_admin: Current SuperAdmin user
        user_repo: UserRepository

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found
    """
    # Get user first
    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log admin action
    log_audit(
        user=current_admin["email"],
        action="admin.update_user_status",
        resource_type="user",
        resource_id=user_id,
        details={
            "old_status": user.get("status"),
            "new_status": request.status.value,
            "reason": request.reason
        }
    )

    # Update status
    updated_user = user_repo.update_status(user_id, request.status)

    logger.warning(
        f"SuperAdmin {current_admin['email']} changed user {user_id} status to {request.status.value}",
        extra={
            "admin_id": current_admin["id"],
            "user_id": str(user_id),
            "new_status": request.status.value,
            "reason": request.reason
        }
    )

    return UserResponse(**updated_user)


@router.patch("/admin/users/{user_id}/system-role", response_model=UserResponse)
async def update_user_system_role(
    user_id: UUID,
    request: SystemRoleUpdateRequest,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Update user system role (e.g., promote to SuperAdmin).

    SuperAdmin only. Requires reason for audit trail.

    CRITICAL: This allows creating new SuperAdmins!

    Args:
        user_id: User ID
        request: System role update request with reason
        current_admin: Current SuperAdmin user
        user_repo: UserRepository

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found
    """
    # Get user first
    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log admin action (CRITICAL severity if promoting to SuperAdmin)
    severity = "CRITICAL" if request.system_role == SystemRole.SUPERADMIN else "INFO"
    log_audit(
        user=current_admin["email"],
        action="admin.update_system_role",
        resource_type="user",
        resource_id=user_id,
        details={
            "old_role": user.get("system_role", SystemRole.USER.value),
            "new_role": request.system_role.value,
            "reason": request.reason
        },
        success=True
    )

    # Update system role
    updated_user = user_repo.update_system_role(user_id, request.system_role)

    logger.critical(
        f"SuperAdmin {current_admin['email']} changed user {user_id} system role to {request.system_role.value}",
        extra={
            "admin_id": current_admin["id"],
            "user_id": str(user_id),
            "new_role": request.system_role.value,
            "reason": request.reason
        }
    )

    return UserResponse(**updated_user)


@router.post("/admin/users/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    user_id: UUID,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Reset user password (SuperAdmin only).

    Generates new random secure password and returns it.
    User should be notified via email (future implementation).

    Args:
        user_id: User ID
        current_admin: Current SuperAdmin user
        user_repo: UserRepository

    Returns:
        New password and user info

    Raises:
        HTTPException: 404 if user not found
    """
    # Get user first
    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate secure password (16 characters)
    new_password = generate_secure_password(length=16)

    # Update user password
    success = user_repo.update_password(user_id, new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")

    # Log admin action (CRITICAL severity)
    log_audit(
        user=current_admin["email"],
        action="admin.reset_password",
        resource_type="user",
        resource_id=user_id,
        details={
            "target_user_email": user["email"],
            "reset_by": current_admin["email"]
        },
        success=True
    )

    logger.critical(
        f"SuperAdmin {current_admin['email']} reset password for user {user_id}",
        extra={
            "admin_id": current_admin["id"],
            "target_user_id": str(user_id),
            "target_user_email": user["email"]
        }
    )

    return PasswordResetResponse(
        user_id=str(user_id),
        email=user["email"],
        new_password=new_password,
        message="Password reset successful. User should change this password after login."
    )


# ============================================================================
# Organisation Management (SuperAdmin only)
# ============================================================================


@router.get("/admin/organisations", response_model=List[OrganisationResponse])
async def list_all_organisations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
):
    """List ALL organisations.

    SuperAdmin only. Logs access to audit trail.

    Args:
        skip: Pagination offset
        limit: Max items to return
        current_admin: Current SuperAdmin user
        org_repo: OrganisationRepository

    Returns:
        List of organisations
    """
    # Log admin action
    log_audit(
        user=current_admin["email"],
        action="admin.list_organisations",
        resource_type="organisation"
    )

    orgs, total = org_repo.list_all(skip=skip, limit=limit)

    logger.info(
        f"SuperAdmin {current_admin['email']} listed {len(orgs)} organisations (total: {total})",
        extra={"admin_id": current_admin["id"], "total": total}
    )

    return [OrganisationResponse(**org) for org in orgs]


@router.get("/admin/organisations/{org_id}/architectures")
async def get_organisation_architectures(
    org_id: UUID,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    arch_repo: ArchitectureRepository = Depends(get_architecture_repository),
):
    """Get ALL architectures of an organisation.

    SuperAdmin only. Logs access to audit trail.

    Findet alle Architectures, indem es die Organisation Members durchsucht
    und deren Architectures aggregiert.

    Args:
        org_id: Organisation ID
        current_admin: Current SuperAdmin user
        org_repo: OrganisationRepository
        arch_repo: ArchitectureRepository

    Returns:
        List of architectures

    Raises:
        HTTPException: 404 if organisation not found
    """
    # Check if organisation exists
    org = org_repo.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Log admin action
    log_audit(
        user=current_admin["email"],
        action="admin.view_org_architectures",
        resource_type="organisation",
        resource_id=org_id
    )

    # Get all members of the organisation
    members = org_repo.get_members(org_id)

    # Collect all architectures from all members
    all_architectures = []
    for member in members:
        user_id = member.get("user_id")
        if user_id:
            # Get architectures for this user
            user_archs, _ = arch_repo.list(skip=0, limit=1000, owner=user_id)
            all_architectures.extend(user_archs)

    logger.info(
        f"SuperAdmin {current_admin['email']} viewed {len(all_architectures)} architectures for org {org_id}",
        extra={"admin_id": current_admin["id"], "org_id": str(org_id)}
    )

    return all_architectures


# ============================================================================
# Audit Logs (Support & SuperAdmin & Auditor)
# ============================================================================


@router.get("/admin/audit-logs")
async def get_audit_logs(
    user: Optional[str] = Query(None, description="Filter by user email"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[UUID] = Query(None, description="Filter by resource ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Annotated[dict, Depends(get_current_auditor)] = None,
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
):
    """Query audit logs.

    Support, Auditor & SuperAdmin. Logs own access to audit logs.

    Args:
        user: Filter by user email
        action: Filter by action
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_date: Filter by start date
        end_date: Filter by end date
        skip: Pagination offset
        limit: Max items to return
        current_user: Current authenticated user (Support/Auditor/SuperAdmin)
        audit_repo: AuditLogRepository

    Returns:
        List of audit logs
    """
    # Log audit access (meta: audit of audit access)
    log_audit(
        user=current_user["email"],
        action="admin.view_audit_logs",
        resource_type="audit_log",
        details={
            "filters": {
                "user": user,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None
            }
        }
    )

    logs, total = audit_repo.list(
        skip=skip,
        limit=limit,
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date
    )

    logger.info(
        f"{current_user.get('system_role', 'user')} {current_user['email']} queried {len(logs)} audit logs",
        extra={"user_id": current_user["id"], "total": total}
    )

    return {
        "items": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ============================================================================
# User Impersonation (SuperAdmin only - DANGEROUS!)
# ============================================================================


@router.post("/admin/impersonate/{user_id}", response_model=ImpersonationResponse)
async def impersonate_user(
    user_id: UUID,
    reason: str = Body(..., min_length=10, max_length=500, embed=True, description="Required: Why impersonating?"),
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Generate token for another user (impersonation).

    DANGEROUS: Use only for debugging customer issues.
    Requires reason, logs to audit trail with CRITICAL severity.

    Token is valid for 15 minutes only.

    Args:
        user_id: User ID to impersonate
        reason: Reason for impersonation (required, min 10 chars)
        current_admin: Current SuperAdmin user
        user_repo: UserRepository

    Returns:
        Impersonation token response

    Raises:
        HTTPException: 404 if user not found
    """
    target_user = user_repo.get(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # CRITICAL: Log impersonation attempt (triggers alerts!)
    log_audit(
        user=current_admin["email"],
        action="admin.impersonate_user",
        resource_type="user",
        resource_id=user_id,
        details={
            "impersonated_user_email": target_user["email"],
            "reason": reason
        },
        success=True
    )

    # Create short-lived token (15 minutes)
    # Note: create_access_token uses ACCESS_TOKEN_EXPIRE_MINUTES from settings (15 min)
    token = create_access_token(
        data={
            "sub": str(user_id),
            "email": target_user["email"],
            "impersonated_by": str(current_admin["id"])
        }
    )

    logger.critical(
        f"SuperAdmin {current_admin['email']} impersonated user {target_user['email']}",
        extra={
            "admin_id": current_admin["id"],
            "impersonated_user_id": str(user_id),
            "impersonated_user_email": target_user["email"],
            "reason": reason
        }
    )

    return ImpersonationResponse(
        access_token=token,
        expires_in=900,  # 15 minutes
        impersonated_user_email=target_user["email"],
        impersonated_user_id=str(user_id)
    )


# ============================================================================
# System Health & Stats (Support & SuperAdmin)
# ============================================================================


@router.get("/admin/stats")
async def get_system_stats(
    current_user: Annotated[dict, Depends(get_current_support)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
):
    """Get system statistics.

    Support & SuperAdmin. Shows high-level metrics.

    Args:
        current_user: Current authenticated user (Support/SuperAdmin)
        user_repo: UserRepository
        org_repo: OrganisationRepository
        audit_repo: AuditLogRepository

    Returns:
        System statistics
    """
    # Get counts
    users, user_count = user_repo.list(skip=0, limit=1)  # Just get count
    orgs, org_count = org_repo.list_all(skip=0, limit=1)
    audit_stats = audit_repo.get_stats()

    return {
        "users": {
            "total": user_count,
            "active": user_count  # TODO: Filter by status
        },
        "organisations": {
            "total": org_count
        },
        "audit": audit_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/admin/statistics", response_model=StatisticsResponse)
async def get_platform_statistics(
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    arch_repo: ArchitectureRepository = Depends(get_architecture_repository),
):
    """Get detailed platform statistics (SuperAdmin only).

    Returns comprehensive metrics about users, organisations, and architectures.

    Args:
        current_admin: Current SuperAdmin user
        user_repo: UserRepository
        org_repo: OrganisationRepository
        arch_repo: ArchitectureRepository

    Returns:
        Platform statistics
    """
    # Log admin action
    log_audit(
        user=current_admin["email"],
        action="admin.view_statistics",
        resource_type="statistics"
    )

    # Get all users to count by status
    all_users, total_users = user_repo.list(skip=0, limit=10000)
    active_users = len([u for u in all_users if u.get("status") == UserStatus.ACTIVE.value])
    suspended_users = total_users - active_users

    # Get organisations count
    _, total_orgs = org_repo.list_all(skip=0, limit=1)

    # Get all architectures to count by status
    # Note: arch_repo.list() nimmt owner parameter, aber wir brauchen ALLE
    # Workaround: Sammle von allen Users
    all_architectures = []
    for user in all_users:
        user_archs, _ = arch_repo.list(skip=0, limit=1000, owner=user.get("id"))
        all_architectures.extend(user_archs)

    total_archs = len(all_architectures)
    deployed_archs = len([a for a in all_architectures if a.get("status") == "deployed"])
    draft_archs = total_archs - deployed_archs

    logger.info(
        f"SuperAdmin {current_admin['email']} viewed platform statistics",
        extra={
            "admin_id": current_admin["id"],
            "stats": {
                "users": total_users,
                "orgs": total_orgs,
                "architectures": total_archs
            }
        }
    )

    return StatisticsResponse(
        users={
            "total": total_users,
            "active": active_users,
            "suspended": suspended_users
        },
        organisations={
            "total": total_orgs
        },
        architectures={
            "total": total_archs,
            "deployed": deployed_archs,
            "draft": draft_archs
        },
        timestamp=datetime.utcnow().isoformat()
    )
