"""Billing & Subscription API Endpoints.

Hybrid Pricing Model: Base Fee + % AWS Infrastructure Costs.
Stripe Integration for Plan Upgrades, Subscriptions, and Billing Portal.
"""

import logging
from typing import Annotated, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.organisation import OrganisationRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.aws_cost import AWSCostRepository
from app.repositories.invoice import InvoiceRepository
from app.services.stripe_service import StripeService, get_stripe_service
from app.services.invoice_generator import InvoiceGenerator
from app.services.aws_cost_tracker import AWSCostTracker
from app.models.organisation import OrganisationPlan, get_plan_price, calculate_yearly_discount
from app.models.billing import (
    BillingTier,
    BillingPeriod,
    BillingStatus,
    InvoiceStatus,
    get_tier_config,
    get_base_price,
    calculate_monthly_cost_example
)
from app.models.user import UserRole
from app.api.auth import get_current_user
from app.api.organisations import check_org_permission, get_organisation_repository

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Schemas
# ============================================================================


class CheckoutRequest(BaseModel):
    """Checkout Session Request."""

    plan: OrganisationPlan = Field(..., description="Target plan")
    interval: str = Field(..., description="Billing interval: monthly or yearly")
    auto_renewal: bool = Field(False, description="Enable automatic renewal")
    success_url: str = Field(..., description="Redirect URL after successful payment")
    cancel_url: str = Field(..., description="Redirect URL if user cancels")


class CheckoutResponse(BaseModel):
    """Checkout Session Response."""

    checkout_url: str = Field(..., description="Stripe Checkout URL")
    session_id: str = Field(..., description="Checkout Session ID")
    expires_at: int = Field(..., description="Session expiration timestamp")


class BillingPortalResponse(BaseModel):
    """Billing Portal Response."""

    portal_url: str = Field(..., description="Stripe Billing Portal URL")


class PricingResponse(BaseModel):
    """Plan Pricing Information."""

    plan: OrganisationPlan
    monthly_price_eur: float
    yearly_price_eur: float
    yearly_discount_percent: float
    currency: str = "EUR"


class SubscriptionStatusResponse(BaseModel):
    """Subscription Status."""

    has_subscription: bool
    plan: OrganisationPlan | None = None
    interval: str | None = None
    status: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool = False
    auto_renewal_enabled: bool = False


class HybridPricingTier(BaseModel):
    """Hybrid Pricing Tier Information."""

    tier: str
    base_price_monthly: float
    base_price_annual: float
    aws_cost_percentage: int
    limits: dict
    features: List[str]


class CostEstimateRequest(BaseModel):
    """Cost Estimate Request."""

    tier: str = Field(..., description="Billing tier")
    estimated_aws_costs: float = Field(..., description="Estimated monthly AWS costs")
    num_deployments: int = Field(0, description="Number of deployments (for PAYG)")


class CostEstimateResponse(BaseModel):
    """Cost Estimate Response."""

    tier: str
    base_price: float
    aws_costs: float
    markup_percentage: int
    markup_fee: float
    deployment_fees: float
    subtotal: float
    tax: float
    total: float
    currency: str = "EUR"


class InvoiceLineItem(BaseModel):
    """Invoice Line Item."""

    description: str
    amount: float
    currency: str
    breakdown: Optional[dict] = None


class InvoiceResponse(BaseModel):
    """Invoice Response."""

    id: str
    invoice_number: str
    org_id: str
    period_start: str
    period_end: str
    line_items: List[InvoiceLineItem]
    subtotal: float
    tax: float
    total: float
    status: str
    created_at: str
    paid_at: Optional[str] = None


class CostTrendItem(BaseModel):
    """Cost Trend Item."""

    month: str
    aws_costs: float
    overcloud_fee: float
    total: float


class CostProjectionResponse(BaseModel):
    """Cost Projection Response."""

    current_aws_costs: float
    projected_aws_costs: float
    projected_overcloud_fee: float
    projected_total: float
    days_elapsed: int
    days_in_month: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/pricing", response_model=list[PricingResponse])
async def get_pricing():
    """Get pricing for all plans.

    Public endpoint - no authentication required.
    """
    pricing = []

    for plan in [OrganisationPlan.FREE, OrganisationPlan.PRO, OrganisationPlan.ENTERPRISE]:
        pricing.append(PricingResponse(
            plan=plan,
            monthly_price_eur=get_plan_price(plan, "monthly"),
            yearly_price_eur=get_plan_price(plan, "yearly"),
            yearly_discount_percent=calculate_yearly_discount(plan),
        ))

    return pricing


