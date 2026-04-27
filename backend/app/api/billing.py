"""Billing & Subscription API Endpoints.

Stripe Integration for Plan Upgrades, Subscriptions, and Billing Portal.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, Field

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.organisation import OrganisationRepository
from app.services.stripe_service import StripeService, get_stripe_service
from app.models.organisation import OrganisationPlan, get_plan_price, calculate_yearly_discount
from app.models.user import UserRole
from app.api.auth import get_current_user
from app.api.organisations import check_org_permission, get_organisation_repository

logger = logging.getLogger(__name__)

router = APIRouter()


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
async def create_checkout_session(
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
async def create_billing_portal_session(
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
