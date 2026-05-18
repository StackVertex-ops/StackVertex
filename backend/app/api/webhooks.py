"""Webhook Endpoints.

Handles webhooks from external services (Stripe, etc.).
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Request, HTTPException, status, Header, Depends
from uuid import UUID

from app.config import settings
from app.db.dynamodb import get_dynamodb_table
from app.repositories.organisation import OrganisationRepository
from app.repositories.audit_log import AuditLogRepository
from app.services.stripe_service import StripeService, get_stripe_service
from app.models.organisation import OrganisationPlan, OrganisationStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Stripe Webhooks
# ============================================================================


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Annotated[str, Header(alias="stripe-signature")],
    stripe_service: StripeService = Depends(get_stripe_service),
    table=Depends(get_dynamodb_table)
):
    """Handle Stripe webhook events.

    Events:
    - checkout.session.completed: Subscription created
    - customer.subscription.updated: Subscription changed
    - customer.subscription.deleted: Subscription canceled
    - invoice.payment_succeeded: Payment successful
    - invoice.payment_failed: Payment failed
    """
    # Validate webhook secret is configured
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook handler not configured"
        )

    # Read raw body
    payload = await request.body()

    # Verify webhook signature
    event = stripe_service.verify_webhook_signature(
        payload=payload,
        signature=stripe_signature,
        webhook_secret=settings.STRIPE_WEBHOOK_SECRET
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    # Initialize repositories
    org_repo = OrganisationRepository(table=table)
    audit_repo = AuditLogRepository(table=table)

    # Handle event
    event_type = event["type"]
    event_data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}", extra={"event_id": event["id"]})

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(event_data, org_repo, audit_repo)

        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(event_data, org_repo, audit_repo)

        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(event_data, org_repo, audit_repo)

        elif event_type == "invoice.payment_succeeded":
            await _handle_payment_succeeded(event_data, org_repo, audit_repo)

        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(event_data, org_repo, audit_repo)

        else:
            logger.info(f"Unhandled webhook event: {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        ) from e

    return {"received": True}


# ============================================================================
# Webhook Event Handlers
# ============================================================================


async def _handle_checkout_completed(
    session: dict,
    org_repo: OrganisationRepository,
    audit_repo: AuditLogRepository
):
    """Handle checkout.session.completed event.

    Creates subscription and upgrades organisation plan.
    """
    org_id = UUID(session["metadata"]["org_id"])
    subscription_id = session["subscription"]

    # Get subscription details
    import stripe
    subscription = stripe.Subscription.retrieve(subscription_id)

    plan = OrganisationPlan(subscription.metadata["plan"])
    interval = subscription.metadata["interval"]

    # Update organisation
    org_repo.update(org_id, {
        "stripe_subscription_id": subscription_id,
        "subscription_interval": interval,
        "subscription_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
        "subscription_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
    })

    # Upgrade plan
    org_repo.upgrade_plan(org_id, plan)

    # Audit log
    audit_repo.create(
        resource_type="organisation",
        resource_id=str(org_id),
        action="subscription.created",
        user_id=None,  # System action
        metadata={
            "plan": plan.value,
            "interval": interval,
            "subscription_id": subscription_id,
        }
    )

    logger.info(
        f"Subscription created for org {org_id}: {plan.value} ({interval})",
        extra={"org_id": str(org_id), "subscription_id": subscription_id}
    )


async def _handle_subscription_updated(
    subscription: dict,
    org_repo: OrganisationRepository,
    audit_repo: AuditLogRepository
):
    """Handle customer.subscription.updated event.

    Updates subscription status (renewal, cancellation scheduled, etc.)
    """
    org_id = UUID(subscription["metadata"]["org_id"])

    # Update subscription period
    org_repo.update(org_id, {
        "subscription_period_start": datetime.fromtimestamp(subscription["current_period_start"]).isoformat(),
        "subscription_period_end": datetime.fromtimestamp(subscription["current_period_end"]).isoformat(),
        "subscription_cancel_at_period_end": subscription.get("cancel_at_period_end", False),
    })

    # Audit log
    audit_repo.create(
        resource_type="organisation",
        resource_id=str(org_id),
        action="subscription.updated",
        user_id=None,
        metadata={
            "subscription_id": subscription["id"],
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
        }
    )

    logger.info(
        f"Subscription updated for org {org_id}",
        extra={"org_id": str(org_id), "subscription_id": subscription["id"]}
    )


async def _handle_subscription_deleted(
    subscription: dict,
    org_repo: OrganisationRepository,
    audit_repo: AuditLogRepository
):
    """Handle customer.subscription.deleted event.

    Downgrades to FREE plan and activates grace period.
    """
    org_id = UUID(subscription["metadata"]["org_id"])

    # Downgrade to FREE
    org_repo.upgrade_plan(org_id, OrganisationPlan.FREE)

    # Set grace period (30 days to re-subscribe before deletion)
    grace_period_end = datetime.utcnow() + timedelta(days=30)

    org_repo.update(org_id, {
        "stripe_subscription_id": None,
        "subscription_interval": None,
        "grace_period_end": grace_period_end.isoformat(),
        "status": OrganisationStatus.SUSPENDED.value,  # Suspended until grace period ends
    })

    # Audit log
    audit_repo.create(
        resource_type="organisation",
        resource_id=str(org_id),
        action="subscription.canceled",
        user_id=None,
        metadata={
            "subscription_id": subscription["id"],
            "grace_period_end": grace_period_end.isoformat(),
        }
    )

    logger.warning(
        f"Subscription canceled for org {org_id}. Grace period until {grace_period_end}",
        extra={"org_id": str(org_id)}
    )


async def _handle_payment_succeeded(
    invoice: dict,
    org_repo: OrganisationRepository,
    audit_repo: AuditLogRepository
):
    """Handle invoice.payment_succeeded event.

    Records successful payment.
    """
    subscription_id = invoice.get("subscription")

    if not subscription_id:
        return  # Not a subscription invoice

    # Find organisation by subscription_id
    # TODO: Add query method or cache subscription → org mapping

    logger.info(f"Payment succeeded for subscription {subscription_id}")


async def _handle_payment_failed(
    invoice: dict,
    org_repo: OrganisationRepository,
    audit_repo: AuditLogRepository
):
    """Handle invoice.payment_failed event.

    Suspends organisation if payment fails.
    """
    subscription_id = invoice.get("subscription")

    if not subscription_id:
        return

    # TODO: Find org by subscription_id and suspend

    logger.warning(f"Payment failed for subscription {subscription_id}")
