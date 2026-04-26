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


# Plan Quotas (hardcoded limits)
PLAN_QUOTAS = {
    OrganisationPlan.FREE: {
        "max_active_deployments": 1,
        "max_members": 3,
        "max_architectures": 50,
        "monitoring_level": MonitoringLevel.BASIC,
        "monitoring_interval_seconds": 300,  # 5 minutes
        "terraform_json_exports": -1,  # unlimited
        "cost_estimation": True,
        "multi_cloud": False,
    },
    OrganisationPlan.PRO: {
        "max_active_deployments": 10,
        "max_members": 10,
        "max_architectures": 500,
        "monitoring_level": MonitoringLevel.ADVANCED,
        "monitoring_interval_seconds": 60,  # 1 minute
        "terraform_json_exports": -1,  # unlimited
        "cost_estimation": True,
        "multi_cloud": False,
        "deployment_history_days": 90,
        "cost_tracking": True,
        "alerts": True,
    },
    OrganisationPlan.ENTERPRISE: {
        "max_active_deployments": -1,  # unlimited
        "max_members": -1,  # unlimited
        "max_architectures": -1,  # unlimited
        "monitoring_level": MonitoringLevel.ENTERPRISE,
        "monitoring_interval_seconds": 30,  # 30 seconds
        "terraform_json_exports": -1,  # unlimited
        "cost_estimation": True,
        "multi_cloud": True,  # AWS + Azure + GCP
        "deployment_history_days": 365,
        "cost_tracking": True,
        "alerts": True,
        "sla": True,
        "dedicated_support": True,
        "blue_green_deployments": True,
        "drift_detection": True,
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
