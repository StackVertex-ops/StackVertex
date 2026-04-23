"""JSON Engine Migrations Package.

Framework für Schema-Migrationen zwischen Versionen.
"""

from app.core.json_engine.migrations.base import BaseMigration, MigrationChain

__all__ = ["BaseMigration", "MigrationChain"]
