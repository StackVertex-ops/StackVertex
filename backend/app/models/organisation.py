"""Organisation Models & Enums.

Domain models für Multi-Tenant Organisation Management.
"""

from enum import Enum
from typing import Optional


class OrganisationPlan(str, Enum):
    """Subscription Plan Tiers."""

    FREE = "free"              # 1 Active Deployment, 3 Users, Basic Monitoring
    PRO = "pro"                # 10 Active Deployments, 10 Users, Advanced Monitoring
    ENTERPRISE = "enterprise"  # Unlimited Everything, Multi-Cloud, SLA


class OrganisationStatus(str, Enum):
    """Organisation Account Status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"      # Payment failed, ToS violation
    TRIAL = "trial"              # 14-day trial period
    CANCELLED = "cancelled"      # Marked for deletion


class MonitoringLevel(str, Enum):
    """Monitoring Feature Level."""

    BASIC = "basic"          # Free: Status + Simple Metrics (5min interval)
    ADVANCED = "advanced"    # Pro: CloudWatch Integration, Live Charts (1min interval)
    ENTERPRISE = "enterprise"  # Enterprise: Custom Metrics, SLA Tracking, Alerts


class OrganisationType(str, Enum):
    """Organisation Type."""

    PERSONAL = "personal"    # Single user, auto-created on signup
    TEAM = "team"            # Multi-user organisation
    ENTERPRISE = "enterprise"  # Enterprise organisation with SLA


# Plan Pricing (EUR)
PLAN_PRICING = {
    OrganisationPlan.FREE: {
        "monthly": 0,
        "yearly": 0,
    },
    OrganisationPlan.PRO: {
        "monthly": 29.00,  # €29/month
        "yearly": 290.00,  # €290/year (17% discount = 10 months)
    },
    OrganisationPlan.ENTERPRISE: {
        "monthly": 149.00,  # €149/month
        "yearly": 1491.00,  # €1,491/year (17% discount)
    },
}

# Plan Quotas (hardcoded limits)
PLAN_QUOTAS = {
    OrganisationPlan.FREE: {
        "max_active_deployments": 1,  # Nur 1 kleines Deployment
        "max_members": 1,  # Nur Owner (keine Team-Members)
        "max_architectures": 10,  # Begrenzt für Testing
        "monitoring_level": MonitoringLevel.BASIC,
        "monitoring_interval_seconds": 600,  # 10 minutes (langsamer als PRO)
        "terraform_json_exports": -1,  # JSON Export unlimited (Core Feature!)
        "terraform_apply": False,  # ❌ KEIN echtes Deployment! Nur JSON Export
        "cost_estimation": True,
        "multi_cloud": False,
        "max_deployment_components": 3,  # Max 3 Components pro Architecture (klein)
    },
    OrganisationPlan.PRO: {
        "max_active_deployments": 10,
        "max_members": 10,
        "max_architectures": 500,
        "monitoring_level": MonitoringLevel.ADVANCED,
        "monitoring_interval_seconds": 60,  # 1 minute
        "terraform_json_exports": -1,  # unlimited
        "terraform_apply": True,  # ✅ Echte Deployments möglich
        "cost_estimation": True,
        "multi_cloud": False,
        "deployment_history_days": 90,
        "cost_tracking": True,
        "alerts": True,
        "max_deployment_components": -1,  # Unlimited Components
    },
    OrganisationPlan.ENTERPRISE: {
        "max_active_deployments": -1,  # unlimited
        "max_members": -1,  # unlimited
        "max_architectures": -1,  # unlimited
        "monitoring_level": MonitoringLevel.ENTERPRISE,
        "monitoring_interval_seconds": 30,  # 30 seconds
        "terraform_json_exports": -1,  # unlimited
        "terraform_apply": True,  # ✅ Echte Deployments
        "cost_estimation": True,
        "multi_cloud": True,  # AWS + Azure + GCP
        "deployment_history_days": 365,
        "cost_tracking": True,
        "alerts": True,
        "sla": True,
        "dedicated_support": True,
        "blue_green_deployments": True,
        "drift_detection": True,
        "max_deployment_components": -1,  # Unlimited
        "priority_support": True,
        "custom_integrations": True,
    },
}


def get_quota(plan: OrganisationPlan, quota_key: str) -> int | bool:
    """Get quota value for a plan.

    Args:
        plan: Organisation plan
        quota_key: Quota key (e.g., "max_active_deployments")

    Returns:
        Quota value (-1 = unlimited)
    """
    return PLAN_QUOTAS[plan].get(quota_key, 0)


def can_exceed_quota(plan: OrganisationPlan, quota_key: str) -> bool:
    """Check if quota is unlimited for this plan.

    Args:
        plan: Organisation plan
        quota_key: Quota key

    Returns:
        True if unlimited (quota = -1)
    """
    quota = get_quota(plan, quota_key)
    return isinstance(quota, int) and quota == -1


def get_plan_price(plan: OrganisationPlan, interval: str = "monthly") -> float:
    """Get price for a plan.

    Args:
        plan: Organisation plan
        interval: Billing interval ("monthly" or "yearly")

    Returns:
        Price in EUR
    """
    return PLAN_PRICING[plan].get(interval, 0.0)


def calculate_yearly_discount(plan: OrganisationPlan) -> float:
    """Calculate yearly discount percentage.

    Args:
        plan: Organisation plan

    Returns:
        Discount percentage (e.g., 17.0 for 17%)
    """
    if plan == OrganisationPlan.FREE:
        return 0.0

    monthly_price = get_plan_price(plan, "monthly")
    yearly_price = get_plan_price(plan, "yearly")

    if monthly_price == 0:
        return 0.0

    # Yearly discount: (1 - (yearly / (monthly * 12))) * 100
    full_year_price = monthly_price * 12
    discount = (1 - (yearly_price / full_year_price)) * 100

    return round(discount, 1)
