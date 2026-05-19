"""Pydantic Schemas für Review API."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# Request Schemas
# ============================================================================


class ReviewCreateRequest(BaseModel):
    """Request schema für Review submission (public)."""

    name: str = Field(..., min_length=2, max_length=100, description="Name des Reviewers")
    email: EmailStr = Field(..., description="Email (nicht öffentlich)")
    rating: int = Field(..., ge=1, le=5, description="Stern-Bewertung (1-5)")
    comment: str = Field(..., min_length=10, max_length=500, description="Kommentar-Text")

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        """Validate comment text."""
        # Strip whitespace
        v = v.strip()

        if len(v) < 10:
            raise ValueError("Kommentar muss mindestens 10 Zeichen lang sein")

        if len(v) > 500:
            raise ValueError("Kommentar darf maximal 500 Zeichen lang sein")

        return v


class ReviewUpdateStatusRequest(BaseModel):
    """Request schema für Status-Update (admin only)."""

    status: str = Field(..., pattern="^(approved|rejected|spam)$")
    reason: str | None = Field(None, max_length=200, description="Ablehnungsgrund (optional)")


class ReviewBulkActionRequest(BaseModel):
    """Request schema für Bulk-Actions (admin only)."""

    review_ids: list[str] = Field(..., min_length=1, description="Liste von Review IDs")
    action: str = Field(..., pattern="^(approve|reject|spam|delete)$")


# ============================================================================
# Response Schemas
# ============================================================================


class ReviewPublicResponse(BaseModel):
    """Public review response (keine private Daten)."""

    id: str
    name: str
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewAdminResponse(BaseModel):
    """Admin review response (alle Felder)."""

    id: str
    name: str
    email: str
    rating: int
    comment: str
    status: str
    is_spam: bool
    ip_address: str | None = None
    user_agent: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_by: str | None = None
    rejected_at: datetime | None = None
    rejected_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RatingDistribution(BaseModel):
    """Rating distribution."""

    stars_1: int = Field(0, alias="1")
    stars_2: int = Field(0, alias="2")
    stars_3: int = Field(0, alias="3")
    stars_4: int = Field(0, alias="4")
    stars_5: int = Field(0, alias="5")

    class Config:
        populate_by_name = True


class RatingStats(BaseModel):
    """Rating statistics."""

    average: float
    count: int
    distribution: dict[int, int]


class ReviewListPublicResponse(BaseModel):
    """Public review list with stats."""

    reviews: list[ReviewPublicResponse]
    stats: RatingStats


class ReviewBulkActionResponse(BaseModel):
    """Response für Bulk-Actions."""

    success_count: int
    failed_count: int
    total: int
