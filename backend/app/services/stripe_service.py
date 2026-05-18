"""Stripe Payment Integration.

Handles Stripe Checkout, Subscriptions, and Webhooks.
"""

import logging
from datetime import datetime
from typing import Any

import stripe

from app.config import settings
from app.models.organisation import OrganisationPlan, get_plan_price

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None


class StripeService:
    """Stripe API Integration."""

    def __init__(self, api_key: str | None = None):
        """Initialize Stripe Service.

        Args:
            api_key: Stripe Secret Key (optional, defaults to settings)
        """
        self.api_key = api_key or stripe.api_key
        if self.api_key:
            stripe.api_key = self.api_key

    def create_customer(
        self,
        org_id: str,
        org_name: str,
        user_email: str,
        user_name: str
    ) -> str:
        """Create Stripe Customer.

        Args:
            org_id: Organisation UUID
            org_name: Organisation name
            user_email: Owner email
            user_name: Owner name

        Returns:
            Stripe Customer ID
        """
        customer = stripe.Customer.create(
            name=org_name,
            email=user_email,
            metadata={
                "org_id": org_id,
                "org_name": org_name,
                "owner_name": user_name,
            }
        )

        logger.info(f"Created Stripe customer for org {org_id}: {customer.id}")
        return customer.id

    def create_checkout_session(
        self,
        org_id: str,
        customer_id: str,
        plan: OrganisationPlan,
        interval: str,
        success_url: str,
        cancel_url: str,
        auto_renewal: bool = False
    ) -> dict[str, Any]:
        """Create Stripe Checkout Session.

        Args:
            org_id: Organisation UUID
            customer_id: Stripe Customer ID
            plan: Target plan
            interval: "monthly" or "yearly"
            success_url: Redirect URL after successful payment
            cancel_url: Redirect URL if user cancels
            auto_renewal: Enable automatic renewal (default: False)

        Returns:
            Checkout Session object
        """
        price_amount = int(get_plan_price(plan, interval) * 100)  # Convert to cents

        # Create Price object
        price = stripe.Price.create(
            unit_amount=price_amount,
            currency="eur",
            recurring={
                "interval": "month" if interval == "monthly" else "year",
            },
            product_data={
                "name": f"OverCloud {plan.value.upper()} Plan",
                "description": self._get_plan_description(plan),
            },
        )

        # Create Checkout Session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card", "sepa_debit"],
            line_items=[{
                "price": price.id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                "metadata": {
                    "org_id": org_id,
                    "plan": plan.value,
                    "interval": interval,
                    "auto_renewal": str(auto_renewal),
                },
                # Cancel at period end if auto_renewal is False
                "cancel_at_period_end": not auto_renewal,
            },
            metadata={
                "org_id": org_id,
            }
        )

        logger.info(
            f"Created checkout session for org {org_id}: {session.id}",
            extra={"plan": plan.value, "interval": interval, "auto_renewal": auto_renewal}
        )

        return {
            "id": session.id,
            "url": session.url,
            "expires_at": session.expires_at,
        }

    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> str:
        """Create Billing Portal Session.

        Args:
            customer_id: Stripe Customer ID
            return_url: Return URL after portal session

        Returns:
            Portal Session URL
        """
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        logger.info(f"Created billing portal session for customer {customer_id}")
        return portal_session.url

    def get_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        """Get Subscription details.

        Args:
            subscription_id: Stripe Subscription ID

        Returns:
            Subscription data or None
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                "plan": subscription.metadata.get("plan"),
                "interval": subscription.metadata.get("interval"),
                "auto_renewal": subscription.metadata.get("auto_renewal") == "True",
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            return None

    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> bool:
        """Cancel subscription.

        Args:
            subscription_id: Stripe Subscription ID
            immediately: Cancel immediately (True) or at period end (False)

        Returns:
            True if successful
        """
        try:
            if immediately:
                stripe.Subscription.delete(subscription_id)
                logger.info(f"Canceled subscription {subscription_id} immediately")
            else:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Scheduled subscription {subscription_id} for cancellation at period end")

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            return False

    def enable_auto_renewal(self, subscription_id: str) -> bool:
        """Enable automatic renewal for subscription.

        Args:
            subscription_id: Stripe Subscription ID

        Returns:
            True if successful
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
                metadata={
                    "auto_renewal": "True"
                }
            )
            logger.info(f"Enabled auto-renewal for subscription {subscription_id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to enable auto-renewal: {e}")
            return False

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> dict[str, Any] | None:
        """Verify Stripe Webhook signature.

        Args:
            payload: Request body (bytes)
            signature: Stripe-Signature header
            webhook_secret: Webhook signing secret

        Returns:
            Event data or None if verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return None

    @staticmethod
    def _get_plan_description(plan: OrganisationPlan) -> str:
        """Get plan description for Stripe.

        Args:
            plan: Organisation plan

        Returns:
            Description string
        """
        descriptions = {
            OrganisationPlan.FREE: "Free tier - JSON exports only",
            OrganisationPlan.PRO: "Professional tier - 10 active deployments, advanced monitoring",
            OrganisationPlan.ENTERPRISE: "Enterprise tier - unlimited deployments, multi-cloud, SLA",
        }
        return descriptions.get(plan, "OverCloud subscription")


# Dependency for FastAPI
def get_stripe_service() -> StripeService:
    """Get StripeService instance (FastAPI dependency)."""
    return StripeService()
