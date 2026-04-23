"""Tests für JSON Schema Validation Utilities."""

import json
import pytest
from pathlib import Path

from app.utils.validation import (
    load_schema,
    validate_json,
    clear_schema_cache,
    SchemaValidationError,
    _format_path,
)
from collections import deque


class TestSchemaLoading:
    """Tests für Schema-Lade-Funktionalität."""

    def test_load_schema_success(self):
        """Test: Schema erfolgreich laden."""
        clear_schema_cache()
        schema = load_schema("architecture-v1.0.0.schema.json")

        assert schema is not None
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"] == "OverCloud Architecture Definition"
        assert "version" in schema["required"]

    def test_load_schema_caching(self):
        """Test: Schema wird gecacht."""
        clear_schema_cache()

        # Erstes Laden
        schema1 = load_schema("architecture-v1.0.0.schema.json")

        # Zweites Laden (sollte aus Cache kommen)
        schema2 = load_schema("architecture-v1.0.0.schema.json")

        # Sollten das gleiche Objekt sein
        assert schema1 is schema2

    def test_load_schema_not_found(self):
        """Test: FileNotFoundError wenn Schema nicht existiert."""
        clear_schema_cache()

        with pytest.raises(FileNotFoundError):
            load_schema("non-existent-schema.json")

    def test_clear_schema_cache(self):
        """Test: Schema-Cache kann geleert werden."""
        # Lade Schema
        load_schema("architecture-v1.0.0.schema.json")

        # Lösche Cache
        clear_schema_cache()

        # Sollte neu geladen werden (neues Objekt)
        schema = load_schema("architecture-v1.0.0.schema.json")
        assert schema is not None


class TestValidation:
    """Tests für JSON-Validierung."""

    def test_validate_valid_minimal_architecture(self):
        """Test: Minimale valide Architekturdefinition."""
        data = {
            "version": "1.0.0",
            "metadata": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Test Architecture",
                "provider": "aws",
                "created_at": "2024-03-24T10:00:00Z",
                "updated_at": "2024-03-24T10:00:00Z",
            },
            "requirements": {},
            "architecture": {
                "components": [],
                "relationships": [],
            },
        }

        is_valid, errors = validate_json(data, "architecture-v1.0.0.schema.json")

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_required_field(self):
        """Test: Fehlende Pflichtfelder werden erkannt."""
        data = {
            "version": "1.0.0",
            # 'metadata' fehlt
            "requirements": {},
            "architecture": {
                "components": [],
                "relationships": [],
            },
        }

        is_valid, errors = validate_json(data, "architecture-v1.0.0.schema.json")

        assert is_valid is False
        assert len(errors) > 0
        assert any("metadata" in error["message"].lower() for error in errors)

    def test_validate_invalid_version_format(self):
        """Test: Ungültiges Versionsformat wird erkannt."""
        data = {
            "version": "invalid-version",  # Sollte Semantic Version sein
            "metadata": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Test",
                "provider": "aws",
                "created_at": "2024-03-24T10:00:00Z",
                "updated_at": "2024-03-24T10:00:00Z",
            },
            "requirements": {},
            "architecture": {
                "components": [],
                "relationships": [],
            },
        }

        is_valid, errors = validate_json(data, "architecture-v1.0.0.schema.json")

        assert is_valid is False
        assert len(errors) > 0
        # Sollte Pattern-Fehler bei version sein
        assert any("version" in error["path"] for error in errors)

    def test_validate_invalid_provider(self):
        """Test: Ungültiger Provider-Wert wird erkannt."""
        data = {
            "version": "1.0.0",
            "metadata": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Test",
                "provider": "invalid-provider",  # Nur aws, azure, gcp erlaubt
                "created_at": "2024-03-24T10:00:00Z",
                "updated_at": "2024-03-24T10:00:00Z",
            },
            "requirements": {},
            "architecture": {
                "components": [],
                "relationships": [],
            },
        }

        is_valid, errors = validate_json(data, "architecture-v1.0.0.schema.json")

        assert is_valid is False
        assert len(errors) > 0
        # Sollte Enum-Fehler bei provider sein
        assert any("provider" in error["path"] for error in errors)

    def test_validate_component_with_invalid_type(self):
        """Test: Ungültiger Component-Typ wird erkannt."""
        data = {
            "version": "1.0.0",
            "metadata": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Test",
                "provider": "aws",
                "created_at": "2024-03-24T10:00:00Z",
                "updated_at": "2024-03-24T10:00:00Z",
            },
            "requirements": {},
            "architecture": {
                "components": [
                    {
                        "id": "test-component",
                        "type": "invalid-type",  # Ungültiger Typ
                        "name": "Test Component",
                        "provider_service": "ec2",
                    }
                ],
                "relationships": [],
            },
        }

        is_valid, errors = validate_json(data, "architecture-v1.0.0.schema.json")

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_error_paths(self):
        """Test: Fehler-Pfade werden korrekt formatiert."""
        data = {
            "version": "1.0.0",
            "metadata": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "",  # Leerer Name - verletzt minLength: 1
                "provider": "aws",
                "created_at": "2024-03-24T10:00:00Z",
                "updated_at": "2024-03-24T10:00:00Z",
            },
            "requirements": {},
            "architecture": {
                "components": [],
                "relationships": [],
            },
        }

        is_valid, errors = validate_json(data, "architecture-v1.0.0.schema.json")

        assert is_valid is False
        assert len(errors) > 0
        # Prüfe dass Pfad korrekt ist
        assert any("$.metadata.name" in error["path"] for error in errors)


class TestFormatPath:
    """Tests für Pfad-Formatierung."""

    def test_format_empty_path(self):
        """Test: Leerer Pfad wird zu '$'."""
        path = deque([])
        assert _format_path(path) == "$"

    def test_format_simple_path(self):
        """Test: Einfacher Pfad mit Feldern."""
        path = deque(["metadata", "name"])
        assert _format_path(path) == "$.metadata.name"

    def test_format_path_with_array_index(self):
        """Test: Pfad mit Array-Index."""
        path = deque(["components", 0, "id"])
        assert _format_path(path) == "$.components[0].id"

    def test_format_complex_path(self):
        """Test: Komplexer Pfad mit mehreren Ebenen und Arrays."""
        path = deque(["architecture", "components", 2, "artifacts", 0, "type"])
        assert _format_path(path) == "$.architecture.components[2].artifacts[0].type"
