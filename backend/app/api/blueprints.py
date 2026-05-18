"""API Endpoints für Blueprint-Management.

Stellt REST-Endpunkte zur Verwaltung von Infrastructure Blueprints bereit.
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.data.blueprints import (
    get_blueprint,
    list_blueprints,
    get_blueprints_by_category,
    search_blueprints,
    BLUEPRINT_REGISTRY,
    BlueprintCategory,
    BlueprintDifficulty,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class BlueprintListResponse(BaseModel):
    """Response für Blueprint-Liste."""

    blueprints: List[Any] = Field(..., description="Liste von Blueprints")
    total: int = Field(..., description="Gesamtanzahl")


class BlueprintResponse(BaseModel):
    """Response für einzelnen Blueprint."""

    blueprint: Any = Field(..., description="Blueprint-Daten")


@router.get(
    "/blueprints",
    response_model=BlueprintListResponse,
    status_code=status.HTTP_200_OK,
    summary="Liste alle Blueprints",
    description="Gibt alle verfügbaren Blueprints zurück, optional gefiltert",
)
async def get_blueprints(
    category: Optional[str] = Query(None, description="Filtere nach Kategorie (static, webapp, api, database)"),
    difficulty: Optional[str] = Query(None, description="Filtere nach Schwierigkeit (beginner, intermediate, advanced)"),
    max_cost_usd: Optional[float] = Query(None, description="Maximale monatliche Kosten (typical)"),
    search: Optional[str] = Query(None, description="Suchbegriff für Name, Description oder Use Cases"),
) -> BlueprintListResponse:
    """Liste alle Blueprints mit optionalen Filtern."""

    try:
        # Search query hat Vorrang
        if search:
            blueprints = search_blueprints(search)
        else:
            # Konvertiere String zu Enum
            category_enum = None
            if category:
                try:
                    category_enum = BlueprintCategory(category)
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ungültige Kategorie: {category}. Gültige Werte: static, webapp, api, database"
                    ) from e

            difficulty_enum = None
            if difficulty:
                try:
                    difficulty_enum = BlueprintDifficulty(difficulty)
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ungültige Schwierigkeit: {difficulty}. Gültige Werte: beginner, intermediate, advanced"
                    ) from e

            blueprints = list_blueprints(
                category=category_enum,
                difficulty=difficulty_enum,
                max_cost_usd=max_cost_usd
            )

        # Konvertiere Blueprints zu Dict (für JSON Response)
        blueprints_data = [bp.model_dump() for bp in blueprints]

        return BlueprintListResponse(
            blueprints=blueprints_data,
            total=len(blueprints_data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden der Blueprints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden der Blueprints"
        ) from e


@router.get(
    "/blueprints/categories",
    status_code=status.HTTP_200_OK,
    summary="Gruppiere Blueprints nach Kategorie",
    description="Gibt alle Blueprints gruppiert nach Kategorie zurück",
)
async def get_blueprints_grouped_by_category() -> Dict[str, List[Any]]:
    """Gruppiere alle Blueprints nach Kategorie."""

    try:
        grouped = get_blueprints_by_category()

        # Konvertiere Blueprints zu Dict
        result = {}
        for category, blueprints in grouped.items():
            result[category] = [bp.model_dump() for bp in blueprints]

        return result

    except Exception as e:
        logger.error(f"Fehler beim Gruppieren der Blueprints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Gruppieren der Blueprints"
        ) from e


@router.get(
    "/blueprints/{blueprint_id}",
    response_model=BlueprintResponse,
    status_code=status.HTTP_200_OK,
    summary="Hole einzelnen Blueprint",
    description="Gibt Details zu einem spezifischen Blueprint zurück",
)
async def get_blueprint_by_id(blueprint_id: str) -> BlueprintResponse:
    """Hole einzelnen Blueprint anhand der ID."""

    try:
        blueprint = get_blueprint(blueprint_id)

        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint '{blueprint_id}' nicht gefunden"
            )

        return BlueprintResponse(
            blueprint=blueprint.model_dump()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden des Blueprints {blueprint_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden des Blueprints"
        ) from e


@router.get(
    "/blueprints/{blueprint_id}/terraform",
    status_code=status.HTTP_200_OK,
    summary="Generiere Terraform-Template",
    description="Gibt das Terraform-Template für einen Blueprint zurück (Jinja2 Template)",
)
async def get_blueprint_terraform_template(blueprint_id: str) -> Dict[str, str]:
    """Hole Terraform-Template für Blueprint."""

    try:
        blueprint = get_blueprint(blueprint_id)

        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint '{blueprint_id}' nicht gefunden"
            )

        # TODO: Template-File lesen und zurückgeben
        # Für jetzt: Placeholder
        return {
            "blueprint_id": blueprint_id,
            "template_path": blueprint.terraform_template,
            "template": "# TODO: Load actual template from file"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden des Terraform-Templates für {blueprint_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden des Terraform-Templates"
        ) from e
