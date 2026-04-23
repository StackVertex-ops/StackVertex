"""Custom Exceptions für JSON Engine.

Definiert alle spezifischen Exceptions für Versioning, Validation und Migrations.
"""

from typing import List, Dict, Any, Optional


class JSONEngineException(Exception):
    """Base Exception für alle JSON Engine Fehler."""

    pass


class ValidationError(JSONEngineException):
    """Exception für JSON Schema Validation Fehler.

    Attributes:
        errors: Liste von Validation-Fehlern mit Details
        schema_version: Version des Schemas gegen das validiert wurde
    """

    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        schema_version: Optional[str] = None
    ):
        super().__init__(message)
        self.errors = errors or []
        self.schema_version = schema_version

    def __str__(self) -> str:
        """String representation mit Error-Details."""
        base = super().__str__()
        if self.errors:
            error_details = "\n".join(
                f"  - {err.get('path', 'unknown')}: {err.get('message', 'unknown error')}"
                for err in self.errors
            )
            return f"{base}\nValidation Errors:\n{error_details}"
        return base


class VersionNotFoundError(JSONEngineException):
    """Exception wenn eine Version nicht gefunden wurde."""

    def __init__(self, version_id: str):
        super().__init__(f"Version not found: {version_id}")
        self.version_id = version_id


class InvalidVersionError(JSONEngineException):
    """Exception für ungültige Version-Strings."""

    def __init__(self, version: str, reason: str):
        super().__init__(f"Invalid version '{version}': {reason}")
        self.version = version
        self.reason = reason


class MigrationError(JSONEngineException):
    """Exception für Fehler bei Migrations."""

    def __init__(
        self,
        message: str,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None
    ):
        super().__init__(message)
        self.source_version = source_version
        self.target_version = target_version

    def __str__(self) -> str:
        """String representation mit Versions-Info."""
        base = super().__str__()
        if self.source_version and self.target_version:
            return f"{base} (from {self.source_version} to {self.target_version})"
        return base


class SchemaNotFoundError(JSONEngineException):
    """Exception wenn ein JSON Schema nicht gefunden wurde."""

    def __init__(self, schema_name: str):
        super().__init__(f"Schema not found: {schema_name}")
        self.schema_name = schema_name


class DiffGenerationError(JSONEngineException):
    """Exception bei Fehlern während Diff-Generierung."""

    pass


class CircularReferenceError(JSONEngineException):
    """Exception bei zirkulären Referenzen in Version-Chain."""

    def __init__(self, version_ids: List[str]):
        super().__init__(
            f"Circular reference detected in version chain: {' -> '.join(version_ids)}"
        )
        self.version_ids = version_ids
