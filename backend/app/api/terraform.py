"""Terraform Generation API Endpoints.

REST API für Terraform Code-Generierung aus Blueprints und Architecture JSON.
"""

import logging
from typing import Dict, Any, Annotated
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, status, Depends

from app.services.terraform_generator import generate_terraform_from_blueprint
from app.services.terraform_generator_v2 import TerraformGeneratorV2
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/terraform/generate",
    status_code=status.HTTP_200_OK,
    summary="Generate Terraform Code",
    description="Generiert Terraform HCL Code aus Blueprint und Konfiguration",
    responses={
        200: {"description": "Terraform generation successful"},
        400: {"description": "Invalid configuration"},
        404: {"description": "Blueprint not found"},
        500: {"description": "Internal server error"},
    },
)
async def generate_terraform(
    blueprint_id: str = Body(..., description="Blueprint ID"),
    configuration: Dict[str, Any] = Body(..., description="Blueprint Configuration"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> Dict[str, Any]:
    """Generiert Terraform Code aus Blueprint + Configuration.

    Args:
        blueprint_id: ID des Blueprints (z.B. "static-website")
        configuration: User-Konfiguration aus Form

    Returns:
        Dict mit terraform_code (String)

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # Generate Terraform
        terraform_code = generate_terraform_from_blueprint(blueprint_id, configuration)

        return {
            "terraform_code": terraform_code,
            "blueprint_id": blueprint_id,
            "generated_at": None,  # TODO: Add timestamp
        }

    except FileNotFoundError as e:
        logger.error(f"Blueprint template not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint template not found: {blueprint_id}",
        ) from e

    except ValueError as e:
        logger.error(f"Validation error in Terraform generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Error generating Terraform: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Terraform: {str(e)}",
        ) from e


@router.post(
    "/terraform/validate",
    status_code=status.HTTP_200_OK,
    summary="Validate Terraform Code",
    description="Validiert generiertes Terraform HCL",
    responses={
        200: {"description": "Validation successful"},
        400: {"description": "Invalid Terraform code"},
        500: {"description": "Internal server error"},
    },
)
async def validate_terraform(
    terraform_code: str = Body(..., description="Terraform HCL Code"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> Dict[str, Any]:
    """Validiert Terraform Code.

    Args:
        terraform_code: HCL Code zum Validieren

    Returns:
        Validation result

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # TODO: Implementiere terraform fmt -check
        # Für jetzt: Einfache Syntax-Checks
        if not terraform_code.strip():
            raise ValueError("Terraform code ist leer")

        if "resource" not in terraform_code and "module" not in terraform_code:
            raise ValueError("Kein resource oder module gefunden")

        return {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

    except ValueError as e:
        logger.error(f"Terraform validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Terraform code: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Error validating Terraform: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating Terraform: {str(e)}",
        ) from e


@router.post(
    "/terraform/generate-from-json",
    status_code=status.HTTP_200_OK,
    summary="Generate Terraform from Architecture JSON",
    description="Generiert Terraform HCL Code aus Architecture JSON (Infrastructure Designer)",
    responses={
        200: {"description": "Terraform generation successful"},
        400: {"description": "Invalid architecture JSON"},
        500: {"description": "Internal server error"},
    },
)
async def generate_terraform_from_json(
    architecture: Dict[str, Any] = Body(..., description="Architecture JSON from Infrastructure Designer"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> Dict[str, Any]:
    """Generiert Terraform Code aus Architecture JSON (Component-based).

    Args:
        architecture: Complete Architecture JSON mit metadata, components, connections

    Returns:
        Dict mit terraform_files (Dict[filename, content])

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # Validate basic structure
        if "components" not in architecture:
            raise ValueError("Architecture JSON muss 'components' enthalten")

        if not architecture["components"]:
            raise ValueError("Architecture hat keine components")

        # Initialize Generator
        generator = TerraformGeneratorV2()

        # Generate Terraform files
        terraform_files = generator.generate(architecture)

        metadata = architecture.get("metadata", {})

        return {
            "terraform_files": terraform_files,
            "project_name": metadata.get("name", "infrastructure"),
            "generated_at": datetime.utcnow().isoformat(),
            "file_count": len(terraform_files),
            "component_count": len(architecture["components"]),
        }

    except ValueError as e:
        logger.error(f"Validation error in Architecture JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid architecture JSON: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Error generating Terraform from JSON: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Terraform: {str(e)}",
        ) from e
