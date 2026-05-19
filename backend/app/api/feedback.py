"""Feedback API Endpoints.

Public feedback submission + Admin management.
"""

import logging
from typing import Annotated, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Query,
    Body,
)
from pydantic import BaseModel, Field, EmailStr

from app.api.auth import get_current_user, get_current_superadmin
from app.schemas.user import UserResponse
from app.services.feedback_service import FeedbackService, get_feedback_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class FeedbackSubmitRequest(BaseModel):
    """Request body for submitting feedback."""

    type: str = Field(..., description="Feedback type: bug, feature, feedback, other")
    title: str = Field(..., min_length=5, max_length=200, description="Feedback title")
    description: str = Field(..., min_length=10, max_length=1000, description="Feedback description")
    email: EmailStr | None = Field(None, description="Optional email for followup")
    url: str | None = Field(None, description="URL where feedback was submitted")
    user_agent: str | None = Field(None, description="Browser user agent")
    browser_info: dict | None = Field(None, description="Parsed browser info")


class FeedbackResponse(BaseModel):
    """Response model for feedback."""

    feedback_id: str
    type: str
    status: str
    title: str
    description: str
    email: str | None
    url: str | None
    user_agent: str | None
    browser_info: dict | None
    screenshot_s3_key: str | None
    screenshot_url: str | None
    is_resolved: bool
    resolved_at: str | None
    resolved_by: str | None
    notes: List[dict]
    created_at: str
    updated_at: str


class FeedbackListResponse(BaseModel):
    """Response for feedback list."""

    items: List[FeedbackResponse]
    total: int
    last_evaluated_key: dict | None = None


class FeedbackStatsResponse(BaseModel):
    """Response for feedback statistics."""

    total: int
    by_status: dict
    by_type: dict
    unresolved: int


class UpdateStatusRequest(BaseModel):
    """Request to update feedback status."""

    status: str = Field(..., description="New status: new, in_progress, resolved, closed")
    note: str | None = Field(None, description="Optional note")


class AddNoteRequest(BaseModel):
    """Request to add note to feedback."""

    note: str = Field(..., min_length=1, max_length=1000, description="Note text")


class ResolveRequest(BaseModel):
    """Request to resolve feedback."""

    resolution_note: str = Field(..., min_length=10, max_length=500, description="Resolution explanation")


# ============================================================================
# Dependencies
# ============================================================================


def get_service(service: FeedbackService = Depends(get_feedback_service)) -> FeedbackService:
    """Get FeedbackService dependency."""
    return service


def require_admin(current_user: UserResponse = Depends(get_current_superadmin)) -> UserResponse:
    """Require admin privileges (SuperAdmin only)."""
    return current_user


# ============================================================================
# Public Endpoints (No Auth)
# ============================================================================


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    response_model=FeedbackResponse,
    summary="Submit Feedback (Public)",
    description="Submit feedback, bug report, or feature request (anonymous)",
)
async def submit_feedback(
    type: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    email: str | None = Form(None),
    url: str | None = Form(None),
    user_agent: str | None = Form(None),
    browser_info: str | None = Form(None),  # JSON string
    screenshot: UploadFile | None = File(None),
    service: FeedbackService = Depends(get_service),
) -> FeedbackResponse:
    """Submit feedback (public, no auth required).

    Allows anonymous users to submit feedback with optional screenshot.
    """
    # Validate type
    valid_types = ["bug", "feature", "feedback", "other"]
    if type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid type. Must be one of: {', '.join(valid_types)}",
        )

    # Validate title length
    if len(title) < 5 or len(title) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title must be between 5 and 200 characters",
        )

    # Validate description length
    if len(description) < 10 or len(description) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be between 10 and 1000 characters",
        )

    # Parse browser_info JSON
    import json
    parsed_browser_info = None
    if browser_info:
        try:
            parsed_browser_info = json.loads(browser_info)
        except json.JSONDecodeError:
            logger.warning("Invalid browser_info JSON, ignoring")

    # Validate screenshot file type
    if screenshot:
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if screenshot.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid screenshot type. Allowed: {', '.join(allowed_types)}",
            )

        # Check file size (max 5MB)
        content = await screenshot.read()
        await screenshot.seek(0)  # Reset for service upload
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Screenshot too large (max 5MB)",
            )

    # Submit feedback
    feedback = await service.submit_feedback(
        feedback_type=type,
        title=title,
        description=description,
        email=email,
        screenshot=screenshot,
        url=url,
        user_agent=user_agent,
        browser_info=parsed_browser_info,
    )

    return FeedbackResponse(**feedback)


