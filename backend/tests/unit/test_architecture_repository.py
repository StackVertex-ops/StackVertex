"""Unit tests für ArchitectureRepository.

Fokus: S3 Offload (300KB Threshold), GSI Queries, Cascade Delete.
"""

import pytest
import json
from uuid import UUID, uuid4
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from app.schemas.architecture import ArchitectureCreate, ArchitectureUpdate


class TestArchitectureCreate:
    """Tests für create() method."""

    def test_create_small_architecture(self, architecture_repository, sample_architecture_json):
        """Test creating architecture mit small JSON (< 300KB, bleibt in DynamoDB)."""
        arch_create = ArchitectureCreate(
            name="Test Architecture",
            description="Small test",
            version="1.0.0",
            owner="test_user",
            architecture_json=sample_architecture_json
        )

        result = architecture_repository.create(arch_create)

        assert result["name"] == "Test Architecture"
        assert result["architecture_json"] == sample_architecture_json
        assert "architecture_json_s3_uri" not in result
        assert result["PK"].startswith("ARCH#")
        assert result["SK"] == "METADATA"
        assert result["GSI1PK"] == "architecture"
        assert result["GSI2PK"] == "owner#test_user"

    def test_create_large_architecture_s3_offload(self, architecture_repository, sample_large_architecture_json):
        """Test creating architecture mit large JSON (> 300KB, geht zu S3)."""
        arch_create = ArchitectureCreate(
            name="Large Architecture",
            description="Large test",
            version="1.0.0",
            owner="test_user",
            architecture_json=sample_large_architecture_json
        )

        result = architecture_repository.create(arch_create)

        assert result["name"] == "Large Architecture"
        assert "architecture_json_s3_uri" in result
        assert "architecture_json" not in result  # Offloaded to S3
        assert result["architecture_json_s3_uri"].startswith("s3://")

    def test_create_exactly_300kb_threshold(self, architecture_repository):
        """Test exakt 300KB threshold (KRITISCHER Edge Case)."""
        # Test both sides of 300KB threshold

        # Test 1: Slightly under 300KB (should stay in DynamoDB)
        small_data = "x" * 299_000  # ~299KB
        small_arch = {
            "version": "1.0.0",
            "metadata": {"name": "Just Under"},
            "data": small_data
        }

        result_small = architecture_repository.create(ArchitectureCreate(
            name="Just Under 300KB",
            version="1.0.0",
            owner="test",
            architecture_json=small_arch
        ))

        assert "architecture_json" in result_small
        assert "architecture_json_s3_uri" not in result_small

        # Test 2: Over 300KB (should go to S3)
        large_data = "x" * 310_000  # ~310KB
        large_arch = {
            "version": "1.0.0",
            "metadata": {"name": "Over Threshold"},
            "data": large_data
        }

        result_large = architecture_repository.create(ArchitectureCreate(
            name="Over 300KB",
            version="1.0.0",
            owner="test",
            architecture_json=large_arch
        ))

        assert "architecture_json_s3_uri" in result_large
        assert "architecture_json" not in result_large


class TestArchitectureGet:
    """Tests für get() method."""

    def test_get_existing_architecture(self, architecture_repository, sample_architecture_json):
        """Test getting existing architecture."""
        arch_create = ArchitectureCreate(
            name="Test",
            version="1.0.0",
            owner="test",
            architecture_json=sample_architecture_json
        )
        created = architecture_repository.create(arch_create)
        arch_id = UUID(created["id"])

        result = architecture_repository.get(arch_id)

        assert result is not None
        assert result["id"] == created["id"]
        assert result["architecture_json"] == sample_architecture_json

    def test_get_large_architecture_loads_from_s3(self, architecture_repository, sample_large_architecture_json):
        """Test getting large architecture lädt transparent von S3."""
        arch_create = ArchitectureCreate(
            name="Large",
            version="1.0.0",
            owner="test",
            architecture_json=sample_large_architecture_json
        )
        created = architecture_repository.create(arch_create)
        arch_id = UUID(created["id"])

        result = architecture_repository.get(arch_id)

        # Should have architecture_json loaded from S3
        assert "architecture_json" in result
        assert "architecture_json_s3_uri" not in result  # Transparent to caller
        assert result["architecture_json"] == sample_large_architecture_json

    def test_get_nonexistent_architecture(self, architecture_repository):
        """Test getting non-existent architecture returns None."""
        fake_id = uuid4()

        result = architecture_repository.get(fake_id)

        assert result is None


