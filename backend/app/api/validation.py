"""API Endpoints für JSON Schema Validation.

Stellt REST-Endpunkte zur Validierung von Architekturdefinitionen bereit.
Erweitert um AWS-spezifische Field-Level-Validation für Smart Forms.
"""

import logging
from typing import Any, Dict, List, Optional, Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.utils.validation import validate_json, SchemaValidationError
from app.data import (
    validate_rds_storage,
    validate_vpc_cidr,
    validate_lambda_memory,
    validate_lambda_timeout,
    get_ec2_instance_type,
    get_rds_engine,
    EC2_INSTANCE_TYPES,
    RDS_ENGINES,
    RDS_INSTANCE_CLASSES,
    RDS_STORAGE_TYPES,
    S3_STORAGE_CLASSES,
)
from app.api.auth import get_current_user

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
    description="Validiert eine JSON-Architekturdefinition gegen das StackVertex Schema v1.0.0",
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
async def validate_architecture(
    request: ValidationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> ValidationResponse:
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
            detail=f"Schema-Datei konnte nicht geladen werden: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei Validierung: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interner Fehler bei Validierung: {str(e)}"
        ) from e


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
            detail=f"Schema konnte nicht geladen werden: {str(e)}"
        ) from e


# ============================================================================
# AWS Field-Level Validation (für Smart Forms)
# ============================================================================

class FieldValidationResponse(BaseModel):
    """Response für Field-Level-Validation"""
    valid: bool = Field(..., description="Ob der Wert valide ist")
    errors: List[str] = Field(default_factory=list, description="Fehlermeldungen")
    warnings: List[str] = Field(default_factory=list, description="Warnungen")
    suggestions: List[str] = Field(default_factory=list, description="Verbesserungsvorschläge")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten (z.B. usable IPs, cost)")


class StorageValidationRequest(BaseModel):
    """Request für Storage-Validation"""
    service: str = Field(..., description="AWS Service (rds, ebs, s3)")
    size: int = Field(..., description="Storage Size")
    unit: str = Field(default="GB", description="Einheit (GB, TB)")
    engine: Optional[str] = Field(None, description="RDS Engine (mysql, postgres, etc.) - nur für RDS")


class InstanceTypeValidationRequest(BaseModel):
    """Request für EC2 Instance Type Validation"""
    instance_type: str = Field(..., description="EC2 Instance Type (z.B. t3.micro)")
    use_case: Optional[str] = Field(None, description="Anwendungsfall")


class CIDRValidationRequest(BaseModel):
    """Request für CIDR-Validation"""
    cidr: str = Field(..., description="CIDR Block (z.B. 10.0.0.0/16)")


class LambdaValidationRequest(BaseModel):
    """Request für Lambda-Validation"""
    memory_mb: Optional[int] = Field(None, description="Memory in MB")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in Sekunden")


@router.post(
    "/validate-storage",
    response_model=FieldValidationResponse,
    summary="Validiere Storage-Konfiguration",
    description="Validiert Storage Size gegen AWS Service Limits (RDS, EBS, S3)"
)
async def validate_storage_field(req: StorageValidationRequest) -> FieldValidationResponse:
    """
    Validiert Storage-Konfiguration gegen AWS Limits

    Prüft:
    - Minimum/Maximum Storage Size je Service
    - Service-spezifische Constraints
    - Gibt Warnungen für suboptimale Konfigurationen

    Args:
        req: Storage Validation Request

    Returns:
        Validierungsergebnis mit Errors/Warnings/Suggestions
    """
    errors = []
    warnings = []
    suggestions = []
    metadata = {}

    # Konvertiere zu GB falls TB
    size_gb = req.size if req.unit == "GB" else req.size * 1024

    if req.service == "rds":
        if not req.engine:
            return FieldValidationResponse(
                valid=False,
                errors=["RDS Engine muss angegeben werden"]
            )

        # Validiere gegen RDS Constraints
        is_valid, error = validate_rds_storage(size_gb, req.engine)

        if not is_valid:
            errors.append(error)

        # Warnungen für Production-Workloads
        if is_valid and size_gb < 50:
            warnings.append("Empfohlen: Mindestens 50 GB für Production-Workloads")

        if is_valid and size_gb < 100:
            suggestions.append("100+ GB empfohlen für bessere Burst-Performance")

        # Preisberechnung (grobe Schätzung gp3)
        if is_valid:
            monthly_cost = size_gb * 0.092  # gp3 pricing
            metadata["estimated_monthly_cost_usd"] = round(monthly_cost, 2)

    elif req.service == "ebs":
        # EBS hat ähnliche Limits wie RDS
        if size_gb < 1:
            errors.append("EBS Volume muss mindestens 1 GB groß sein")
        elif size_gb > 16384:
            errors.append("EBS Volume kann maximal 16 TB (16384 GB) sein")
        else:
            # Preisberechnung (gp3)
            monthly_cost = size_gb * 0.08
            metadata["estimated_monthly_cost_usd"] = round(monthly_cost, 2)

    elif req.service == "s3":
        # S3 hat keine praktischen Limits
        if size_gb < 0:
            errors.append("S3 Storage Size muss positiv sein")
        else:
            # Preisberechnung (Standard Storage Class)
            monthly_cost = size_gb * 0.023
            metadata["estimated_monthly_cost_usd"] = round(monthly_cost, 2)

            suggestions.append("Erwäge S3 Intelligent-Tiering für automatische Kostenoptimierung")

    else:
        errors.append(f"Unbekannter Service: {req.service}")

    return FieldValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
        metadata=metadata
    )