# ============================================================================
# Admin Endpoints (Auth Required)
# ============================================================================


@router.get(
    "/feedback",
    response_model=FeedbackListResponse,
    dependencies=[Depends(require_admin)],
    summary="List Feedback (Admin)",
    description="List all feedback with optional filters",
)
def list_feedback(
    status: str | None = Query(None, description="Filter by status"),
    type: str | None = Query(None, description="Filter by type"),
    limit: int = Query(100, ge=1, le=500, description="Max items"),
    service: FeedbackService = Depends(get_service),
) -> FeedbackListResponse:
    """List feedback (admin only).

    Supports filtering by status and type.
    """
    items, last_key = service.list_feedback(
        status=status,
        feedback_type=type,
        limit=limit,
    )

    return FeedbackListResponse(
        items=[FeedbackResponse(**item) for item in items],
        total=len(items),
        last_evaluated_key=last_key,
    )


@router.get(
    "/feedback/{feedback_id}",
    response_model=FeedbackResponse,
    dependencies=[Depends(require_admin)],
    summary="Get Feedback Detail (Admin)",
    description="Get single feedback item by ID",
)
def get_feedback_detail(
    feedback_id: str,
    service: FeedbackService = Depends(get_service),
) -> FeedbackResponse:
    """Get feedback detail (admin only)."""
    feedback = service.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse(**feedback)


@router.patch(
    "/feedback/{feedback_id}",
    response_model=FeedbackResponse,
    summary="Update Feedback Status (Admin)",
    description="Update feedback status and optionally add note",
)
def update_feedback_status(
    feedback_id: str,
    request: UpdateStatusRequest,
    current_user: UserResponse = Depends(require_admin),
    service: FeedbackService = Depends(get_service),
) -> FeedbackResponse:
    """Update feedback status (admin only)."""
    # Validate status
    valid_statuses = ["new", "in_progress", "resolved", "closed"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    feedback = service.update_feedback_status(
        feedback_id=feedback_id,
        admin_id=str(current_user.id),
        admin_email=current_user.email,
        status=request.status,
        note=request.note,
    )

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse(**feedback)


@router.post(
    "/feedback/{feedback_id}/notes",
    response_model=FeedbackResponse,
    summary="Add Note to Feedback (Admin)",
    description="Add admin note to feedback",
)
def add_note(
    feedback_id: str,
    request: AddNoteRequest,
    current_user: UserResponse = Depends(require_admin),
    service: FeedbackService = Depends(get_service),
) -> FeedbackResponse:
    """Add note to feedback (admin only)."""
    feedback = service.add_note(
        feedback_id=feedback_id,
        admin_id=str(current_user.id),
        admin_email=current_user.email,
        note=request.note,
    )

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse(**feedback)


@router.post(
    "/feedback/{feedback_id}/resolve",
    response_model=FeedbackResponse,
    summary="Resolve Feedback (Admin)",
    description="Mark feedback as resolved with resolution note",
)
def resolve_feedback(
    feedback_id: str,
    request: ResolveRequest,
    current_user: UserResponse = Depends(require_admin),
    service: FeedbackService = Depends(get_service),
) -> FeedbackResponse:
    """Resolve feedback (admin only)."""
    feedback = service.resolve_feedback(
        feedback_id=feedback_id,
        admin_id=str(current_user.id),
        admin_email=current_user.email,
        resolution_note=request.resolution_note,
    )

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse(**feedback)


@router.get(
    "/feedback-stats",
    response_model=FeedbackStatsResponse,
    dependencies=[Depends(require_admin)],
    summary="Get Feedback Statistics (Admin)",
    description="Get feedback counts by status and type",
)
def get_feedback_stats(
    service: FeedbackService = Depends(get_service),
) -> FeedbackStatsResponse:
    """Get feedback statistics (admin only)."""
    stats = service.get_stats()
    return FeedbackStatsResponse(**stats)
