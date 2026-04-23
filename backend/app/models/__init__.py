"""OverCloud Backend - Data Models.

DynamoDB-basierte Repositories verwenden. SQLAlchemy wurde entfernt.
"""

from app.models.deployment import DeploymentStatus

__all__ = ["DeploymentStatus"]
