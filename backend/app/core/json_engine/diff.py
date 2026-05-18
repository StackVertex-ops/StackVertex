"""JSON Diff Generator - Vergleicht Architecture JSONs.

Generiert strukturierte Diffs zwischen zwei Architecture JSON Versionen
und erstellt human-readable Summaries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.json_engine.exceptions import DiffGenerationError


@dataclass
class DiffResult:
    """Ergebnis eines JSON Diffs.

    Attributes:
        added: Neu hinzugefügte Keys/Components
        removed: Entfernte Keys/Components
        modified: Geänderte Werte
        unchanged: Unveränderte Keys (optional, für Details)
        summary: Human-readable Summary
        generated_at: Zeitpunkt der Diff-Generierung
    """

    added: dict[str, Any] = field(default_factory=dict)
    removed: dict[str, Any] = field(default_factory=dict)
    modified: dict[str, Any] = field(default_factory=dict)
    unchanged: set[str] | None = None
    summary: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


class JSONDiff:
    """Generiert Diffs zwischen Architecture JSONs.

    Unterstützt:
    - Shallow und Deep Comparison
    - Component-Level Diffs
    - Human-Readable Summaries
    - Patch-Generation (für Migrations)
    """

    def __init__(self, deep: bool = True):
        """Initialize JSON Diff Generator.

        Args:
            deep: Ob Deep Comparison durchgeführt werden soll
        """
        self.deep = deep

    def generate_diff(
        self,
        old_json: dict[str, Any],
        new_json: dict[str, Any],
        path: str = "$"
    ) -> DiffResult:
        """Generiert Diff zwischen zwei JSONs.

        Args:
            old_json: Original JSON
            new_json: Neues JSON
            path: JSON Path (für rekursive Calls)

        Returns:
            DiffResult mit allen Änderungen

        Raises:
            DiffGenerationError: Bei Fehlern während der Diff-Generierung
        """
        try:
            result = DiffResult()

            # Alle Keys aus beiden JSONs
            old_keys = set(old_json.keys()) if isinstance(old_json, dict) else set()
            new_keys = set(new_json.keys()) if isinstance(new_json, dict) else set()

            # Added: Keys die nur in new_json sind
            added_keys = new_keys - old_keys
            for key in added_keys:
                result.added[f"{path}.{key}"] = new_json[key]

            # Removed: Keys die nur in old_json sind
            removed_keys = old_keys - new_keys
            for key in removed_keys:
                result.removed[f"{path}.{key}"] = old_json[key]

            # Prüfe gemeinsame Keys auf Änderungen
            common_keys = old_keys & new_keys
            for key in common_keys:
                old_value = old_json[key]
                new_value = new_json[key]

                # Rekursive Deep Comparison für nested dicts
                if self.deep and isinstance(old_value, dict) and isinstance(new_value, dict):
                    nested_diff = self.generate_diff(old_value, new_value, f"{path}.{key}")
                    result.added.update(nested_diff.added)
                    result.removed.update(nested_diff.removed)
                    result.modified.update(nested_diff.modified)
                # Rekursive Comparison für Lists
                elif self.deep and isinstance(old_value, list) and isinstance(new_value, list):
                    list_diff = self._diff_lists(old_value, new_value, f"{path}.{key}")
                    result.modified.update(list_diff)
                # Value-Comparison
                elif old_value != new_value:
                    result.modified[f"{path}.{key}"] = {
                        "old": old_value,
                        "new": new_value
                    }

            # Summary generieren
            result.summary = self._generate_summary(result)

            return result

        except Exception as e:
            raise DiffGenerationError(f"Failed to generate diff: {str(e)}") from e

    def _diff_lists(
        self,
        old_list: list[Any],
        new_list: list[Any],
        path: str
    ) -> dict[str, Any]:
        """Vergleicht zwei Listen und findet Änderungen.

        Args:
            old_list: Original Liste
            new_list: Neue Liste
            path: JSON Path

        Returns:
            Dict mit Änderungen
        """
        changes = {}

        # Einfacher Vergleich: Länge und Elemente
        if len(old_list) != len(new_list):
            changes[f"{path}[length]"] = {
                "old": len(old_list),
                "new": len(new_list)
            }

        # Element-by-Element Vergleich (nur für primitive types)
        for i, (old_item, new_item) in enumerate(zip(old_list, new_list)):
            if old_item != new_item:
                if isinstance(old_item, dict) and isinstance(new_item, dict):
                    # Rekursiver Vergleich für dicts in listen
                    nested_diff = self.generate_diff(old_item, new_item, f"{path}[{i}]")
                    if nested_diff.modified or nested_diff.added or nested_diff.removed:
                        changes[f"{path}[{i}]"] = {
                            "old": old_item,
                            "new": new_item
                        }
                else:
                    changes[f"{path}[{i}]"] = {
                        "old": old_item,
                        "new": new_item
                    }

        return changes

    def _generate_summary(self, diff: DiffResult) -> str:
        """Generiert human-readable Summary.

        Args:
            diff: DiffResult

        Returns:
            Summary-String
        """
        parts = []

        if diff.added:
            parts.append(f"{len(diff.added)} added")
        if diff.removed:
            parts.append(f"{len(diff.removed)} removed")
        if diff.modified:
            parts.append(f"{len(diff.modified)} modified")

        if not parts:
            return "No changes"

        return ", ".join(parts)

    def generate_component_diff(
        self,
        old_architecture: dict[str, Any],
        new_architecture: dict[str, Any]
    ) -> dict[str, Any]:
        """Generiert Component-Level Diff.

        Spezialisierter Diff für Architecture Components.

        Args:
            old_architecture: Original Architecture JSON
            new_architecture: Neue Architecture JSON

        Returns:
            Dict mit Component-Änderungen
        """
        component_diff = {
            "added_components": [],
            "removed_components": [],
            "modified_components": [],
            "added_relationships": [],
            "removed_relationships": []
        }

        # Components extrahieren
        old_components = old_architecture.get("architecture", {}).get("components", [])
        new_components = new_architecture.get("architecture", {}).get("components", [])

        # Component IDs für Vergleich
        old_ids = {comp["id"]: comp for comp in old_components if "id" in comp}
        new_ids = {comp["id"]: comp for comp in new_components if "id" in comp}

        # Added components
        added_ids = set(new_ids.keys()) - set(old_ids.keys())
        component_diff["added_components"] = [new_ids[id_] for id_ in added_ids]

        # Removed components
        removed_ids = set(old_ids.keys()) - set(new_ids.keys())
        component_diff["removed_components"] = [old_ids[id_] for id_ in removed_ids]

        # Modified components
        common_ids = set(old_ids.keys()) & set(new_ids.keys())
        for comp_id in common_ids:
            if old_ids[comp_id] != new_ids[comp_id]:
                component_diff["modified_components"].append({
                    "id": comp_id,
                    "old": old_ids[comp_id],
                    "new": new_ids[comp_id]
                })

        # Relationships
        old_rels = old_architecture.get("architecture", {}).get("relationships", [])
        new_rels = new_architecture.get("architecture", {}).get("relationships", [])

        # Relationship Comparison (einfache Liste)
        for rel in new_rels:
            if rel not in old_rels:
                component_diff["added_relationships"].append(rel)

        for rel in old_rels:
            if rel not in new_rels:
                component_diff["removed_relationships"].append(rel)

        return component_diff

    def apply_diff(
        self,
        base_json: dict[str, Any],
        diff: DiffResult
    ) -> dict[str, Any]:
        """Wendet Diff auf Base JSON an.

        Nützlich für Migrations und Rollbacks.

        Args:
            base_json: Base JSON
            diff: DiffResult zum Anwenden

        Returns:
            Modifiziertes JSON

        Raises:
            DiffGenerationError: Bei Fehlern
        """
        try:
            result = base_json.copy()

            # Added keys hinzufügen
            for path, value in diff.added.items():
                self._set_value_by_path(result, path, value)

            # Removed keys entfernen
            for path in diff.removed.keys():
                self._delete_value_by_path(result, path)

            # Modified keys ändern
            for path, change in diff.modified.items():
                if isinstance(change, dict) and "new" in change:
                    self._set_value_by_path(result, path, change["new"])

            return result

        except Exception as e:
            raise DiffGenerationError(f"Failed to apply diff: {str(e)}") from e

    def _set_value_by_path(
        self,
        obj: dict[str, Any],
        path: str,
        value: Any
    ) -> None:
        """Setzt Wert an JSON Path.

        Args:
            obj: Ziel-Objekt
            path: JSON Path (e.g., "$.metadata.name")
            value: Zu setzender Wert
        """
        keys = path.strip("$").strip(".").split(".")
        current = obj

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _delete_value_by_path(
        self,
        obj: dict[str, Any],
        path: str
    ) -> None:
        """Löscht Wert an JSON Path.

        Args:
            obj: Ziel-Objekt
            path: JSON Path
        """
        keys = path.strip("$").strip(".").split(".")
        current = obj

        for key in keys[:-1]:
            if key not in current:
                return
            current = current[key]

        if keys[-1] in current:
            del current[keys[-1]]
