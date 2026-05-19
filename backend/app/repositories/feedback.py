"""Feedback Repository - DynamoDB Data Access.

Handles user feedback, bug reports, feature requests:
- Anonymous feedback submission
- Admin review and management
- Notes and status tracking
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key, Attr
from mypy_boto3_dynamodb.service_resource import Table

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FeedbackRepository(BaseRepository):
    """Repository für Feedback & Error Tracking.

    DynamoDB Structure:
        Feedback Item:
            PK: FEEDBACK#{feedback_id}
            SK: METADATA
            Attributes: feedback_id, type, status, title, description, email,
                       url, user_agent, browser_info, screenshot_s3_key,
                       is_resolved, resolved_at, resolved_by, notes
            GSI1: feedback_status#{status} + created_at (für Status-Filter)
            GSI2: feedback_type#{type} + created_at (für Type-Filter)

        Note Structure (embedded in notes array):
            - note_id: UUID
            - admin_id: UUID (who added the note)
            - admin_email: Email des Admins
            - note: Text content
            - created_at: ISO timestamp
    """

    # ========================================================================
    # Create Feedback
    # ========================================================================

    def create_feedback(
        self,
        feedback_type: str,
        title: str,
        description: str,
        email: str | None = None,
        url: str | None = None,
        user_agent: str | None = None,
        browser_info: dict[str, Any] | None = None,
        screenshot_s3_key: str | None = None,
    ) -> dict[str, Any]:
        """Create new feedback item.

        Args:
            feedback_type: bug, feature, feedback, other
            title: Feedback title
            description: Feedback description
            email: Optional email for followup
            url: URL where feedback was submitted
            user_agent: Browser user agent
            browser_info: Parsed browser information
            screenshot_s3_key: S3 key for uploaded screenshot

        Returns:
            Created feedback item
        """
        feedback_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            "PK": f"FEEDBACK#{feedback_id}",
            "SK": "METADATA",
            "feedback_id": feedback_id,
            "type": feedback_type,
            "status": "new",
            "title": title,
            "description": description,
            "email": email,
            "url": url,
            "user_agent": user_agent,
            "browser_info": browser_info or {},
            "screenshot_s3_key": screenshot_s3_key,
            "is_resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "notes": [],
            "entity_type": "feedback",
            # GSI1: Query by status
            "GSI1PK": f"feedback_status#{feedback_type}",
            "GSI1SK": now,
            # GSI2: Query by type
            "GSI2PK": f"feedback_type#{feedback_type}",
            "GSI2SK": now,
            "created_at": now,
            "updated_at": now,
        }

        return self._put_item(item)

    # ========================================================================
    # Get Feedback
    # ========================================================================

    def get_feedback(self, feedback_id: str) -> dict[str, Any] | None:
        """Get feedback by ID.

        Args:
            feedback_id: Feedback UUID

        Returns:
            Feedback item or None
        """
        return self._get_item(f"FEEDBACK#{feedback_id}", "METADATA")

    # ========================================================================
    # List Feedback (Admin)
    # ========================================================================

    def list_feedback(
        self,
        status: str | None = None,
        feedback_type: str | None = None,
        limit: int = 100,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """List feedback with optional filters.

        Args:
            status: Filter by status (new/in_progress/resolved/closed)
            feedback_type: Filter by type (bug/feature/feedback/other)
            limit: Max items to return
            last_evaluated_key: Pagination key

        Returns:
            Tuple of (items list, last_evaluated_key)
        """
        # Filter by status (GSI1)
        if status:
            items, last_key = self._query(
                key_condition=Key("GSI1PK").eq(f"feedback_status#{status}"),
                index_name="GSI1",
                limit=limit,
                scan_index_forward=False,  # Newest first
                exclusive_start_key=last_evaluated_key,
            )
            return items, last_key

        # Filter by type (GSI2)
        if feedback_type:
            items, last_key = self._query(
                key_condition=Key("GSI2PK").eq(f"feedback_type#{feedback_type}"),
                index_name="GSI2",
                limit=limit,
                scan_index_forward=False,
                exclusive_start_key=last_evaluated_key,
            )
            return items, last_key

        # No filter: Scan all feedback (expensive, nur für kleine Datenmengen)
        items, last_key = self._scan(
            filter_condition=Attr("entity_type").eq("feedback"),
            limit=limit,
            exclusive_start_key=last_evaluated_key,
        )
        # Sort by created_at DESC
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items, last_key

    # ========================================================================
    # Update Feedback
    # ========================================================================

    def update_feedback(
        self,
        feedback_id: str,
        status: str | None = None,
        is_resolved: bool | None = None,
        resolved_by: str | None = None,
    ) -> dict[str, Any] | None:
        """Update feedback status.

        Args:
            feedback_id: Feedback UUID
            status: New status
            is_resolved: Mark as resolved
            resolved_by: Admin user ID who resolved it

        Returns:
            Updated feedback item or None
        """
        feedback = self.get_feedback(feedback_id)
        if not feedback:
            return None

        # Update fields
        if status is not None:
            feedback["status"] = status
            # Update GSI1PK for status filter
            feedback["GSI1PK"] = f"feedback_status#{status}"

        if is_resolved is not None:
            feedback["is_resolved"] = is_resolved
            if is_resolved:
                feedback["resolved_at"] = datetime.utcnow().isoformat()
                feedback["resolved_by"] = resolved_by

        feedback["updated_at"] = datetime.utcnow().isoformat()

        return self._put_item(feedback)

    # ========================================================================
    # Notes Management
    # ========================================================================

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
            admin_email: Admin email for display
            note: Note text

        Returns:
            Updated feedback item or None
        """
        feedback = self.get_feedback(feedback_id)
        if not feedback:
            return None

        note_item = {
            "note_id": str(uuid4()),
            "admin_id": admin_id,
            "admin_email": admin_email,
            "note": note,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Append note to notes array
        notes = feedback.get("notes", [])
        notes.append(note_item)
        feedback["notes"] = notes
        feedback["updated_at"] = datetime.utcnow().isoformat()

        return self._put_item(feedback)

    # ========================================================================
    # Mark Resolved
    # ========================================================================

    def mark_resolved(
        self,
        feedback_id: str,
        admin_id: str,
        admin_email: str,
        resolution_note: str,
    ) -> dict[str, Any] | None:
        """Mark feedback as resolved and add resolution note.

        Args:
            feedback_id: Feedback UUID
            admin_id: Admin user ID
            admin_email: Admin email
            resolution_note: Resolution explanation

        Returns:
            Updated feedback item or None
        """
        feedback = self.get_feedback(feedback_id)
        if not feedback:
            return None

        # Add resolution note
        note_item = {
            "note_id": str(uuid4()),
            "admin_id": admin_id,
            "admin_email": admin_email,
            "note": f"✅ RESOLVED: {resolution_note}",
            "created_at": datetime.utcnow().isoformat(),
        }

        notes = feedback.get("notes", [])
        notes.append(note_item)

        # Update status
        feedback["notes"] = notes
        feedback["status"] = "resolved"
        feedback["is_resolved"] = True
        feedback["resolved_at"] = datetime.utcnow().isoformat()
        feedback["resolved_by"] = admin_id
        feedback["GSI1PK"] = "feedback_status#resolved"
        feedback["updated_at"] = datetime.utcnow().isoformat()

        return self._put_item(feedback)

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get feedback statistics.

        Returns:
            Dict with counts per status and type
        """
        # Scan all feedback (für kleine Datenmengen OK)
        all_feedback, _ = self._scan(
            filter_condition=Attr("entity_type").eq("feedback"),
        )

        stats = {
            "total": len(all_feedback),
            "by_status": {
                "new": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0,
            },
            "by_type": {
                "bug": 0,
                "feature": 0,
                "feedback": 0,
                "other": 0,
            },
            "unresolved": 0,
        }

        for item in all_feedback:
            status = item.get("status", "new")
            feedback_type = item.get("type", "other")
            is_resolved = item.get("is_resolved", False)

            if status in stats["by_status"]:
                stats["by_status"][status] += 1

            if feedback_type in stats["by_type"]:
                stats["by_type"][feedback_type] += 1

            if not is_resolved:
                stats["unresolved"] += 1

        return stats