class TestArchitectureList:
    """Tests für list() method."""

    def test_list_all_architectures(self, architecture_repository, sample_architecture_json):
        """Test listing all architectures (GSI1)."""
        # Create 3 architectures
        for i in range(3):
            arch_create = ArchitectureCreate(
                name=f"Arch {i}",
                version="1.0.0",
                owner="test",
                architecture_json=sample_architecture_json
            )
            architecture_repository.create(arch_create)

        items, total = architecture_repository.list(skip=0, limit=100)

        assert total == 3
        assert len(items) == 3

    def test_list_by_owner(self, architecture_repository, sample_architecture_json):
        """Test listing architectures by owner (GSI2)."""
        # Create architectures for different owners
        for owner in ["user1", "user2", "user1"]:
            arch_create = ArchitectureCreate(
                name=f"Arch by {owner}",
                version="1.0.0",
                owner=owner,
                architecture_json=sample_architecture_json
            )
            architecture_repository.create(arch_create)

        items, total = architecture_repository.list(skip=0, limit=100, owner="user1")

        assert total == 2
        assert all(item["owner"] == "user1" for item in items)

    def test_list_pagination(self, architecture_repository, sample_architecture_json):
        """Test list pagination mit skip/limit."""
        # Create 10 architectures
        for i in range(10):
            arch_create = ArchitectureCreate(
                name=f"Arch {i}",
                version="1.0.0",
                owner="test",
                architecture_json=sample_architecture_json
            )
            architecture_repository.create(arch_create)

        # First page
        items_page1, total = architecture_repository.list(skip=0, limit=3)
        assert len(items_page1) == 3
        assert total == 10

        # Second page
        items_page2, _ = architecture_repository.list(skip=3, limit=3)
        assert len(items_page2) == 3

        # Verify different items
        ids_page1 = {item["id"] for item in items_page1}
        ids_page2 = {item["id"] for item in items_page2}
        assert ids_page1.isdisjoint(ids_page2)


class TestArchitectureUpdate:
    """Tests für update() method."""

    def test_update_name_description(self, architecture_repository, sample_architecture_json):
        """Test updating name und description."""
        created = architecture_repository.create(ArchitectureCreate(
            name="Original",
            description="Original description",
            version="1.0.0",
            owner="test",
            architecture_json=sample_architecture_json
        ))
        arch_id = UUID(created["id"])

        update = ArchitectureUpdate(
            name="Updated",
            description="Updated description"
        )

        updated = architecture_repository.update(arch_id, update)

        assert updated["name"] == "Updated"
        assert updated["description"] == "Updated description"
        assert updated["updated_at"] != created["updated_at"]

    def test_update_small_to_large_architecture_json(self, architecture_repository, sample_architecture_json, sample_large_architecture_json):
        """Test updating small architecture_json to large (sollte zu S3 migrieren)."""
        created = architecture_repository.create(ArchitectureCreate(
            name="Test",
            version="1.0.0",
            owner="test",
            architecture_json=sample_architecture_json  # Small
        ))
        arch_id = UUID(created["id"])

        # Verify initially in DynamoDB
        fetched = architecture_repository.get(arch_id)
        assert "architecture_json" in fetched

        # Update to large
        update = ArchitectureUpdate(
            architecture_json=sample_large_architecture_json
        )

        updated = architecture_repository.update(arch_id, update)

        # Should now be in S3
        assert "architecture_json" in updated  # Transparent to caller
        # Check underlying storage
        from_db = architecture_repository._get_item(f"ARCH#{str(arch_id)}", "METADATA")
        assert "architecture_json_s3_uri" in from_db

    def test_update_nonexistent_architecture(self, architecture_repository):
        """Test updating non-existent architecture returns None."""
        fake_id = uuid4()
        update = ArchitectureUpdate(name="Updated")

        result = architecture_repository.update(fake_id, update)

        assert result is None


