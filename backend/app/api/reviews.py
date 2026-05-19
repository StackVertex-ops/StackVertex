"""Reviews API Endpoints - Public Reviews & Admin Moderation."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.dynamodb import get_dynamodb_table
from app.repositories.review import ReviewRepository
from app.services.review_service import ReviewService
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewPublicResponse,
    ReviewAdminResponse,
    ReviewListPublicResponse,
    ReviewUpdateStatusRequest,
    ReviewBulkActionRequest,
    ReviewBulkActionResponse,
    RatingStats,
)
from app.api.auth import get_current_user, get_current_superadmin

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Dependencies
# ============================================================================


def get_review_repository(table=Depends(get_dynamodb_table)) -> ReviewRepository:
    """Get ReviewRepository instance."""
    return ReviewRepository(table=table)


def get_review_service(
    review_repo: ReviewRepository = Depends(get_review_repository)
) -> ReviewService:
    """Get ReviewService instance."""
    return ReviewService(review_repo)


# ============================================================================
# Public Endpoints (No Auth)
# ============================================================================


@router.post(
    "/reviews",
    response_model=ReviewPublicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Review",
    description="Submit customer review (public endpoint, rate limited)"
)
@limiter.limit("3/hour")  # Max 3 reviews pro IP pro Stunde
async def submit_review(
    request: Request,
    review_data: ReviewCreateRequest,
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Submit new review (public).

    Args:
        request: FastAPI request (für IP extraction)
        review_data: Review data
        review_service: ReviewService instance

    Returns:
        Created review (public fields only)

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Get IP address + User-Agent
        ip_address = get_remote_address(request)
        user_agent = request.headers.get("user-agent")

        # Submit review
        review = await review_service.submit_review(
            name=review_data.name,
            email=review_data.email,
            rating=review_data.rating,
            comment=review_data.comment,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Return nur public fields
        return {
            "id": review["id"],
            "name": review["name"],
            "rating": review["rating"],
            "comment": review["comment"],
            "created_at": review["created_at"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting review: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Einreichen des Kommentars"
        )


@router.get(
    "/reviews",
    response_model=ReviewListPublicResponse,
    summary="Get Public Reviews",
    description="Get approved reviews with rating stats"
)
async def get_public_reviews(
    limit: int = 20,
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Get approved reviews (public).

    Args:
        limit: Max items to return (default: 20)
        review_service: ReviewService instance

    Returns:
        {reviews: [...], stats: {...}}
    """
    try:
        return await review_service.get_public_reviews(limit=limit)

    except Exception as e:
        logger.error(f"Error fetching public reviews: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden der Bewertungen"
        )


