"""User Management API Endpoints.

User CRUD operations (Admin only).
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

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
async def list_users(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """List all users (Admin only in production).

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
async def get_user(
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get user by ID.

    Users can view their own profile + other users (public info only).
    """
    user = user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Update user profile.

    Users can only update their own profile.
    """
    # Check if user is updating their own profile
    if str(user_id) != current_user["id"]:
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
async def delete_user(
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Delete user account (soft delete).

    Users can only delete their own account.
    """
    # Check if user is deleting their own account
    if str(user_id) != current_user["id"]:
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
async def get_user_organisations(
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get all organisations user is member of.

    Users can only view their own organisations.
    """
    # Check if user is requesting their own organisations
    if str(user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own organisations"
        )

    organisations = user_repo.get_organisations(user_id)

    return organisations


@router.patch("/{user_id}/password", response_model=dict)
async def update_password(
    user_id: UUID,
    password_update: UserPasswordUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Update user password.

    Users can only update their own password.
    Requires current password for verification.
    """
    # Check if user is updating their own password
    if str(user_id) != current_user["id"]:
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

    # Hash new password (using passlib directly like in UserRepository.create)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    new_password_hash = pwd_context.hash(password_update.new_password)

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
