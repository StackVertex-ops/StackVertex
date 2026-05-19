"""ReviewRepository - DynamoDB Review/Testimonial Management.

Handles customer reviews with moderation and spam detection.
"""

import logging
import re
from datetime import datetime
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ReviewRepository(BaseRepository):
    """Repository für Review/Kommentar Management."""

    def __init__(self, table: Table):
        """Initialize ReviewRepository.

        Args:
            table: DynamoDB Table Resource
        """
        super().__init__(table)

    # ========================================================================
    # Create
    # ========================================================================

    def create(
        self,
        name: str,
        email: str,
        rating: int,
        comment: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """Create new review (status: pending).

        Args:
            name: Reviewer name (öffentlich)
            email: Reviewer email (privat, nicht öffentlich)
            rating: Star rating (1-5)
            comment: Review comment text
            ip_address: Requester IP (for rate limiting)
            user_agent: Browser user agent

        Returns:
            Review item (DynamoDB format)
        """
        review_id = uuid4()
        now = datetime.utcnow().isoformat()

        # Spam-Check
        is_spam = self._detect_spam(comment)

        review_item = {
            "PK": f"REVIEW#{str(review_id)}",
            "SK": "METADATA",
            "id": str(review_id),
            "name": name,
            "email": email.lower(),
            "rating": rating,
            "comment": comment,
            "status": "spam" if is_spam else "pending",
            "is_spam": is_spam,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": now,
            "updated_at": now,
            # GSI1: Query by status + created_at (Newest first)
            "GSI1PK": f"review_status#{('spam' if is_spam else 'pending')}",
            "GSI1SK": now,
            # GSI2: Query by rating + created_at
            "GSI2PK": f"review_rating#{rating}",
            "GSI2SK": now,
        }

        self._put_item(review_item)

        logger.info(
            f"Created review {review_id} (status: {'spam' if is_spam else 'pending'})",
            extra={"review_id": str(review_id), "email": email, "rating": rating}
        )

        return review_item

    # ========================================================================
    # Read
    # ========================================================================

    def get(self, review_id: UUID) -> dict | None:
        """Get review by ID.

        Args:
            review_id: Review UUID

        Returns:
            Review item or None
        """
        return self._get_item(f"REVIEW#{str(review_id)}", "METADATA")

    def list_by_status(
        self,
        status: str = "approved",
        limit: int = 20,
        scan_index_forward: bool = False  # False = Newest first
    ) -> list[dict]:
        """List reviews by status (newest first).

        Args:
            status: Review status (pending/approved/rejected/spam)
            limit: Max items to return
            scan_index_forward: False = DESC (newest first), True = ASC

        Returns:
            List of review items
        """
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq(f"review_status#{status}"),
            index_name="GSI1",
            limit=limit,
            scan_index_forward=scan_index_forward
        )

        return items

    def list_by_rating(
        self,
        rating: int,
        limit: int = 20,
        scan_index_forward: bool = False
    ) -> list[dict]:
        """List reviews by rating (newest first).

        Args:
            rating: Star rating (1-5)
            limit: Max items to return
            scan_index_forward: False = DESC (newest first), True = ASC

        Returns:
            List of review items
        """
        items, _ = self._query(
            key_condition=Key("GSI2PK").eq(f"review_rating#{rating}"),
            index_name="GSI2",
            limit=limit,
            scan_index_forward=scan_index_forward
        )

        return items

    def get_rating_stats(self) -> dict:
        """Get rating statistics (average, count, distribution).

        Returns:
            {
                "average": 4.5,
                "count": 123,
                "distribution": {1: 5, 2: 10, 3: 20, 4: 30, 5: 58}
            }
        """
        # Query nur APPROVED reviews für Statistik
        approved_reviews = self.list_by_status(status="approved", limit=1000)

        if not approved_reviews:
            return {
                "average": 0.0,
                "count": 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        # Calculate distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_rating = 0

        for review in approved_reviews:
            rating = review.get("rating", 0)
            distribution[rating] += 1
            total_rating += rating

        count = len(approved_reviews)
        average = round(total_rating / count, 1) if count > 0 else 0.0

        return {
            "average": average,
            "count": count,
            "distribution": distribution
        }

    # ========================================================================
    # Update
    # ========================================================================

    def update_status(
        self,
        review_id: UUID,
        status: str,
        admin_user_id: str | None = None,
        rejected_reason: str | None = None
    ) -> dict | None:
        """Update review status (pending → approved/rejected).

        Args:
            review_id: Review UUID
            status: New status (approved/rejected/spam)
            admin_user_id: Admin user who approved/rejected
            rejected_reason: Optional reason for rejection

        Returns:
            Updated review item or None if not found
        """
        review = self.get(review_id)
        if not review:
            return None

        now = datetime.utcnow().isoformat()

        updates = {
            "status": status,
        }

        # Update GSI1PK for new status
        updates["GSI1PK"] = f"review_status#{status}"

        if status == "approved":
            updates["approved_by"] = admin_user_id
            updates["approved_at"] = now

        if status == "rejected" and rejected_reason:
            updates["rejected_reason"] = rejected_reason
            updates["rejected_by"] = admin_user_id
            updates["rejected_at"] = now

        updated = self._update_item(
            f"REVIEW#{str(review_id)}",
            "METADATA",
            updates
        )

        logger.info(
            f"Updated review {review_id} status to {status}",
            extra={"review_id": str(review_id), "status": status, "admin_id": admin_user_id}
        )

        return updated

    def bulk_update_status(
        self,
        review_ids: list[UUID],
        status: str,
        admin_user_id: str
    ) -> int:
        """Bulk update review status.

        Args:
            review_ids: List of review UUIDs
            status: New status (approved/rejected)
            admin_user_id: Admin user performing action

        Returns:
            Number of successfully updated reviews
        """
        success_count = 0

        for review_id in review_ids:
            updated = self.update_status(review_id, status, admin_user_id)
            if updated:
                success_count += 1

        logger.info(
            f"Bulk updated {success_count}/{len(review_ids)} reviews to {status}",
            extra={"status": status, "admin_id": admin_user_id, "count": success_count}
        )

        return success_count

    # ========================================================================
    # Delete
    # ========================================================================

    def delete(self, review_id: UUID) -> bool:
        """Delete review (hard delete).

        Args:
            review_id: Review UUID

        Returns:
            True (DynamoDB delete is idempotent)
        """
        # DynamoDB delete_item ist idempotent - wirft keine Exception wenn Item nicht existiert
        deleted = self._delete_item(f"REVIEW#{str(review_id)}", "METADATA")

        if deleted:
            logger.info(
                f"Deleted review {review_id}",
                extra={"review_id": str(review_id)}
            )

        return True  # Idempotent

    # ========================================================================
    # Spam Detection
    # ========================================================================

    def _detect_spam(self, comment: str) -> bool:
        """Detect potential spam in comment.

        Simple heuristics:
        - More than 2 URLs
        - Comment too short (< 10 chars)
        - Comment too long (> 500 chars)
        - Excessive caps (> 50%)

        Args:
            comment: Comment text

        Returns:
            True if likely spam
        """
        # Count URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, comment)
        if len(urls) > 2:
            logger.warning(f"Spam detected: Too many URLs ({len(urls)})")
            return True

        # Check length
        if len(comment) < 10:
            logger.warning(f"Spam detected: Comment too short ({len(comment)} chars)")
            return True

        if len(comment) > 500:
            logger.warning(f"Spam detected: Comment too long ({len(comment)} chars)")
            return True

        # Check excessive caps
        if comment.isupper() and len(comment) > 20:
            logger.warning("Spam detected: All caps")
            return True

        uppercase_count = sum(1 for c in comment if c.isupper())
        if len(comment) > 0 and uppercase_count / len(comment) > 0.5:
            logger.warning(f"Spam detected: Excessive caps ({uppercase_count}/{len(comment)})")
            return True

        return False
