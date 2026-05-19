"""FAQ API Endpoints.

Public endpoints for viewing FAQs and admin endpoints for management.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.auth import get_current_superadmin, get_current_user
from app.db.dynamodb import get_dynamodb_table
from app.repositories.faq import FaqRepository
from app.services.faq_service import FaqService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


def get_faq_repository(table=Depends(get_dynamodb_table)) -> FaqRepository:
    """Get FaqRepository instance."""
    return FaqRepository(table=table)


def get_faq_service(
    faq_repo: FaqRepository = Depends(get_faq_repository),
) -> FaqService:
    """Get FaqService instance."""
    return FaqService(faq_repo=faq_repo)


# ============================================================================
# Pydantic Schemas
# ============================================================================


class FaqResponse(BaseModel):
    """FAQ response model."""

    faq_id: str
    category: str
    question: str
    answer: str
    sort_order: int
    status: str
    view_count: int
    created_at: str
    updated_at: str


class CategoryResponse(BaseModel):
    """Category response model."""

    category_id: str
    name: str
    slug: str
    icon: str
    sort_order: int


class CreateFaqRequest(BaseModel):
    """Request model for creating FAQ."""

    category: str = Field(..., description="Category slug")
    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=10)
    status: str = Field(default="draft", pattern="^(published|draft)$")
    sort_order: int = Field(default=0, ge=0)


class UpdateFaqRequest(BaseModel):
    """Request model for updating FAQ."""

    category: str | None = None
    question: str | None = Field(None, min_length=5, max_length=500)
    answer: str | None = Field(None, min_length=10)
    status: str | None = Field(None, pattern="^(published|draft)$")
    sort_order: int | None = Field(None, ge=0)


class ReorderFaqsRequest(BaseModel):
    """Request model for reordering FAQs."""

    faq_ids: list[str] = Field(..., min_items=1)


class CreateCategoryRequest(BaseModel):
    """Request model for creating category."""

    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50, pattern="^[a-z0-9-]+$")
    icon: str = Field(default="", max_length=100)
    sort_order: int = Field(default=0, ge=0)


class UpdateCategoryRequest(BaseModel):
    """Request model for updating category."""

    name: str | None = Field(None, min_length=2, max_length=100)
    slug: str | None = Field(None, min_length=2, max_length=50, pattern="^[a-z0-9-]+$")
    icon: str | None = Field(None, max_length=100)
    sort_order: int | None = Field(None, ge=0)


# ============================================================================
# Public Endpoints
# ============================================================================


@router.get("/faq")
async def get_faqs(
    category: str | None = Query(None, description="Filter by category slug"),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Get published FAQs, optionally filtered by category.

    Public endpoint - no authentication required.
    """
    try:
        result = service.get_public_faqs(category=category)
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error fetching FAQs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch FAQs",
        )


