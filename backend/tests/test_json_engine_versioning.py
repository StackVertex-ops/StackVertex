"""Tests für VersioningService.

Testet Version Creation, History Tracking und Diff Generation.
"""

import pytest
from uuid import uuid4

from app.core.json_engine.versioning import VersioningService
from app.core.json_engine.exceptions import (
    ValidationError,
    VersionNotFoundError,
    CircularReferenceError
)


class TestVersioningService:
    """Tests für VersioningService."""

    def test_create_version_valid(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Erstelle Version mit validem JSON."""
        service = VersioningService()

        arch = service.create_version(
            db_session,
            sample_architecture_minimal,
            name="Test Version",
            owner="test-user"
        )

        assert arch is not None
        assert arch.name == "Test Version"
        assert arch.version == "1.0.0"

    def test_create_version_with_parent(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Erstelle Child Version mit Parent."""
        service = VersioningService()

        # Create parent
        parent = service.create_version(
            db_session,
            sample_architecture_minimal,
            name="Parent",
            owner="test-user"
        )

        # Create child
        child = service.create_version(
            db_session,
            sample_architecture_minimal,
            name="Child",
            owner="test-user",
            parent_version_id=parent.id
        )

        assert child.architecture_json["metadata"]["parent_version"] == str(parent.id)

    def test_create_version_invalid_json(self, db_session):
        """Test: Erstelle Version mit invalidem JSON."""
        service = VersioningService()

        invalid_json = {"version": "1.0.0"}

        with pytest.raises(ValidationError):
            service.create_version(
                db_session,
                invalid_json,
                name="Invalid",
                owner="test-user",
                validate=True
            )

    def test_create_version_skip_validation(self, db_session):
        """Test: Erstelle Version ohne Validation."""
        service = VersioningService()

        # Invalid JSON but validation skipped
        invalid_json = {"version": "1.0.0", "metadata": {}}

        arch = service.create_version(
            db_session,
            invalid_json,
            name="No Validation",
            owner="test-user",
            validate=False
        )

        assert arch is not None

    def test_get_version_history_single(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Version History mit single version."""
        service = VersioningService()

        arch = service.create_version(
            db_session,
            sample_architecture_minimal,
            name="Single",
            owner="test-user"
        )

        history = service.get_version_history(db_session, arch.id)

        assert len(history) == 1
        assert history[0].id == arch.id

    def test_get_version_history_chain(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Version History mit parent-child chain."""
        service = VersioningService()

        # Create version chain
        v1 = service.create_version(
            db_session, sample_architecture_minimal, name="V1", owner="user"
        )
        v2 = service.create_version(
            db_session, sample_architecture_minimal, name="V2", owner="user",
            parent_version_id=v1.id
        )
        v3 = service.create_version(
            db_session, sample_architecture_minimal, name="V3", owner="user",
            parent_version_id=v2.id
        )

        history = service.get_version_history(db_session, v3.id)

        assert len(history) == 3
        assert history[0].id == v3.id  # Neueste zuerst
        assert history[1].id == v2.id
        assert history[2].id == v1.id

    def test_get_version_history_with_limit(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Version History mit limit."""
        service = VersioningService()

        # Create chain
        v1 = service.create_version(
            db_session, sample_architecture_minimal, name="V1", owner="user"
        )
        v2 = service.create_version(
            db_session, sample_architecture_minimal, name="V2", owner="user",
            parent_version_id=v1.id
        )
        v3 = service.create_version(
            db_session, sample_architecture_minimal, name="V3", owner="user",
            parent_version_id=v2.id
        )

        history = service.get_version_history(db_session, v3.id, limit=2)

        assert len(history) == 2

    def test_get_version_history_not_found(self, db_session):
        """Test: Version History für nicht-existente Version."""
        service = VersioningService()

        with pytest.raises(VersionNotFoundError):
            service.get_version_history(db_session, uuid4())

    def test_compare_versions(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Compare zwei Versionen."""
        service = VersioningService()

        v1 = service.create_version(
            db_session, sample_architecture_minimal, name="V1", owner="user"
        )

        # Modified version
        modified_json = sample_architecture_minimal.copy()
        modified_json["metadata"]["name"] = "Modified"

        v2 = service.create_version(
            db_session, modified_json, name="V2", owner="user",
            validate=False
        )

        comparison = service.compare_versions(db_session, v1.id, v2.id)

        assert "version_a" in comparison
        assert "version_b" in comparison
        assert "diff" in comparison
        assert comparison["version_a"]["id"] == str(v1.id)
        assert comparison["version_b"]["id"] == str(v2.id)

    def test_compare_versions_with_component_diff(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Compare mit Component-Level Diff."""
        service = VersioningService()

        v1 = service.create_version(
            db_session, sample_architecture_minimal, name="V1", owner="user"
        )
        v2 = service.create_version(
            db_session, sample_architecture_minimal, name="V2", owner="user"
        )

        comparison = service.compare_versions(
            db_session, v1.id, v2.id, component_level=True
        )

        assert "component_diff" in comparison

    def test_validate_version(self, sample_architecture_minimal):
        """Test: Validate ohne zu speichern."""
        service = VersioningService()

        result = service.validate_version(sample_architecture_minimal)

        assert result.valid is True
        assert result.version == "1.0.0"

    def test_get_latest_version(self, db_session, sample_architecture_minimal, clear_db):
        """Test: Hole neueste Version."""
        service = VersioningService()

        v1 = service.create_version(
            db_session, sample_architecture_minimal, name="Test", owner="user"
        )

        latest = service.get_latest_version(db_session, v1.id)

        assert latest.id == v1.id