@router.post(
    "/validate-instance-type",
    response_model=FieldValidationResponse,
    summary="Validiere EC2 Instance Type",
    description="Validiert EC2 Instance Type und gibt Empfehlungen basierend auf Use-Case"
)
async def validate_instance_type_field(req: InstanceTypeValidationRequest) -> FieldValidationResponse:
    """
    Validiert EC2 Instance Type

    Prüft:
    - Ob Instance Type existiert
    - Ob Instance Type für Use-Case geeignet ist
    - Gibt bessere Alternativen

    Args:
        req: Instance Type Validation Request

    Returns:
        Validierungsergebnis mit Details zum Instance Type
    """
    errors = []
    warnings = []
    suggestions = []
    metadata = {}

    instance_type = get_ec2_instance_type(req.instance_type)

    if not instance_type:
        errors.append(f"Unbekannter Instance Type: {req.instance_type}")

        # Suggest ähnliche Types
        if req.instance_type.startswith("t3"):
            suggestions.append("Verfügbare t3 Instances: t3.micro, t3.small, t3.medium, t3.large")
        elif req.instance_type.startswith("m5"):
            suggestions.append("Verfügbare m5 Instances: m5.large, m5.xlarge, m5.2xlarge")

        return FieldValidationResponse(
            valid=False,
            errors=errors,
            suggestions=suggestions
        )

    # Metadata mit Instance Details
    metadata = {
        "vcpus": instance_type.vcpus,
        "memory_gb": instance_type.memory_gb,
        "network_performance": instance_type.network_performance,
        "price_per_hour_usd": instance_type.price_per_hour_usd,
        "estimated_monthly_cost_usd": round(instance_type.price_per_hour_usd * 730, 2),  # 730h = Monat
        "use_cases": instance_type.use_cases
    }

    # Warnungen für Production
    if req.instance_type.startswith("t3.micro") or req.instance_type.startswith("t3.small"):
        warnings.append("T3 Micro/Small nicht empfohlen für Production (Burstable Performance)")

    # Use-Case-basierte Suggestions
    if req.use_case:
        use_case_lower = req.use_case.lower()

        if "database" in use_case_lower and not req.instance_type.startswith("r5"):
            suggestions.append("Erwäge R5-Instances (Memory-Optimized) für Datenbanken")

        if "batch" in use_case_lower or "compute" in use_case_lower:
            if not req.instance_type.startswith("c5"):
                suggestions.append("Erwäge C5-Instances (Compute-Optimized) für CPU-intensive Workloads")

        if "production" in use_case_lower and req.instance_type.startswith("t3"):
            suggestions.append("Erwäge M5-Instances für stabile Production-Performance")

    return FieldValidationResponse(
        valid=True,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
        metadata=metadata
    )


@router.post(
    "/validate-cidr",
    response_model=FieldValidationResponse,
    summary="Validiere VPC CIDR Block",
    description="Validiert CIDR Block für VPC/Subnet und berechnet nutzbare IPs"
)
async def validate_cidr_field(req: CIDRValidationRequest) -> FieldValidationResponse:
    """
    Validiert VPC/Subnet CIDR Block

    Prüft:
    - Gültiges CIDR-Format
    - AWS VPC Constraints (/16 bis /28)
    - Private IP Range
    - Berechnet nutzbare IPs

    Args:
        req: CIDR Validation Request

    Returns:
        Validierungsergebnis mit usable IPs
    """
    errors = []
    warnings = []
    suggestions = []
    metadata = {}

    is_valid, error, usable_ips = validate_vpc_cidr(req.cidr)

    if not is_valid:
        errors.append(error)
        return FieldValidationResponse(
            valid=False,
            errors=errors
        )

    # Metadata
    prefix = int(req.cidr.split('/')[1])
    total_ips = 2 ** (32 - prefix)

    metadata = {
        "total_ips": total_ips,
        "usable_ips": usable_ips,
        "aws_reserved_ips": 5,
        "prefix": prefix
    }

    # Warnungen für kleine Subnets
    if prefix >= 27:  # /27 = 32 IPs (27 usable)
        warnings.append(f"Kleines Subnet: Nur {usable_ips} nutzbare IPs")

    if prefix == 28:  # /28 = 16 IPs (11 usable)
        warnings.append("Sehr kleines Subnet - kann schnell voll werden")

    # Suggestions
    if prefix > 24:
        suggestions.append("Erwäge größeres Subnet (z.B. /24 = 256 IPs) für mehr Flexibilität")

    if prefix < 20:
        suggestions.append("Sehr großes Subnet - ggf. in kleinere Subnets aufteilen")

    return FieldValidationResponse(
        valid=True,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
        metadata=metadata
    )


