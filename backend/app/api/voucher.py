"""Voucher API Endpoints.

Public endpoints für Voucher-Validierung und -Verwendung.
Admin endpoints für Voucher-Management.
"""

import logging
from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from app.api.auth import get_current_user, get_current_superadmin
from app.db.dynamodb import get_dynamodb_table
from app.repositories.voucher import VoucherRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.organisation import OrganisationRepository
from app.services.voucher_service import VoucherService
from app.services.audit_logger import log_audit

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


def get_voucher_repository(table=Depends(get_dynamodb_table)) -> VoucherRepository:
    """Get VoucherRepository instance."""
    return VoucherRepository(table=table)


def get_subscription_repository(table=Depends(get_dynamodb_table)) -> SubscriptionRepository:
    """Get SubscriptionRepository instance."""
    return SubscriptionRepository(table=table)


def get_organisation_repository(table=Depends(get_dynamodb_table)) -> OrganisationRepository:
    """Get OrganisationRepository instance."""
    return OrganisationRepository(table=table, s3_storage=None)


def get_voucher_service(
    voucher_repo: VoucherRepository = Depends(get_voucher_repository),
    subscription_repo: SubscriptionRepository = Depends(get_subscription_repository)
) -> VoucherService:
    """Get VoucherService instance."""
    return VoucherService(voucher_repo=voucher_repo, subscription_repo=subscription_repo)


# ============================================================================
# Request/Response Schemas
# ============================================================================


class VoucherValidateRequest(BaseModel):
    """Request body for voucher validation."""

    code: str = Field(..., min_length=4, max_length=32, description="Voucher code")


class VoucherValidateResponse(BaseModel):
    """Response for voucher validation."""

    valid: bool
    code: str
    discount_type: str
    discount_value: float
    applies_to: str
    remaining_uses: int
    message: Optional[str] = None


class VoucherRedeemRequest(BaseModel):
    """Request body for voucher redemption."""

    code: str = Field(..., min_length=4, max_length=32, description="Voucher code")
    org_id: UUID = Field(..., description="Organisation ID to apply voucher to")


class VoucherRedeemResponse(BaseModel):
    """Response for voucher redemption."""

    success: bool
    message: str
    voucher_code: str
    org_id: str
    subscription: dict


class VoucherCreateRequest(BaseModel):
    """Request body for creating voucher (SuperAdmin only)."""

    code: str = Field(..., min_length=4, max_length=32, description="Unique voucher code")
    discount_type: str = Field(..., pattern="^(percentage|fixed)$", description="Discount type")
    discount_value: float = Field(..., gt=0, description="Discount value (percentage or EUR)")
    applies_to: str = Field(..., pattern="^(base_fee|aws_percentage|both)$", description="What to discount")
    max_uses: int = Field(1, ge=-1, description="Max uses (-1 = unlimited, 0 = disabled)")
    valid_from: Optional[datetime] = Field(None, description="Valid from (optional)")
    valid_until: Optional[datetime] = Field(None, description="Valid until (optional)")


class VoucherResponse(BaseModel):
    """Response for voucher details."""

    code: str
    discount_type: str
    discount_value: float
    applies_to: str
    max_uses: int
    current_uses: int
    is_active: bool
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    created_at: str
    created_by: Optional[str] = None
    last_used_at: Optional[str] = None


class VoucherStatsResponse(BaseModel):
    """Response for voucher usage statistics."""

    code: str
    max_uses: int
    current_uses: int
    remaining_uses: int
    usage_percentage: float
    unique_users: int
    is_active: bool
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    last_used_at: Optional[str] = None


# ============================================================================
# Public Voucher Endpoints (Authenticated Users)
# ============================================================================


