"""Organisation Pydantic Schemas.

API Request/Response Models für Organisation Management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.organisation import (
    OrganisationPlan,
    OrganisationStatus,
    OrganisationType,
    MonitoringLevel,
)
from app.models.user import UserRole


# ============================================================================
# Organisation Base Schemas
# ============================================================================


class OrganisationBase(BaseModel):
    """Base Organisation Schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Organisation name")
    type: OrganisationType = Field(default=OrganisationType.TEAM)


class OrganisationCreate(OrganisationBase):
    """Schema für Organisation Creation.

    User der erstellt wird automatisch Owner.
    """

    # AWS Credentials werden später via separaten Endpoint hinzugefügt
    pass


class OrganisationUpdate(BaseModel):
    """Schema für Organisation Update.

    Alle Felder optional.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    # Plan kann nur via separate upgrade/downgrade Endpoints geändert werden


# ============================================================================
# Organisation Response Schemas
# ============================================================================


class OrganisationQuotaResponse(BaseModel):
    """Current Quota Usage & Limits."""

    # Deployments
    active_deployments: int = Field(..., description="Currently active deployments")
    max_active_deployments: int = Field(..., description="Max allowed (-1 = unlimited)")

    # Members
    members: int = Field(..., description="Current member count")
    max_members: int = Field(..., description="Max allowed (-1 = unlimited)")

    # Architectures
    architectures: int = Field(..., description="Current architecture count")
    max_architectures: int = Field(..., description="Max allowed (-1 = unlimited)")

    # Monitoring
    monitoring_level: MonitoringLevel


class OrganisationResponse(OrganisationBase):
    """Organisation Response."""

    id: UUID
    owner_user_id: UUID = Field(..., description="Organisation owner (creator)")
    plan: OrganisationPlan
    status: OrganisationStatus
    aws_role_arn: Optional[str] = Field(None, description="AWS IAM Role ARN (encrypted in storage)")
    aws_account_id: Optional[str] = Field(None, description="Connected AWS Account ID")
    quota: OrganisationQuotaResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganisationDetailResponse(OrganisationResponse):
    """Extended Organisation Response mit Members."""

    members: List["OrganisationMemberResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Organisation Member Management
# ============================================================================


class OrganisationMemberResponse(BaseModel):
    """Member innerhalb einer Organisation."""

    user_id: UUID
    email: str
    name: str
    role: UserRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganisationInviteCreate(BaseModel):
    """Invite User to Organisation."""

    email: str = Field(..., description="Email of user to invite")
    role: UserRole = Field(default=UserRole.MEMBER)


class OrganisationMemberUpdateRole(BaseModel):
    """Update Member Role."""

    role: UserRole


# ============================================================================
# Organisation AWS Credentials
# ============================================================================


class OrganisationAWSCredentialsCreate(BaseModel):
    """Connect AWS Account via IAM Role."""

    aws_role_arn: str = Field(
        ...,
        description="IAM Role ARN with Trust to OverCloud Platform Account",
        pattern=r"^arn:aws:iam::\d{12}:role/.+$"
    )


class OrganisationAWSCredentialsResponse(BaseModel):
    """AWS Credentials Status (NOT the actual credentials!)."""

    connected: bool
    aws_account_id: Optional[str] = None
    aws_role_arn_partial: Optional[str] = Field(
        None,
        description="Partial ARN for display (e.g., 'arn:aws:iam::123456******:role/Over***')"
    )
    verified_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


# ============================================================================
# Plan Management
# ============================================================================


class OrganisationPlanUpgrade(BaseModel):
    """Upgrade/Downgrade Plan."""

    new_plan: OrganisationPlan


class OrganisationBillingResponse(BaseModel):
    """Billing Information."""

    plan: OrganisationPlan
    monthly_price_eur: float = Field(..., description="Monthly price in EUR")
    current_period_start: datetime
    current_period_end: datetime
    usage_this_month: Dict[str, Any] = Field(
        default_factory=dict,
        description="Usage metrics (deployments, etc.)"
    )


# ============================================================================
# Organisation List Response
# ============================================================================


class OrganisationListResponse(BaseModel):
    """Paginated Organisation List Response."""

    items: List[OrganisationResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
