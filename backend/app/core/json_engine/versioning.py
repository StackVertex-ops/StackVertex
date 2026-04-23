"""Versioning Service - Core Version Tracking Logic.

Verwaltet Architecture Versionen, parent-child Beziehungen,
und koordiniert Validation + Diff Generation.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.repositories.architecture import ArchitectureRepository
from app.schemas.architecture import ArchitectureCreate
from app.core.json_engine.validator import ArchitectureValidator, ValidationResult
from app.core.json_engine.diff import JSONDiff, DiffResult
from app.core.json_engine.exceptions import (
    VersionNotFoundError,
    ValidationError,
    CircularReferenceError
)


class VersioningService:
    """Service für Architecture Version Management.

    Verwaltet:
    - Version Creation mit Validation
    - Parent-Child Relationships
    - Version History Tracking
    - Diff Generation zwischen Versionen
    """

    def __init__(self):
        """Initialize Versioning Service."""
        self.validator = ArchitectureValidator()
        self.diff_generator = JSONDiff(deep=True)

    def create_version(
        self,
        architecture_json: Dict[str, Any],
        name: str,
        description: Optional[str] = None,
        owner: str = "system",
        parent_version_id: Optional[UUID] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """Erstellt neue Architecture Version mit Validation.

        Args:
            architecture_json: Architecture JSON
            name: Name der Architecture
            description: Optionale Beschreibung
            owner: Owner/Creator
            parent_version_id: Optional Parent Version ID
            validate: Ob JSON validiert werden soll

        Returns:
            Neu erstellte Architecture (dict)

        Raises:
            ValidationError: Bei invaliden JSON
            VersionNotFoundError: Wenn Parent nicht existiert
        """
        # Validation durchführen (falls aktiviert)
        if validate:
            self.validator.validate_and_raise(architecture_json)

        # Version aus JSON extrahieren
        version = architecture_json.get("version", "1.0.0")

        # Parent Version prüfen (falls angegeben)
        repo = ArchitectureRepository()
        if parent_version_id:
            parent_item = repo.get(parent_version_id)

            if not parent_item:
                raise VersionNotFoundError(str(parent_version_id))

            # Parent Version ID in JSON metadata eintragen
            if "metadata" not in architecture_json:
                architecture_json["metadata"] = {}
            architecture_json["metadata"]["parent_version"] = str(parent_version_id)

        # Architecture erstellen
        arch_create = ArchitectureCreate(
            name=name,
            description=description or "",
            version=version,
            owner=owner,
            architecture_json=architecture_json
        )

        item = repo.create(arch_create)
        return item

    def get_version_history(
        self,
        architecture_id: UUID,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Holt Version History für Architecture.

        Verfolgt die Version-Chain von aktueller Version bis zur Root.

        Args:
            architecture_id: Architecture ID (kann beliebige Version sein)
            limit: Max. Anzahl Versionen (optional)

        Returns:
            Liste von Architecture items (dict, neueste zuerst)

        Raises:
            VersionNotFoundError: Wenn Architecture nicht existiert
            CircularReferenceError: Bei zirkulären Referenzen
        """
        # Initiale Architecture laden
        repo = ArchitectureRepository()
        current = repo.get(architecture_id)

        if not current:
            raise VersionNotFoundError(str(architecture_id))

        # Version Chain aufbauen
        history = [current]
        seen_ids = {str(architecture_id)}
        max_iterations = limit or 100  # Safety limit gegen infinite loops

        # Rückwärts durch Parent-Kette gehen
        for _ in range(max_iterations):
            # Parent Version ID aus JSON metadata
            metadata = current.get("architecture_json", {}).get("metadata", {})
            parent_id = metadata.get("parent_version")

            if not parent_id:
                # Keine weitere Parent Version
                break

            # Circular reference check
            if parent_id in seen_ids:
                raise CircularReferenceError(list(seen_ids) + [parent_id])

            # Parent laden
            parent = repo.get(UUID(parent_id))

            if not parent:
                # Parent nicht mehr vorhanden - Chain endet hier
                break

            history.append(parent)
            seen_ids.add(parent_id)
            current = parent

            # Limit check
            if limit and len(history) >= limit:
                break

        return history

    def compare_versions(
        self,
        version_a_id: UUID,
        version_b_id: UUID,
        component_level: bool = False
    ) -> Dict[str, Any]:
        """Vergleicht zwei Architecture Versionen.

        Args:
            version_a_id: Erste Version (alt)
            version_b_id: Zweite Version (neu)
            component_level: Ob Component-Level Diff generiert werden soll

        Returns:
            Dict mit Diff-Informationen

        Raises:
            VersionNotFoundError: Wenn eine Version nicht existiert
        """
        # Versionen laden
        repo = ArchitectureRepository()
        version_a = repo.get(version_a_id)
        version_b = repo.get(version_b_id)

        if not version_a:
            raise VersionNotFoundError(str(version_a_id))
        if not version_b:
            raise VersionNotFoundError(str(version_b_id))

        # Standard Diff generieren
        diff_result = self.diff_generator.generate_diff(
            version_a["architecture_json"],
            version_b["architecture_json"]
        )

        # Response zusammenstellen
        comparison = {
            "version_a": {
                "id": version_a["id"],
                "name": version_a["name"],
                "version": version_a["version"],
                "created_at": version_a["created_at"]
            },
            "version_b": {
                "id": version_b["id"],
                "name": version_b["name"],
                "version": version_b["version"],
                "created_at": version_b["created_at"]
            },
            "diff": {
                "added": diff_result.added,
                "removed": diff_result.removed,
                "modified": diff_result.modified,
                "summary": diff_result.summary
            }
        }

        # Component-Level Diff (optional)
        if component_level:
            component_diff = self.diff_generator.generate_component_diff(
                version_a["architecture_json"],
                version_b["architecture_json"]
            )
            comparison["component_diff"] = component_diff

        return comparison

    def get_latest_version(
        self,
        architecture_id: UUID
    ) -> Dict[str, Any]:
        """Holt die neueste Version einer Architecture.

        Geht die Version-Chain vorwärts bis zur neuesten Version.

        Args:
            architecture_id: Beliebige Version der Architecture

        Returns:
            Neueste Version (dict)

        Raises:
            VersionNotFoundError: Wenn Architecture nicht existiert
        """
        # Alle Versionen der gleichen Architecture finden
        # (Identifiziert über Name - könnte verbessert werden mit Architecture Group ID)
        repo = ArchitectureRepository()
        initial = repo.get(architecture_id)

        if not initial:
            raise VersionNotFoundError(str(architecture_id))

        # Alle Architectures mit gleichem Namen laden
        all_items, _ = repo.list(skip=0, limit=1000)  # Assume max 1000 versions

        # Filtern nach gleichem Namen
        same_name = [
            item for item in all_items
            if item["name"] == initial["name"]
        ]

        # Sortieren nach created_at DESC
        same_name.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Neueste Version ist die erste
        return same_name[0] if same_name else initial

    def validate_version(
        self,
        architecture_json: Dict[str, Any],
        version: Optional[str] = None
    ) -> ValidationResult:
        """Validiert Architecture JSON ohne zu speichern.

        Args:
            architecture_json: Zu validierendes JSON
            version: Schema Version (optional)

        Returns:
            ValidationResult

        Raises:
            SchemaNotFoundError: Wenn Schema nicht existiert
        """
        return self.validator.validate(architecture_json, version)

    def is_descendant_of(
        self,
        version_id: UUID,
        ancestor_id: UUID
    ) -> bool:
        """Prüft ob version_id ein Nachfahre von ancestor_id ist.

        Args:
            version_id: Zu prüfende Version
            ancestor_id: Potentieller Vorfahr

        Returns:
            True wenn version_id von ancestor_id abstammt

        Raises:
            VersionNotFoundError: Wenn eine Version nicht existiert
        """
        try:
            history = self.get_version_history(version_id)
            ancestor_ids = {item["id"] for item in history}
            return str(ancestor_id) in ancestor_ids
        except VersionNotFoundError:
            return False
