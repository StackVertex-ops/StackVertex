"""AuditLog Repository - DynamoDB Data Access.

Handles audit log creation and querying with time-based partitioning
and pre-aggregated statistics support.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Attr, Key

from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository):
    """Repository for AuditLog entities.

    DynamoDB Structure:
        Audit Log Item:
            PK: AUDIT#{yyyymm}
            SK: {timestamp}#{log_id}
            Attributes: id, user, action, resource_type, resource_id,
                       ip_address, user_agent, details, success, error_message, timestamp
            GSI5: user#{user} + timestamp (list by user)
            GSI6: action#{action} + timestamp (list by action)

        Pre-Aggregated Stats Item:
            PK: STATS#AUDIT
            SK: REALTIME
            Attributes: total_logs, failed_count, action_counts (Map), user_counts (Map), last_updated

    Note:
        Time-based partitioning (AUDIT#{yyyymm}) ensures efficient queries
        and natural data lifecycle management.
    """

    def create(
        self,
        user: str,
        action: str,
        resource_type: str,
        resource_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None
    ) -> dict[str, Any]:
        """Create new audit log entry.

        Args:
            user: User who performed the action
            action: Action performed (deploy, cancel, retry, destroy, etc.)
            resource_type: Type of resource (deployment, architecture, etc.)
            resource_id: Optional resource UUID
            ip_address: Optional IP address
            user_agent: Optional user agent string
            details: Optional additional details (JSON)
            success: Whether action succeeded
            error_message: Optional error message (if success=False)

        Returns:
            Created audit log item

        Raises:
            Exception: If creation fails

        Note:
            This does NOT update pre-aggregated stats. Stats are updated
            via DynamoDB Streams + Lambda (see Phase 4 implementation).
        """
        log_id = str(uuid4())
        now = datetime.utcnow()
        timestamp_iso = now.isoformat()

        # Time-based partition key (AUDIT#{yyyymm})
        partition_suffix = now.strftime("%Y%m")

        # Sort key format: {timestamp}#{log_id} for chronological ordering
        sort_key = f"{timestamp_iso}#{log_id}"

        item: dict[str, Any] = {
            "PK": f"AUDIT#{partition_suffix}",
            "SK": sort_key,
            "id": log_id,
            "user": user,
            "action": action,
            "resource_type": resource_type,
            "success": success,
            "timestamp": timestamp_iso,
            "entity_type": "audit_log",
            # GSI attributes
            "GSI5PK": f"user#{user}",
            "GSI5SK": timestamp_iso,
            "GSI6PK": f"action#{action}",
            "GSI6SK": timestamp_iso,
        }

        # Optional fields
        if resource_id:
            item["resource_id"] = str(resource_id)
        if ip_address:
            item["ip_address"] = ip_address
        if user_agent:
            item["user_agent"] = user_agent
        if details:
            item["details"] = details
        if error_message:
            item["error_message"] = error_message

        return self._put_item(item)

    def get(self, log_id: UUID, timestamp: datetime) -> dict[str, Any] | None:
        """Get audit log by ID and timestamp.

        Args:
            log_id: Log UUID
            timestamp: Log timestamp (needed for partition key)

        Returns:
            Audit log item or None if not found

        Note:
            Requires timestamp to determine partition key (AUDIT#{yyyymm}).
        """
        partition_suffix = timestamp.strftime("%Y%m")
        timestamp_iso = timestamp.isoformat()

        # Query by PK and SK prefix
        items, _ = self._query(
            key_condition=Key("PK").eq(f"AUDIT#{partition_suffix}") & Key("SK").begins_with(f"{timestamp_iso}#{str(log_id)}")
        )

        return items[0] if items else None

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        user: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        """List audit logs with filtering and pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum items to return
            user: Optional filter by user
            action: Optional filter by action
            resource_type: Optional filter by resource type
            resource_id: Optional filter by resource ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Tuple of (items list, total count)

        Note:
            For best performance:
            - Provide user OR action for GSI queries
            - Provide start_date/end_date to limit partition scans
            - Avoid scanning all partitions (can be expensive)
        """
        items: list[dict[str, Any]] = []

        if user:
            # Query GSI5 (by user)
            filter_expr = None
            if action:
                filter_expr = Attr("action").eq(action)
            if resource_type:
                cond = Attr("resource_type").eq(resource_type)
                filter_expr = filter_expr & cond if filter_expr else cond
            if resource_id:
                cond = Attr("resource_id").eq(str(resource_id))
                filter_expr = filter_expr & cond if filter_expr else cond

            items, _ = self._query(
                key_condition=Key("GSI5PK").eq(f"user#{user}"),
                filter_condition=filter_expr,
                index_name="GSI5",
                scan_index_forward=False  # DESC order (newest first)
            )

        elif action:
            # Query GSI6 (by action)
            filter_expr = None
            if resource_type:
                filter_expr = Attr("resource_type").eq(resource_type)
            if resource_id:
                cond = Attr("resource_id").eq(str(resource_id))
                filter_expr = filter_expr & cond if filter_expr else cond

            items, _ = self._query(
                key_condition=Key("GSI6PK").eq(f"action#{action}"),
                filter_condition=filter_expr,
                index_name="GSI6",
                scan_index_forward=False  # DESC order (newest first)
            )

        else:
            # Scan recent partitions (last 3 months)
            # This is less efficient but supports arbitrary filtering
            end = end_date or datetime.utcnow()
            start = start_date or datetime(end.year, end.month - 2 if end.month > 2 else 12, 1)

            # Generate partition keys for date range
            current = end
            while current >= start:
                partition_suffix = current.strftime("%Y%m")

                # Build filter expression
                filter_expr = None
                if resource_type:
                    filter_expr = Attr("resource_type").eq(resource_type)
                if resource_id:
                    cond = Attr("resource_id").eq(str(resource_id))
                    filter_expr = filter_expr & cond if filter_expr else cond

                # Query partition
                partition_items, _ = self._query(
                    key_condition=Key("PK").eq(f"AUDIT#{partition_suffix}"),
                    filter_condition=filter_expr,
                    scan_index_forward=False  # DESC order (newest first)
                )
                items.extend(partition_items)

                # Move to previous month
                if current.month == 1:
                    current = datetime(current.year - 1, 12, 1)
                else:
                    current = datetime(current.year, current.month - 1, 1)

            # Sort by timestamp DESC (newest first)
            items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Get total count before pagination
        total = len(items)

        # Apply skip/limit
        paginated_items = items[skip : skip + limit]

        return paginated_items, total

    def get_stats(self) -> dict[str, Any]:
        """Get pre-aggregated audit log statistics.

        Returns:
            Statistics dict with total_logs, failed_count, action_counts, user_counts

        Note:
            Returns pre-aggregated stats from STATS#AUDIT/REALTIME item.
            This item is updated in real-time via DynamoDB Streams + Lambda.
            If stats item doesn't exist yet, returns empty stats.
        """
        stats_item = self._get_item("STATS#AUDIT", "REALTIME")

        if not stats_item:
            # Stats not initialized yet (will be created by Lambda on first audit log)
            return {
                "total_logs": 0,
                "failed_count": 0,
                "action_counts": {},
                "user_counts": {},
                "last_updated": None
            }

        return {
            "total_logs": stats_item.get("total_logs", 0),
            "failed_count": stats_item.get("failed_count", 0),
            "action_counts": stats_item.get("action_counts", {}),
            "user_counts": stats_item.get("user_counts", {}),
            "last_updated": stats_item.get("last_updated")
        }

    def initialize_stats(self) -> dict[str, Any]:
        """Initialize stats item (for testing or manual setup).

        Returns:
            Created stats item

        Note:
            Normally, stats are created automatically by DynamoDB Streams Lambda.
            This method is useful for testing or manual initialization.
        """
        stats_item = {
            "PK": "STATS#AUDIT",
            "SK": "REALTIME",
            "total_logs": 0,
            "failed_count": 0,
            "action_counts": {},
            "user_counts": {},
            "entity_type": "audit_stats"
        }

        return self._put_item(stats_item)
