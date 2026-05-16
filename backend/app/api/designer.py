"""OverCloud Backend - Infrastructure Designer API Endpoints.

REST API für den Infrastructure Designer (Visual Canvas + Component-based Architecture).
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

from app.config import settings
from app.repositories.architecture import ArchitectureRepository
from app.services.terraform_generator_v2 import TerraformGeneratorV2
from app.core.json_engine import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Schemas
# ============================================================================

class DesignerSaveRequest(BaseModel):
    """Request body für Designer Save."""
    name: str = Field(..., description="Architecture name")
    description: Optional[str] = Field(None, description="Architecture description")
    architecture_json: Dict[str, Any] = Field(..., description="Complete architecture JSON from designer")
    owner: Optional[str] = Field(None, description="Owner user ID")


class DesignerSaveResponse(BaseModel):
    """Response für Designer Save."""
    architecture_id: str = Field(..., description="UUID of saved architecture")
    name: str
    version: str
    created_at: str
    updated_at: str


class TerraformGenerateRequest(BaseModel):
    """Request body für Terraform Generation."""
    architecture_json: Dict[str, Any] = Field(..., description="Complete architecture JSON")


class TerraformGenerateResponse(BaseModel):
    """Response für Terraform Generation."""
    files: Dict[str, str] = Field(..., description="Generated Terraform files (filename -> content)")
    component_count: int = Field(..., description="Number of components processed")
    warnings: list[str] = Field(default_factory=list, description="Generation warnings")


class ValidationRequest(BaseModel):
    """Request body für Architecture Validation."""
    architecture_json: Dict[str, Any] = Field(..., description="Architecture JSON to validate")


class ValidationResponse(BaseModel):
    """Response für Architecture Validation."""
    valid: bool = Field(..., description="True if architecture is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    component_count: int = Field(default=0, description="Number of components")
    connection_count: int = Field(default=0, description="Number of connections")


# ============================================================================
# Dependencies
# ============================================================================

def get_architecture_repo() -> ArchitectureRepository:
    """Get ArchitectureRepository instance."""
    return ArchitectureRepository()


def get_terraform_generator() -> TerraformGeneratorV2:
    """Get TerraformGeneratorV2 instance."""
    return TerraformGeneratorV2()


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/designer/save",
    response_model=DesignerSaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Speichere Designer-Architektur",
    description="Speichert eine Architecture aus dem Infrastructure Designer in der Datenbank",
    responses={
        201: {"description": "Architektur erfolgreich gespeichert"},
        422: {"description": "Validierungsfehler in den Eingabedaten"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Interner Serverfehler"},
    },
)
@limiter.limit("1000/minute" if settings.TESTING else "50/minute")
async def save_designer_architecture(
    request: Request,
    data: DesignerSaveRequest,
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> DesignerSaveResponse:
    """Speichert Designer-Architektur in Datenbank.

    Args:
        data: Architecture data from designer
        repo: ArchitectureRepository (Dependency Injection)

    Returns:
        Saved architecture metadata

    Raises:
        HTTPException: Bei Fehlern während des Speicherns
    """
    try:
        # Validate JSON structure
        if 'components' not in data.architecture_json:
            raise ValueError("Architecture JSON must contain 'components'")

        # Prepare architecture data for repository
        from app.schemas.architecture import ArchitectureCreate

        architecture_data = ArchitectureCreate(
            name=data.name,
            description=data.description or "",
            architecture_json=data.architecture_json,  # FIXED: use architecture_json not definition
            owner=data.owner or "system",
        )

        # Save to database
        item = repo.create(architecture_data)

        logger.info(
            f"Designer architecture saved: {item['id']} ({item['name']}) "
            f"with {len(data.architecture_json.get('components', {}))} components"
        )

        return DesignerSaveResponse(
            architecture_id=str(item['id']),
            name=item['name'],
            version=data.architecture_json.get('version', '1.0.0'),
            created_at=item['created_at'].isoformat(),
            updated_at=item['updated_at'].isoformat(),
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error saving designer architecture: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving architecture: {str(e)}",
        )


@router.get(
    "/designer/load/{architecture_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Lade Designer-Architektur",
    description="Lädt eine Architecture aus der Datenbank für den Infrastructure Designer",
    responses={
        200: {"description": "Architektur erfolgreich geladen"},
        404: {"description": "Architektur nicht gefunden"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def load_designer_architecture(
    architecture_id: UUID,
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> Dict[str, Any]:
    """Lädt Designer-Architektur aus Datenbank.

    Args:
        architecture_id: UUID of architecture to load
        repo: ArchitectureRepository (Dependency Injection)

    Returns:
        Complete architecture JSON for designer

    Raises:
        HTTPException: Wenn Architektur nicht gefunden oder Fehler
    """
    try:
        item = repo.get(str(architecture_id))

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Architecture {architecture_id} not found",
            )

        logger.info(f"Designer architecture loaded: {architecture_id}")

        # Return the definition (which contains the full architecture JSON)
        return item['definition']

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading designer architecture: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading architecture: {str(e)}",
        )


@router.post(
    "/designer/generate-terraform",
    response_model=TerraformGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generiere Terraform Code",
    description="Generiert Terraform HCL Code aus Architecture JSON",
    responses={
        200: {"description": "Terraform erfolgreich generiert"},
        422: {"description": "Ungültige Architektur"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Interner Serverfehler"},
    },
)
@limiter.limit("1000/minute" if settings.TESTING else "20/minute")
async def generate_terraform(
    request: Request,
    data: TerraformGenerateRequest,
    generator: TerraformGeneratorV2 = Depends(get_terraform_generator),
) -> TerraformGenerateResponse:
    """Generiert Terraform aus Architecture JSON.

    Args:
        data: Architecture JSON from designer
        generator: TerraformGeneratorV2 (Dependency Injection)

    Returns:
        Generated Terraform files

    Raises:
        HTTPException: Bei Fehlern während der Generierung
    """
    try:
        # Validate JSON structure
        if 'components' not in data.architecture_json:
            raise ValueError("Architecture JSON must contain 'components'")

        # Generate Terraform
        terraform_files = generator.generate(data.architecture_json)

        logger.info(
            f"Terraform generated: {len(terraform_files)} files, "
            f"{len(data.architecture_json.get('components', {}))} components"
        )

        return TerraformGenerateResponse(
            files=terraform_files,
            component_count=len(data.architecture_json.get('components', {})),
            warnings=[],  # Generator could return warnings
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating Terraform: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Terraform: {str(e)}",
        )


@router.post(
    "/designer/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validiere Architektur",
    description="Validiert Architecture JSON auf Fehler und Warnungen",
    responses={
        200: {"description": "Validation durchgeführt"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def validate_architecture(
    data: ValidationRequest,
) -> ValidationResponse:
    """Validiert Architecture JSON.

    Args:
        data: Architecture JSON to validate

    Returns:
        Validation result with errors and warnings

    Raises:
        HTTPException: Bei internen Fehlern
    """
    try:
        errors = []
        warnings = []

        architecture = data.architecture_json

        # Basic structure validation
        if not architecture.get('version'):
            errors.append("Missing 'version' field")

        if not architecture.get('metadata'):
            warnings.append("Missing 'metadata' field")

        if 'components' not in architecture:
            errors.append("Missing 'components' field")

        components = architecture.get('components', {})

        # Validate each component
        for comp_id, comp in components.items():
            if not comp.get('type'):
                errors.append(f"Component {comp_id}: Missing 'type' field")

            if not comp.get('name'):
                warnings.append(f"Component {comp_id}: Missing 'name' field")

            if not comp.get('config'):
                warnings.append(f"Component {comp_id}: Missing 'config' field")

        # Validate connections
        connections = architecture.get('connections', [])
        component_ids = set(architecture.get('components', {}).keys())

        for conn in connections:
            from_id = conn.get('from')
            to_id = conn.get('to')

            if from_id not in component_ids:
                errors.append(f"Connection references unknown component: {from_id}")

            if to_id not in component_ids:
                errors.append(f"Connection references unknown component: {to_id}")

        # VPC-specific validations
        vpcs = {k: v for k, v in architecture.get('components', {}).items() if v.get('type') == 'vpc'}
        subnets = {k: v for k, v in architecture.get('components', {}).items() if v.get('type') == 'subnet'}

        for subnet_id, subnet in subnets.items():
            # Support both 'vpc_id' and 'vpc' for flexibility
            vpc_id = subnet.get('config', {}).get('vpc_id') or subnet.get('config', {}).get('vpc')
            if not vpc_id:
                errors.append(f"Subnet {subnet_id}: Missing vpc_id or vpc")
            elif vpc_id not in vpcs:
                errors.append(f"Subnet {subnet_id}: References unknown VPC {vpc_id}")

        logger.info(
            f"Architecture validation: {len(errors)} errors, {len(warnings)} warnings"
        )

        return ValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            component_count=len(architecture.get('components', {})),
            connection_count=len(architecture.get('connections', [])),
        )

    except Exception as e:
        logger.error(f"Error validating architecture: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating architecture: {str(e)}",
        )
