"""Unit tests für AuditLogRepository.

Fokus: Time-Partitioning (AUDIT#{yyyymm}), GSI Queries, Stats.
"""

import pytest
from uuid import uuid4
from freezegun import freeze_time
from datetime import datetime


class TestAuditLogCreate:
    """Tests für create() method."""

    @freeze_time("2026-04-24 10:30:00")
    def test_create_audit_log(self, audit_log_repository):
        """Test creating audit log mit time-based partitioning."""
        result = audit_log_repository.create(
            user="test_user",
            action="deploy",
            resource_type="deployment",
            resource_id=str(uuid4()),
            success=True
        )

        # Verify partition key format: AUDIT#{yyyymm}
        assert result["PK"] == "AUDIT#202604"

        # Verify sort key format: {timestamp}#{log_id}
        assert result["SK"].startswith("2026-04-24T10:30:00")
        assert "#" in result["SK"]

        # Verify GSI attributes
        assert result["GSI5PK"] == "user#test_user"
        assert result["GSI6PK"] == "action#deploy"

    @freeze_time("2026-12-31 23:59:59")
    def test_create_audit_log_december(self, audit_log_repository):
        """Test creating audit log in December (year boundary)."""
        result = audit_log_repository.create(
            user="test_user",
            action="deploy",
            resource_type="deployment",
            success=True
        )

        # Should be AUDIT#202612
        assert result["PK"] == "AUDIT#202612"

    def test_create_failed_action_with_error(self, audit_log_repository):
        """Test creating audit log für failed action."""
        result = audit_log_repository.create(
            user="test_user",
            action="deploy",
            resource_type="deployment",
            success=False,
            error_message="Terraform apply failed"
        )

        assert result["success"] is False
        assert result["error_message"] == "Terraform apply failed"

    def test_create_with_details(self, audit_log_repository):
        """Test creating audit log mit details JSON."""
        details = {
            "deployment_id": str(uuid4()),
            "architecture_id": str(uuid4()),
            "duration_seconds": 120
        }

        result = audit_log_repository.create(
            user="test_user",
            action="deploy",
            resource_type="deployment",
            success=True,
            details=details
        )

        assert result["details"] == details


class TestAuditLogGet:
    """Tests für get() method."""

    @freeze_time("2026-04-24 15:00:00")
    def test_get_audit_log(self, audit_log_repository):
        """Test getting audit log by timestamp and id."""
        created = audit_log_repository.create(
            user="test_user",
            action="deploy",
            resource_type="deployment",
            success=True
        )

        log_id = created["id"]
        timestamp_str = created["timestamp"]
        # Parse timestamp string to datetime
        timestamp = datetime.fromisoformat(timestamp_str)

        result = audit_log_repository.get(log_id, timestamp)

        assert result is not None
        assert result["id"] == log_id

    def test_get_nonexistent_audit_log(self, audit_log_repository):
        """Test getting non-existent audit log returns None."""
        fake_id = str(uuid4())
        fake_timestamp = datetime.fromisoformat("2026-04-24T12:00:00")

        result = audit_log_repository.get(fake_id, fake_timestamp)

        assert result is None


class TestAuditLogList:
    """Tests für list() method."""

    @freeze_time("2026-04-24 12:00:00")
    def test_list_by_user(self, audit_log_repository):
        """Test listing audit logs by user (GSI5)."""
        # Create logs for different users
        for user in ["user1", "user2", "user1"]:
            audit_log_repository.create(
                user=user,
                action="deploy",
                resource_type="deployment",
                success=True
            )

        items, total = audit_log_repository.list(user="user1")

        assert total == 2
        assert all(item["user"] == "user1" for item in items)

    @freeze_time("2026-04-24 12:00:00")
    def test_list_by_action(self, audit_log_repository):
        """Test listing audit logs by action (GSI6)."""
        actions = ["deploy", "cancel", "deploy", "destroy"]
        for action in actions:
            audit_log_repository.create(
                user="test",
                action=action,
                resource_type="deployment",
                success=True
            )

        items, total = audit_log_repository.list(action="deploy")

        assert total == 2
        assert all(item["action"] == "deploy" for item in items)

    def test_list_cross_month_queries(self, audit_log_repository):
        """Test querying across multiple month partitions."""
        # Create logs in different months
        with freeze_time("2026-03-15 12:00:00"):
            audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )

        with freeze_time("2026-04-10 12:00:00"):
            audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )

        with freeze_time("2026-05-05 12:00:00"):
            audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )

        # List without date filter (scans recent months)
        with freeze_time("2026-05-10 12:00:00"):
            items, total = audit_log_repository.list()

            # Should find logs from multiple months
            assert total >= 3

    def test_list_sort_order_newest_first(self, audit_log_repository):
        """Test list returns logs in DESC order (newest first)."""
        # Create logs at different times (without freezegun)
        log_ids = []
        timestamps = []

        with freeze_time("2026-04-24 12:00:00"):
            result = audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )
            log_ids.append(result["id"])
            timestamps.append(result["timestamp"])

        with freeze_time("2026-04-24 12:01:00"):
            result = audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )
            log_ids.append(result["id"])
            timestamps.append(result["timestamp"])

        with freeze_time("2026-04-24 12:02:00"):
            result = audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )
            log_ids.append(result["id"])
            timestamps.append(result["timestamp"])

        # List (should be DESC order - newest first)
        items, _ = audit_log_repository.list()

        # First item should have latest timestamp
        assert items[0]["timestamp"] == timestamps[-1]
        assert items[0]["id"] == log_ids[-1]

    @freeze_time("2026-04-24 12:00:00")
    def test_list_pagination(self, audit_log_repository):
        """Test list pagination mit skip/limit."""
        # Create 10 logs
        for i in range(10):
            audit_log_repository.create(
                user="test",
                action="deploy",
                resource_type="deployment",
                success=True
            )

        # First page
        items_page1, total = audit_log_repository.list(skip=0, limit=3)
        assert len(items_page1) == 3
        assert total == 10

        # Second page
        items_page2, _ = audit_log_repository.list(skip=3, limit=3)
        assert len(items_page2) == 3

        # Verify different items
        ids_page1 = {item["id"] for item in items_page1}
        ids_page2 = {item["id"] for item in items_page2}
        assert ids_page1.isdisjoint(ids_page2)


class TestAuditLogStats:
    """Tests für stats methods."""

    def test_get_stats_not_initialized(self, audit_log_repository):
        """Test get_stats returns empty when not initialized."""
        stats = audit_log_repository.get_stats()

        assert stats["total_logs"] == 0
        assert stats["failed_count"] == 0
        assert stats["action_counts"] == {}
        assert stats["user_counts"] == {}
        assert stats["last_updated"] is None

    def test_initialize_stats(self, audit_log_repository):
        """Test initializing stats item."""
        stats_item = audit_log_repository.initialize_stats()

        assert stats_item["PK"] == "STATS#AUDIT"
        assert stats_item["SK"] == "REALTIME"
        assert stats_item["total_logs"] == 0
        assert stats_item["failed_count"] == 0

        # Verify retrieval
        stats = audit_log_repository.get_stats()
        assert stats["total_logs"] == 0

    def test_get_stats_after_initialization(self, audit_log_repository):
        """Test get_stats after initialization returns initialized values."""
        # Initialize
        audit_log_repository.initialize_stats()

        # Get stats
        stats = audit_log_repository.get_stats()

        assert stats["total_logs"] == 0
        assert stats["failed_count"] == 0
        assert "action_counts" in stats
        assert "user_counts" in stats
