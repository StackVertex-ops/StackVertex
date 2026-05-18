"""AWS Cost Repository.

Tracks AWS infrastructure costs per organisation and deployment.
"""

from typing import Any
from uuid import UUID

from boto3.dynamodb.conditions import Key

from app.repositories.base import BaseRepository


class AWSCostRepository(BaseRepository):
    """Repository für AWS Cost Tracking."""

    def store_monthly_costs(
        self,
        org_id: UUID,
        month: str,  # Format: "2026-05"
        deployment_costs: dict[str, dict[str, float]],
        total_aws_costs: float,
        percentage_fee: float
    ) -> dict[str, Any]:
        """Store AWS costs for a month.

        Args:
            org_id: Organisation UUID
            month: Month in format YYYY-MM
            deployment_costs: Dict[deployment_id] -> Dict[service] -> cost
            total_aws_costs: Total AWS costs for month
            percentage_fee: OverCloud markup fee

        Returns:
            Stored cost record
        """
        item = {
            "PK": f"ORG#{org_id}",
            "SK": f"AWS_COST#{month}",
            "org_id": str(org_id),
            "month": month,
            "deployment_costs": deployment_costs,
            "total_aws_costs": total_aws_costs,
            "overcloud_percentage_fee": percentage_fee,
            # GSI für Cross-Org Cost Analysis
            "GSI1PK": f"MONTH#{month}",
            "GSI1SK": f"ORG#{org_id}",
        }

        return self._put_item(item)

    def get_monthly_costs(
        self,
        org_id: UUID,
        month: str
    ) -> dict[str, Any] | None:
        """Get AWS costs for a specific month.

        Args:
            org_id: Organisation UUID
            month: Month in format YYYY-MM

        Returns:
            Cost record or None
        """
        return self._get_item(
            pk=f"ORG#{org_id}",
            sk=f"AWS_COST#{month}"
        )

    def list_costs_by_org(
        self,
        org_id: UUID,
        limit: int = 12
    ) -> list[dict[str, Any]]:
        """List cost records for organisation (most recent first).

        Args:
            org_id: Organisation UUID
            limit: Maximum number of months to return

        Returns:
            List of cost records
        """
        items, _ = self._query(
            key_condition=Key("PK").eq(f"ORG#{org_id}") &
                         Key("SK").begins_with("AWS_COST#"),
            scan_index_forward=False,  # DESC order (newest first)
            limit=limit
        )

        return items

    def get_deployment_costs(
        self,
        org_id: UUID,
        deployment_id: str,
        months: int = 3
    ) -> list[dict[str, Any]]:
        """Get cost history for a specific deployment.

        Args:
            org_id: Organisation UUID
            deployment_id: Deployment UUID
            months: Number of months to retrieve

        Returns:
            List of monthly costs for this deployment
        """
        all_costs = self.list_costs_by_org(org_id, limit=months)

        deployment_cost_history = []

        for cost_record in all_costs:
            deployment_costs = cost_record.get("deployment_costs", {})

            if deployment_id in deployment_costs:
                deployment_cost_history.append({
                    "month": cost_record["month"],
                    "costs_by_service": deployment_costs[deployment_id],
                    "total": sum(deployment_costs[deployment_id].values())
                })

        return deployment_cost_history

    def calculate_yearly_total(
        self,
        org_id: UUID,
        year: int
    ) -> dict[str, float]:
        """Calculate total AWS costs for a year.

        Args:
            org_id: Organisation UUID
            year: Year (e.g., 2026)

        Returns:
            Dict with totals
        """
        total_aws_costs = 0.0
        total_overcloud_fees = 0.0

        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            cost_record = self.get_monthly_costs(org_id, month_str)

            if cost_record:
                total_aws_costs += cost_record.get("total_aws_costs", 0.0)
                total_overcloud_fees += cost_record.get("overcloud_percentage_fee", 0.0)

        return {
            "year": year,
            "total_aws_costs": round(total_aws_costs, 2),
            "total_overcloud_fees": round(total_overcloud_fees, 2),
            "total": round(total_aws_costs + total_overcloud_fees, 2)
        }

    def get_top_spending_deployments(
        self,
        org_id: UUID,
        month: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get top spending deployments for a month.

        Args:
            org_id: Organisation UUID
            month: Month in format YYYY-MM
            limit: Number of top deployments to return

        Returns:
            List of deployments sorted by cost (highest first)
        """
        cost_record = self.get_monthly_costs(org_id, month)

        if not cost_record:
            return []

        deployment_costs = cost_record.get("deployment_costs", {})

        # Calculate total cost per deployment
        deployment_totals = []
        for deployment_id, costs_by_service in deployment_costs.items():
            total = sum(costs_by_service.values())
            deployment_totals.append({
                "deployment_id": deployment_id,
                "total_cost": round(total, 2),
                "costs_by_service": costs_by_service
            })

        # Sort by cost (descending)
        deployment_totals.sort(key=lambda x: x["total_cost"], reverse=True)

        return deployment_totals[:limit]

    def get_cost_trend(
        self,
        org_id: UUID,
        months: int = 6
    ) -> list[dict[str, Any]]:
        """Get cost trend over time.

        Args:
            org_id: Organisation UUID
            months: Number of months to analyze

        Returns:
            List of monthly cost data
        """
        cost_records = self.list_costs_by_org(org_id, limit=months)

        trend = []
        for record in reversed(cost_records):  # Chronological order
            trend.append({
                "month": record["month"],
                "aws_costs": round(record.get("total_aws_costs", 0.0), 2),
                "overcloud_fee": round(record.get("overcloud_percentage_fee", 0.0), 2),
                "total": round(
                    record.get("total_aws_costs", 0.0) +
                    record.get("overcloud_percentage_fee", 0.0),
                    2
                )
            })

        return trend
