"""Subscription Repository.

Manages subscription lifecycle, tier changes, and billing periods.
"""

from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from boto3.dynamodb.conditions import Key

from app.repositories.base import BaseRepository
from app.models.billing import (
    BillingTier,
    BillingPeriod,
    BillingStatus,
    get_tier_config,
    get_base_price,
    get_aws_markup_percentage
)


class SubscriptionRepository(BaseRepository):
    """Repository für Subscription Management."""

    def create(
        self,
        org_id: UUID,
        tier: BillingTier,
        billing_period: BillingPeriod = BillingPeriod.MONTHLY,
        trial_days: int = 0
    ) -> Dict[str, Any]:
        """Erstellt neue Subscription für Organisation.

        Args:
            org_id: Organisation UUID
            tier: Billing tier
            billing_period: Monthly oder Annual
            trial_days: Trial period in days (0 = no trial)

        Returns:
            Created subscription item
        """
        subscription_id = str(uuid4())
        config = get_tier_config(tier)

        # Calculate period dates
        now = datetime.utcnow()
        period_start = now

        if trial_days > 0:
            period_end = now + timedelta(days=trial_days)
            status = BillingStatus.TRIALING
        else:
            if billing_period == BillingPeriod.MONTHLY:
                period_end = now + timedelta(days=30)
            else:
                period_end = now + timedelta(days=365)
            status = BillingStatus.ACTIVE

        item = {
            "PK": f"ORG#{org_id}",
            "SK": "SUBSCRIPTION",
            "id": subscription_id,
            "org_id": str(org_id),
            "tier": tier.value,
            "billing_period": billing_period.value,
            "status": status.value,
            "base_price": get_base_price(tier, billing_period),
            "aws_cost_percentage": get_aws_markup_percentage(tier),
            "limits": config["limits"],
            "features": config["features"],
            "current_period_start": period_start.isoformat(),
            "current_period_end": period_end.isoformat(),
            "trial_end": (now + timedelta(days=trial_days)).isoformat() if trial_days > 0 else None,
            "stripe_subscription_id": None,  # Wird später gesetzt
            "stripe_customer_id": None,
            # GSI für Subscription Lookup
            "GSI1PK": f"SUBSCRIPTION#{subscription_id}",
            "GSI1SK": "METADATA",
        }

        return self._put_item(item)

    def get_by_org(self, org_id: UUID) -> Optional[Dict[str, Any]]:
        """Get active subscription for organisation.

        Args:
            org_id: Organisation UUID

        Returns:
            Subscription item or None
        """
        return self._get_item(f"ORG#{org_id}", "SUBSCRIPTION")

    def get_by_id(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by ID.

        Args:
            subscription_id: Subscription UUID

        Returns:
            Subscription item or None
        """
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq(f"SUBSCRIPTION#{subscription_id}"),
            index_name="GSI1"
        )

        return items[0] if items else None

    def update_tier(
        self,
        org_id: UUID,
        new_tier: BillingTier,
        new_billing_period: Optional[BillingPeriod] = None
    ) -> Dict[str, Any]:
        """Change subscription tier (upgrade/downgrade).

        Args:
            org_id: Organisation UUID
            new_tier: Target tier
            new_billing_period: Optional new billing period

        Returns:
            Updated subscription
        """
        subscription = self.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        config = get_tier_config(new_tier)
        billing_period = new_billing_period or BillingPeriod(subscription["billing_period"])

        updates = {
            "tier": new_tier.value,
            "base_price": get_base_price(new_tier, billing_period),
            "aws_cost_percentage": get_aws_markup_percentage(new_tier),
            "limits": config["limits"],
            "features": config["features"],
        }

        if new_billing_period:
            updates["billing_period"] = new_billing_period.value

        return self._update_item(
            pk=f"ORG#{org_id}",
            sk="SUBSCRIPTION",
            updates=updates
        )

    def update_status(
        self,
        org_id: UUID,
        status: BillingStatus
    ) -> Dict[str, Any]:
        """Update subscription status.

        Args:
            org_id: Organisation UUID
            status: New status

        Returns:
            Updated subscription
        """
        return self._update_item(
            pk=f"ORG#{org_id}",
            sk="SUBSCRIPTION",
            updates={"status": status.value}
        )

    def link_stripe_subscription(
        self,
        org_id: UUID,
        stripe_subscription_id: str,
        stripe_customer_id: str
    ) -> Dict[str, Any]:
        """Link Stripe subscription to OverCloud subscription.

        Args:
            org_id: Organisation UUID
            stripe_subscription_id: Stripe subscription ID
            stripe_customer_id: Stripe customer ID

        Returns:
            Updated subscription
        """
        return self._update_item(
            pk=f"ORG#{org_id}",
            sk="SUBSCRIPTION",
            updates={
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id
            }
        )

    def renew_period(
        self,
        org_id: UUID
    ) -> Dict[str, Any]:
        """Renew subscription period (nach Zahlung).

        Args:
            org_id: Organisation UUID

        Returns:
            Updated subscription
        """
        subscription = self.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        current_end = datetime.fromisoformat(subscription["current_period_end"])
        billing_period = BillingPeriod(subscription["billing_period"])

        # Calculate new period
        if billing_period == BillingPeriod.MONTHLY:
            new_end = current_end + timedelta(days=30)
        else:
            new_end = current_end + timedelta(days=365)

        return self._update_item(
            pk=f"ORG#{org_id}",
            sk="SUBSCRIPTION",
            updates={
                "current_period_start": current_end.isoformat(),
                "current_period_end": new_end.isoformat(),
                "status": BillingStatus.ACTIVE.value
            }
        )

    def cancel(
        self,
        org_id: UUID,
        immediately: bool = False
    ) -> Dict[str, Any]:
        """Cancel subscription.

        Args:
            org_id: Organisation UUID
            immediately: Cancel immediately (True) or at period end (False)

        Returns:
            Updated subscription
        """
        if immediately:
            return self._update_item(
                pk=f"ORG#{org_id}",
                sk="SUBSCRIPTION",
                updates={
                    "status": BillingStatus.CANCELLED.value,
                    "cancelled_at": datetime.utcnow().isoformat()
                }
            )
        else:
            return self._update_item(
                pk=f"ORG#{org_id}",
                sk="SUBSCRIPTION",
                updates={
                    "cancel_at_period_end": True
                }
            )

    def list_expiring_soon(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """List subscriptions expiring in the next N days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of expiring subscriptions
        """
        # Note: This requires a scan. For production, consider a GSI on expiration date
        threshold = (datetime.utcnow() + timedelta(days=days)).isoformat()

        items, _ = self._scan(
            filter_condition=Key("SK").eq("SUBSCRIPTION") &
                           Key("current_period_end").lte(threshold) &
                           Key("status").eq(BillingStatus.ACTIVE.value)
        )

        return items

    def get_limits(self, org_id: UUID) -> Dict[str, Any]:
        """Get subscription limits for organisation.

        Args:
            org_id: Organisation UUID

        Returns:
            Limits dict
        """
        subscription = self.get_by_org(org_id)
        if not subscription:
            # Return default FREE limits if no subscription
            return get_tier_config(BillingTier.STARTER)["limits"]

        return subscription.get("limits", {})

    def check_limit(
        self,
        org_id: UUID,
        limit_key: str,
        current_value: int
    ) -> bool:
        """Check if organisation has reached a limit.

        Args:
            org_id: Organisation UUID
            limit_key: Limit key (e.g., "max_deployments")
            current_value: Current usage value

        Returns:
            True if within limit, False if exceeded
        """
        limits = self.get_limits(org_id)
        limit = limits.get(limit_key, 0)

        # -1 = unlimited
        if limit == -1:
            return True

        return current_value < limit
