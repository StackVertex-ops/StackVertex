"""Deployment Enums.

Status definitions für Deployments.
"""

import enum


class DeploymentStatus(str, enum.Enum):
    """Deployment Status Enum."""

    PENDING = "pending"
    GENERATING = "generating"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    APPLYING = "applying"
    SUCCESS = "success"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    CANCELLED = "cancelled"
