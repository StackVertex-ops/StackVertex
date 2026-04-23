"""API Endpoints für JSON Schema Validation.

Stellt REST-Endpunkte zur Validierung von Architekturdefinitionen bereit.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.utils.validation import validate_json, SchemaValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


class ValidationErrorDetail(BaseModel):
    """Details zu einem einzelnen Validierungsfehler."""

    message: str = Field(..., description="Fehlermeldung")
    path: str = Field(..., description="JSON-Pfad zum fehlerhaften Feld (z.B. '$.metadata.name')")
    schema_path: str = Field(..., description="Pfad im Schema")
    validator: str = Field(..., description="Name des Validators der fehlgeschlagen ist")
    validator_value: Any = Field(..., description="Erwarteter Wert vom Validator")
    context: List[Dict[str, Any]] | None = Field(
        None, description="Zusätzlicher Kontext bei verschachtelten Fehlern"
    )


class ValidationRequest(BaseModel):
    """Request-Body für Validierung."""

    data: Dict[str, Any] = Field(
        ..., description="Die zu validierenden JSON-Daten"
    )


class ValidationResponse(BaseModel):
    """Response für erfolgreiche Validierung."""

    valid: bool = Field(..., description="Ob die Daten valide sind")
    message: str = Field(..., description="Status-Nachricht")
    errors: List[ValidationErrorDetail] = Field(
        default_factory=list, description="Liste von Validierungsfehlern (leer wenn valide)"
    )
    error_count: int = Field(default=0, description="Anzahl der Fehler")


@router.post(
    "/validate/architecture",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validiere Architekturdefinition",
    description="Validiert eine JSON-Architekturdefinition gegen das OverCloud Schema v1.0.0",
    responses={
        200: {
            "description": "Validierung durchgeführt (kann Fehler enthalten)",
            "content": {
                "application/json": {
                    "examples": {
                        "valid": {
                            "summary": "Valide Daten",
                            "value": {
                                "valid": True,
                                "message": "Validierung erfolgreich",
                                "errors": [],
                                "error_count": 0,
                            },
                        },
                        "invalid": {
                            "summary": "Invalide Daten",
                            "value": {
                                "valid": False,
                                "message": "Validierung fehlgeschlagen",
                                "errors": [
                                    {
                                        "message": "'version' is a required property",
                                        "path": "$",
                                        "schema_path": "$.required",
                                        "validator": "required",
                                        "validator_value": ["version", "metadata"],
                                        "context": None,
                                    }
                                ],
                                "error_count": 1,
                            },
                        },
                    }
                }
            },
        },
        500: {"description": "Interner Serverfehler (z.B. Schema nicht gefunden)"},
    },
)
async def validate_architecture(request: ValidationRequest) -> ValidationResponse:
    """Validiert eine Architekturdefinition gegen das JSON Schema.

    Args:
        request: ValidationRequest mit den zu validierenden Daten

    Returns:
        ValidationResponse mit Validierungsergebnis und ggf. Fehlern

    Raises:
        HTTPException: Bei internen Fehlern (Schema nicht gefunden, etc.)
    """
    try:
        # Validiere gegen Schema
        is_valid, errors = validate_json(
            request.data, "architecture-v1.0.0.schema.json"
        )

        # Konvertiere Fehler zu Pydantic-Modellen
        error_details = [
            ValidationErrorDetail(
                message=error["message"],
                path=error["path"],
                schema_path=error["schema_path"],
                validator=error["validator"],
                validator_value=error["validator_value"],
                context=error.get("context"),
            )
            for error in errors
        ]

        return ValidationResponse(
            valid=is_valid,
            message="Validierung erfolgreich" if is_valid else "Validierung fehlgeschlagen",
            errors=error_details,
            error_count=len(error_details),
        )

    except FileNotFoundError as e:
        logger.error(f"Schema-Datei nicht gefunden: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema-Datei konnte nicht geladen werden: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei Validierung: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interner Fehler bei Validierung: {str(e)}",
        )


@router.get(
    "/validate/health",
    status_code=status.HTTP_200_OK,
    summary="Health-Check für Validation Service",
    description="Prüft ob der Validation Service funktioniert und das Schema geladen werden kann",
)
async def validation_health() -> Dict[str, Any]:
    """Health-Check für den Validation Service.

    Prüft ob das Schema erfolgreich geladen werden kann.

    Returns:
        Status-Dictionary mit Service-Status

    Raises:
        HTTPException: Wenn Schema nicht geladen werden kann
    """
    try:
        from app.utils.validation import load_schema

        schema = load_schema("architecture-v1.0.0.schema.json")

        return {
            "status": "healthy",
            "schema_loaded": True,
            "schema_version": schema.get("$id", "unknown"),
            "schema_title": schema.get("title", "unknown"),
        }
    except Exception as e:
        logger.error(f"Validation Service Health-Check fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema konnte nicht geladen werden: {str(e)}",
        )
