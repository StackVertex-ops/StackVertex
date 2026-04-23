"""Cost Estimator Service.

Berechnet Kosten für Architecture Deployments.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass, field

from app.services.pricing_data import PricingDataLoader

logger = logging.getLogger(__name__)


@dataclass
class ComponentCost:
    """Kosten für ein einzelnes Component."""

    component_id: str
    component_type: str
    component_name: str
    hourly_cost: Decimal
    monthly_cost: Decimal
    breakdown: Dict[str, Decimal] = field(default_factory=dict)


@dataclass
class CostEstimate:
    """Gesamt-Kostenabschätzung für Architecture."""

    total_hourly: Decimal
    total_monthly: Decimal
    total_yearly: Decimal
    currency: str = "USD"
    components: List[ComponentCost] = field(default_factory=list)
    breakdown_by_type: Dict[str, Decimal] = field(default_factory=dict)

    def add_component(self, component_cost: ComponentCost) -> None:
        """Fügt Component-Kosten hinzu."""
        self.components.append(component_cost)
        self.total_hourly += component_cost.hourly_cost
        self.total_monthly += component_cost.monthly_cost
        self.total_yearly = self.total_monthly * 12

        # Update breakdown by type
        comp_type = component_cost.component_type
        if comp_type not in self.breakdown_by_type:
            self.breakdown_by_type[comp_type] = Decimal("0")
        self.breakdown_by_type[comp_type] += component_cost.monthly_cost


class CostEstimator:
    """Berechnet Architecture Kosten basierend auf Components."""

    HOURS_PER_MONTH = 730  # Durchschnitt (365 * 24 / 12)

    def __init__(self, pricing_loader: Optional[PricingDataLoader] = None):
        """Initialisiert Cost Estimator.

        Args:
            pricing_loader: PricingDataLoader Instance (optional)
        """
        self.pricing = pricing_loader or PricingDataLoader()

    def estimate_architecture_cost(
        self,
        architecture_json: Dict[str, Any],
        period: str = "monthly"
    ) -> CostEstimate:
        """Berechnet Gesamtkosten einer Architecture.

        Args:
            architecture_json: Architecture Definition
            period: Berechnungs-Period ("hourly", "monthly", "yearly")

        Returns:
            CostEstimate mit Details
        """
        logger.info("Starting cost estimation...")

        # Extract metadata
        metadata = architecture_json.get("metadata", {})
        region = metadata.get("region", "us-east-1")

        # Initialize estimate
        estimate = CostEstimate(
            total_hourly=Decimal("0"),
            total_monthly=Decimal("0"),
            total_yearly=Decimal("0"),
        )

        # Extract components
        components = architecture_json.get("architecture", {}).get("components", [])

        if not components:
            logger.warning("No components found in architecture")
            return estimate

        # Calculate cost per component
        for component in components:
            component_type = component.get("type")
            component_id = component.get("id", "unknown")
            component_name = component.get("name", component_id)
            config = component.get("configuration", {})

            try:
                component_cost = self._estimate_component_cost(
                    component_type, component_id, component_name, config, region
                )

                if component_cost:
                    estimate.add_component(component_cost)
                    logger.debug(
                        f"Component {component_id}: "
                        f"${component_cost.monthly_cost:.2f}/month"
                    )

            except Exception as e:
                logger.error(
                    f"Error estimating cost for component {component_id}: {e}"
                )
                # Continue with other components

        logger.info(
            f"Total estimated cost: ${estimate.total_monthly:.2f}/month "
            f"(${estimate.total_yearly:.2f}/year)"
        )

        return estimate

    def _estimate_component_cost(
        self,
        component_type: str,
        component_id: str,
        component_name: str,
        config: Dict[str, Any],
        region: str
    ) -> Optional[ComponentCost]:
        """Berechnet Kosten für ein einzelnes Component.

        Args:
            component_type: Type des Components
            component_id: Component ID
            component_name: Component Name
            config: Component Configuration
            region: AWS Region

        Returns:
            ComponentCost oder None
        """
        # Dispatch zu service-spezifischem Calculator
        if component_type in ["ec2", "compute", "instance"]:
            return self._estimate_ec2_cost(component_id, component_name, config, region)

        elif component_type in ["rds", "database", "db"]:
            return self._estimate_rds_cost(component_id, component_name, config, region)

        elif component_type in ["s3", "storage", "bucket"]:
            return self._estimate_s3_cost(component_id, component_name, config, region)

        elif component_type in ["lambda", "function"]:
            return self._estimate_lambda_cost(component_id, component_name, config, region)

        else:
            # Unsupported component type - return zero cost
            logger.warning(f"Unsupported component type for costing: {component_type}")
            return ComponentCost(
                component_id=component_id,
                component_type=component_type,
                component_name=component_name,
                hourly_cost=Decimal("0"),
                monthly_cost=Decimal("0"),
            )

    def _estimate_ec2_cost(
        self,
        component_id: str,
        component_name: str,
        config: Dict[str, Any],
        region: str
    ) -> ComponentCost:
        """Berechnet EC2 Kosten.

        Args:
            component_id: Component ID
            component_name: Component Name
            config: Component Configuration
            region: AWS Region

        Returns:
            ComponentCost
        """
        instance_type = config.get("instance_type", "t3.micro")
        hourly_price = self.pricing.get_ec2_price(instance_type, region)

        if hourly_price is None:
            logger.warning(f"EC2 price not found for {instance_type}, using default")
            hourly_price = Decimal("0.0104")  # t3.micro default

        monthly_cost = hourly_price * self.HOURS_PER_MONTH

        return ComponentCost(
            component_id=component_id,
            component_type="ec2",
            component_name=component_name,
            hourly_cost=hourly_price,
            monthly_cost=monthly_cost,
            breakdown={
                "compute": monthly_cost,
            }
        )

    def _estimate_rds_cost(
        self,
        component_id: str,
        component_name: str,
        config: Dict[str, Any],
        region: str
    ) -> ComponentCost:
        """Berechnet RDS Kosten.

        Args:
            component_id: Component ID
            component_name: Component Name
            config: Component Configuration
            region: AWS Region

        Returns:
            ComponentCost
        """
        instance_class = config.get("instance_class", "db.t3.micro")
        allocated_storage = config.get("allocated_storage", 20)  # GB
        storage_type = config.get("storage_type", "gp3")

        # Instance cost
        instance_hourly = self.pricing.get_rds_price(instance_class, region)
        if instance_hourly is None:
            logger.warning(f"RDS price not found for {instance_class}, using default")
            instance_hourly = Decimal("0.017")  # db.t3.micro default

        # Storage cost (per hour)
        storage_hourly = self.pricing.get_rds_storage_price(storage_type, region)
        storage_hourly_total = storage_hourly * Decimal(str(allocated_storage))

        # Total
        total_hourly = instance_hourly + storage_hourly_total
        total_monthly = total_hourly * self.HOURS_PER_MONTH

        return ComponentCost(
            component_id=component_id,
            component_type="rds",
            component_name=component_name,
            hourly_cost=total_hourly,
            monthly_cost=total_monthly,
            breakdown={
                "instance": instance_hourly * self.HOURS_PER_MONTH,
                "storage": storage_hourly_total * self.HOURS_PER_MONTH,
            }
        )

    def _estimate_s3_cost(
        self,
        component_id: str,
        component_name: str,
        config: Dict[str, Any],
        region: str
    ) -> ComponentCost:
        """Berechnet S3 Kosten.

        Args:
            component_id: Component ID
            component_name: Component Name
            config: Component Configuration
            region: AWS Region

        Returns:
            ComponentCost
        """
        storage_gb = config.get("estimated_storage_gb", 100)  # Default 100 GB
        storage_class = config.get("storage_class", "standard")

        # Storage cost (per month)
        storage_price_per_gb = self.pricing.get_s3_price(storage_class, region)
        monthly_storage_cost = storage_price_per_gb * Decimal(str(storage_gb))

        # S3 hat keine hourly cost (nur monthly)
        hourly_cost = monthly_storage_cost / Decimal(str(self.HOURS_PER_MONTH))

        return ComponentCost(
            component_id=component_id,
            component_type="s3",
            component_name=component_name,
            hourly_cost=hourly_cost,
            monthly_cost=monthly_storage_cost,
            breakdown={
                "storage": monthly_storage_cost,
            }
        )

    def _estimate_lambda_cost(
        self,
        component_id: str,
        component_name: str,
        config: Dict[str, Any],
        region: str
    ) -> ComponentCost:
        """Berechnet Lambda Kosten.

        Args:
            component_id: Component ID
            component_name: Component Name
            config: Component Configuration
            region: AWS Region

        Returns:
            ComponentCost
        """
        # Geschätzte monatliche Invocations
        monthly_requests = config.get("estimated_monthly_requests", 1000000)

        # Memory (MB)
        memory_mb = config.get("memory_size", 128)

        # Durchschnittliche Duration (seconds)
        avg_duration = config.get("average_duration_seconds", 0.2)

        # Get pricing
        lambda_pricing = self.pricing.get_lambda_price(region)

        # Request costs (after free tier)
        free_tier_requests = 1000000
        billable_requests = max(0, monthly_requests - free_tier_requests)
        request_cost = (
            Decimal(str(billable_requests)) / Decimal("1000000")
        ) * lambda_pricing["requests_per_million"]

        # Compute costs (GB-seconds)
        gb_seconds = (
            Decimal(str(monthly_requests)) *
            Decimal(str(avg_duration)) *
            (Decimal(str(memory_mb)) / Decimal("1024"))
        )

        free_tier_gb_seconds = 400000
        billable_gb_seconds = max(0, gb_seconds - free_tier_gb_seconds)
        compute_cost = billable_gb_seconds * lambda_pricing["compute_per_gb_second"]

        # Total monthly cost
        monthly_cost = request_cost + compute_cost
        hourly_cost = monthly_cost / Decimal(str(self.HOURS_PER_MONTH))

        return ComponentCost(
            component_id=component_id,
            component_type="lambda",
            component_name=component_name,
            hourly_cost=hourly_cost,
            monthly_cost=monthly_cost,
            breakdown={
                "requests": request_cost,
                "compute": compute_cost,
            }
        )