@router.post("/{org_id}/checkout", response_model=CheckoutResponse)
@limiter.limit("1000/minute" if settings.TESTING else "20/minute")
async def create_checkout_session(
    request: Request,
    org_id: UUID,
    checkout_request: CheckoutRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Create Stripe Checkout Session for plan upgrade.

    Requires: OWNER role
    """
    # Check permission
    org = await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    # Validate Stripe is enabled
    if not settings.STRIPE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment integration is currently disabled"
        )

    # Validate plan upgrade (can't downgrade to FREE)
    if checkout_request.plan == OrganisationPlan.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot purchase FREE plan. Use cancel subscription instead."
        )

    # Validate interval
    if checkout_request.interval not in ["monthly", "yearly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interval. Must be 'monthly' or 'yearly'."
        )

    # Create or retrieve Stripe customer
    customer_id = org.get("stripe_customer_id")

    if not customer_id:
        customer_id = stripe_service.create_customer(
            org_id=str(org_id),
            org_name=org["name"],
            user_email=current_user["email"],
            user_name=current_user["name"]
        )

        # Save customer ID
        org_repo.update(org_id, {"stripe_customer_id": customer_id})

    # Create Checkout Session
    session = stripe_service.create_checkout_session(
        org_id=str(org_id),
        customer_id=customer_id,
        plan=checkout_request.plan,
        interval=checkout_request.interval,
        success_url=checkout_request.success_url,
        cancel_url=checkout_request.cancel_url,
        auto_renewal=checkout_request.auto_renewal
    )

    logger.info(
        f"Checkout session created for org {org_id}: {session['id']}",
        extra={"org_id": str(org_id), "plan": checkout_request.plan.value}
    )

    return CheckoutResponse(
        checkout_url=session["url"],
        session_id=session["id"],
        expires_at=session["expires_at"]
    )


@router.post("/{org_id}/billing-portal", response_model=BillingPortalResponse)
@limiter.limit("1000/minute" if settings.TESTING else "20/minute")
async def create_billing_portal_session(
    request: Request,
    org_id: UUID,
    return_url: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Create Billing Portal Session.

    Allows user to manage subscription, payment methods, invoices.
    Requires: OWNER role
    """
    # Check permission
    org = await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    # Validate Stripe customer exists
    customer_id = org.get("stripe_customer_id")

    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No billing account found. Please subscribe to a plan first."
        )

    # Create Billing Portal Session
    portal_url = stripe_service.create_billing_portal_session(
        customer_id=customer_id,
        return_url=return_url
    )

    logger.info(
        f"Billing portal session created for org {org_id}",
        extra={"org_id": str(org_id)}
    )

    return BillingPortalResponse(portal_url=portal_url)


@router.get("/{org_id}/subscription", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get subscription status.

    Requires: MEMBER role
    """
    # Check permission
    org = await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    subscription_id = org.get("stripe_subscription_id")

    if not subscription_id:
        # No active subscription
        return SubscriptionStatusResponse(
            has_subscription=False,
            plan=OrganisationPlan(org["plan"]),
        )

    # Retrieve subscription from Stripe
    subscription = stripe_service.get_subscription(subscription_id)

    if not subscription:
        return SubscriptionStatusResponse(
            has_subscription=False,
            plan=OrganisationPlan(org["plan"]),
        )

    return SubscriptionStatusResponse(
        has_subscription=True,
        plan=OrganisationPlan(subscription["plan"]),
        interval=subscription["interval"],
        status=subscription["status"],
        current_period_end=subscription["current_period_end"].isoformat(),
        cancel_at_period_end=subscription["cancel_at_period_end"],
        auto_renewal_enabled=subscription["auto_renewal"]
    )


@router.post("/{org_id}/subscription/enable-auto-renewal")
async def enable_auto_renewal(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Enable automatic renewal for subscription.

    Requires: OWNER role
    """
    # Check permission
    org = await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    subscription_id = org.get("stripe_subscription_id")

    if not subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    success = stripe_service.enable_auto_renewal(subscription_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable auto-renewal"
        )

    logger.info(
        f"Auto-renewal enabled for org {org_id}",
        extra={"org_id": str(org_id)}
    )

    return {"message": "Auto-renewal enabled successfully"}


@router.post("/{org_id}/subscription/cancel")
async def cancel_subscription(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    stripe_service: StripeService = Depends(get_stripe_service),
    immediately: bool = False
):
    """Cancel subscription.

    Requires: OWNER role

    Args:
        immediately: Cancel immediately (True) or at period end (False)
    """
    # Check permission
    org = await check_org_permission(org_id, current_user, UserRole.OWNER, org_repo)

    subscription_id = org.get("stripe_subscription_id")

    if not subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    success = stripe_service.cancel_subscription(subscription_id, immediately=immediately)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

    logger.info(
        f"Subscription canceled for org {org_id} (immediate={immediately})",
        extra={"org_id": str(org_id), "immediately": immediately}
    )

    if immediately:
        # Downgrade to FREE immediately
        org_repo.upgrade_plan(org_id, OrganisationPlan.FREE)

    return {
        "message": "Subscription canceled at period end" if not immediately else "Subscription canceled immediately"
    }


# ============================================================================
# New Hybrid Pricing Endpoints
# ============================================================================


@router.get("/pricing/hybrid", response_model=List[HybridPricingTier])
async def get_hybrid_pricing():
    """Get hybrid pricing information for all tiers.

    Public endpoint - no authentication required.
    Returns: Base price + AWS cost percentage for each tier.
    """
    tiers = []

    for tier in [BillingTier.STARTER, BillingTier.PRO, BillingTier.ENTERPRISE, BillingTier.PAY_AS_YOU_GO]:
        config = get_tier_config(tier)

        tiers.append(HybridPricingTier(
            tier=tier.value,
            base_price_monthly=config["base_price_monthly"],
            base_price_annual=config["base_price_annual"],
            aws_cost_percentage=config["aws_cost_percentage"],
            limits=config["limits"],
            features=config["features"]
        ))

    return tiers


@router.post("/pricing/estimate", response_model=CostEstimateResponse)
async def estimate_monthly_cost(estimate_request: CostEstimateRequest):
    """Estimate monthly costs for a tier.

    Public endpoint - helps users calculate their expected costs.
    """
    try:
        tier = BillingTier(estimate_request.tier)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {estimate_request.tier}"
        )

    cost_breakdown = calculate_monthly_cost_example(
        tier=tier,
        aws_costs=estimate_request.estimated_aws_costs,
        num_deployments=estimate_request.num_deployments
    )

    return CostEstimateResponse(
        tier=tier.value,
        **cost_breakdown
    )


