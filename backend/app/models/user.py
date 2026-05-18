"""User Models & Enums.

Domain models für User Management.
"""

from enum import Enum


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


class SystemRole(str, Enum):
    """System-level Roles (nicht Organisation-gebunden).

    Diese Rollen sind global und unabhängig von Organisation-Memberships.
    """

    USER = "user"              # Regular User (default)
    SUPERADMIN = "superadmin"  # System Administrator - Zugriff auf ALLE Daten
    SUPPORT = "support"        # Support Staff - Read-only Zugriff für Support
    AUDITOR = "auditor"        # Audit/Compliance - Read-only Zugriff auf Logs
