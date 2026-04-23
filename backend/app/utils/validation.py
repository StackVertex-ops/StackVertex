"""JSON Schema Validation Utilities.

Stellt Funktionen zur Validierung von JSON-Daten gegen JSON Schemas bereit.
Das Schema wird gecacht, um wiederholtes Laden von der Festplatte zu vermeiden.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator, ValidationError
from jsonschema.exceptions import SchemaError

logger = logging.getLogger(__name__)

# Cache für geladene Schemas
_schema_cache: Dict[str, Dict[str, Any]] = {}

# Basis-Pfad für JSON Schemas
SCHEMA_BASE_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "json-schemas"


class SchemaValidationError(Exception):
    """Exception für Schema-Validierungsfehler."""

    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        self.message = message
        self.errors = errors
        super().__init__(self.message)


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Lädt ein JSON Schema von der Festplatte und cached es.

    Args:
        schema_name: Name der Schema-Datei (z.B. "architecture-v1.0.0.schema.json")

    Returns:
        Das geladene JSON Schema als Dictionary

    Raises:
        FileNotFoundError: Wenn die Schema-Datei nicht gefunden wurde
        json.JSONDecodeError: Wenn das Schema kein valides JSON ist
        SchemaError: Wenn das Schema selbst ungültig ist
    """
    # Prüfe Cache
    if schema_name in _schema_cache:
        logger.debug(f"Schema '{schema_name}' aus Cache geladen")
        return _schema_cache[schema_name]

    # Lade Schema von Festplatte
    schema_path = SCHEMA_BASE_PATH / schema_name
    logger.info(f"Lade Schema von: {schema_path}")

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema-Datei nicht gefunden: {schema_path}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Validiere, dass das Schema selbst gültig ist
        Draft202012Validator.check_schema(schema)

        # Cache Schema
        _schema_cache[schema_name] = schema
        logger.info(f"Schema '{schema_name}' erfolgreich geladen und gecacht")

        return schema

    except json.JSONDecodeError as e:
        logger.error(f"Ungültiges JSON in Schema-Datei {schema_name}: {e}")
        raise
    except SchemaError as e:
        logger.error(f"Ungültiges JSON Schema {schema_name}: {e}")
        raise


def validate_json(
    data: Dict[str, Any], schema_name: str
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Validiert JSON-Daten gegen ein Schema.

    Args:
        data: Die zu validierenden Daten
        schema_name: Name der Schema-Datei

    Returns:
        Tuple[bool, List[Dict]]: (ist_valid, fehler_liste)
        - ist_valid: True wenn valide, False wenn Fehler vorhanden
        - fehler_liste: Liste von Fehler-Dictionaries mit Details

    Raises:
        FileNotFoundError: Wenn Schema nicht gefunden
        SchemaError: Wenn Schema ungültig ist
    """
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)

    errors: List[Dict[str, Any]] = []

    # Sammle alle Validierungsfehler
    for error in validator.iter_errors(data):
        error_dict = {
            "message": error.message,
            "path": _format_path(error.absolute_path),
            "schema_path": _format_path(error.absolute_schema_path),
            "validator": error.validator,
            "validator_value": error.validator_value,
        }

        # Füge optionale Felder hinzu
        if error.context:
            error_dict["context"] = [
                {
                    "message": ctx_error.message,
                    "path": _format_path(ctx_error.absolute_path),
                }
                for ctx_error in error.context
            ]

        errors.append(error_dict)

    is_valid = len(errors) == 0

    if is_valid:
        logger.info(f"Daten erfolgreich gegen Schema '{schema_name}' validiert")
    else:
        logger.warning(
            f"Validierung gegen Schema '{schema_name}' fehlgeschlagen: {len(errors)} Fehler"
        )

    return is_valid, errors


def _format_path(path_deque) -> str:
    """Formatiert einen JSONPath aus einer deque in einen lesbaren String.

    Args:
        path_deque: collections.deque mit Pfad-Elementen

    Returns:
        Formatierter Pfad als String (z.B. "$.metadata.name" oder "$[0].id")
    """
    if not path_deque:
        return "$"

    path_parts = ["$"]
    for part in path_deque:
        if isinstance(part, int):
            path_parts.append(f"[{part}]")
        else:
            path_parts.append(f".{part}")

    return "".join(path_parts)


def clear_schema_cache() -> None:
    """Löscht den Schema-Cache.

    Nützlich für Tests oder wenn Schemas zur Laufzeit aktualisiert werden.
    """
    global _schema_cache
    _schema_cache.clear()
    logger.info("Schema-Cache geleert")
