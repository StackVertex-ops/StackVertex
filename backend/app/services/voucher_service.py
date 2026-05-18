"""Voucher Service.

Business Logic für Voucher-Validierung und Discount-Berechnung.
"""

import logging
from typing import Any
from uuid import UUID

from app.repositories.subscription import SubscriptionRepository
from app.repositories.voucher import VoucherRepository

logger = logging.getLogger(__name__)


class VoucherService:
    """Service für Voucher-Operationen und Discount-Berechnungen."""

    def __init__(
        self,
        voucher_repo: VoucherRepository,
        subscription_repo: SubscriptionRepository
    ):
        """Initialize Voucher Service.

        Args:
            voucher_repo: Voucher Repository
            subscription_repo: Subscription Repository
        """
        self.voucher_repo = voucher_repo
        self.subscription_repo = subscription_repo

    def validate_voucher(self, code: str, user_id: UUID) -> dict[str, Any]:
        """Validiert Voucher für User.

        Args:
            code: Gutscheincode
            user_id: User ID

        Returns:
            Voucher-Details mit Validierungsstatus

        Raises:
            ValueError: Wenn Voucher ungültig
        """
        try:
            result = self.voucher_repo.validate(code, user_id)
            logger.info(
                f"Voucher {code} validated successfully for user {user_id}",
                extra={"code": code, "user_id": str(user_id)}
            )
            return result
        except ValueError as e:
            logger.warning(
                f"Voucher validation failed: {str(e)}",
                extra={"code": code, "user_id": str(user_id), "error": str(e)}
            )
            raise

    def apply_discount(
        self,
        base_price: float,
        aws_costs: float,
        aws_percentage: float,
        voucher_code: str | None = None,
        user_id: UUID | None = None
    ) -> dict[str, Any]:
        """Berechnet finale Kosten mit angewendetem Gutschein.

        Args:
            base_price: Base subscription fee
            aws_costs: AWS infrastructure costs
            aws_percentage: AWS markup percentage
            voucher_code: Optional voucher code
            user_id: User ID (required if voucher_code provided)

        Returns:
            Dict mit Kostenaufschlüsselung und angewendetem Rabatt
        """
        # Ursprüngliche Kosten
        aws_markup = aws_costs * (aws_percentage / 100)
        subtotal_before_discount = base_price + aws_markup

        # Keine Voucher? Return original
        if not voucher_code or not user_id:
            return {
                "base_price": round(base_price, 2),
                "aws_costs": round(aws_costs, 2),
                "aws_percentage": aws_percentage,
                "aws_markup": round(aws_markup, 2),
                "subtotal": round(subtotal_before_discount, 2),
                "discount_applied": False,
                "discount_amount": 0.0,
                "voucher_code": None,
                "final_subtotal": round(subtotal_before_discount, 2)
            }

        # Validiere Voucher (wirft ValueError wenn ungültig)
        try:
            voucher = self.voucher_repo.validate(voucher_code, user_id)
        except ValueError as e:
            logger.warning(f"Voucher validation failed during apply_discount: {str(e)}")
            # Return ohne Discount wenn Voucher ungültig
            return {
                "base_price": round(base_price, 2),
                "aws_costs": round(aws_costs, 2),
                "aws_percentage": aws_percentage,
                "aws_markup": round(aws_markup, 2),
                "subtotal": round(subtotal_before_discount, 2),
                "discount_applied": False,
                "discount_amount": 0.0,
                "voucher_code": voucher_code,
                "voucher_error": str(e),
                "final_subtotal": round(subtotal_before_discount, 2)
            }

        # Berechne Discount
        discount_amount = self._calculate_discount(
            base_price=base_price,
            aws_markup=aws_markup,
            voucher=voucher
        )

        final_subtotal = max(0, subtotal_before_discount - discount_amount)

        logger.info(
            f"Voucher {voucher_code} applied: €{discount_amount:.2f} discount",
            extra={
                "code": voucher_code,
                "user_id": str(user_id),
                "discount": discount_amount,
                "final_subtotal": final_subtotal
            }
        )

        return {
            "base_price": round(base_price, 2),
            "aws_costs": round(aws_costs, 2),
            "aws_percentage": aws_percentage,
            "aws_markup": round(aws_markup, 2),
            "subtotal": round(subtotal_before_discount, 2),
            "discount_applied": True,
            "discount_type": voucher["discount_type"],
            "discount_value": voucher["discount_value"],
            "discount_amount": round(discount_amount, 2),
            "voucher_code": voucher_code,
            "applies_to": voucher["applies_to"],
            "final_subtotal": round(final_subtotal, 2)
        }

    def _calculate_discount(
        self,
        base_price: float,
        aws_markup: float,
        voucher: dict[str, Any]
    ) -> float:
        """Berechnet Discount-Betrag basierend auf Voucher-Config.

        Args:
            base_price: Base subscription fee
            aws_markup: AWS markup fee
            voucher: Voucher dict mit discount_type, discount_value, applies_to

        Returns:
            Discount amount in EUR
        """
        discount_type = voucher["discount_type"]
        discount_value = voucher["discount_value"]
        applies_to = voucher["applies_to"]

        # Was soll rabattiert werden?
        target_amount = 0.0

        if applies_to == "base_fee":
            target_amount = base_price
        elif applies_to == "aws_percentage":
            target_amount = aws_markup
        elif applies_to == "both":
            target_amount = base_price + aws_markup

        # Percentage oder Fixed?
        if discount_type == "percentage":
            discount = target_amount * (discount_value / 100)
        else:  # fixed
            discount = min(discount_value, target_amount)  # Nicht mehr als target

        return discount

    def redeem_voucher(
        self,
        code: str,
        user_id: UUID,
        org_id: UUID
    ) -> dict[str, Any]:
        """Wendet Voucher auf Subscription an.

        Args:
            code: Gutscheincode
            user_id: User ID
            org_id: Organisation ID

        Returns:
            Aktualisierte Subscription mit Voucher

        Raises:
            ValueError: Wenn Voucher ungültig oder Subscription nicht gefunden
        """
        # Validiere Voucher
        voucher = self.validate_voucher(code, user_id)

        # Get Subscription
        subscription = self.subscription_repo.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        # Prüfe ob bereits ein Voucher angewendet wurde
        if subscription.get("voucher_code"):
            raise ValueError(
                f"Subscription already has voucher '{subscription['voucher_code']}' applied. "
                "Remove it first before applying a new one."
            )

        # Redeem Voucher (markiert als verwendet)
        self.voucher_repo.redeem(code, user_id)

        # Update Subscription mit Voucher
        updated_subscription = self.subscription_repo._update_item(
            pk=f"ORG#{org_id}",
            sk="SUBSCRIPTION",
            updates={
                "voucher_code": code.upper(),
                "voucher_discount_type": voucher["discount_type"],
                "voucher_discount_value": voucher["discount_value"],
                "voucher_applies_to": voucher["applies_to"],
                "voucher_applied_at": voucher["applied_at"] if "applied_at" in voucher else None,
                "voucher_applied_by": str(user_id)
            }
        )

        logger.info(
            f"Voucher {code} applied to subscription for org {org_id}",
            extra={
                "code": code,
                "org_id": str(org_id),
                "user_id": str(user_id)
            }
        )

        return updated_subscription

    def remove_voucher_from_subscription(
        self,
        org_id: UUID
    ) -> dict[str, Any]:
        """Entfernt Voucher von Subscription.

        Note: Voucher wird NICHT als "ungenutzt" markiert - einmal verwendet = verwendet.

        Args:
            org_id: Organisation ID

        Returns:
            Aktualisierte Subscription

        Raises:
            ValueError: Wenn keine Subscription gefunden
        """
        subscription = self.subscription_repo.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        # Remove voucher fields
        updated_subscription = self.subscription_repo._update_item(
            pk=f"ORG#{org_id}",
            sk="SUBSCRIPTION",
            updates={
                "voucher_code": None,
                "voucher_discount_type": None,
                "voucher_discount_value": None,
                "voucher_applies_to": None,
                "voucher_applied_at": None,
                "voucher_applied_by": None,
                "voucher_removed_at": None  # Track removal
            }
        )

        logger.info(
            f"Voucher removed from subscription for org {org_id}",
            extra={"org_id": str(org_id)}
        )

        return updated_subscription

    def calculate_subscription_price_with_voucher(
        self,
        org_id: UUID,
        aws_costs: float = 0.0
    ) -> dict[str, Any]:
        """Berechnet finale Subscription-Kosten inkl. Voucher (falls vorhanden).

        Args:
            org_id: Organisation ID
            aws_costs: Aktuelle AWS Kosten

        Returns:
            Dict mit Kostenaufschlüsselung

        Raises:
            ValueError: Wenn keine Subscription gefunden
        """
        subscription = self.subscription_repo.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        base_price = subscription["base_price"]
        aws_percentage = subscription["aws_cost_percentage"]
        voucher_code = subscription.get("voucher_code")

        # Hole User ID aus Subscription (voucher_applied_by)
        user_id = subscription.get("voucher_applied_by")

        return self.apply_discount(
            base_price=base_price,
            aws_costs=aws_costs,
            aws_percentage=aws_percentage,
            voucher_code=voucher_code,
            user_id=UUID(user_id) if user_id else None
        )