@router.post(
    "/validate-lambda",
    response_model=FieldValidationResponse,
    summary="Validiere Lambda-Konfiguration",
    description="Validiert Lambda Memory und Timeout gegen AWS Limits"
)
async def validate_lambda_field(req: LambdaValidationRequest) -> FieldValidationResponse:
    """
    Validiert Lambda-Konfiguration

    Prüft:
    - Memory (128 MB - 10240 MB, in 64 MB Schritten)
    - Timeout (1s - 900s)

    Args:
        req: Lambda Validation Request

    Returns:
        Validierungsergebnis
    """
    errors = []
    warnings = []
    suggestions = []
    metadata = {}

    # Validiere Memory
    if req.memory_mb is not None:
        is_valid, error = validate_lambda_memory(req.memory_mb)

        if not is_valid:
            errors.append(error)
        else:
            # Grobe Preisberechnung (us-east-1)
            # $0.0000166667 per GB-second
            price_per_gb_second = 0.0000166667
            gb = req.memory_mb / 1024

            # Beispiel: 1 Million Invocations à 1 Sekunde
            monthly_cost_1m_invocations = price_per_gb_second * gb * 1_000_000

            metadata["memory_gb"] = round(gb, 2)
            metadata["estimated_cost_1m_invocations_usd"] = round(monthly_cost_1m_invocations, 2)

            if req.memory_mb < 512:
                warnings.append("Niedrige Memory-Konfiguration - kann zu Timeouts führen")

            if req.memory_mb > 3008:
                suggestions.append("Hohe Memory-Konfiguration - prüfe ob wirklich benötigt (Kosten)")

    # Validiere Timeout
    if req.timeout_seconds is not None:
        is_valid, error = validate_lambda_timeout(req.timeout_seconds)

        if not is_valid:
            errors.append(error)
        else:
            metadata["timeout_seconds"] = req.timeout_seconds

            if req.timeout_seconds < 10:
                warnings.append("Kurzer Timeout - kann bei langsamen APIs zu Abbrüchen führen")

            if req.timeout_seconds > 300:
                warnings.append("Langer Timeout - erwäge Auslagerung auf ECS/Fargate für lange Tasks")

    return FieldValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
        metadata=metadata
    )


@router.get(
    "/instance-types",
    summary="Liste verfügbare EC2 Instance Types",
    description="Gibt alle verfügbaren EC2 Instance Types mit Details zurück"
)
async def list_instance_types(
    use_case: Optional[str] = None
) -> Dict[str, Any]:
    """
    Listet alle verfügbaren EC2 Instance Types

    Args:
        use_case: Optionaler Filter nach Use-Case

    Returns:
        Dictionary mit Instance Types
    """
    types = {}

    for name, instance in EC2_INSTANCE_TYPES.items():
        if use_case:
            # Filter nach Use-Case
            if not any(use_case.lower() in uc.lower() for uc in instance.use_cases):
                continue

        types[name] = {
            "name": instance.name,
            "vcpus": instance.vcpus,
            "memory_gb": instance.memory_gb,
            "network_performance": instance.network_performance,
            "price_per_hour_usd": instance.price_per_hour_usd,
            "estimated_monthly_cost_usd": round(instance.price_per_hour_usd * 730, 2),
            "use_cases": instance.use_cases
        }

    return {
        "count": len(types),
        "instance_types": types
    }


@router.get(
    "/rds-engines",
    summary="Liste verfügbare RDS Engines",
    description="Gibt alle verfügbaren RDS Engines mit Details zurück"
)
async def list_rds_engines() -> Dict[str, Any]:
    """
    Listet alle verfügbaren RDS Engines

    Returns:
        Dictionary mit RDS Engines
    """
    engines = {}

    for name, engine in RDS_ENGINES.items():
        engines[name] = {
            "name": engine.name,
            "display_name": engine.display_name,
            "versions": engine.versions,
            "min_storage_gb": engine.min_storage_gb,
            "max_storage_gb": engine.max_storage_gb,
            "default_port": engine.default_port,
            "use_cases": engine.use_cases
        }

    return {
        "count": len(engines),
        "engines": engines
    }


@router.get(
    "/rds-instance-classes",
    summary="Liste verfügbare RDS Instance Classes",
    description="Gibt alle verfügbaren RDS Instance Classes mit Details zurück"
)
async def list_rds_instance_classes() -> Dict[str, Any]:
    """
    Listet alle verfügbaren RDS Instance Classes

    Returns:
        Dictionary mit RDS Instance Classes
    """
    classes = {}

    for name, instance_class in RDS_INSTANCE_CLASSES.items():
        classes[name] = {
            "name": instance_class.name,
            "vcpus": instance_class.vcpus,
            "memory_gb": instance_class.memory_gb,
            "price_per_hour_usd": instance_class.price_per_hour_usd,
            "estimated_monthly_cost_usd": round(instance_class.price_per_hour_usd * 730, 2),
            "use_cases": instance_class.use_cases
        }

    return {
        "count": len(classes),
        "instance_classes": classes
    }
