"""Unit tests für BaseRepository.

Nutzt moto für mocked DynamoDB und S3.
Fokus: Timestamps, S3 Offload (300KB Threshold), Pagination, Error Handling.
"""

import pytest
import json
from datetime import datetime
from freezegun import freeze_time
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


class TestBaseRepositoryPutItem:
    """Tests für _put_item method."""

    def test_put_item_creates_timestamps(self, base_repository):
        """Test dass _put_item created_at und updated_at hinzufügt."""
        item = {
            "PK": "TEST#1",
            "SK": "METADATA",
            "name": "Test Item"
        }

        result = base_repository._put_item(item)

        assert "created_at" in result
        assert "updated_at" in result
        assert result["created_at"] == result["updated_at"]
        # Verify ISO format
        datetime.fromisoformat(result["created_at"])

    def test_put_item_preserves_existing_created_at(self, base_repository):
        """Test dass _put_item existierendes created_at NICHT überschreibt."""
        original_created = "2025-01-01T00:00:00"

        item = {
            "PK": "TEST#2",
            "SK": "METADATA",
            "created_at": original_created,
            "name": "Test"
        }

        result = base_repository._put_item(item)

        assert result["created_at"] == original_created
        assert result["updated_at"] != original_created  # updated_at ist neuer

    def test_put_item_updates_updated_at(self, base_repository):
        """Test dass _put_item immer updated_at aktualisiert."""
        with freeze_time("2025-01-01 12:00:00"):
            item1 = {"PK": "TEST#3", "SK": "METADATA", "value": 1}
            result1 = base_repository._put_item(item1)
            first_updated = result1["updated_at"]

        with freeze_time("2025-01-01 13:00:00"):
            item2 = {
                "PK": "TEST#3",
                "SK": "METADATA",
                "created_at": result1["created_at"],
                "value": 2
            }
            result2 = base_repository._put_item(item2)

        assert result2["updated_at"] != first_updated
        assert result2["updated_at"] > first_updated


class TestBaseRepositoryGetItem:
    """Tests für _get_item method."""

    def test_get_item_existing(self, base_repository):
        """Test getting existing item."""
        base_repository._put_item({"PK": "TEST#1", "SK": "DATA", "value": 42})

        result = base_repository._get_item("TEST#1", "DATA")

        assert result is not None
        assert result["value"] == 42

    def test_get_item_not_found(self, base_repository):
        """Test getting non-existent item returns None."""
        result = base_repository._get_item("NONEXISTENT", "METADATA")

        assert result is None


class TestBaseRepositoryQuery:
    """Tests für _query method."""

    def test_query_basic(self, base_repository):
        """Test basic query by partition key."""
        # Insert test data
        base_repository._put_item({"PK": "ARCH#1", "SK": "METADATA", "name": "Arch1"})
        base_repository._put_item({"PK": "ARCH#1", "SK": "DEPLOY#1", "status": "pending"})
        base_repository._put_item({"PK": "ARCH#1", "SK": "DEPLOY#2", "status": "success"})
        base_repository._put_item({"PK": "ARCH#2", "SK": "METADATA", "name": "Arch2"})

        items, last_key = base_repository._query(
            key_condition=Key("PK").eq("ARCH#1")
        )

        assert len(items) == 3
        assert all(item["PK"] == "ARCH#1" for item in items)
        assert last_key is None  # No pagination

    def test_query_with_filter(self, base_repository):
        """Test query with filter expression."""
        base_repository._put_item({"PK": "ARCH#1", "SK": "DEPLOY#1", "status": "pending"})
        base_repository._put_item({"PK": "ARCH#1", "SK": "DEPLOY#2", "status": "success"})

        items, _ = base_repository._query(
            key_condition=Key("PK").eq("ARCH#1"),
            filter_condition=Attr("status").eq("success")
        )

        assert len(items) == 1
        assert items[0]["SK"] == "DEPLOY#2"

    def test_query_pagination(self, base_repository):
        """Test query with pagination (limit and exclusive_start_key)."""
        # Insert 10 items
        for i in range(10):
            base_repository._put_item({
                "PK": "TEST#PAGINATION",
                "SK": f"ITEM#{i:02d}",
                "value": i
            })

        # First page (limit 3)
        items_page1, last_key_page1 = base_repository._query(
            key_condition=Key("PK").eq("TEST#PAGINATION"),
            limit=3
        )

        assert len(items_page1) == 3
        assert last_key_page1 is not None

        # Second page (continue from last_key)
        items_page2, last_key_page2 = base_repository._query(
            key_condition=Key("PK").eq("TEST#PAGINATION"),
            limit=3,
            exclusive_start_key=last_key_page1
        )

        assert len(items_page2) == 3
        assert items_page2[0]["SK"] != items_page1[0]["SK"]  # Different items
        assert last_key_page2 is not None

    def test_query_sort_order(self, base_repository):
        """Test scan_index_forward controls sort order."""
        base_repository._put_item({"PK": "TEST", "SK": "C", "name": "Third"})
        base_repository._put_item({"PK": "TEST", "SK": "A", "name": "First"})
        base_repository._put_item({"PK": "TEST", "SK": "B", "name": "Second"})

        # Ascending
        items_asc, _ = base_repository._query(
            key_condition=Key("PK").eq("TEST"),
            scan_index_forward=True
        )
        assert [item["SK"] for item in items_asc] == ["A", "B", "C"]

        # Descending
        items_desc, _ = base_repository._query(
            key_condition=Key("PK").eq("TEST"),
            scan_index_forward=False
        )
        assert [item["SK"] for item in items_desc] == ["C", "B", "A"]


