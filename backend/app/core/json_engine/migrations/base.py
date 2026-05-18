"""Migration Base Class - Framework für JSON Schema Migrations.

Ermöglicht Schema-Migrationen zwischen Versionen (z.B. v1.0.0 → v2.0.0).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.core.json_engine.exceptions import MigrationError


class BaseMigration(ABC):
    """Abstract Base Class für Schema Migrations.

    Subclasses implementieren spezifische Migrations zwischen Versionen.

    Example:
        class Migration_1_0_0_to_2_0_0(BaseMigration):
            source_version = "1.0.0"
            target_version = "2.0.0"

            def upgrade(self, data):
                # Transform v1.0.0 to v2.0.0
                data["new_field"] = "default"
                return data

            def downgrade(self, data):
                # Revert v2.0.0 to v1.0.0
                del data["new_field"]
                return data
    """

    source_version: str = ""
    target_version: str = ""
    description: str = ""

    @abstractmethod
    def upgrade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrates data from source_version to target_version.

        Args:
            data: Architecture JSON in source_version format

        Returns:
            Migrated data in target_version format

        Raises:
            MigrationError: Bei Fehlern während der Migration
        """
        pass

    @abstractmethod
    def downgrade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Reverts migration from target_version to source_version.

        Args:
            data: Architecture JSON in target_version format

        Returns:
            Reverted data in source_version format

        Raises:
            MigrationError: Bei Fehlern während der Migration
        """
        pass

    def validate_source(self, data: dict[str, Any]) -> bool:
        """Validates that data matches source_version.

        Args:
            data: Architecture JSON

        Returns:
            True if valid for source version
        """
        version = data.get("version", "")
        return version == self.source_version

    def validate_target(self, data: dict[str, Any]) -> bool:
        """Validates that data matches target_version.

        Args:
            data: Architecture JSON

        Returns:
            True if valid for target version
        """
        version = data.get("version", "")
        return version == self.target_version

    def apply(
        self,
        data: dict[str, Any],
        direction: str = "upgrade"
    ) -> dict[str, Any]:
        """Applies migration in specified direction.

        Args:
            data: Architecture JSON
            direction: "upgrade" oder "downgrade"

        Returns:
            Migrated data

        Raises:
            MigrationError: Bei ungültiger Direction oder Migrations-Fehlern
        """
        if direction not in ["upgrade", "downgrade"]:
            raise MigrationError(
                f"Invalid migration direction: {direction}. Must be 'upgrade' or 'downgrade'."
            )

        try:
            if direction == "upgrade":
                if not self.validate_source(data):
                    raise MigrationError(
                        f"Data version mismatch. Expected {self.source_version}, "
                        f"got {data.get('version', 'unknown')}",
                        source_version=self.source_version,
                        target_version=self.target_version
                    )
                result = self.upgrade(data)
                # Update version field
                result["version"] = self.target_version
                # Add migration metadata
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["migrated_from"] = self.source_version
                result["metadata"]["migrated_at"] = datetime.utcnow().isoformat()
                return result

            else:  # downgrade
                if not self.validate_target(data):
                    raise MigrationError(
                        f"Data version mismatch. Expected {self.target_version}, "
                        f"got {data.get('version', 'unknown')}",
                        source_version=self.source_version,
                        target_version=self.target_version
                    )
                result = self.downgrade(data)
                # Update version field
                result["version"] = self.source_version
                # Remove migration metadata
                if "metadata" in result:
                    result["metadata"].pop("migrated_from", None)
                    result["metadata"].pop("migrated_at", None)
                return result

        except Exception as e:
            if isinstance(e, MigrationError):
                raise
            raise MigrationError(
                f"Migration failed: {str(e)}",
                source_version=self.source_version,
                target_version=self.target_version
            ) from e

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<{self.__class__.__name__} "
            f"{self.source_version} → {self.target_version}>"
        )


class MigrationChain:
    """Verwaltet eine Kette von Migrations.

    Ermöglicht Migrations über mehrere Versionen hinweg (z.B. v1→v2→v3).
    """

    def __init__(self):
        """Initialize Migration Chain."""
        self.migrations: dict[tuple, BaseMigration] = {}

    def register(self, migration: BaseMigration) -> None:
        """Registriert eine Migration.

        Args:
            migration: Migration Instance
        """
        key = (migration.source_version, migration.target_version)
        self.migrations[key] = migration

    def find_path(
        self,
        source_version: str,
        target_version: str
    ) -> list | None:
        """Findet Migration-Pfad zwischen Versionen.

        Args:
            source_version: Start-Version
            target_version: Ziel-Version

        Returns:
            Liste von Migrations oder None wenn kein Pfad existiert
        """
        # Simple direct path for now
        key = (source_version, target_version)
        if key in self.migrations:
            return [self.migrations[key]]

        # TODO: Implement multi-step path finding (BFS/DFS)
        return None

    def migrate(
        self,
        data: dict[str, Any],
        target_version: str
    ) -> dict[str, Any]:
        """Migrates data to target version.

        Args:
            data: Architecture JSON
            target_version: Ziel-Version

        Returns:
            Migrated data

        Raises:
            MigrationError: Wenn kein Pfad oder Migration fehlschlägt
        """
        current_version = data.get("version", "unknown")

        if current_version == target_version:
            return data

        path = self.find_path(current_version, target_version)

        if not path:
            raise MigrationError(
                f"No migration path found from {current_version} to {target_version}"
            )

        # Apply migrations sequentially
        result = data
        for migration in path:
            result = migration.apply(result, direction="upgrade")

        return result
