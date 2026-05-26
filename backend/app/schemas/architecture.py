"""StackVertex Backend - Architecture Schemas.

Pydantic schemas für Validierung und Serialisierung von Architecture-Daten.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ArchitectureBase(BaseModel):
    """Basis-Schema mit gemeinsamen Feldern."""

    name: str = Field(..., min_length=1, max_length=255, description="Name der Architektur")
    description: str | None = Field(None, description="Beschreibung der Architektur")
    version: str = Field("1.0.0", max_length=50, description="Version der Architektur")
    architecture_json: dict[str, Any] = Field(
        ...,
        description="JSON-Definition der Architektur (components, connections, config)",
    )


class ArchitectureCreate(ArchitectureBase):
    """Schema für das Erstellen einer neuen Architektur."""

    owner: str = Field("system", max_length=255, description="Owner/Creator der Architektur")

    # Optionale Validierung des JSON-Schemas kann hier später hinzugefügt werden
    # z.B. mit einem validator für architecture_json


class ArchitectureUpdate(BaseModel):
    """Schema für das Aktualisieren einer Architektur.

    Alle Felder sind optional, nur die übergebenen werden aktualisiert.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    version: str | None = Field(None, max_length=50)
    architecture_json: dict[str, Any] | None = None
    owner: str | None = Field(None, max_length=255)


class ArchitectureInDB(ArchitectureBase):
    """Schema für Architektur-Daten aus der Datenbank.

    Enthält alle Felder inklusive ID und Timestamps.
    """

    id: UUID
    owner: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArchitectureResponse(ArchitectureInDB):
    """Schema für API-Responses.

    Aktuell identisch mit ArchitectureInDB, kann bei Bedarf erweitert werden.
    """

    pass


class ArchitectureListResponse(BaseModel):
    """Schema für paginated List-Responses."""

    items: list[ArchitectureResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