class TestBaseRepositoryUpdateItem:
    """Tests für _update_item method."""

    def test_update_item_success(self, base_repository):
        """Test successful update."""
        base_repository._put_item({"PK": "TEST#1", "SK": "METADATA", "value": 1})

        updated = base_repository._update_item(
            "TEST#1", "METADATA",
            {"value": 2, "new_field": "added"}
        )

        assert updated["value"] == 2
        assert updated["new_field"] == "added"
        assert "updated_at" in updated

    def test_update_item_sets_updated_at(self, base_repository):
        """Test dass _update_item automatisch updated_at setzt."""
        base_repository._put_item({"PK": "TEST#2", "SK": "METADATA", "value": 1})
        original = base_repository._get_item("TEST#2", "METADATA")
        original_updated_at = original["updated_at"]

        # Wait a bit
        import time
        time.sleep(0.1)

        updated = base_repository._update_item(
            "TEST#2", "METADATA",
            {"value": 2}
        )

        assert updated["updated_at"] != original_updated_at
        assert updated["updated_at"] > original_updated_at

    def test_update_item_with_condition_success(self, base_repository):
        """Test conditional update succeeds when condition met."""
        base_repository._put_item({"PK": "TEST#3", "SK": "METADATA", "status": "pending"})

        updated = base_repository._update_item(
            "TEST#3", "METADATA",
            {"status": "processing"},
            condition_expression=Attr("status").eq("pending")
        )

        assert updated["status"] == "processing"

    def test_update_item_with_condition_fails(self, base_repository):
        """Test conditional update throws exception when condition fails."""
        base_repository._put_item({"PK": "TEST#4", "SK": "METADATA", "status": "completed"})

        with pytest.raises(ClientError) as exc_info:
            base_repository._update_item(
                "TEST#4", "METADATA",
                {"status": "processing"},
                condition_expression=Attr("status").eq("pending")
            )

        assert exc_info.value.response["Error"]["Code"] == "ConditionalCheckFailedException"


class TestBaseRepositoryDeleteItem:
    """Tests für _delete_item method."""

    def test_delete_item_success(self, base_repository):
        """Test successful deletion returns True."""
        base_repository._put_item({"PK": "TEST#1", "SK": "METADATA"})

        result = base_repository._delete_item("TEST#1", "METADATA")

        assert result is True
        assert base_repository._get_item("TEST#1", "METADATA") is None

    def test_delete_nonexistent_item(self, base_repository):
        """Test deleting non-existent item returns True (DynamoDB behavior)."""
        result = base_repository._delete_item("NONEXISTENT", "METADATA")

        # DynamoDB delete is idempotent - returns success even if item doesn't exist
        assert result is True

    def test_delete_with_condition_success(self, base_repository):
        """Test conditional delete succeeds when condition met."""
        base_repository._put_item({"PK": "TEST#2", "SK": "METADATA", "deletable": True})

        result = base_repository._delete_item(
            "TEST#2", "METADATA",
            condition_expression=Attr("deletable").eq(True)
        )

        assert result is True

    def test_delete_with_condition_fails(self, base_repository):
        """Test conditional delete returns False when condition fails."""
        base_repository._put_item({"PK": "TEST#3", "SK": "METADATA", "deletable": False})

        result = base_repository._delete_item(
            "TEST#3", "METADATA",
            condition_expression=Attr("deletable").eq(True)
        )

        # NOTE: _delete_item catches exception and returns False
        assert result is False
        # Item should still exist
        assert base_repository._get_item("TEST#3", "METADATA") is not None


