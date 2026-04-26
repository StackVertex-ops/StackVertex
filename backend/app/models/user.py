"""User Models & Enums.

Domain models für User Management.
"""

from enum import Enum
from typing import Optional


class AuthProvider(str, Enum):
    """Authentication Provider."""

    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class UserRole(str, Enum):
    """User Role innerhalb einer Organisation."""

    OWNER = "owner"      # Organisation Owner - Full Access
    ADMIN = "admin"      # Admin - Manage Users, Billing
    MEMBER = "member"    # Member - Deploy, Edit Architectures
    VIEWER = "viewer"    # Viewer - Read-only Access


class UserStatus(str, Enum):
    """User Account Status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_EMAIL_VERIFICATION = "pending_email_verification"
