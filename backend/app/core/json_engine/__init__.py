"""JSON Engine Package - Architecture JSON Versioning & Validation.

Provides:
- Schema Validation
- Version Tracking
- JSON Diff Generation
- Migration Framework
"""

from app.core.json_engine.versioning import VersioningService
from app.core.json_engine.validator import ArchitectureValidator, ValidationResult
from app.core.json_engine.diff import JSONDiff, DiffResult
from app.core.json_engine.exceptions import (
    JSONEngineException,
    ValidationError,
    VersionNotFoundError,
    InvalidVersionError,
    MigrationError,
    SchemaNotFoundError,
    DiffGenerationError,
    CircularReferenceError
)

__all__ = [
    # Services
    "VersioningService",
    "ArchitectureValidator",
    "JSONDiff",
    # Result Types
    "ValidationResult",
    "DiffResult",
    # Exceptions
    "JSONEngineException",
    "ValidationError",
    "VersionNotFoundError",
    "InvalidVersionError",
    "MigrationError",
    "SchemaNotFoundError",
    "DiffGenerationError",
    "CircularReferenceError",
]
