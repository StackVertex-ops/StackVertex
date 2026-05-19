"""Feedback Service - Business Logic.

Handles feedback submission, admin management, and screenshot uploads.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import UploadFile

from app.db.dynamodb import get_dynamodb_table
from app.db.s3_storage import S3Storage
from app.repositories.feedback import FeedbackRepository

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service für Feedback & Error Tracking."""

    def __init__(
        self,
        feedback_repo: FeedbackRepository | None = None,
        s3_storage: S3Storage | None = None,
    ):
        """Initialize service.

        Args:
            feedback_repo: Feedback repository
            s3_storage: S3 storage helper
        """
        self.feedback_repo = feedback_repo or FeedbackRepository(
            table=get_dynamodb_table()
        )
        self.s3_storage = s3_storage or S3Storage()

    # ========================================================================
    # Submit Feedback (Public)
    # ========================================================================

    async def submit_feedback(
        self,
        feedback_type: str,
        title: str,
        description: str,
        email: str | None = None,
        screenshot: UploadFile | None = None,
        url: str | None = None,
        user_agent: str | None = None,
        browser_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Submit new feedback.

        Args:
            feedback_type: bug, feature, feedback, other
            title: Feedback title
            description: Feedback description
            email: Optional email for followup
            screenshot: Optional screenshot file
            url: URL where feedback was submitted
            user_agent: Browser user agent
            browser_info: Parsed browser info

        Returns:
            Created feedback item
        """
        # Upload screenshot to S3 if provided
        screenshot_s3_key = None
        if screenshot:
            screenshot_s3_key = await self._upload_screenshot(screenshot)

        # Create feedback in DynamoDB
        feedback = self.feedback_repo.create_feedback(
            feedback_type=feedback_type,
            title=title,
            description=description,
            email=email,
            url=url,
            user_agent=user_agent,
            browser_info=browser_info,
            screenshot_s3_key=screenshot_s3_key,
        )

        logger.info(f"New feedback submitted: {feedback['feedback_id']} (type: {feedback_type})")

        return feedback

    async def _upload_screenshot(self, screenshot: UploadFile) -> str:
        """Upload screenshot to S3.

        Args:
            screenshot: Uploaded file

        Returns:
            S3 key (path in bucket)
        """
        from datetime import datetime

        # Read file content
        content = await screenshot.read()

        # Generate S3 key: feedback/screenshots/{date}/{filename}
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        s3_key = f"feedback/screenshots/{date_prefix}/{screenshot.filename}"

        # Upload to S3
        self.s3_storage.put_object(
            key=s3_key,
            data=content,
            content_type=screenshot.content_type or "image/png",
        )

        logger.info(f"Screenshot uploaded to S3: {s3_key}")
        return s3_key

    # ========================================================================
    # Get Feedback (Admin)
    # ========================================================================

    def get_feedback(self, feedback_id: str) -> dict[str, Any] | None:
        """Get feedback by ID.

        Args:
            feedback_id: Feedback UUID

        Returns:
            Feedback item with presigned URL for screenshot
        """
        feedback = self.feedback_repo.get_feedback(feedback_id)
        if not feedback:
            return None

        # Add presigned URL for screenshot
        if feedback.get("screenshot_s3_key"):
            feedback["screenshot_url"] = self.s3_storage.generate_presigned_url(
                key=feedback["screenshot_s3_key"],
                expiration=3600,  # 1 hour
            )

        return feedback

    def list_feedback(
        self,
        status: str | None = None,
        feedback_type: str | None = None,
        limit: int = 100,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """List feedback for admin.

        Args:
            status: Filter by status
            feedback_type: Filter by type
            limit: Max items
            last_evaluated_key: Pagination key

        Returns:
            Tuple of (items, last_key)
        """
        items, last_key = self.feedback_repo.list_feedback(
            status=status,
            feedback_type=feedback_type,
            limit=limit,
            last_evaluated_key=last_evaluated_key,
        )

        # Add presigned URLs for screenshots
        for item in items:
            if item.get("screenshot_s3_key"):
                item["screenshot_url"] = self.s3_storage.generate_presigned_url(
                    key=item["screenshot_s3_key"],
                    expiration=3600,
                )

        return items, last_key

    # ========================================================================
    # Update Feedback (Admin)
    # ========================================================================

    def update_feedback_status(
        self,
        feedback_id: str,
        admin_id: str,
        admin_email: str,
        status: str,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        """Update feedback status.

        Args:
            feedback_id: Feedback UUID
            admin_id: Admin user ID
            admin_email: Admin email
            status: New status
            note: Optional note

        Returns:
            Updated feedback item
        """
        # Update status
        feedback = self.feedback_repo.update_feedback(
            feedback_id=feedback_id,
            status=status,
        )

        if not feedback:
            return None

        # Add note if provided
        if note:
            feedback = self.feedback_repo.add_note(
                feedback_id=feedback_id,
                admin_id=admin_id,
                admin_email=admin_email,
                note=note,
            )

        logger.info(f"Feedback {feedback_id} status updated to {status} by {admin_email}")

        return feedback

    def add_note(
        self,
        feedback_id: str,
        admin_id: str,
        admin_email: str,
        note: str,
    ) -> dict[str, Any] | None:
        """Add note to feedback.

        Args:
            feedback_id: Feedback UUID
            admin_id: Admin user ID
            admin_email: Admin email
            note: Note text

        Returns:
            Updated feedback item
        """
        feedback = self.feedback_repo.add_note(
            feedback_id=feedback_id,
            admin_id=admin_id,
            admin_email=admin_email,
            note=note,
        )

        if feedback:
            logger.info(f"Note added to feedback {feedback_id} by {admin_email}")

        return feedback

    def resolve_feedback(
        self,
        feedback_id: str,
        admin_id: str,
        admin_email: str,
        resolution_note: str,
    ) -> dict[str, Any] | None:
        """Mark feedback as resolved.

        Args:
            feedback_id: Feedback UUID
            admin_id: Admin user ID
            admin_email: Admin email
            resolution_note: Resolution explanation

        Returns:
            Updated feedback item
        """
        feedback = self.feedback_repo.mark_resolved(
            feedback_id=feedback_id,
            admin_id=admin_id,
            admin_email=admin_email,
            resolution_note=resolution_note,
        )

        if feedback:
            logger.info(f"Feedback {feedback_id} resolved by {admin_email}")

        return feedback

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get feedback statistics.

        Returns:
            Stats dict
        """
        return self.feedback_repo.get_stats()


# Global service instance (lazy initialization)
_feedback_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    """Get or create global FeedbackService instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
