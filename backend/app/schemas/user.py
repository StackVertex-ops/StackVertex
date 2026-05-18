"""User Pydantic Schemas.

API Request/Response Models für User Management.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import AuthProvider, SystemRole, UserRole, UserStatus

# ============================================================================
# User Base Schemas
# ============================================================================


class UserBase(BaseModel):
    """Base User Schema mit gemeinsamen Feldern."""

    email: EmailStr = Field(..., description="User email (unique)")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")


class UserCreate(BaseModel):
    """Schema für User Registration.

    Nur Email + Name, Password wird via Auth Provider gehandhabt.
    SECURITY: Password Complexity Requirements enforced.
    """

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128, description="Plain password (wird gehasht)")

    # Optional: Auth Provider Info (für OAuth)
    auth_provider: AuthProvider = Field(default=AuthProvider.EMAIL)
    auth_provider_id: str | None = Field(None, description="OAuth Provider User ID")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password complexity.

        SECURITY FIX: Enforce strong passwords.

        Requirements:
        - Min 8 characters (Pydantic Field handles this)
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character (!@#$%^&*(),.?":{}|<>)

        Args:
            v: Password string

        Returns:
            Password if valid

        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')

        return v


class UserUpdate(BaseModel):
    """Schema für User Profile Update.

    Alle Felder optional.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    # Email change requires verification
    # Password change via separate endpoint


class UserPasswordUpdate(BaseModel):
    """Schema für Password Update.

    SECURITY: New password must meet complexity requirements.
    """

    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password complexity (same rules as UserCreate)."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')

        return v


class UserLogin(BaseModel):
    """Schema für User Login."""

    email: EmailStr
    password: str


# ============================================================================
# User Response Schemas
# ============================================================================


class UserResponse(UserBase):
    """User Response (Public Info).

    Wird zurückgegeben bei GET /users/{id}.
    KEIN Password Hash!
    """

    id: UUID
    auth_provider: AuthProvider
    status: UserStatus
    system_role: SystemRole = Field(default=SystemRole.USER, description="System-level role")
    personal_org_id: UUID = Field(..., description="Personal Organisation ID")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserResponse):
    """Extended User Profile (für authenticated User selbst).

    Enthält zusätzliche private Info.
    """

    # Additional private info that only the user themselves should see
    # z.B. email verification status, payment info, etc.
    pass


class UserMembershipResponse(BaseModel):
    """User's Membership in einer Organisation."""

    organisation_id: UUID
    organisation_name: str
    role: UserRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithOrganisationsResponse(UserResponse):
    """User Response mit ihren Organisations."""

    organisations: list[UserMembershipResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Authentication Response Schemas
# ============================================================================


class TokenResponse(BaseModel):
    """JWT Token Response nach Login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT Token Payload (was im Token drin ist)."""

    sub: str = Field(..., description="User ID")
    email: str
    org_id: str | None = Field(None, description="Current active organisation")
    exp: int = Field(..., description="Expiration timestamp")


# ============================================================================
# User List Response
# ============================================================================


class UserListResponse(BaseModel):
    """Paginated User List Response."""

    items: list[UserResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
