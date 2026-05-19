"""Review Service - Business Logic für Reviews/Testimonials.

Handles review submission, moderation, und public display.
"""

import logging
from uuid import UUID

from app.repositories.review import ReviewRepository

logger = logging.getLogger(__name__)


class ReviewService:
    """Service für Review Management."""

    def __init__(self, review_repository: ReviewRepository):
        """Initialize ReviewService.

        Args:
            review_repository: ReviewRepository instance
        """
        self.review_repo = review_repository

    async def submit_review(
        self,
        name: str,
        email: str,
        rating: int,
        comment: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> dict:
        """Submit new review (public endpoint).

        Args:
            name: Reviewer name
            email: Reviewer email (nicht öffentlich)
            rating: Star rating (1-5)
            comment: Review comment
            ip_address: Requester IP
            user_agent: Browser user agent

        Returns:
            Created review item
        """
        # Validation
        if rating < 1 or rating > 5:
            raise ValueError("Rating muss zwischen 1 und 5 liegen")

        if len(comment) < 10:
            raise ValueError("Kommentar muss mindestens 10 Zeichen lang sein")

        if len(comment) > 500:
            raise ValueError("Kommentar darf maximal 500 Zeichen lang sein")

        # Create review
        review = self.review_repo.create(
            name=name,
            email=email,
            rating=rating,
            comment=comment,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(
            f"Review submitted: {review['id']} (status: {review['status']})",
            extra={"review_id": review["id"], "rating": rating}
        )

        return review

    async def get_public_reviews(self, limit: int = 20) -> dict:
        """Get approved reviews für öffentliche Anzeige.

        Args:
            limit: Max items to return

        Returns:
            {
                "reviews": [...],
                "stats": {average, count, distribution}
            }
        """
        # Nur approved reviews
        reviews = self.review_repo.list_by_status(
            status="approved",
            limit=limit,
            scan_index_forward=False  # Newest first
        )

        # Remove private fields (email, IP, etc.)
        public_reviews = [
            {
                "id": r["id"],
                "name": r["name"],
                "rating": r["rating"],
                "comment": r["comment"],
                "created_at": r["created_at"],
            }
            for r in reviews
        ]

        # Get rating stats
        stats = self.review_repo.get_rating_stats()

        return {
            "reviews": public_reviews,
            "stats": stats
        }

    async def get_reviews_for_moderation(
        self,
        status: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Get reviews für Admin-Moderation (alle Felder).

        Args:
            status: Filter by status (pending/approved/rejected/spam)
            limit: Max items to return

        Returns:
            List of review items (mit Email, IP, etc.)
        """
        if status:
            return self.review_repo.list_by_status(
                status=status,
                limit=limit,
                scan_index_forward=False
            )
        else:
            # Get all statuses
            pending = self.review_repo.list_by_status("pending", limit=limit)
            approved = self.review_repo.list_by_status("approved", limit=limit)
            rejected = self.review_repo.list_by_status("rejected", limit=limit)
            spam = self.review_repo.list_by_status("spam", limit=limit)

            # Combine and sort by created_at DESC
            all_reviews = pending + approved + rejected + spam
            all_reviews.sort(key=lambda x: x["created_at"], reverse=True)

            return all_reviews[:limit]

    async def approve_review(
        self,
        review_id: UUID,
        admin_user_id: str
    ) -> dict:
        """Approve review (Admin only).

        Args:
            review_id: Review UUID
            admin_user_id: Admin user performing action

        Returns:
            Updated review item

        Raises:
            ValueError: If review not found
        """
        updated = self.review_repo.update_status(
            review_id=review_id,
            status="approved",
            admin_user_id=admin_user_id
        )

        if not updated:
            raise ValueError(f"Review {review_id} nicht gefunden")

        logger.info(
            f"Review approved: {review_id}",
            extra={"review_id": str(review_id), "admin_id": admin_user_id}
        )

        return updated

    async def reject_review(
        self,
        review_id: UUID,
        admin_user_id: str,
        reason: str | None = None
    ) -> dict:
        """Reject review (Admin only).

        Args:
            review_id: Review UUID
            admin_user_id: Admin user performing action
            reason: Optional rejection reason

        Returns:
            Updated review item

        Raises:
            ValueError: If review not found
        """
        updated = self.review_repo.update_status(
            review_id=review_id,
            status="rejected",
            admin_user_id=admin_user_id,
            rejected_reason=reason
        )

        if not updated:
            raise ValueError(f"Review {review_id} nicht gefunden")

        logger.info(
            f"Review rejected: {review_id}",
            extra={"review_id": str(review_id), "admin_id": admin_user_id}
        )

        return updated

    async def mark_spam(
        self,
        review_id: UUID,
        admin_user_id: str
    ) -> dict:
        """Mark review as spam (Admin only).

        Args:
            review_id: Review UUID
            admin_user_id: Admin user performing action

        Returns:
            Updated review item

        Raises:
            ValueError: If review not found
        """
        updated = self.review_repo.update_status(
            review_id=review_id,
            status="spam",
            admin_user_id=admin_user_id
        )

        if not updated:
            raise ValueError(f"Review {review_id} nicht gefunden")

        logger.info(
            f"Review marked as spam: {review_id}",
            extra={"review_id": str(review_id), "admin_id": admin_user_id}
        )

        return updated

    async def bulk_approve(
        self,
        review_ids: list[UUID],
        admin_user_id: str
    ) -> dict:
        """Bulk approve reviews (Admin only).

        Args:
            review_ids: List of review UUIDs
            admin_user_id: Admin user performing action

        Returns:
            {success_count, failed_count, total}
        """
        success_count = self.review_repo.bulk_update_status(
            review_ids=review_ids,
            status="approved",
            admin_user_id=admin_user_id
        )

        failed_count = len(review_ids) - success_count

        logger.info(
            f"Bulk approved {success_count}/{len(review_ids)} reviews",
            extra={"admin_id": admin_user_id, "success": success_count, "failed": failed_count}
        )

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(review_ids)
        }

    async def delete_review(
        self,
        review_id: UUID,
        admin_user_id: str
    ) -> bool:
        """Delete review (Admin only).

        Args:
            review_id: Review UUID
            admin_user_id: Admin user performing action

        Returns:
            True (idempotent - returns True even if review doesn't exist)
        """
        # DynamoDB delete ist idempotent - keine Existenz-Prüfung nötig
        self.review_repo.delete(review_id)

        logger.info(
            f"Review deleted: {review_id}",
            extra={"review_id": str(review_id), "admin_id": admin_user_id}
        )

        return True

    async def get_rating_summary(self) -> dict:
        """Get rating summary statistics.

        Returns:
            {average, count, distribution}
        """
        return self.review_repo.get_rating_stats()