@router.post("/api/v1/voucher/validate", response_model=VoucherValidateResponse)
async def validate_voucher(
    request: VoucherValidateRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    voucher_service: VoucherService = Depends(get_voucher_service)
):
    """Validiert Voucher ohne ihn zu verwenden.

    Prüft ob Code gültig, verfügbar und für User verwendbar ist.

    Args:
        request: Validation request mit Code
        current_user: Aktueller User
        voucher_service: Voucher Service

    Returns:
        Validation response mit Discount-Details

    Raises:
        HTTPException: 400 wenn Voucher ungültig
    """
    try:
        result = voucher_service.validate_voucher(
            code=request.code,
            user_id=UUID(current_user["id"])
        )

        return VoucherValidateResponse(
            valid=True,
            code=result["code"],
            discount_type=result["discount_type"],
            discount_value=result["discount_value"],
            applies_to=result["applies_to"],
            remaining_uses=result["remaining_uses"],
            message="Voucher is valid and can be used"
        )

    except ValueError as e:
        logger.warning(f"Voucher validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.post("/api/v1/voucher/redeem", response_model=VoucherRedeemResponse)
async def redeem_voucher(
    request: VoucherRedeemRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    voucher_service: VoucherService = Depends(get_voucher_service),
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Wendet Voucher auf Subscription an.

    Markiert Voucher als verwendet und speichert Rabatt in Subscription.

    Args:
        request: Redeem request mit Code und Org ID
        current_user: Aktueller User
        voucher_service: Voucher Service
        org_repo: Organisation Repository

    Returns:
        Redeem response mit aktualisierter Subscription

    Raises:
        HTTPException: 400/404 bei Fehler
    """
    user_id = UUID(current_user["id"])

    # Prüfe ob User Mitglied der Organisation ist
    is_member = org_repo.is_member(request.org_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organisation"
        )

    try:
        # Redeem voucher
        updated_subscription = voucher_service.redeem_voucher(
            code=request.code,
            user_id=user_id,
            org_id=request.org_id
        )

        # Log audit
        log_audit(
            user=current_user["email"],
            action="voucher.redeem",
            resource_type="voucher",
            resource_id=request.code,
            details={
                "code": request.code,
                "org_id": str(request.org_id)
            },
            success=True
        )

        logger.info(
            f"User {current_user['email']} redeemed voucher {request.code} for org {request.org_id}",
            extra={
                "user_id": str(user_id),
                "code": request.code,
                "org_id": str(request.org_id)
            }
        )

        return VoucherRedeemResponse(
            success=True,
            message=f"Voucher {request.code} successfully applied to subscription",
            voucher_code=request.code.upper(),
            org_id=str(request.org_id),
            subscription=updated_subscription
        )

    except ValueError as e:
        logger.warning(f"Voucher redemption failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.delete("/api/v1/voucher/remove/{org_id}")
async def remove_voucher_from_subscription(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    voucher_service: VoucherService = Depends(get_voucher_service),
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Entfernt Voucher von Subscription.

    Note: Voucher bleibt als "verwendet" markiert.

    Args:
        org_id: Organisation ID
        current_user: Aktueller User
        voucher_service: Voucher Service
        org_repo: Organisation Repository

    Returns:
        Success message

    Raises:
        HTTPException: 403/404 bei Fehler
    """
    user_id = UUID(current_user["id"])

    # Prüfe ob User Mitglied der Organisation ist
    is_member = org_repo.is_member(org_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organisation"
        )

    try:
        updated_subscription = voucher_service.remove_voucher_from_subscription(org_id)

        # Log audit
        log_audit(
            user=current_user["email"],
            action="voucher.remove",
            resource_type="voucher",
            resource_id=org_id,
            details={"org_id": str(org_id)},
            success=True
        )

        return {
            "success": True,
            "message": "Voucher removed from subscription",
            "org_id": str(org_id),
            "subscription": updated_subscription
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e


# ============================================================================
# Admin Voucher Endpoints (SuperAdmin only)
# ============================================================================


@router.get("/api/v1/admin/vouchers", response_model=List[VoucherResponse])
async def list_all_vouchers(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Max items"),
    include_inactive: bool = Query(False, description="Include deactivated vouchers"),
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    voucher_repo: VoucherRepository = Depends(get_voucher_repository)
):
    """Liste alle Vouchers (SuperAdmin only).

    Args:
        skip: Pagination offset
        limit: Max items
        include_inactive: Include deactivated vouchers
        current_admin: Current SuperAdmin user
        voucher_repo: Voucher Repository

    Returns:
        List of vouchers
    """
    # Log admin action
    log_audit(
        user=current_admin["email"],
        action="admin.list_vouchers",
        resource_type="voucher"
    )

    vouchers, total = voucher_repo.list_all(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )

    logger.info(
        f"SuperAdmin {current_admin['email']} listed {len(vouchers)} vouchers",
        extra={"admin_id": current_admin["id"], "total": total}
    )

    return [VoucherResponse(**v) for v in vouchers]


@router.get("/api/v1/admin/vouchers/{code}", response_model=VoucherResponse)
async def get_voucher_details(
    code: str,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    voucher_repo: VoucherRepository = Depends(get_voucher_repository)
):
    """Get Voucher Details (SuperAdmin only).

    Args:
        code: Voucher code
        current_admin: Current SuperAdmin user
        voucher_repo: Voucher Repository

    Returns:
        Voucher details

    Raises:
        HTTPException: 404 wenn Voucher nicht gefunden
    """
    voucher = voucher_repo.get_by_code(code)
    if not voucher:
        raise HTTPException(status_code=404, detail=f"Voucher '{code}' not found")

    return VoucherResponse(**voucher)


@router.get("/api/v1/admin/vouchers/{code}/stats", response_model=VoucherStatsResponse)
async def get_voucher_stats(
    code: str,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    voucher_repo: VoucherRepository = Depends(get_voucher_repository)
):
    """Get Voucher Usage Statistics (SuperAdmin only).

    Args:
        code: Voucher code
        current_admin: Current SuperAdmin user
        voucher_repo: Voucher Repository

    Returns:
        Usage statistics

    Raises:
        HTTPException: 404 wenn Voucher nicht gefunden
    """
    try:
        stats = voucher_repo.get_usage_stats(code)
        return VoucherStatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/api/v1/admin/vouchers", response_model=VoucherResponse, status_code=status.HTTP_201_CREATED)
async def create_voucher(
    request: VoucherCreateRequest,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    voucher_repo: VoucherRepository = Depends(get_voucher_repository)
):
    """Erstellt neuen Voucher (SuperAdmin only).

    Args:
        request: Voucher creation request
        current_admin: Current SuperAdmin user
        voucher_repo: Voucher Repository

    Returns:
        Created voucher

    Raises:
        HTTPException: 400 bei Validierungsfehler oder duplicate code
    """
    try:
        voucher = voucher_repo.create(
            code=request.code,
            discount_type=request.discount_type,
            discount_value=request.discount_value,
            applies_to=request.applies_to,
            max_uses=request.max_uses,
            valid_from=request.valid_from,
            valid_until=request.valid_until,
            created_by=UUID(current_admin["id"])
        )

        # Log admin action
        log_audit(
            user=current_admin["email"],
            action="admin.create_voucher",
            resource_type="voucher",
            resource_id=request.code,
            details={
                "code": request.code,
                "discount_type": request.discount_type,
                "discount_value": request.discount_value,
                "applies_to": request.applies_to
            },
            success=True
        )

        logger.info(
            f"SuperAdmin {current_admin['email']} created voucher {request.code}",
            extra={
                "admin_id": current_admin["id"],
                "code": request.code
            }
        )

        return VoucherResponse(**voucher)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.delete("/api/v1/admin/vouchers/{code}")
async def deactivate_voucher(
    code: str,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    voucher_repo: VoucherRepository = Depends(get_voucher_repository)
):
    """Deaktiviert Voucher (SuperAdmin only).

    Args:
        code: Voucher code
        current_admin: Current SuperAdmin user
        voucher_repo: Voucher Repository

    Returns:
        Success message

    Raises:
        HTTPException: 404 wenn Voucher nicht gefunden
    """
    try:
        updated_voucher = voucher_repo.deactivate(code)

        # Log admin action
        log_audit(
            user=current_admin["email"],
            action="admin.deactivate_voucher",
            resource_type="voucher",
            resource_id=code,
            success=True
        )

        logger.warning(
            f"SuperAdmin {current_admin['email']} deactivated voucher {code}",
            extra={"admin_id": current_admin["id"], "code": code}
        )

        return {
            "success": True,
            "message": f"Voucher {code} deactivated",
            "voucher": updated_voucher
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/api/v1/admin/vouchers/{code}/reactivate")
async def reactivate_voucher(
    code: str,
    current_admin: Annotated[dict, Depends(get_current_superadmin)] = None,
    voucher_repo: VoucherRepository = Depends(get_voucher_repository)
):
    """Reaktiviert deaktivierten Voucher (SuperAdmin only).

    Args:
        code: Voucher code
        current_admin: Current SuperAdmin user
        voucher_repo: Voucher Repository

    Returns:
        Success message

    Raises:
        HTTPException: 404 wenn Voucher nicht gefunden
    """
    try:
        updated_voucher = voucher_repo.reactivate(code)

        # Log admin action
        log_audit(
            user=current_admin["email"],
            action="admin.reactivate_voucher",
            resource_type="voucher",
            resource_id=code,
            success=True
        )

        logger.info(
            f"SuperAdmin {current_admin['email']} reactivated voucher {code}",
            extra={"admin_id": current_admin["id"], "code": code}
        )

        return {
            "success": True,
            "message": f"Voucher {code} reactivated",
            "voucher": updated_voucher
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
