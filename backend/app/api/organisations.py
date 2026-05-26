"""Organisation Management API Endpoints.

Organisation CRUD, Member Management, AWS Credentials, Plan Upgrades.
"""

import logging
import re
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.db.dynamodb import get_dynamodb_table
from app.db.s3_storage import get_s3_storage
from app.repositories.organisation import OrganisationRepository
from app.repositories.user import UserRepository
from app.services.secrets_manager import SecretsManager, get_secrets_manager
from app.schemas.organisation import (
    OrganisationCreate,
    OrganisationUpdate,
    OrganisationResponse,
    OrganisationDetailResponse,
    OrganisationListResponse,
    OrganisationMemberResponse,
    OrganisationInviteCreate,
    OrganisationMemberUpdateRole,
    OrganisationAWSCredentialsCreate,
    OrganisationAWSCredentialsResponse,
    OrganisationPlanUpgrade,
    OrganisationQuotaResponse,
)
from app.models.organisation import (
    OrganisationPlan,
    OrganisationType,
    get_quota as get_plan_quota,
)
from app.models.user import UserRole
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


def get_organisation_repository(
    table=Depends(get_dynamodb_table),
    s3=Depends(get_s3_storage),
    secrets_manager: SecretsManager = Depends(get_secrets_manager)
) -> OrganisationRepository:
    """Get OrganisationRepository instance with AWS Secrets Manager."""
    return OrganisationRepository(table=table, s3_storage=s3, secrets_manager=secrets_manager)


def get_user_repository(table=Depends(get_dynamodb_table)) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(table=table)


async def check_org_permission(
    org_id: UUID,
    current_user: dict,
    required_role: UserRole,
    org_repo: OrganisationRepository
) -> dict:
    """Check if user has required role in organisation.

    Args:
        org_id: Organisation ID
        current_user: Current authenticated user
        required_role: Minimum required role
        org_repo: OrganisationRepository

    Returns:
        Organisation dict

    Raises:
        HTTPException: If user doesn't have permission
    """
    org = org_repo.get(org_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    # Check if user is member
    member = org_repo.get_member(org_id, UUID(current_user["id"]))

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organisation"
        )

    # Check role hierarchy: OWNER > ADMIN > MEMBER > VIEWER
    role_hierarchy = {
        UserRole.OWNER: 4,
        UserRole.ADMIN: 3,
        UserRole.MEMBER: 2,
        UserRole.VIEWER: 1,
    }

    user_role = UserRole(member["role"])
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 999)

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_role.value}"
        )

    return org


def map_org_type_field(org_dict: dict) -> dict:
    """Map organisation_type field from DB to type field for API response.

    Args:
        org_dict: Organisation dict from repository

    Returns:
        Dict with organisation_type mapped to type
    """
    if "organisation_type" in org_dict:
        org_dict["type"] = org_dict.pop("organisation_type")
    return org_dict


# ============================================================================
# Organisation CRUD
# ============================================================================