class TestBaseRepositoryBatchOperations:
    """Tests für batch get/write operations."""

    def test_batch_get_items(self, base_repository):
        """Test batch get multiple items."""
        base_repository._put_item({"PK": "ITEM#1", "SK": "DATA", "value": 1})
        base_repository._put_item({"PK": "ITEM#2", "SK": "DATA", "value": 2})
        base_repository._put_item({"PK": "ITEM#3", "SK": "DATA", "value": 3})

        keys = [
            {"PK": "ITEM#1", "SK": "DATA"},
            {"PK": "ITEM#2", "SK": "DATA"},
            {"PK": "ITEM#999", "SK": "DATA"}  # Non-existent
        ]

        items = base_repository._batch_get_items(keys)

        # Order not guaranteed, but should get 2 items
        assert len(items) == 2
        values = {item["value"] for item in items}
        assert values == {1, 2}

    def test_batch_get_empty_keys(self, base_repository):
        """Test batch get with empty keys returns empty list."""
        items = base_repository._batch_get_items([])

        assert items == []

    def test_batch_write_items_put(self, base_repository):
        """Test batch write with put requests."""
        items = [
            {"PK": "BATCH#1", "SK": "DATA", "value": 1},
            {"PK": "BATCH#2", "SK": "DATA", "value": 2},
        ]

        result = base_repository._batch_write_items(items)

        assert result is True
        assert base_repository._get_item("BATCH#1", "DATA")["value"] == 1
        assert base_repository._get_item("BATCH#2", "DATA")["value"] == 2

    def test_batch_write_items_delete(self, base_repository):
        """Test batch write with delete requests."""
        base_repository._put_item({"PK": "DELETE#1", "SK": "DATA"})
        base_repository._put_item({"PK": "DELETE#2", "SK": "DATA"})

        delete_keys = [
            {"PK": "DELETE#1", "SK": "DATA"},
            {"PK": "DELETE#2", "SK": "DATA"},
        ]

        result = base_repository._batch_write_items([], delete_keys)

        assert result is True
        assert base_repository._get_item("DELETE#1", "DATA") is None
        assert base_repository._get_item("DELETE#2", "DATA") is None


class TestBaseRepositoryS3Offload:
    """Tests für S3 large item storage (KRITISCH!)."""

    def test_store_large_item(self, base_repository):
        """Test storing large item in S3."""
        large_data = "x" * 500_000  # 500KB
        s3_key = "test/large_item.json"

        s3_uri = base_repository._store_large_item(large_data, s3_key)

        assert s3_uri.startswith("s3://")
        assert "stackvertex-test-bucket" in s3_uri
        assert s3_key in s3_uri

    def test_load_large_item(self, base_repository):
        """Test loading large item from S3."""
        test_data = "Large test data content"
        s3_key = "test/load_test.json"

        s3_uri = base_repository._store_large_item(test_data, s3_key)
        loaded_data = base_repository._load_large_item(s3_uri)

        assert loaded_data == test_data

    def test_delete_large_item(self, base_repository):
        """Test deleting large item from S3."""
        test_data = "Data to be deleted"
        s3_key = "test/delete_test.json"

        s3_uri = base_repository._store_large_item(test_data, s3_key)
        result = base_repository._delete_large_item(s3_uri)

        assert result is True

        # Verify deletion
        with pytest.raises(ClientError) as exc_info:
            base_repository._load_large_item(s3_uri)
        assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"

    def test_store_and_load_utf8_data(self, base_repository):
        """Test S3 offload mit UTF-8 Sonderzeichen (Umlaute)."""
        test_data = "Tëst däta wïth Ümlaütë: äöüßÄÖÜ 中文"
        s3_key = "test/utf8_test.json"

        s3_uri = base_repository._store_large_item(test_data, s3_key)
        loaded_data = base_repository._load_large_item(s3_uri)

        assert loaded_data == test_data
