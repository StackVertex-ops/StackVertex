"""DSGVO Repository - DynamoDB Data Access.

Handles DSGVO/GDPR compliance data:
- Data Export Requests (Art. 15)
- Data Deletion Requests (Art. 17)
- Consent Management (Art. 7)
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class DsgvoRepository(BaseRepository):
    """Repository für DSGVO/GDPR Compliance Daten.

    DynamoDB Structure:
        Data Export Item:
            PK: USER#{user_id}
            SK: EXPORT#{export_id}
            Attributes: export_id, user_id, format, status, expires_at, s3_key, created_at
            GSI1: export_by_status + created_at

        Data Deletion Item:
            PK: USER#{user_id}
            SK: DELETION#{deletion_id}
            Attributes: deletion_id, user_id, reason, status, scheduled_at, completed_at, created_at
            GSI1: deletion_by_status + scheduled_at

        Consent Item:
            PK: USER#{user_id}
            SK: CONSENT#{consent_type}
            Attributes: consent_type, granted, granted_at, revoked_at, ip_address, user_agent
    """

    # ========================================================================
    # Data Export (Art. 15)
    # ========================================================================

    def create_export_request(
        self,
        user_id: UUID,
        format: str = "json",
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Create data export request.

        Args:
            user_id: User UUID
            format: Export format (json, csv, pdf)
            include_metadata: Include timestamps, IDs, etc.

        Returns:
            Export request item
        """
        export_id = str(uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(days=7)

        item = {
            "PK": f"USER#{str(user_id)}",
            "SK": f"EXPORT#{export_id}",
            "export_id": export_id,
            "user_id": str(user_id),
            "format": format,
            "include_metadata": include_metadata,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
            "entity_type": "data_export",
            # GSI1: Query exports by status
            "GSI1PK": f"export_status#{format}",
            "GSI1SK": now.isoformat(),
        }

        return self._put_item(item)

    def get_export(self, user_id: UUID, export_id: str) -> dict[str, Any] | None:
        """Get export request by ID.

        Args:
            user_id: User UUID
            export_id: Export UUID

        Returns:
            Export item or None
        """
        return self._get_item(f"USER#{str(user_id)}", f"EXPORT#{export_id}")

    def update_export_status(
        self,
        user_id: UUID,
        export_id: str,
        status: str,
        s3_key: str | None = None,
        download_url: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update export status.

        Args:
            user_id: User UUID
            export_id: Export UUID
            status: New status (pending, ready, failed, expired)
            s3_key: S3 key where export is stored
            download_url: Pre-signed download URL
            error: Error message (if status=failed)

        Returns:
            Updated export item
        """
        pk = f"USER#{str(user_id)}"
        sk = f"EXPORT#{export_id}"

        updates = {"status": status}

        if s3_key:
            updates["s3_key"] = s3_key

        if download_url:
            updates["download_url"] = download_url

        if error:
            updates["error"] = error

        return self._update_item(pk=pk, sk=sk, updates=updates)

    def list_exports_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """List all exports for a user.

        Args:
            user_id: User UUID
            limit: Max number of exports to return

        Returns:
            List of export items
        """
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"USER#{str(user_id)}")
            & Key("SK").begins_with("EXPORT#"),
            Limit=limit,
            ScanIndexForward=False,  # Newest first
        )

        return response.get("Items", [])

    def list_expired_exports(self, limit: int = 100) -> list[dict[str, Any]]:
        """List expired exports (for cleanup job).

        Args:
            limit: Max number to return

        Returns:
            List of expired export items
        """
        cutoff = datetime.utcnow().isoformat()

        # Query GSI1 for exports with expires_at < now
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").begins_with("export_status#")
            & Key("GSI1SK").lt(cutoff),
            Limit=limit,
        )

        return response.get("Items", [])

    # ========================================================================
    # Data Deletion (Art. 17)
    # ========================================================================

    def create_deletion_request(
        self,
        user_id: UUID,
        reason: str,
        delete_backups: bool = True,
    ) -> dict[str, Any]:
        """Create data deletion request.

        Args:
            user_id: User UUID
            reason: Deletion reason
            delete_backups: Also delete from backups

        Returns:
            Deletion request item
        """
        deletion_id = str(uuid4())
        now = datetime.utcnow()
        scheduled_at = now + timedelta(days=7)  # 7-day grace period
        estimated_completion = scheduled_at + timedelta(hours=24)

        item = {
            "PK": f"USER#{str(user_id)}",
            "SK": f"DELETION#{deletion_id}",
            "deletion_id": deletion_id,
            "user_id": str(user_id),
            "reason": reason,
            "delete_backups": delete_backups,
            "status": "scheduled",
            "scheduled_at": scheduled_at.isoformat(),
            "estimated_completion": estimated_completion.isoformat(),
            "entity_type": "data_deletion",
            # GSI1: Query deletions by status + scheduled_at
            "GSI1PK": "deletion_status#scheduled",
            "GSI1SK": scheduled_at.isoformat(),
        }

        return self._put_item(item)

    def get_deletion(self, user_id: UUID, deletion_id: str) -> dict[str, Any] | None:
        """Get deletion request by ID.

        Args:
            user_id: User UUID
            deletion_id: Deletion UUID

        Returns:
            Deletion item or None
        """
        return self._get_item(f"USER#{str(user_id)}", f"DELETION#{deletion_id}")

    def update_deletion_status(
        self,
        user_id: UUID,
        deletion_id: str,
        status: str,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update deletion status.

        Args:
            user_id: User UUID
            deletion_id: Deletion UUID
            status: New status (scheduled, in_progress, completed, cancelled, failed)
            error: Error message (if status=failed)

        Returns:
            Updated deletion item
        """
        pk = f"USER#{str(user_id)}"
        sk = f"DELETION#{deletion_id}"

        updates = {
            "status": status,
            "GSI1PK": f"deletion_status#{status}",
        }

        if status == "completed":
            updates["completed_at"] = datetime.utcnow().isoformat()

        if error:
            updates["error"] = error

        return self._update_item(pk=pk, sk=sk, updates=updates)

    def list_scheduled_deletions(self, limit: int = 100) -> list[dict[str, Any]]:
        """List scheduled deletions ready to execute.

        Args:
            limit: Max number to return

        Returns:
            List of scheduled deletion items
        """
        now = datetime.utcnow().isoformat()

        # Query GSI1 for scheduled deletions with scheduled_at <= now
        response = self.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq("deletion_status#scheduled")
            & Key("GSI1SK").lte(now),
            Limit=limit,
        )

        return response.get("Items", [])

    # ========================================================================
    # Consent Management (Art. 7)
    # ========================================================================

    def get_consent(
        self, user_id: UUID, consent_type: str
    ) -> dict[str, Any] | None:
        """Get user consent by type.

        Args:
            user_id: User UUID
            consent_type: Consent type (marketing, analytics, third_party)

        Returns:
            Consent item or None
        """
        return self._get_item(f"USER#{str(user_id)}", f"CONSENT#{consent_type}")

    def list_consents(self, user_id: UUID) -> list[dict[str, Any]]:
        """List all consents for a user.

        Args:
            user_id: User UUID

        Returns:
            List of consent items
        """
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"USER#{str(user_id)}")
            & Key("SK").begins_with("CONSENT#"),
        )

        return response.get("Items", [])

    def update_consent(
        self,
        user_id: UUID,
        consent_type: str,
        granted: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Update user consent.

        Args:
            user_id: User UUID
            consent_type: Consent type
            granted: True to grant, False to revoke
            ip_address: IP address of request
            user_agent: User agent of request
            reason: Optional reason for change

        Returns:
            Updated consent item
        """
        pk = f"USER#{str(user_id)}"
        sk = f"CONSENT#{consent_type}"
        now = datetime.utcnow().isoformat()

        # Check if consent exists
        existing = self.get_consent(user_id, consent_type)

        if not existing:
            # Create new consent
            item = {
                "PK": pk,
                "SK": sk,
                "user_id": str(user_id),
                "consent_type": consent_type,
                "granted": granted,
                "granted_at": now if granted else None,
                "revoked_at": None if granted else now,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "reason": reason,
                "entity_type": "consent",
            }
            return self._put_item(item)
        else:
            # Update existing consent
            updates = {"granted": granted}

            if granted:
                updates["granted_at"] = now
                updates["revoked_at"] = None
            else:
                updates["revoked_at"] = now

            if ip_address:
                updates["ip_address"] = ip_address

            if user_agent:
                updates["user_agent"] = user_agent

            if reason:
                updates["reason"] = reason

            return self._update_item(pk=pk, sk=sk, updates=updates)
