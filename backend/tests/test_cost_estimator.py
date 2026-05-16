"""Tests für CostEstimator.

Testet Cost Calculation für Components.
"""

import pytest
from decimal import Decimal

from app.services.cost_estimator import CostEstimator, ComponentCost, CostEstimate


class TestCostEstimate:
    """Tests für CostEstimate Dataclass."""

    def test_create_empty_estimate(self):
        """Test: Leere Cost Estimate."""
        estimate = CostEstimate(
            total_hourly=Decimal("0"),
            total_monthly=Decimal("0"),
            total_yearly=Decimal("0"),
        )

        assert estimate.total_hourly == Decimal("0")
        assert estimate.total_monthly == Decimal("0")
        assert len(estimate.components) == 0

    def test_add_component_cost(self):
        """Test: Component Cost hinzufügen."""
        estimate = CostEstimate(
            total_hourly=Decimal("0"),
            total_monthly=Decimal("0"),
            total_yearly=Decimal("0"),
        )

        component_cost = ComponentCost(
            component_id="test",
            component_type="ec2",
            component_name="Test",
            hourly_cost=Decimal("0.10"),
            monthly_cost=Decimal("73.00"),
        )

        estimate.add_component(component_cost)

        assert estimate.total_hourly == Decimal("0.10")
        assert estimate.total_monthly == Decimal("73.00")
        assert len(estimate.components) == 1


class TestCostEstimator:
    """Tests für CostEstimator."""

    def test_create_estimator(self):
        """Test: Estimator erstellen."""
        estimator = CostEstimator()

        assert estimator.pricing is not None

    def test_estimate_empty_architecture(self, sample_architecture_minimal):
        """Test: Architecture ohne Components."""
        estimator = CostEstimator()

        # Ensure architecture key exists
        if "architecture" not in sample_architecture_minimal:
            sample_architecture_minimal["architecture"] = {}
        if "components" not in sample_architecture_minimal["architecture"]:
            sample_architecture_minimal["architecture"]["components"] = []

        estimate = estimator.estimate_architecture_cost(sample_architecture_minimal)

        assert estimate.total_hourly == Decimal("0")
        assert estimate.total_monthly == Decimal("0")
        assert len(estimate.components) == 0

    def test_estimate_ec2_cost(self, sample_architecture_minimal):
        """Test: EC2 Component Cost."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "web_server",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {
                    "instance_type": "t3.micro"
                }
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert estimate.total_monthly > 0
        assert len(estimate.components) == 1
        assert estimate.components[0].component_type == "ec2"

    def test_estimate_rds_cost(self, sample_architecture_minimal):
        """Test: RDS Component Cost."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "database",
                "type": "rds",
                "name": "Database",
                "configuration": {
                    "instance_class": "db.t3.micro",
                    "allocated_storage": 20,
                    "storage_type": "gp3"
                }
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert estimate.total_monthly > 0
        assert len(estimate.components) == 1

        # RDS sollte breakdown für instance + storage haben
        component = estimate.components[0]
        assert "instance" in component.breakdown
        assert "storage" in component.breakdown

    def test_estimate_s3_cost(self, sample_architecture_minimal):
        """Test: S3 Component Cost."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "storage",
                "type": "s3",
                "name": "Storage Bucket",
                "configuration": {
                    "estimated_storage_gb": 100,
                    "storage_class": "standard"
                }
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert estimate.total_monthly > 0
        assert len(estimate.components) == 1
        assert estimate.components[0].component_type == "s3"

    def test_estimate_lambda_cost(self, sample_architecture_minimal):
        """Test: Lambda Component Cost."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "function",
                "type": "lambda",
                "name": "Lambda Function",
                "configuration": {
                    "estimated_monthly_requests": 2000000,
                    "memory_size": 128,
                    "average_duration_seconds": 0.2
                }
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert estimate.total_monthly >= 0  # Could be 0 with free tier
        assert len(estimate.components) == 1

        # Lambda sollte breakdown für requests + compute haben
        component = estimate.components[0]
        assert "requests" in component.breakdown
        assert "compute" in component.breakdown

    def test_estimate_multiple_components(self, sample_architecture_minimal):
        """Test: Architecture mit mehreren Components."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "web",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {"instance_type": "t3.micro"}
            },
            {
                "id": "db",
                "type": "rds",
                "name": "Database",
                "configuration": {
                    "instance_class": "db.t3.micro",
                    "allocated_storage": 20
                }
            },
            {
                "id": "storage",
                "type": "s3",
                "name": "Storage",
                "configuration": {"estimated_storage_gb": 50}
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert len(estimate.components) == 3
        assert estimate.total_monthly > 0

        # Breakdown by type sollte alle Types enthalten
        assert "ec2" in estimate.breakdown_by_type
        assert "rds" in estimate.breakdown_by_type
        assert "s3" in estimate.breakdown_by_type

    def test_estimate_unsupported_component_type(self, sample_architecture_minimal):
        """Test: Unsupported Component Type gibt $0 zurück."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "unknown",
                "type": "unsupported_type",
                "name": "Unknown",
                "configuration": {}
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert len(estimate.components) == 1
        assert estimate.total_monthly == Decimal("0")

    def test_estimate_with_custom_region(self, sample_architecture_minimal):
        """Test: Cost Estimation mit custom Region."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "metadata" not in arch:
            arch["metadata"] = {}
        arch["metadata"]["region"] = "eu-central-1"
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "web",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {"instance_type": "t3.micro"}
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        assert estimate.total_monthly > 0

    def test_yearly_cost_calculation(self, sample_architecture_minimal):
        """Test: Yearly Cost wird korrekt berechnet."""
        estimator = CostEstimator()

        arch = sample_architecture_minimal.copy()
        if "architecture" not in arch:
            arch["architecture"] = {}
        arch["architecture"]["components"] = [
            {
                "id": "web",
                "type": "ec2",
                "name": "Web",
                "configuration": {"instance_type": "t3.micro"}
            }
        ]

        estimate = estimator.estimate_architecture_cost(arch)

        # Yearly = Monthly * 12
        assert estimate.total_yearly == estimate.total_monthly * 12
