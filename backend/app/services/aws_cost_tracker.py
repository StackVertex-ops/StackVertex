"""AWS Cost Tracking Service.

Fetches AWS costs via Cost Explorer API and tracks them per deployment.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
import boto3
from botocore.exceptions import ClientError

from app.repositories.aws_cost import AWSCostRepository
from app.repositories.subscription import SubscriptionRepository

logger = logging.getLogger(__name__)


class AWSCostTracker:
    """Tracks AWS infrastructure costs for billing."""

    def __init__(
        self,
        cost_repo: AWSCostRepository,
        subscription_repo: SubscriptionRepository
    ):
        """Initialize AWS Cost Tracker.

        Args:
            cost_repo: AWS cost repository
            subscription_repo: Subscription repository
        """
        self.cost_repo = cost_repo
        self.subscription_repo = subscription_repo

    async def fetch_and_store_monthly_costs(
        self,
        org_id: UUID,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        month: str  # Format: "2026-05"
    ) -> Dict[str, Any]:
        """Fetch AWS costs for a month and store them.

        Args:
            org_id: Organisation UUID
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            aws_region: AWS region
            month: Month in format YYYY-MM

        Returns:
            Cost data with breakdown
        """
        try:
            # Get costs from AWS Cost Explorer
            cost_data = await self._fetch_from_cost_explorer(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_region=aws_region,
                month=month
            )

            # Get subscription to calculate percentage fee
            subscription = self.subscription_repo.get_by_org(org_id)
            if not subscription:
                raise ValueError(f"No subscription found for org {org_id}")

            percentage = subscription["aws_cost_percentage"]
            total_aws_costs = cost_data["total_aws_costs"]
            percentage_fee = total_aws_costs * (percentage / 100)

            # Store in database
            stored_record = self.cost_repo.store_monthly_costs(
                org_id=org_id,
                month=month,
                deployment_costs=cost_data["deployment_costs"],
                total_aws_costs=total_aws_costs,
                percentage_fee=percentage_fee
            )

            logger.info(
                f"Stored AWS costs for org {org_id} for month {month}: "
                f"€{total_aws_costs:.2f} AWS + €{percentage_fee:.2f} markup"
            )

            return stored_record

        except Exception as e:
            logger.error(f"Failed to fetch AWS costs for org {org_id}: {e}")
            raise

    async def _fetch_from_cost_explorer(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        month: str
    ) -> Dict[str, Any]:
        """Fetch costs from AWS Cost Explorer API.

        Args:
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            aws_region: AWS region
            month: Month in format YYYY-MM

        Returns:
            Cost breakdown by deployment and service
        """
        # Create AWS session with customer credentials
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )

        ce_client = session.client('ce')  # Cost Explorer

        # Parse month to get date range
        year, month_num = month.split('-')
        start_date = f"{year}-{month_num}-01"

        # Calculate end date (first day of next month)
        if month_num == "12":
            end_date = f"{int(year)+1}-01-01"
        else:
            end_date = f"{year}-{int(month_num)+1:02d}-01"

        try:
            # Query Cost Explorer
            # WICHTIG: Filter NUR OverCloud-managed Ressourcen (via Tag)
            # Group by Service AND by Tag (overcloud:deployment_id)
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                # ✅ Filter: Nur Ressourcen mit overcloud:managed Tag
                Filter={
                    "Tags": {
                        "Key": "overcloud:managed",
                        "Values": ["true"]
                    }
                },
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'TAG', 'Key': 'overcloud:deployment_id'}
                ]
            )

            # Parse results into deployment -> service -> cost structure
            deployment_costs: Dict[str, Dict[str, float]] = {}
            total_cost = 0.0

            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    keys = group.get('Keys', [])
                    if len(keys) < 2:
                        continue

                    service = keys[0]
                    deployment_id = keys[1] if keys[1] else 'untagged'

                    cost_str = group['Metrics']['UnblendedCost']['Amount']
                    cost = float(cost_str)

                    if deployment_id not in deployment_costs:
                        deployment_costs[deployment_id] = {}

                    deployment_costs[deployment_id][service] = cost
                    total_cost += cost

            # Calculate totals per deployment
            for deployment_id, services in deployment_costs.items():
                services['total'] = sum(services.values())

            return {
                "month": month,
                "deployment_costs": deployment_costs,
                "total_aws_costs": round(total_cost, 2)
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']

            logger.error(
                f"AWS Cost Explorer API error: {error_code} - {error_message}"
            )

            # Fallback: Return empty data if Cost Explorer is not enabled
            if error_code == 'AccessDeniedException':
                logger.warning(
                    "Cost Explorer not enabled or insufficient permissions. "
                    "Returning empty cost data."
                )
                return {
                    "month": month,
                    "deployment_costs": {},
                    "total_aws_costs": 0.0
                }

            raise

    def get_current_month_costs(
        self,
        org_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get costs for current month.

        Args:
            org_id: Organisation UUID

        Returns:
            Cost record or None
        """
        current_month = datetime.utcnow().strftime("%Y-%m")
        return self.cost_repo.get_monthly_costs(org_id, current_month)

    def get_cost_projection(
        self,
        org_id: UUID
    ) -> Dict[str, float]:
        """Project end-of-month costs based on current usage.

        Args:
            org_id: Organisation UUID

        Returns:
            Projected costs
        """
        current_month = datetime.utcnow().strftime("%Y-%m")
        cost_record = self.cost_repo.get_monthly_costs(org_id, current_month)

        if not cost_record:
            return {
                "current_aws_costs": 0.0,
                "projected_aws_costs": 0.0,
                "projected_overcloud_fee": 0.0,
                "projected_total": 0.0
            }

        # Simple projection: (current_cost / days_elapsed) * days_in_month
        now = datetime.utcnow()
        days_in_month = (
            datetime(now.year, now.month + 1, 1) - datetime(now.year, now.month, 1)
        ).days if now.month < 12 else 31
        days_elapsed = now.day

        current_costs = cost_record["total_aws_costs"]
        projected_costs = (current_costs / days_elapsed) * days_in_month

        subscription = self.subscription_repo.get_by_org(org_id)
        percentage = subscription["aws_cost_percentage"] if subscription else 10

        projected_fee = projected_costs * (percentage / 100)

        return {
            "current_aws_costs": round(current_costs, 2),
            "projected_aws_costs": round(projected_costs, 2),
            "projected_overcloud_fee": round(projected_fee, 2),
            "projected_total": round(projected_costs + projected_fee, 2),
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month
        }