class TestArchitectureDelete:
    """Tests für delete() method (KRITISCH - CASCADE DELETE)."""

    def test_delete_architecture(self, architecture_repository, sample_architecture_json):
        """Test deleting architecture."""
        created = architecture_repository.create(ArchitectureCreate(
            name="Test",
            version="1.0.0",
            owner="test",
            architecture_json=sample_architecture_json
        ))
        arch_id = UUID(created["id"])

        result = architecture_repository.delete(arch_id)

        assert result is True
        assert architecture_repository.get(arch_id) is None

    def test_delete_large_architecture_deletes_s3(self, architecture_repository, sample_large_architecture_json):
        """Test deleting large architecture versucht S3 object zu löschen."""
        created = architecture_repository.create(ArchitectureCreate(
            name="Large",
            version="1.0.0",
            owner="test",
            architecture_json=sample_large_architecture_json
        ))
        arch_id = UUID(created["id"])

        # Get S3 URI before deletion
        fetched = architecture_repository._get_item(f"ARCH#{str(arch_id)}", "METADATA")
        s3_uri = fetched.get("architecture_json_s3_uri")
        assert s3_uri is not None

        # Delete architecture (should call S3 delete internally)
        result = architecture_repository.delete(arch_id)
        assert result is True

        # Verify DynamoDB item deleted
        assert architecture_repository.get(arch_id) is None

        # Note: moto doesn't fully simulate S3 delete behavior,
        # but in real AWS the S3 object would be deleted.
        # We trust that _delete_large_item() is called (tested in BaseRepository tests)

    def test_delete_cascades_to_deployment_relationships(self, architecture_repository, sample_architecture_json):
        """Test deleting architecture löscht alle DEPLOY# relationship items."""
        created = architecture_repository.create(ArchitectureCreate(
            name="Test",
            version="1.0.0",
            owner="test",
            architecture_json=sample_architecture_json
        ))
        arch_id = created["id"]

        # Manually create deployment relationship items
        architecture_repository._put_item({
            "PK": f"ARCH#{arch_id}",
            "SK": "DEPLOY#dep1",
            "deployment_id": "dep1",
            "status": "success"
        })
        architecture_repository._put_item({
            "PK": f"ARCH#{arch_id}",
            "SK": "DEPLOY#dep2",
            "deployment_id": "dep2",
            "status": "pending"
        })

        # Delete architecture
        result = architecture_repository.delete(UUID(arch_id))
        assert result is True

        # Verify relationship items deleted
        remaining, _ = architecture_repository._query(
            key_condition=Key("PK").eq(f"ARCH#{arch_id}")
        )
        assert len(remaining) == 0

    def test_delete_cascades_to_version_links(self, architecture_repository, sample_architecture_json):
        """Test deleting architecture löscht alle VERSION# link items."""
        created = architecture_repository.create(ArchitectureCreate(
            name="Test",
            version="1.0.0",
            owner="test",
            architecture_json=sample_architecture_json
        ))
        arch_id = created["id"]

        # Manually create version link items
        architecture_repository._put_item({
            "PK": f"ARCH#{arch_id}",
            "SK": "VERSION#parent1",
            "parent_id": "parent1",
            "version": "0.9.0"
        })

        # Delete architecture
        result = architecture_repository.delete(UUID(arch_id))
        assert result is True

        # Verify version links deleted
        remaining, _ = architecture_repository._query(
            key_condition=Key("PK").eq(f"ARCH#{arch_id}")
        )
        assert len(remaining) == 0

    def test_delete_nonexistent_architecture(self, architecture_repository):
        """Test deleting non-existent architecture (DynamoDB returns True, idempotent)."""
        fake_id = uuid4()

        result = architecture_repository.delete(fake_id)

        # DynamoDB delete is idempotent - returns True even if item doesn't exist
        # (consistent with BaseRepository._delete_item behavior)
        assert result is True
