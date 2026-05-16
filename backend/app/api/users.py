"""User Management API Endpoints.

User CRUD operations (Admin only).
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.user import UserRepository
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserPasswordUpdate,
    UserListResponse,
)
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Dependencies
# ============================================================================


def get_user_repository(table=Depends(get_dynamodb_table)) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(table=table)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=UserListResponse)
@limiter.limit("1000/minute" if settings.TESTING else "100/minute")
async def list_users(
    request: Request,  # Required for rate limiting
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """List all users (Admin only in production).

    SECURITY: Rate Limited - 100 requests/minute.
    For now: Any authenticated user can list users.
    TODO: Add admin role check.
    """
    items, total = user_repo.list(skip=skip, limit=limit)

    return UserListResponse(
        items=[UserResponse(**item) for item in items],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("1000/minute" if settings.TESTING else "100/minute")
async def get_user(
    request: Request,  # Required for rate limiting
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get user by ID - FIXED: Authorization check (IDOR prevention).

    SECURITY: Rate Limited - 100 requests/minute.
    SECURITY: Users können nur ihr eigenes Profil sehen.
    Ausnahme: SuperAdmins können alle Profile sehen.
    """
    # SECURITY FIX: Prevent IDOR - users can only view their own profile
    if str(user_id) != str(current_user["id"]):
        # Check if SuperAdmin (admins can view all profiles)
        if current_user.get("system_role") != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )

    user = user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**user)


@router.patch("/{user_id}", response_model=UserResponse)
@limiter.limit("1000/minute" if settings.TESTING else "50/minute")
async def update_user(
    request: Request,  # Required for rate limiting
    user_id: UUID,
    user_update: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Update user profile - FIXED: Authorization check.

    SECURITY: Rate Limited - 50 requests/minute.
    SECURITY: Users können nur ihr eigenes Profil ändern.
    Ausnahme: SuperAdmins können alle Profile ändern.
    """
    # SECURITY FIX: Check if user is updating their own profile or is SuperAdmin
    if str(user_id) != str(current_user["id"]):
        if current_user.get("system_role") != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )

    # Update user
    updated_user = user_repo.update(
        user_id,
        user_update.model_dump(exclude_unset=True)
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(
        f"User updated: {user_id}",
        extra={"user_id": str(user_id)}
    )

    return UserResponse(**updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("1000/minute" if settings.TESTING else "10/minute")
async def delete_user(
    request: Request,  # Required for rate limiting
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Delete user account (soft delete) - FIXED: Authorization check.

    SECURITY: Rate Limited - 10 requests/minute (destructive operation).
    SECURITY: Users können nur ihr eigenes Konto löschen.
    Ausnahme: SuperAdmins können alle Konten löschen.
    """
    # SECURITY FIX: Check if user is deleting their own account or is SuperAdmin
    if str(user_id) != str(current_user["id"]):
        if current_user.get("system_role") != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own account"
            )

    deleted = user_repo.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(
        f"User deleted: {user_id}",
        extra={"user_id": str(user_id)}
    )

    return None


@router.get("/{user_id}/organisations", response_model=list[dict])
@limiter.limit("1000/minute" if settings.TESTING else "100/minute")
async def get_user_organisations(
    request: Request,  # Required for rate limiting
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get all organisations user is member of - FIXED: Authorization check.

    SECURITY: Rate Limited - 100 requests/minute.
    SECURITY: Users können nur ihre eigenen Organisationen sehen.
    Ausnahme: SuperAdmins können alle Organisationen sehen.
    """
    # SECURITY FIX: Check if user is requesting their own organisations or is SuperAdmin
    if str(user_id) != str(current_user["id"]):
        if current_user.get("system_role") != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own organisations"
            )

    organisations = user_repo.get_organisations(user_id)

    return organisations


@router.patch("/{user_id}/password", response_model=dict)
@limiter.limit("1000/minute" if settings.TESTING else "10/minute")
async def update_password(
    request: Request,  # Required for rate limiting
    user_id: UUID,
    password_update: UserPasswordUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Update user password - FIXED: Authorization check.

    SECURITY: Rate Limited - 10 requests/minute (sensitive operation).
    SECURITY: Users können nur ihr eigenes Passwort ändern.
    SuperAdmins können NICHT fremde Passwörter ändern (würde altes PW benötigen).
    Requires current password for verification.
    """
    # SECURITY FIX: STRICT - Only user themselves can change password (not even SuperAdmin)
    if str(user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own password"
        )

    # Get user
    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not user_repo.verify_password(password_update.current_password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Hash new password (bcrypt has 72-byte limit, same as in UserRepository.create)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_truncated = password_update.new_password[:72] if len(password_update.new_password) > 72 else password_update.new_password
    new_password_hash = pwd_context.hash(password_truncated)

    # Update password
    updated_user = user_repo.update(user_id, {"password_hash": new_password_hash})

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

    logger.info(
        f"Password updated for user: {user_id}",
        extra={"user_id": str(user_id)}
    )

    return {"message": "Password updated successfully"}
