"""Tests für ArchitectureValidator.

Testet JSON Schema Validation Wrapper mit vollständiger Coverage.
"""

import pytest
from datetime import datetime

from app.core.json_engine.validator import ArchitectureValidator, ValidationResult
from app.core.json_engine.exceptions import ValidationError, SchemaNotFoundError


class TestArchitectureValidator:
    """Tests für ArchitectureValidator."""

    def test_validate_valid_architecture(self, sample_architecture_minimal):
        """Test: Validiere valides Architecture JSON."""
        validator = ArchitectureValidator()

        result = validator.validate(sample_architecture_minimal)

        assert result.valid is True
        assert result.version == "1.0.0"
        assert result.errors is None
        assert isinstance(result.validated_at, datetime)

    def test_validate_with_custom_version(self, sample_architecture_minimal):
        """Test: Validiere mit custom Schema-Version."""
        validator = ArchitectureValidator(default_version="1.0.0")

        result = validator.validate(sample_architecture_minimal, version="1.0.0")

        assert result.valid is True
        assert result.version == "1.0.0"

    def test_validate_invalid_architecture(self):
        """Test: Validiere invalides JSON."""
        validator = ArchitectureValidator()

        invalid_json = {
            "version": "1.0.0",
            # Missing required fields
        }

        result = validator.validate(invalid_json)

        assert result.valid is False
        assert result.errors is not None
        assert len(result.errors) > 0

    def test_validate_and_raise_valid(self, sample_architecture_minimal):
        """Test: validate_and_raise mit validem JSON."""
        validator = ArchitectureValidator()

        result = validator.validate_and_raise(sample_architecture_minimal)

        assert result.valid is True

    def test_validate_and_raise_invalid(self):
        """Test: validate_and_raise mit invalidem JSON wirft Exception."""
        validator = ArchitectureValidator()

        invalid_json = {"version": "1.0.0"}

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_raise(invalid_json)

        assert "validation failed" in str(exc_info.value).lower()
        assert exc_info.value.schema_version == "1.0.0"
        assert len(exc_info.value.errors) > 0

    def test_validate_nonexistent_schema(self, sample_architecture_minimal):
        """Test: Validation mit nicht-existentem Schema."""
        validator = ArchitectureValidator()

        with pytest.raises(SchemaNotFoundError) as exc_info:
            validator.validate(sample_architecture_minimal, version="99.99.99")

        assert "architecture-v99.99.99.schema.json" in str(exc_info.value)

    def test_extract_version_from_json(self, sample_architecture_minimal):
        """Test: Version aus JSON extrahieren."""
        validator = ArchitectureValidator()

        version = validator.extract_version(sample_architecture_minimal)

        assert version == "1.0.0"

    def test_extract_version_missing_defaults(self):
        """Test: Version extrahieren mit default fallback."""
        validator = ArchitectureValidator(default_version="2.0.0")

        json_without_version = {"metadata": {}}
        version = validator.extract_version(json_without_version)

        assert version == "2.0.0"

    def test_is_compatible_true(self, sample_architecture_minimal):
        """Test: Architecture ist kompatibel mit Version."""
        validator = ArchitectureValidator()

        compatible = validator.is_compatible(sample_architecture_minimal, "1.0.0")

        assert compatible is True

    def test_is_compatible_false(self):
        """Test: Architecture ist nicht kompatibel."""
        validator = ArchitectureValidator()

        invalid_json = {"version": "1.0.0"}
        compatible = validator.is_compatible(invalid_json, "1.0.0")

        assert compatible is False

    def test_is_compatible_schema_not_found(self, sample_architecture_minimal):
        """Test: is_compatible mit nicht-existentem Schema."""
        validator = ArchitectureValidator()

        compatible = validator.is_compatible(sample_architecture_minimal, "99.99.99")

        assert compatible is False

    def test_validation_result_str(self, sample_architecture_minimal):
        """Test: ValidationResult String representation."""
        validator = ArchitectureValidator()

        invalid_json = {"version": "1.0.0"}

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_raise(invalid_json)

        error_str = str(exc_info.value)
        assert "validation failed" in error_str.lower()
        assert "validation errors" in error_str.lower()
