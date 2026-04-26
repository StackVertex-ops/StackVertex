"""Repository layer for DynamoDB data access.

Provides clean abstraction over DynamoDB operations with automatic
S3 offload for large items.
"""

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository
from app.repositories.organisation import OrganisationRepository
from app.repositories.architecture import ArchitectureRepository
from app.repositories.deployment import DeploymentRepository
from app.repositories.audit_log import AuditLogRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "OrganisationRepository",
    "ArchitectureRepository",
    "DeploymentRepository",
    "AuditLogRepository",
]
