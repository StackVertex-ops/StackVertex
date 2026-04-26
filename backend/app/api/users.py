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