@router.get("/faq/search")
async def search_faqs(
    q: str = Query(..., min_length=2, description="Search query"),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Search published FAQs by question or answer text.

    Public endpoint - no authentication required.
    """
    try:
        results = service.search_faqs(query=q)
        return {
            "success": True,
            "query": q,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        logger.error(f"Error searching FAQs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search FAQs",
        )


@router.get("/faq/categories")
async def get_categories(
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Get all FAQ categories.

    Public endpoint - no authentication required.
    """
    try:
        categories = service.get_categories()
        return {
            "success": True,
            "categories": categories,
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories",
        )


@router.get("/faq/{faq_id}")
async def get_faq_detail(
    faq_id: str,
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Get single FAQ detail with view tracking.

    Public endpoint - no authentication required.
    Automatically increments view count.
    """
    try:
        faq = service.get_faq_detail(faq_id=faq_id, track_view=True)

        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ not found",
            )

        return {
            "success": True,
            "data": faq,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching FAQ detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch FAQ",
        )


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.get("/admin/faq")
async def list_all_faqs(
    category: str | None = Query(None, description="Filter by category"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """List all FAQs (including drafts) for admin.

    Requires SuperAdmin authentication.
    """
    try:
        faqs = service.list_all_faqs(category=category, status=status_filter)
        return {
            "success": True,
            "faqs": faqs,
            "total": len(faqs),
        }
    except Exception as e:
        logger.error(f"Admin: Error listing FAQs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list FAQs",
        )


@router.post("/admin/faq", status_code=status.HTTP_201_CREATED)
async def create_faq(
    request: CreateFaqRequest,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Create new FAQ.

    Requires SuperAdmin authentication.
    """
    try:
        faq = service.create_faq(
            admin_id=current_user["user_id"],
            category=request.category,
            question=request.question,
            answer=request.answer,
            status=request.status,
            sort_order=request.sort_order,
        )
        return {
            "success": True,
            "message": "FAQ created successfully",
            "data": faq,
        }
    except Exception as e:
        logger.error(f"Admin: Error creating FAQ: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create FAQ",
        )


@router.patch("/admin/faq/{faq_id}")
async def update_faq(
    faq_id: str,
    request: UpdateFaqRequest,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Update FAQ.

    Requires SuperAdmin authentication.
    """
    try:
        # Nur geänderte Felder übergeben
        updates = {k: v for k, v in request.model_dump().items() if v is not None}

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        faq = service.update_faq(
            faq_id=faq_id,
            admin_id=current_user["user_id"],
            **updates,
        )

        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ not found",
            )

        return {
            "success": True,
            "message": "FAQ updated successfully",
            "data": faq,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error updating FAQ: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update FAQ",
        )


@router.delete("/admin/faq/{faq_id}")
async def delete_faq(
    faq_id: str,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Delete FAQ.

    Requires SuperAdmin authentication.
    """
    try:
        success = service.delete_faq(faq_id=faq_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ not found",
            )

        return {
            "success": True,
            "message": "FAQ deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error deleting FAQ: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete FAQ",
        )


@router.post("/admin/faq/reorder")
async def reorder_faqs(
    request: ReorderFaqsRequest,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Reorder FAQs within category.

    Requires SuperAdmin authentication.
    """
    try:
        success = service.reorder_faqs(
            faq_ids=request.faq_ids,
            admin_id=current_user["user_id"],
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reorder FAQs",
            )

        return {
            "success": True,
            "message": "FAQs reordered successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error reordering FAQs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder FAQs",
        )


@router.get("/admin/faq/analytics")
async def get_analytics(
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Get FAQ analytics.

    Requires SuperAdmin authentication.
    """
    try:
        analytics = service.get_faq_analytics()
        return {
            "success": True,
            "analytics": analytics,
        }
    except Exception as e:
        logger.error(f"Admin: Error fetching analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics",
        )


# ============================================================================
# Category Management (Admin)
# ============================================================================


@router.post("/admin/faq/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CreateCategoryRequest,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Create new FAQ category.

    Requires SuperAdmin authentication.
    """
    try:
        category = service.create_category(
            name=request.name,
            slug=request.slug,
            icon=request.icon,
            sort_order=request.sort_order,
        )
        return {
            "success": True,
            "message": "Category created successfully",
            "data": category,
        }
    except Exception as e:
        logger.error(f"Admin: Error creating category: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category",
        )


@router.patch("/admin/faq/categories/{category_id}")
async def update_category(
    category_id: str,
    request: UpdateCategoryRequest,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Update FAQ category.

    Requires SuperAdmin authentication.
    """
    try:
        # Nur geänderte Felder übergeben
        updates = {k: v for k, v in request.model_dump().items() if v is not None}

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        category = service.update_category(
            category_id=category_id,
            **updates,
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return {
            "success": True,
            "message": "Category updated successfully",
            "data": category,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error updating category: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category",
        )


@router.delete("/admin/faq/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_superadmin),
    service: FaqService = Depends(get_faq_service),
) -> dict[str, Any]:
    """Delete FAQ category.

    Requires SuperAdmin authentication.
    """
    try:
        success = service.delete_category(category_id=category_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return {
            "success": True,
            "message": "Category deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error deleting category: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category",
        )
