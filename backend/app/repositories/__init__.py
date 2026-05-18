"""Repository layer for DynamoDB data access.

Provides clean abstraction over DynamoDB operations with automatic
S3 offload for large items.
"""

from app.repositories.architecture import ArchitectureRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.base import BaseRepository
from app.repositories.deployment import DeploymentRepository
from app.repositories.organisation import OrganisationRepository
from app.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "OrganisationRepository",
    "ArchitectureRepository",
    "DeploymentRepository",
    "AuditLogRepository",
]
