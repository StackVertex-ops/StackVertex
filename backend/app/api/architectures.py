"""StackVertex Backend - Architecture API Endpoints.

REST API für CRUD-Operationen auf Architecture-Definitionen.
"""

import logging
from typing import Optional, Dict, Any, List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.repositories.architecture import ArchitectureRepository
from app.schemas.architecture import (
    ArchitectureCreate,
    ArchitectureUpdate,
    ArchitectureResponse,
    ArchitectureListResponse,
)
from app.core.json_engine import (
    VersioningService,
    ValidationError,
    VersionNotFoundError,
    CircularReferenceError
)
from app.api.auth import get_current_user, get_current_superadmin

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# Dependency injection for ArchitectureRepository
def get_architecture_repo() -> ArchitectureRepository:
    """Get ArchitectureRepository instance."""
    return ArchitectureRepository()


@router.post(
    "/architectures",
    response_model=ArchitectureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Erstelle neue Architektur",
    description="Erstellt eine neue Architektur-Definition in der Datenbank",
    responses={
        201: {"description": "Architektur erfolgreich erstellt"},
        422: {"description": "Validierungsfehler in den Eingabedaten"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Interner Serverfehler"},
    },
)
@limiter.limit("1000/minute" if settings.TESTING else "30/minute")
async def create_architecture_endpoint(
    request: Request,
    architecture: ArchitectureCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> ArchitectureResponse:
    """Erstellt eine neue Architektur.

    Args:
        architecture: ArchitectureCreate Schema mit allen benötigten Daten
        repo: ArchitectureRepository (Dependency Injection)

    Returns:
        Die erstellte Architektur mit ID und Timestamps

    Raises:
        HTTPException: Bei Fehlern während der Erstellung
    """
    try:
        item = repo.create(architecture)
        logger.info(f"Architektur erstellt: {item['id']} ({item['name']})")
        return ArchitectureResponse(**item)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Architektur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen der Architektur: {str(e)}",
        ) from e


@router.get(
    "/architectures",
    response_model=ArchitectureListResponse,
    status_code=status.HTTP_200_OK,
    summary="Liste Architekturen",
    description="Ruft eine paginierte Liste von Architekturen ab",
    responses={
        200: {"description": "Liste erfolgreich abgerufen"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def list_architectures_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
    owner: Optional[str] = Query(None, description="Filter nach Owner"),
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> ArchitectureListResponse:
    """Ruft eine Liste von Architekturen ab mit Pagination.

    Args:
        skip: Anzahl zu überspringender Einträge (für Pagination)
        limit: Maximale Anzahl zurückzugebender Einträge
        owner: Optional - Filter nach Owner
        repo: ArchitectureRepository (Dependency Injection)

    Returns:
        ArchitectureListResponse mit Liste und Metadaten

    Raises:
        HTTPException: Bei Fehlern während des Abrufs
    """
    try:
        items, total = repo.list(skip=skip, limit=limit, owner=owner)
        logger.debug(f"Architekturen abgerufen: {len(items)} von {total}")

        return ArchitectureListResponse(
            items=[ArchitectureResponse(**item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Architekturen: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Architekturen: {str(e)}",
        ) from e


@router.get(
    "/architectures/{architecture_id}",
    response_model=ArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Hole Architektur",
    description="Ruft eine einzelne Architektur anhand der ID ab",
    responses={
        200: {"description": "Architektur gefunden"},
        404: {"description": "Architektur nicht gefunden"},
        422: {"description": "Ungültige UUID"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def get_architecture_endpoint(
    architecture_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> ArchitectureResponse:
    """Ruft eine einzelne Architektur ab.

    Args:
        architecture_id: UUID der gesuchten Architektur
        repo: ArchitectureRepository (Dependency Injection)

    Returns:
        Die gefundene Architektur

    Raises:
        HTTPException: 404 wenn nicht gefunden, 500 bei anderen Fehlern
    """
    try:
        item = repo.get(architecture_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Architektur mit ID {architecture_id} nicht gefunden",
            )

        logger.debug(f"Architektur abgerufen: {item['id']} ({item['name']})")
        return ArchitectureResponse(**item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Architektur {architecture_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Architektur: {str(e)}",
        ) from e


@router.put(
    "/architectures/{architecture_id}",
    response_model=ArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Aktualisiere Architektur",
    description="Aktualisiert eine bestehende Architektur (Partial Update)",
    responses={
        200: {"description": "Architektur erfolgreich aktualisiert"},
        404: {"description": "Architektur nicht gefunden"},
        422: {"description": "Validierungsfehler oder ungültige UUID"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Interner Serverfehler"},
    },
)
@limiter.limit("1000/minute" if settings.TESTING else "30/minute")
async def update_architecture_endpoint(
    request: Request,
    architecture_id: UUID,
    architecture_update: ArchitectureUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> ArchitectureResponse:
    """Aktualisiert eine bestehende Architektur.

    Nur die übergebenen Felder werden aktualisiert (Partial Update).

    Args:
        architecture_id: UUID der zu aktualisierenden Architektur
        architecture_update: ArchitectureUpdate Schema mit den neuen Daten
        repo: ArchitectureRepository (Dependency Injection)

    Returns:
        Die aktualisierte Architektur

    Raises:
        HTTPException: 404 wenn nicht gefunden, 500 bei anderen Fehlern
    """
    try:
        item = repo.update(architecture_id, architecture_update)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Architektur mit ID {architecture_id} nicht gefunden",
            )

        logger.info(f"Architektur aktualisiert: {item['id']} ({item['name']})")
        return ArchitectureResponse(**item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Architektur {architecture_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Aktualisieren der Architektur: {str(e)}",
        ) from e


@router.delete(
    "/architectures/{architecture_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Lösche Architektur",
    description="Löscht eine Architektur aus der Datenbank",
    responses={
        204: {"description": "Architektur erfolgreich gelöscht"},
        404: {"description": "Architektur nicht gefunden"},
        422: {"description": "Ungültige UUID"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Interner Serverfehler"},
    },
)
@limiter.limit("1000/minute" if settings.TESTING else "30/minute")
async def delete_architecture_endpoint(
    request: Request,
    architecture_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: ArchitectureRepository = Depends(get_architecture_repo),
) -> None:
    """Löscht eine Architektur.

    Args:
        architecture_id: UUID der zu löschenden Architektur
        repo: ArchitectureRepository (Dependency Injection)

    Raises:
        HTTPException: 404 wenn nicht gefunden, 500 bei anderen Fehlern
    """
    try:
        success = repo.delete(architecture_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Architektur mit ID {architecture_id} nicht gefunden",
            )

        logger.info(f"Architektur gelöscht: {architecture_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Architektur {architecture_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Architektur: {str(e)}",
        ) from e


# ============================================================================
# Versioning Endpoints
# ============================================================================

versioning_service = VersioningService()


@router.get(
    "/architectures/{architecture_id}/versions",
    response_model=List[ArchitectureResponse],
    status_code=status.HTTP_200_OK,
    summary="Hole Version History",
    description="Ruft die komplette Version-Chain einer Architecture ab",
    responses={
        200: {"description": "Version History erfolgreich abgerufen"},
        404: {"description": "Architecture nicht gefunden"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def get_version_history_endpoint(
    architecture_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: Optional[int] = Query(None, description="Max. Anzahl Versionen"),
) -> List[ArchitectureResponse]:
    """Holt Version History einer Architecture.

    Returns alle Versionen in der Chain (neueste zuerst).

    Args:
        architecture_id: UUID der Architecture
        limit: Optional max. Anzahl Versionen

    Returns:
        Liste von Architecture Versionen

    Raises:
        HTTPException: 404 wenn nicht gefunden
    """
    try:
        history = versioning_service.get_version_history(architecture_id, limit)
        logger.info(f"Version history abgerufen für {architecture_id}: {len(history)} Versionen")
        return [ArchitectureResponse(**item) for item in history]

    except VersionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Architecture mit ID {architecture_id} nicht gefunden",
        ) from e
    except CircularReferenceError as e:
        logger.error(f"Circular reference in version chain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Circular reference detected in version chain",
        ) from e
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Version History: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Version History: {str(e)}",
        ) from e


@router.get(
    "/architectures/{architecture_id}/diff/{other_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Vergleiche Versionen",
    description="Generiert Diff zwischen zwei Architecture Versionen",
    responses={
        200: {"description": "Diff erfolgreich generiert"},
        404: {"description": "Eine oder beide Architectures nicht gefunden"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def compare_versions_endpoint(
    architecture_id: UUID,
    other_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    component_level: bool = Query(False, description="Component-Level Diff generieren"),
) -> Dict[str, Any]:
    """Vergleicht zwei Architecture Versionen.

    Args:
        architecture_id: Erste Version (alt)
        other_id: Zweite Version (neu)
        component_level: Ob Component-Level Diff generiert werden soll

    Returns:
        Dict mit Diff-Informationen

    Raises:
        HTTPException: 404 wenn eine Version nicht gefunden wurde
    """
    try:
        comparison = versioning_service.compare_versions(
            architecture_id, other_id, component_level
        )
        logger.info(f"Diff generiert zwischen {architecture_id} und {other_id}")
        return comparison

    except VersionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Fehler beim Vergleichen der Versionen: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Vergleichen der Versionen: {str(e)}",
        ) from e


@router.post(
    "/architectures/validate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Validiere Architecture JSON",
    description="Validiert Architecture JSON ohne zu speichern",
    responses={
        200: {"description": "Validation erfolgreich"},
        422: {"description": "Validation fehlgeschlagen"},
        500: {"description": "Interner Serverfehler"},
    },
)
async def validate_architecture_endpoint(
    architecture_json: Dict[str, Any] = Body(..., description="Zu validierendes Architecture JSON"),
    current_user: Annotated[dict, Depends(get_current_user)],
    version: Optional[str] = Query(None, description="Schema Version (default: 1.0.0)"),
) -> Dict[str, Any]:
    """Validiert Architecture JSON gegen Schema.

    Validiert ohne in DB zu speichern. Nützlich für Client-Side Validation.

    Args:
        architecture_json: Zu validierendes JSON
        version: Optional Schema Version

    Returns:
        Dict mit Validation-Result

    Raises:
        HTTPException: 422 bei Validation-Fehlern
    """
    try:
        result = versioning_service.validate_version(architecture_json, version)

        if not result.valid:
            logger.warning(f"Validation failed: {len(result.errors)} errors")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "valid": False,
                    "errors": result.errors,
                    "version": result.version
                }
            )

        logger.info(f"Validation successful for version {result.version}")
        return {
            "valid": True,
            "version": result.version,
            "validated_at": result.validated_at.isoformat()
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "valid": False,
                "errors": e.errors,
                "version": e.schema_version,
                "message": str(e)
            }
        ) from e
    except Exception as e:
        logger.error(f"Fehler bei der Validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Validation: {str(e)}",
        ) from e
