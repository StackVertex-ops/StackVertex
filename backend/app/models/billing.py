"""Billing Models & Enums.

Hybrid Pricing Model: Flat Fee + % AWS Infrastructure Costs.
"""

from decimal import Decimal
from enum import Enum
from typing import Dict, Any


class BillingTier(str, Enum):
    """Pricing Tiers mit Hybrid-Model (Base Fee + % AWS Costs)."""

    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    PAY_AS_YOU_GO = "payg"


class BillingPeriod(str, Enum):
    """Billing Period."""

    MONTHLY = "monthly"
    ANNUAL = "annual"  # 2 Monate gratis


class BillingStatus(str, Enum):
    """Subscription Status."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    TRIALING = "trialing"


class InvoiceStatus(str, Enum):
    """Invoice Status."""

    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


# Tier Pricing Configuration
TIER_PRICING = {
    BillingTier.STARTER: {
        "base_price_monthly": Decimal("10.00"),
        "base_price_annual": Decimal("100.00"),  # 2 Monate gratis
        "aws_cost_percentage": 15,
        "limits": {
            "max_deployments": 3,
            "max_organisations": 1,
            "max_resources_per_deployment": 10,
            "support_level": "community",
            "monitoring_interval_minutes": 10,
        },
        "features": [
            "JSON Export",
            "Terraform Apply",
            "Cost Estimation",
            "Basic Monitoring",
            "Community Support"
        ]
    },
    BillingTier.PRO: {
        "base_price_monthly": Decimal("50.00"),
        "base_price_annual": Decimal("500.00"),  # 2 Monate gratis
        "aws_cost_percentage": 10,
        "limits": {
            "max_deployments": 20,
            "max_organisations": 3,
            "max_resources_per_deployment": -1,  # unlimited
            "support_level": "email",
            "support_response_hours": 24,
            "monitoring_interval_minutes": 1,
        },
        "features": [
            "Alles aus STARTER",
            "20 Deployments",
            "Unlimited Resources",
            "Advanced Monitoring",
            "Email Support (24h)",
            "Cost Tracking",
            "Alerts"
        ]
    },
    BillingTier.ENTERPRISE: {
        "base_price_monthly": Decimal("250.00"),
        "base_price_annual": Decimal("2500.00"),  # 2 Monate gratis
        "aws_cost_percentage": 5,
        "limits": {
            "max_deployments": -1,  # unlimited
            "max_organisations": -1,  # unlimited
            "max_resources_per_deployment": -1,  # unlimited
            "support_level": "priority",
            "support_response_hours": 4,
            "monitoring_interval_minutes": 0.5,  # 30 seconds
        },
        "features": [
            "Alles aus PRO",
            "Unlimited Deployments",
            "Unlimited Organisations",
            "Multi-Cloud (AWS + Azure + GCP)",
            "Priority Support (4h)",
            "SLA 99.9%",
            "Dedicated Account Manager",
            "Blue/Green Deployments",
            "Drift Detection",
            "Custom Integrations"
        ]
    },
    BillingTier.PAY_AS_YOU_GO: {
        "base_price_monthly": Decimal("0.00"),
        "base_price_annual": Decimal("0.00"),
        "aws_cost_percentage": 20,
        "per_deployment_fee": Decimal("5.00"),
        "limits": {
            "max_deployments": -1,
            "max_organisations": 1,
            "max_resources_per_deployment": -1,
            "support_level": "community",
            "monitoring_interval_minutes": 10,
        },
        "features": [
            "Pay per Deployment (€5)",
            "No monthly commitment",
            "20% AWS markup",
            "Community Support"
        ]
    }
}


def get_tier_config(tier: BillingTier) -> Dict[str, Any]:
    """Get pricing config for tier.

    Args:
        tier: Billing tier

    Returns:
        Configuration dict with pricing and limits
    """
    return TIER_PRICING[tier]


def get_base_price(tier: BillingTier, period: BillingPeriod) -> Decimal:
    """Get base price for tier and billing period.

    Args:
        tier: Billing tier
        period: Billing period (monthly or annual)

    Returns:
        Base price in EUR
    """
    config = get_tier_config(tier)

    if period == BillingPeriod.MONTHLY:
        return config["base_price_monthly"]
    else:
        return config["base_price_annual"]


def get_aws_markup_percentage(tier: BillingTier) -> int:
    """Get AWS cost markup percentage for tier.

    Args:
        tier: Billing tier

    Returns:
        Markup percentage (e.g., 10 for 10%)
    """
    return get_tier_config(tier)["aws_cost_percentage"]


def calculate_monthly_cost_example(
    tier: BillingTier,
    aws_costs: Decimal,
    num_deployments: int = 0
) -> Dict[str, Decimal]:
    """Calculate example monthly cost for tier.

    Args:
        tier: Billing tier
        aws_costs: Monthly AWS infrastructure costs
        num_deployments: Number of deployments (for PAYG)

    Returns:
        Dict with cost breakdown
    """
    # Ensure aws_costs is Decimal
    if not isinstance(aws_costs, Decimal):
        aws_costs = Decimal(str(aws_costs))

    config = get_tier_config(tier)
    base_price = config["base_price_monthly"]
    markup_percentage = config["aws_cost_percentage"]
    markup_fee = aws_costs * (Decimal(str(markup_percentage)) / Decimal("100"))

    total = base_price + markup_fee

    # PAYG: Add per-deployment fees
    deployment_fees = Decimal("0.00")
    if tier == BillingTier.PAY_AS_YOU_GO and num_deployments > 0:
        deployment_fees = Decimal(str(num_deployments)) * config["per_deployment_fee"]
        total += deployment_fees

    return {
        "base_price": base_price.quantize(Decimal("0.01")),
        "aws_costs": aws_costs.quantize(Decimal("0.01")),
        "markup_percentage": markup_percentage,
        "markup_fee": markup_fee.quantize(Decimal("0.01")),
        "deployment_fees": deployment_fees.quantize(Decimal("0.01")),
        "subtotal": total.quantize(Decimal("0.01")),
        "tax": (total * Decimal("0.19")).quantize(Decimal("0.01")),  # 19% VAT (Germany)
        "total": (total * Decimal("1.19")).quantize(Decimal("0.01"))
    }