@router.post("", response_model=OrganisationResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation(
    org_create: OrganisationCreate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Create new organisation.

    User becomes owner automatically.
    """
    # Create organisation
    org = org_repo.create(
        name=org_create.name,
        owner_user_id=UUID(current_user["id"]),
        organisation_type=org_create.type,
        plan=OrganisationPlan.FREE,  # Always start with free
    )

    # Add current user info to membership
    org_repo.add_member(
        org_id=UUID(org["id"]),
        user_id=UUID(current_user["id"]),
        user_email=current_user["email"],
        user_name=current_user["name"],
        role=UserRole.OWNER
    )

    logger.info(
        f"Organisation created: {org['id']}",
        extra={"org_id": org["id"], "owner": current_user["id"]}
    )

    # Build response with quota
    from app.models.organisation import get_quota
    plan = OrganisationPlan(org["plan"])

    quota_response = OrganisationQuotaResponse(
        active_deployments=org["quota"]["active_deployments"],
        max_active_deployments=get_quota(plan, "max_active_deployments"),
        members=org["quota"]["members"],
        max_members=get_quota(plan, "max_members"),
        architectures=org["quota"]["architectures"],
        max_architectures=get_quota(plan, "max_architectures"),
        monitoring_level=get_quota(plan, "monitoring_level"),
    )

    # Remove quota dict and map organisation_type to type
    org_without_quota = {k: v for k, v in org.items() if k != "quota"}
    # Map organisation_type -> type for response schema
    if "organisation_type" in org_without_quota:
        org_without_quota["type"] = org_without_quota.pop("organisation_type")

    return OrganisationResponse(**org_without_quota, quota=quota_response)


@router.get("", response_model=OrganisationListResponse)
async def list_organisations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    owner_only: bool = Query(False, description="Filter to only owned organisations"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """List organisations.

    By default: All organisations user is member of.
    With owner_only=true: Only organisations user owns.
    """
    owner_id = UUID(current_user["id"]) if owner_only else None

    items, total = org_repo.list(
        skip=skip,
        limit=limit,
        owner_user_id=owner_id
    )

    # Build quota responses
    org_responses = []
    for org in items:
        from app.models.organisation import get_quota
        plan = OrganisationPlan(org["plan"])

        quota_response = OrganisationQuotaResponse(
            active_deployments=org["quota"]["active_deployments"],
            max_active_deployments=get_quota(plan, "max_active_deployments"),
            members=org["quota"]["members"],
            max_members=get_quota(plan, "max_members"),
            architectures=org["quota"]["architectures"],
            max_architectures=get_quota(plan, "max_architectures"),
            monitoring_level=get_quota(plan, "monitoring_level"),
        )

        org_without_quota = {k: v for k, v in org.items() if k != "quota"}
        org_without_quota = map_org_type_field(org_without_quota)
        org_responses.append(OrganisationResponse(**org_without_quota, quota=quota_response))

    return OrganisationListResponse(
        items=org_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{org_id}", response_model=OrganisationDetailResponse)
async def get_organisation(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Get organisation details with members.

    Requires: VIEWER role
    """
    org = await check_org_permission(org_id, current_user, UserRole.VIEWER, org_repo)

    # Get members
    members = org_repo.get_members(org_id)

    member_responses = [
        OrganisationMemberResponse(
            user_id=UUID(m["user_id"]),
            email=m["email"],
            name=m["name"],
            role=UserRole(m["role"]),
            joined_at=datetime.fromisoformat(m["created_at"]) if "created_at" in m else datetime.utcnow()
        )
        for m in members
    ]

    # Build quota response
    from app.models.organisation import get_quota
    plan = OrganisationPlan(org["plan"])

    quota_response = OrganisationQuotaResponse(
        active_deployments=org["quota"]["active_deployments"],
        max_active_deployments=get_quota(plan, "max_active_deployments"),
        members=org["quota"]["members"],
        max_members=get_quota(plan, "max_members"),
        architectures=org["quota"]["architectures"],
        max_architectures=get_quota(plan, "max_architectures"),
        monitoring_level=get_quota(plan, "monitoring_level"),
    )

    org_without_quota = {k: v for k, v in org.items() if k != "quota"}
    org_without_quota = map_org_type_field(org_without_quota)
    return OrganisationDetailResponse(
        **org_without_quota,
        quota=quota_response,
        members=member_responses
    )


@router.patch("/{org_id}", response_model=OrganisationResponse)
async def update_organisation(
    org_id: UUID,
    org_update: OrganisationUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Update organisation.

    Requires: ADMIN role
    """
    await check_org_permission(org_id, current_user, UserRole.ADMIN, org_repo)

    updated_org = org_repo.update(
        org_id,
        org_update.model_dump(exclude_unset=True)
    )

    if not updated_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    logger.info(f"Organisation updated: {org_id}", extra={"org_id": str(org_id)})

    # Build quota response
    from app.models.organisation import get_quota
    plan = OrganisationPlan(updated_org["plan"])

    quota_response = OrganisationQuotaResponse(
        active_deployments=updated_org["quota"]["active_deployments"],
        max_active_deployments=get_quota(plan, "max_active_deployments"),
        members=updated_org["quota"]["members"],
        max_members=get_quota(plan, "max_members"),
        architectures=updated_org["quota"]["architectures"],
        max_architectures=get_quota(plan, "max_architectures"),
        monitoring_level=get_quota(plan, "monitoring_level"),
    )

    org_without_quota = {k: v for k, v in updated_org.items() if k != "quota"}
    org_without_quota = map_org_type_field(org_without_quota)
    return OrganisationResponse(**org_without_quota, quota=quota_response)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organisation(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Delete organisation.

    Requires: OWNER role
    Only owner can delete organisation.
    """
    org = await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    # Don't allow deleting personal organisation
    if org.get("type") == OrganisationType.PERSONAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete personal organisation"
        )

    deleted = org_repo.delete(org_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    logger.info(f"Organisation deleted: {org_id}", extra={"org_id": str(org_id)})

    return None


# ============================================================================
# Member Management
# ============================================================================


@router.post("/{org_id}/members", response_model=OrganisationMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: UUID,
    invite: OrganisationInviteCreate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Invite user to organisation.

    Requires: ADMIN role
    """
    await check_org_permission(org_id, current_user, UserRole.ADMIN, org_repo)

    # Check quota
    can_proceed, current, max_allowed = org_repo.check_quota(org_id, "max_members")
    if not can_proceed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Member limit reached ({current}/{max_allowed}). Upgrade plan."
        )

    # Find user by email
    user_to_invite = user_repo.get_by_email(invite.email)

    if not user_to_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. They must register first."
        )

    # Check if already member
    existing_member = org_repo.get_member(org_id, UUID(user_to_invite["id"]))
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )

    # Add member
    membership = org_repo.add_member(
        org_id=org_id,
        user_id=UUID(user_to_invite["id"]),
        user_email=user_to_invite["email"],
        user_name=user_to_invite["name"],
        role=invite.role
    )

    logger.info(
        f"Member added to org {org_id}: {user_to_invite['id']}",
        extra={"org_id": str(org_id), "user_id": user_to_invite["id"]}
    )

    return OrganisationMemberResponse(
        user_id=UUID(membership["user_id"]),
        email=membership["email"],
        name=membership["name"],
        role=UserRole(membership["role"]),
        joined_at=membership.get("created_at")
    )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Remove member from organisation.

    Requires: ADMIN role
    Cannot remove owner.
    """
    org = await check_org_permission(org_id, current_user, UserRole.ADMIN, org_repo)

    # Cannot remove owner
    if str(user_id) == org["owner_user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organisation owner"
        )

    removed = org_repo.remove_member(org_id, user_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    logger.info(
        f"Member removed from org {org_id}: {user_id}",
        extra={"org_id": str(org_id), "user_id": str(user_id)}
    )

    return None


@router.patch("/{org_id}/members/{user_id}", response_model=OrganisationMemberResponse)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    role_update: OrganisationMemberUpdateRole,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Update member role.

    Requires: OWNER role
    """
    org = await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    # Cannot change owner's role
    if str(user_id) == org["owner_user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner's role"
        )

    updated_member = org_repo.update_member_role(org_id, user_id, role_update.role)

    if not updated_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Fetch full member object (update_member_role only returns updated fields)
    member = org_repo.get_member(org_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    logger.info(
        f"Member role updated in org {org_id}: {user_id} → {role_update.role.value}",
        extra={"org_id": str(org_id), "user_id": str(user_id)}
    )

    return OrganisationMemberResponse(
        user_id=user_id,
        email=member["email"],
        name=member["name"],
        role=role_update.role,
        joined_at=member.get("created_at")
    )


@router.get("/{org_id}/members", response_model=list[OrganisationMemberResponse])
async def list_members(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """List all members of an organisation.

    Requires: MEMBER role
    """
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    members = org_repo.get_members(org_id)

    return [
        OrganisationMemberResponse(
            user_id=UUID(m["user_id"]),
            email=m["email"],
            name=m["name"],
            role=UserRole(m["role"]),
            joined_at=m.get("created_at")
        )
        for m in members
    ]


# ============================================================================
# AWS Credentials
# ============================================================================


@router.post("/{org_id}/aws-credentials", response_model=OrganisationAWSCredentialsResponse)
async def connect_aws_account(
    org_id: UUID,
    credentials: OrganisationAWSCredentialsCreate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Connect AWS account via IAM Role.

    Requires: OWNER role (security-critical operation)

    User provides IAM Role ARN with Trust Policy to StackVertex Platform.
    """
    await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    # Extract AWS Account ID from ARN
    # Format: arn:aws:iam::123456789012:role/RoleName
    match = re.match(r"arn:aws:iam::(\d{12}):role/.+", credentials.aws_role_arn)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid AWS IAM Role ARN format"
        )

    aws_account_id = match.group(1)

    # TODO: Verify AssumeRole actually works by attempting to assume role
    # boto3.client('sts').assume_role(...)

    # Store credentials (encrypted in production via AWS Secrets Manager)
    updated_org = org_repo.update_aws_credentials(
        org_id=org_id,
        aws_role_arn=credentials.aws_role_arn,
        aws_account_id=aws_account_id
    )

    if not updated_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    logger.info(
        f"AWS credentials connected for org {org_id}: Account {aws_account_id}",
        extra={"org_id": str(org_id), "aws_account_id": aws_account_id}
    )

    # Partial ARN for display (mask sensitive parts)
    partial_arn = f"arn:aws:iam::{aws_account_id[:6]}******:role/Over***"

    return OrganisationAWSCredentialsResponse(
        connected=True,
        aws_account_id=aws_account_id,
        aws_role_arn_partial=partial_arn,
        verified_at=updated_org.get("aws_verified_at"),
        last_used_at=updated_org.get("aws_last_used_at")
    )


@router.get("/{org_id}/aws-credentials", response_model=OrganisationAWSCredentialsResponse)
async def get_aws_credentials_status(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Get AWS credentials connection status.

    Requires: MEMBER role
    """
    org = await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    # Check both encrypted (aws_role_arn_secret) and plaintext (aws_role_arn) storage
    connected = org.get("aws_role_arn_secret") is not None or org.get("aws_role_arn") is not None
    aws_account_id = org.get("aws_account_id")

    partial_arn = None
    if connected and aws_account_id:
        partial_arn = f"arn:aws:iam::{aws_account_id[:6]}******:role/Over***"

    return OrganisationAWSCredentialsResponse(
        connected=connected,
        aws_account_id=aws_account_id,
        aws_role_arn_partial=partial_arn,
        verified_at=org.get("aws_verified_at"),
        last_used_at=org.get("aws_last_used_at")
    )


# ============================================================================
# Quota Management
# ============================================================================


@router.get("/{org_id}/quota", response_model=OrganisationQuotaResponse)
async def get_quota(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Get organisation quota usage and limits.

    Requires: MEMBER role
    """
    org = await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    # Get current usage
    quota_usage = org_repo.get_quota(org_id)

    # Get plan limits
    plan = OrganisationPlan(org["plan"])
    max_active_deployments = get_plan_quota(plan, "max_active_deployments")
    max_members = get_plan_quota(plan, "max_members")
    max_architectures = get_plan_quota(plan, "max_architectures")

    return OrganisationQuotaResponse(
        active_deployments=quota_usage.get("active_deployments", 0),
        max_active_deployments=max_active_deployments,
        members=quota_usage.get("members", 1),
        max_members=max_members,
        architectures=quota_usage.get("architectures", 0),
        max_architectures=max_architectures,
        monitoring_level=org.get("monitoring_level", "basic")
    )


# ============================================================================
# Plan Management
# ============================================================================


@router.post("/{org_id}/upgrade-plan", response_model=OrganisationResponse)
async def upgrade_plan(
    org_id: UUID,
    plan_upgrade: OrganisationPlanUpgrade,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Upgrade/downgrade organisation plan.

    Requires: OWNER role
    """
    await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    # TODO: Add payment processing here (Stripe, etc.)
    # For now: Just update plan

    updated_org = org_repo.upgrade_plan(org_id, plan_upgrade.new_plan)

    if not updated_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    logger.info(
        f"Plan upgraded for org {org_id}: {plan_upgrade.new_plan.value}",
        extra={"org_id": str(org_id), "new_plan": plan_upgrade.new_plan.value}
    )

    # Build quota response
    from app.models.organisation import get_quota

    quota_response = OrganisationQuotaResponse(
        active_deployments=updated_org["quota"]["active_deployments"],
        max_active_deployments=get_quota(plan_upgrade.new_plan, "max_active_deployments"),
        members=updated_org["quota"]["members"],
        max_members=get_quota(plan_upgrade.new_plan, "max_members"),
        architectures=updated_org["quota"]["architectures"],
        max_architectures=get_quota(plan_upgrade.new_plan, "max_architectures"),
        monitoring_level=get_quota(plan_upgrade.new_plan, "monitoring_level"),
    )

    org_without_quota = {k: v for k, v in updated_org.items() if k != "quota"}
    org_without_quota = map_org_type_field(org_without_quota)
    return OrganisationResponse(**org_without_quota, quota=quota_response)
