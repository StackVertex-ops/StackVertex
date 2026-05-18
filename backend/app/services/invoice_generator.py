"""Invoice Generation Service.

Generates monthly invoices based on subscription + AWS costs.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.models.billing import BillingTier
from app.repositories.aws_cost import AWSCostRepository
from app.repositories.invoice import InvoiceRepository
from app.repositories.subscription import SubscriptionRepository

logger = logging.getLogger(__name__)


class InvoiceGenerator:
    """Generates invoices for organisations."""

    VAT_RATE = Decimal("0.19")  # 19% VAT (Germany)

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        subscription_repo: SubscriptionRepository,
        cost_repo: AWSCostRepository
    ):
        """Initialize Invoice Generator.

        Args:
            invoice_repo: Invoice repository
            subscription_repo: Subscription repository
            cost_repo: AWS cost repository
        """
        self.invoice_repo = invoice_repo
        self.subscription_repo = subscription_repo
        self.cost_repo = cost_repo

    def generate_monthly_invoice(
        self,
        org_id: UUID,
        month: str  # Format: "2026-05"
    ) -> dict[str, Any]:
        """Generate invoice for an organisation for a specific month.

        Args:
            org_id: Organisation UUID
            month: Month in format YYYY-MM

        Returns:
            Generated invoice

        Raises:
            ValueError: If no subscription exists
        """
        # Get subscription
        subscription = self.subscription_repo.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        # Get AWS costs for month
        cost_record = self.cost_repo.get_monthly_costs(org_id, month)
        aws_costs = Decimal(str(cost_record["total_aws_costs"])) if cost_record else Decimal("0.00")
        deployment_costs = cost_record.get("deployment_costs", {}) if cost_record else {}

        # Build line items
        line_items = self._build_line_items(
            subscription=subscription,
            aws_costs=aws_costs,
            deployment_costs=deployment_costs
        )

        # Calculate totals
        subtotal = sum(Decimal(str(item["amount"])) for item in line_items)
        tax = subtotal * self.VAT_RATE
        total = subtotal + tax

        # Generate invoice number
        invoice_number = self.invoice_repo.generate_invoice_number(org_id, month)

        # Period dates
        year, month_num = month.split('-')
        period_start = datetime(int(year), int(month_num), 1)

        if int(month_num) == 12:
            period_end = datetime(int(year) + 1, 1, 1)
        else:
            period_end = datetime(int(year), int(month_num) + 1, 1)

        # Create invoice
        invoice = self.invoice_repo.create(
            org_id=org_id,
            invoice_number=invoice_number,
            period_start=period_start,
            period_end=period_end,
            line_items=line_items,
            subtotal=subtotal.quantize(Decimal("0.01")),
            tax=tax.quantize(Decimal("0.01")),
            total=total.quantize(Decimal("0.01"))
        )

        logger.info(
            f"Generated invoice {invoice_number} for org {org_id}: €{total:.2f}"
        )

        return invoice

    def _build_line_items(
        self,
        subscription: dict[str, Any],
        aws_costs: Decimal,
        deployment_costs: dict[str, dict[str, float]]
    ) -> list[dict[str, Any]]:
        """Build invoice line items.

        Args:
            subscription: Subscription data
            aws_costs: Total AWS costs
            deployment_costs: Breakdown by deployment

        Returns:
            List of line items
        """
        line_items = []

        tier = BillingTier(subscription["tier"])
        base_price = subscription["base_price"]
        percentage = subscription["aws_cost_percentage"]

        # Line 1: Base subscription fee
        line_items.append({
            "description": f"OverCloud {tier.value.upper()} - Base Fee",
            "amount": base_price,
            "currency": "EUR"
        })

        # Line 2: AWS infrastructure markup
        if aws_costs > 0:
            markup_fee = aws_costs * (Decimal(str(percentage)) / Decimal("100"))

            line_items.append({
                "description": f"AWS Infrastructure Costs ({percentage}% markup)",
                "breakdown": {
                    "aws_costs": aws_costs.quantize(Decimal("0.01")),
                    "percentage": percentage,
                    "fee": markup_fee.quantize(Decimal("0.01")),
                    "deployments": self._summarize_deployment_costs(deployment_costs)
                },
                "amount": markup_fee.quantize(Decimal("0.01")),
                "currency": "EUR"
            })

        # Line 3: PAYG per-deployment fees
        if tier == BillingTier.PAY_AS_YOU_GO:
            num_deployments = len(deployment_costs)
            per_deployment_fee = Decimal("5.00")  # €5 per deployment
            deployment_fees = Decimal(str(num_deployments)) * per_deployment_fee

            if deployment_fees > 0:
                line_items.append({
                    "description": f"Deployments ({num_deployments} × €{per_deployment_fee})",
                    "amount": deployment_fees.quantize(Decimal("0.01")),
                    "currency": "EUR"
                })

        # Line 4: Voucher Discount (if applied)
        voucher_code = subscription.get("voucher_code")
        if voucher_code:
            discount_amount = self._calculate_voucher_discount(
                subscription=subscription,
                base_price=base_price,
                aws_costs=aws_costs,
                percentage=percentage
            )

            if discount_amount > 0:
                line_items.append({
                    "description": f"Discount ({voucher_code})",
                    "breakdown": {
                        "voucher_code": voucher_code,
                        "discount_type": subscription.get("voucher_discount_type"),
                        "discount_value": subscription.get("voucher_discount_value"),
                        "applies_to": subscription.get("voucher_applies_to")
                    },
                    "amount": -discount_amount.quantize(Decimal("0.01")),  # Negative = Rabatt
                    "currency": "EUR"
                })

        return line_items

    def _calculate_voucher_discount(
        self,
        subscription: dict[str, Any],
        base_price: Decimal,
        aws_costs: Decimal,
        percentage: int
    ) -> Decimal:
        """Berechnet Voucher-Rabatt für Invoice.

        Args:
            subscription: Subscription mit Voucher-Daten
            base_price: Base subscription fee
            aws_costs: AWS costs
            percentage: AWS markup percentage

        Returns:
            Discount amount (positive value)
        """
        discount_type = subscription.get("voucher_discount_type")
        discount_value = subscription.get("voucher_discount_value")
        applies_to = subscription.get("voucher_applies_to")

        if not all([discount_type, discount_value, applies_to]):
            return Decimal("0.00")

        # Berechne AWS markup
        aws_markup = aws_costs * (Decimal(str(percentage)) / Decimal("100"))

        # Was soll rabattiert werden?
        target_amount = Decimal("0.00")

        if applies_to == "base_fee":
            target_amount = base_price
        elif applies_to == "aws_percentage":
            target_amount = aws_markup
        elif applies_to == "both":
            target_amount = base_price + aws_markup

        # Percentage oder Fixed?
        if discount_type == "percentage":
            discount = target_amount * (Decimal(str(discount_value)) / Decimal("100"))
        else:  # fixed
            discount = min(Decimal(str(discount_value)), target_amount)

        return discount

    def _summarize_deployment_costs(
        self,
        deployment_costs: dict[str, dict[str, float]]
    ) -> list[dict[str, Any]]:
        """Summarize deployment costs for invoice.

        Args:
            deployment_costs: Costs by deployment and service

        Returns:
            List of deployment summaries
        """
        summaries = []

        for deployment_id, services in deployment_costs.items():
            total = sum(v for k, v in services.items() if k != 'total')
            summaries.append({
                "deployment_id": deployment_id,
                "total_cost": round(total, 2)
            })

        # Sort by cost (descending)
        summaries.sort(key=lambda x: x["total_cost"], reverse=True)

        return summaries

    def generate_invoices_for_all_orgs(self, month: str) -> list[dict[str, Any]]:
        """Generate invoices for all active organisations for a month.

        Args:
            month: Month in format YYYY-MM

        Returns:
            List of generated invoices
        """
        # Note: In production, you'd query all active subscriptions
        # For now, this is a placeholder for a scheduled job

        logger.info(f"Starting invoice generation for month {month}")

        generated_invoices = []

        # TODO: Implement batch processing for all organisations
        # This would typically be run as a monthly cron job

        logger.info(
            f"Generated {len(generated_invoices)} invoices for month {month}"
        )

        return generated_invoices

    def preview_next_invoice(self, org_id: UUID) -> dict[str, Any]:
        """Preview next invoice for organisation (without creating it).

        Args:
            org_id: Organisation UUID

        Returns:
            Invoice preview
        """
        subscription = self.subscription_repo.get_by_org(org_id)
        if not subscription:
            raise ValueError(f"No subscription found for org {org_id}")

        # Get current month costs
        current_month = datetime.utcnow().strftime("%Y-%m")
        cost_record = self.cost_repo.get_monthly_costs(org_id, current_month)

        aws_costs = Decimal(str(cost_record["total_aws_costs"])) if cost_record else Decimal("0.00")
        deployment_costs = cost_record.get("deployment_costs", {}) if cost_record else {}

        # Build line items
        line_items = self._build_line_items(
            subscription=subscription,
            aws_costs=aws_costs,
            deployment_costs=deployment_costs
        )

        # Calculate totals
        subtotal = sum(Decimal(str(item["amount"])) for item in line_items)
        tax = subtotal * self.VAT_RATE
        total = subtotal + tax

        # Get period info
        period_start = datetime(
            datetime.utcnow().year,
            datetime.utcnow().month,
            1
        )
        period_end = subscription.get("current_period_end")

        return {
            "preview": True,
            "org_id": str(org_id),
            "tier": subscription["tier"],
            "period_start": period_start.isoformat(),
            "period_end": period_end,
            "line_items": line_items,
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "tax": tax.quantize(Decimal("0.01")),
            "total": total.quantize(Decimal("0.01")),
            "currency": "EUR"
        }
