"""Architecture Validator - JSON Schema Validation Wrapper.

Wrapper um die existierende validation.py mit zusätzlicher Funktionalität
für Versioning und bessere Error-Handling.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from app.utils.validation import validate_json
from app.core.json_engine.exceptions import ValidationError, SchemaNotFoundError


@dataclass
class ValidationResult:
    """Ergebnis einer Validation.

    Attributes:
        valid: Ob das JSON valid ist
        version: Schema-Version gegen die validiert wurde
        validated_at: Zeitpunkt der Validation
        errors: Liste von Validation-Fehlern (falls invalid)
    """

    valid: bool
    version: str
    validated_at: datetime
    errors: Optional[list] = None


class ArchitectureValidator:
    """Validiert Architecture JSON gegen Schema.

    Wrapper um app.utils.validation mit zusätzlichen Features:
    - Versionierte Schema-Validation
    - Strukturierte Error-Responses
    - Caching und Performance-Optimierungen
    """

    def __init__(self, default_version: str = "1.0.0"):
        """Initialize validator.

        Args:
            default_version: Standard-Version falls nicht angegeben
        """
        self.default_version = default_version

    def validate(
        self,
        architecture_json: Dict[str, Any],
        version: Optional[str] = None
    ) -> ValidationResult:
        """Validiert Architecture JSON gegen Schema.

        Args:
            architecture_json: Das zu validierende Architecture JSON
            version: Schema-Version (optional, default: 1.0.0)

        Returns:
            ValidationResult mit Status und ggf. Errors

        Raises:
            SchemaNotFoundError: Wenn Schema-Datei nicht gefunden wurde
        """
        # Verwende angegebene Version oder default
        schema_version = version or self.default_version

        # Schema-Name konstruieren
        schema_name = f"architecture-v{schema_version}.schema.json"

        # Validierung durchführen (nutzt existierende validation.py)
        try:
            is_valid, errors = validate_json(architecture_json, schema_name)
        except FileNotFoundError as e:
            raise SchemaNotFoundError(schema_name) from e

        # ValidationResult erstellen
        result = ValidationResult(
            valid=is_valid,
            version=schema_version,
            validated_at=datetime.utcnow(),
            errors=errors if not is_valid else None
        )

        return result

    def validate_and_raise(
        self,
        architecture_json: Dict[str, Any],
        version: Optional[str] = None
    ) -> ValidationResult:
        """Validiert und wirft Exception bei Fehler.

        Args:
            architecture_json: Das zu validierende Architecture JSON
            version: Schema-Version (optional)

        Returns:
            ValidationResult bei Erfolg

        Raises:
            ValidationError: Bei Validation-Fehlern
            SchemaNotFoundError: Wenn Schema nicht gefunden wurde
        """
        result = self.validate(architecture_json, version)

        if not result.valid:
            raise ValidationError(
                f"Architecture JSON validation failed for version {result.version}",
                errors=result.errors,
                schema_version=result.version
            )

        return result

    def extract_version(self, architecture_json: Dict[str, Any]) -> str:
        """Extrahiert Version aus Architecture JSON.

        Args:
            architecture_json: Architecture JSON

        Returns:
            Version-String aus JSON oder default_version
        """
        # Versuche Version aus JSON zu extrahieren
        if "version" in architecture_json:
            return architecture_json["version"]

        # Fallback zu default
        return self.default_version

    def is_compatible(
        self,
        architecture_json: Dict[str, Any],
        target_version: str
    ) -> bool:
        """Prüft ob Architecture JSON mit target Version kompatibel ist.

        Args:
            architecture_json: Architecture JSON
            target_version: Ziel-Schema-Version

        Returns:
            True wenn kompatibel, False sonst
        """
        try:
            result = self.validate(architecture_json, target_version)
            return result.valid
        except SchemaNotFoundError:
            return False