@router.get(
    "/reviews/stats",
    response_model=RatingStats,
    summary="Get Rating Stats",
    description="Get rating statistics (average, count, distribution)"
)
async def get_rating_stats(
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Get rating statistics (public).

    Args:
        review_service: ReviewService instance

    Returns:
        Rating statistics
    """
    try:
        return await review_service.get_rating_summary()

    except Exception as e:
        logger.error(f"Error fetching rating stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden der Statistiken"
        )


# ============================================================================
# Admin Endpoints (SuperAdmin Only)
# ============================================================================


@router.get(
    "/admin/reviews",
    response_model=list[ReviewAdminResponse],
    summary="List All Reviews (Admin)",
    description="Get all reviews for moderation (SuperAdmin only)",
    dependencies=[Depends(get_current_superadmin)]
)
async def list_all_reviews(
    status_filter: str | None = None,
    limit: int = 100,
    review_service: ReviewService = Depends(get_review_service)
) -> list[dict]:
    """List all reviews für Admin-Moderation.

    Args:
        status_filter: Filter by status (pending/approved/rejected/spam)
        limit: Max items to return
        review_service: ReviewService instance

    Returns:
        List of reviews (all fields)
    """
    try:
        return await review_service.get_reviews_for_moderation(
            status=status_filter,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Error fetching reviews for moderation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden der Reviews"
        )


@router.patch(
    "/admin/reviews/{review_id}/approve",
    response_model=ReviewAdminResponse,
    summary="Approve Review (Admin)",
    description="Approve pending review (SuperAdmin only)",
    dependencies=[Depends(get_current_superadmin)]
)
async def approve_review(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_superadmin)],
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Approve review (Admin only).

    Args:
        review_id: Review UUID
        current_user: Current authenticated admin
        review_service: ReviewService instance

    Returns:
        Updated review

    Raises:
        HTTPException: 404 if review not found
    """
    try:
        review_uuid = UUID(review_id)
        admin_user_id = current_user["id"]

        return await review_service.approve_review(
            review_id=review_uuid,
            admin_user_id=admin_user_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving review: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Freigeben des Reviews"
        )


@router.patch(
    "/admin/reviews/{review_id}/reject",
    response_model=ReviewAdminResponse,
    summary="Reject Review (Admin)",
    description="Reject pending review (SuperAdmin only)",
    dependencies=[Depends(get_current_superadmin)]
)
async def reject_review(
    review_id: str,
    request_data: ReviewUpdateStatusRequest,
    current_user: Annotated[dict, Depends(get_current_superadmin)],
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Reject review (Admin only).

    Args:
        review_id: Review UUID
        request_data: Status update data (reason)
        current_user: Current authenticated admin
        review_service: ReviewService instance

    Returns:
        Updated review

    Raises:
        HTTPException: 404 if review not found
    """
    try:
        review_uuid = UUID(review_id)
        admin_user_id = current_user["id"]

        return await review_service.reject_review(
            review_id=review_uuid,
            admin_user_id=admin_user_id,
            reason=request_data.reason
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting review: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Ablehnen des Reviews"
        )


@router.patch(
    "/admin/reviews/{review_id}/spam",
    response_model=ReviewAdminResponse,
    summary="Mark Review as Spam (Admin)",
    description="Mark review as spam (SuperAdmin only)",
    dependencies=[Depends(get_current_superadmin)]
)
async def mark_spam(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_superadmin)],
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Mark review as spam (Admin only).

    Args:
        review_id: Review UUID
        current_user: Current authenticated admin
        review_service: ReviewService instance

    Returns:
        Updated review

    Raises:
        HTTPException: 404 if review not found
    """
    try:
        review_uuid = UUID(review_id)
        admin_user_id = current_user["id"]

        return await review_service.mark_spam(
            review_id=review_uuid,
            admin_user_id=admin_user_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error marking review as spam: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Markieren als Spam"
        )


@router.post(
    "/admin/reviews/bulk-approve",
    response_model=ReviewBulkActionResponse,
    summary="Bulk Approve Reviews (Admin)",
    description="Approve multiple reviews at once (SuperAdmin only)",
    dependencies=[Depends(get_current_superadmin)]
)
async def bulk_approve_reviews(
    request_data: ReviewBulkActionRequest,
    current_user: Annotated[dict, Depends(get_current_superadmin)],
    review_service: ReviewService = Depends(get_review_service)
) -> dict:
    """Bulk approve reviews (Admin only).

    Args:
        request_data: Bulk action data (review IDs)
        current_user: Current authenticated admin
        review_service: ReviewService instance

    Returns:
        Bulk action result
    """
    try:
        review_uuids = [UUID(rid) for rid in request_data.review_ids]
        admin_user_id = current_user["id"]

        return await review_service.bulk_approve(
            review_ids=review_uuids,
            admin_user_id=admin_user_id
        )

    except Exception as e:
        logger.error(f"Error bulk approving reviews: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Bulk-Freigeben der Reviews"
        )


@router.delete(
    "/admin/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Review (Admin)",
    description="Permanently delete review (SuperAdmin only)",
    dependencies=[Depends(get_current_superadmin)]
)
async def delete_review(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_superadmin)],
    review_service: ReviewService = Depends(get_review_service)
) -> None:
    """Delete review (Admin only).

    Args:
        review_id: Review UUID
        current_user: Current authenticated admin
        review_service: ReviewService instance

    Raises:
        HTTPException: 404 if review not found
    """
    try:
        review_uuid = UUID(review_id)
        admin_user_id = current_user["id"]

        await review_service.delete_review(
            review_id=review_uuid,
            admin_user_id=admin_user_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting review: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Löschen des Reviews"
        )