@router.get("/{org_id}/costs/current", response_model=dict)
async def get_current_month_costs(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Get AWS costs for current month.

    Requires: MEMBER role
    """
    # Check permission
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    cost_repo = AWSCostRepository()
    current_month = datetime.utcnow().strftime("%Y-%m")
    cost_record = cost_repo.get_monthly_costs(org_id, current_month)

    if not cost_record:
        return {
            "month": current_month,
            "total_aws_costs": 0.0,
            "overcloud_percentage_fee": 0.0,
            "deployment_costs": {}
        }

    return cost_record


@router.get("/{org_id}/costs/trend", response_model=List[CostTrendItem])
async def get_cost_trend(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    months: int = 6
):
    """Get cost trend over time.

    Requires: MEMBER role
    """
    # Check permission
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    cost_repo = AWSCostRepository()
    trend = cost_repo.get_cost_trend(org_id, months=months)

    return [CostTrendItem(**item) for item in trend]


@router.get("/{org_id}/costs/projection", response_model=CostProjectionResponse)
async def get_cost_projection(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Project end-of-month costs based on current usage.

    Requires: MEMBER role
    """
    # Check permission
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    cost_repo = AWSCostRepository()
    subscription_repo = SubscriptionRepository()

    tracker = AWSCostTracker(cost_repo, subscription_repo)
    projection = tracker.get_cost_projection(org_id)

    return CostProjectionResponse(**projection)


@router.get("/{org_id}/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
    limit: int = 50,
    status_filter: Optional[str] = None
):
    """List invoices for organisation.

    Requires: MEMBER role
    """
    # Check permission
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    invoice_repo = InvoiceRepository()

    # Parse status filter
    status = None
    if status_filter:
        try:
            status = InvoiceStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )

    invoices = invoice_repo.list_by_org(org_id, limit=limit, status_filter=status)

    return [
        InvoiceResponse(
            id=inv["id"],
            invoice_number=inv["invoice_number"],
            org_id=inv["org_id"],
            period_start=inv["period_start"],
            period_end=inv["period_end"],
            line_items=[InvoiceLineItem(**item) for item in inv["line_items"]],
            subtotal=inv["subtotal"],
            tax=inv["tax"],
            total=inv["total"],
            status=inv["status"],
            created_at=inv["created_at"],
            paid_at=inv.get("paid_at")
        )
        for inv in invoices
    ]


@router.get("/{org_id}/invoices/{invoice_number}", response_model=InvoiceResponse)
async def get_invoice(
    org_id: UUID,
    invoice_number: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Get invoice details.

    Requires: MEMBER role
    """
    # Check permission
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    invoice_repo = InvoiceRepository()
    invoice = invoice_repo.get_by_number(org_id, invoice_number)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_number} not found"
        )

    return InvoiceResponse(
        id=invoice["id"],
        invoice_number=invoice["invoice_number"],
        org_id=invoice["org_id"],
        period_start=invoice["period_start"],
        period_end=invoice["period_end"],
        line_items=[InvoiceLineItem(**item) for item in invoice["line_items"]],
        subtotal=invoice["subtotal"],
        tax=invoice["tax"],
        total=invoice["total"],
        status=invoice["status"],
        created_at=invoice["created_at"],
        paid_at=invoice.get("paid_at")
    )


@router.get("/{org_id}/invoices/preview/next", response_model=dict)
async def preview_next_invoice(
    org_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    org_repo: OrganisationRepository = Depends(get_organisation_repository)
):
    """Preview next invoice without creating it.

    Requires: MEMBER role
    """
    # Check permission
    await check_org_permission(org_id, current_user, UserRole.MEMBER, org_repo)

    subscription_repo = SubscriptionRepository()
    cost_repo = AWSCostRepository()
    invoice_repo = InvoiceRepository()

    generator = InvoiceGenerator(invoice_repo, subscription_repo, cost_repo)

    try:
        preview = generator.preview_next_invoice(org_id)
        return preview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
