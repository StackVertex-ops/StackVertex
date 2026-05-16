"""Unit Tests für Cost Calculator Service.

Testet alle Cost Calculation Functions.
"""

import pytest
from decimal import Decimal

from app.services.cost_calculator import (
    calculate_ec2_cost,
    calculate_rds_cost,
    calculate_s3_cost,
    calculate_cloudfront_cost,
    calculate_lambda_cost,
    calculate_alb_cost,
    calculate_nat_gateway_cost,
    calculate_route53_cost,
    calculate_blueprint_cost,
    CostItem,
    CostBreakdown,
)


class TestEC2Cost:
    """Tests für EC2 Cost Calculation"""

    def test_calculate_ec2_cost_single_instance(self):
        """Test EC2 cost für single instance"""
        cost_item = calculate_ec2_cost("t3.small", count=1)

        assert cost_item.service == "EC2"
        assert cost_item.resource == "t3.small x 1"
        assert cost_item.unit == "hour"
        assert cost_item.quantity == Decimal("730")  # 730 hours/month
        # t3.small: $0.0208/h * 730h = $15.184
        assert cost_item.total == Decimal("0.0208") * Decimal("730")

    def test_calculate_ec2_cost_multiple_instances(self):
        """Test EC2 cost für multiple instances"""
        cost_item = calculate_ec2_cost("t3.medium", count=3)

        assert cost_item.resource == "t3.medium x 3"
        assert cost_item.quantity == Decimal("2190")  # 730 * 3
        # t3.medium: $0.0416/h * 730h * 3 = $91.008
        assert cost_item.total == Decimal("0.0416") * Decimal("730") * Decimal("3")

    def test_calculate_ec2_cost_invalid_instance_type(self):
        """Test EC2 cost mit invalid instance type"""
        with pytest.raises(ValueError, match="Unknown instance type"):
            calculate_ec2_cost("invalid.type")


class TestRDSCost:
    """Tests für RDS Cost Calculation"""

    def test_calculate_rds_cost_basic(self):
        """Test RDS cost basic configuration"""
        cost_items = calculate_rds_cost(
            instance_class="db.t3.micro",
            engine="postgres",
            storage_gb=20,
            storage_type="gp3",
            multi_az=False
        )

        assert len(cost_items) == 2  # Instance + Storage
        assert cost_items[0].service == "RDS"
        assert "db.t3.micro" in cost_items[0].resource
        assert cost_items[1].resource == "Storage (gp3)"

    def test_calculate_rds_cost_multi_az(self):
        """Test RDS cost mit Multi-AZ"""
        cost_items = calculate_rds_cost(
            instance_class="db.t3.small",
            engine="mysql",
            storage_gb=50,
            storage_type="gp3",
            multi_az=True
        )

        # Multi-AZ verdoppelt Storage und verwendet Multi-AZ pricing
        storage_item = next(item for item in cost_items if "Storage" in item.resource)
        assert storage_item.quantity == Decimal("100")  # 50 * 2 (Multi-AZ)

    def test_calculate_rds_cost_with_extra_backups(self):
        """Test RDS cost mit extended backup retention"""
        cost_items = calculate_rds_cost(
            instance_class="db.t3.micro",
            engine="postgres",
            storage_gb=20,
            backup_retention_days=14  # > 7 days
        )

        # Sollte Backup Storage Item enthalten
        assert len(cost_items) == 3  # Instance + Storage + Backups
        backup_item = next(item for item in cost_items if "Backup" in item.resource)
        assert backup_item.service == "RDS"

    def test_calculate_rds_cost_invalid_instance_class(self):
        """Test RDS cost mit invalid instance class"""
        with pytest.raises(ValueError, match="Unknown RDS instance class"):
            calculate_rds_cost("db.invalid.class", "postgres", 20)


class TestS3Cost:
    """Tests für S3 Cost Calculation"""

    def test_calculate_s3_cost_basic(self):
        """Test S3 cost basic configuration"""
        cost_items = calculate_s3_cost(
            storage_gb=100,
            storage_class="STANDARD",
            monthly_requests=100000,
            data_transfer_gb=10
        )

        assert len(cost_items) == 3  # Storage + Requests + Transfer
        assert cost_items[0].resource == "Storage (STANDARD)"
        assert cost_items[1].resource == "Requests"
        assert cost_items[2].resource == "Data Transfer Out"

    def test_calculate_s3_cost_no_transfer(self):
        """Test S3 cost ohne data transfer (< 1GB free)"""
        cost_items = calculate_s3_cost(
            storage_gb=50,
            monthly_requests=50000,
            data_transfer_gb=0.5  # < 1GB (free)
        )

        # Sollte kein Transfer Item haben
        assert len(cost_items) == 2  # Nur Storage + Requests
        assert all("Transfer" not in item.resource for item in cost_items)


class TestCloudFrontCost:
    """Tests für CloudFront Cost Calculation"""

    def test_calculate_cloudfront_cost_basic(self):
        """Test CloudFront cost basic"""
        cost_items = calculate_cloudfront_cost(
            data_transfer_gb=1000,
            price_class="PriceClass_100",
            monthly_requests=1000000
        )

        assert len(cost_items) == 2  # Data Transfer + Requests
        assert cost_items[0].resource == "Data Transfer"
        assert cost_items[1].resource == "HTTPS Requests"

    def test_calculate_cloudfront_cost_tiered_pricing(self):
        """Test CloudFront cost mit tiered pricing"""
        # > 10TB (10240 GB) sollte tiered pricing verwenden
        cost_items = calculate_cloudfront_cost(
            data_transfer_gb=15000,  # 15 TB
            price_class="PriceClass_100"
        )

        transfer_item = cost_items[0]
        # Tiered: 10TB @ $0.085 + 5TB @ $0.080
        expected = Decimal("0.085") * Decimal("10240") + Decimal("0.080") * Decimal("4760")
        assert transfer_item.total == expected


class TestLambdaCost:
    """Tests für Lambda Cost Calculation"""

    def test_calculate_lambda_cost_within_free_tier(self):
        """Test Lambda cost innerhalb free tier"""
        cost_item = calculate_lambda_cost(
            invocations_per_month=500000,  # < 1M free
            avg_duration_ms=100,
            memory_mb=128
        )

        # Sollte nur compute cost haben (requests free)
        assert cost_item.service == "Lambda"
        assert cost_item.total >= Decimal("0")  # Free tier kann total reduzieren

    def test_calculate_lambda_cost_exceeding_free_tier(self):
        """Test Lambda cost über free tier"""
        cost_item = calculate_lambda_cost(
            invocations_per_month=5000000,  # > 1M free
            avg_duration_ms=500,
            memory_mb=512
        )

        # Sollte request + compute cost haben
        assert cost_item.total > Decimal("0")


class TestALBCost:
    """Tests für ALB Cost Calculation"""

    def test_calculate_alb_cost(self):
        """Test ALB cost"""
        cost_item = calculate_alb_cost(lcu_per_hour=1.0)

        assert cost_item.service == "ALB"
        assert cost_item.resource == "Application Load Balancer"
        # Hourly: $0.0225 + $0.008 * 1 = $0.0305
        # Monthly: $0.0305 * 730 = $22.265
        expected = (Decimal("0.0225") + Decimal("0.008")) * Decimal("730")
        assert cost_item.total == expected


class TestNATGatewayCost:
    """Tests für NAT Gateway Cost Calculation"""

    def test_calculate_nat_gateway_cost(self):
        """Test NAT Gateway cost"""
        cost_items = calculate_nat_gateway_cost(data_processed_gb=1000)

        assert len(cost_items) == 2  # Hourly + Data Processing
        assert cost_items[0].resource == "NAT Gateway (hourly)"
        assert cost_items[1].resource == "NAT Gateway (data processing)"


class TestRoute53Cost:
    """Tests für Route53 Cost Calculation"""

    def test_calculate_route53_cost_basic(self):
        """Test Route53 cost basic"""
        cost_items = calculate_route53_cost(
            hosted_zones=1,
            monthly_queries=500000  # < 1B free
        )

        assert len(cost_items) == 1  # Nur Hosted Zone (queries free)
        assert cost_items[0].resource == "Hosted Zone"

    def test_calculate_route53_cost_high_queries(self):
        """Test Route53 cost mit vielen queries"""
        cost_items = calculate_route53_cost(
            hosted_zones=2,
            monthly_queries=2000000000  # > 1B (billable)
        )

        assert len(cost_items) == 2  # Hosted Zone + Queries
        assert cost_items[1].resource == "DNS Queries"


class TestBlueprintCost:
    """Tests für Blueprint Cost Calculation"""

    def test_calculate_blueprint_cost_static_website(self):
        """Test static website blueprint cost"""
        breakdown = calculate_blueprint_cost(
            blueprint_id="static-website",
            configuration={
                "storage_gb": 50,
                "traffic_gb": 1000,
                "monthly_requests": 1000000,
                "domain_name": "example.com"
            }
        )

        assert isinstance(breakdown, CostBreakdown)
        assert breakdown.currency == "USD"
        assert breakdown.period == "monthly"
        assert len(breakdown.items) > 0
        assert breakdown.total > Decimal("0")
        # Sollte S3, CloudFront, Route53 enthalten
        services = {item.service for item in breakdown.items}
        assert "S3" in services
        assert "CloudFront" in services
        assert "Route53" in services

    def test_calculate_blueprint_cost_three_tier_web(self):
        """Test three-tier web app blueprint cost"""
        breakdown = calculate_blueprint_cost(
            blueprint_id="three-tier-web",
            configuration={
                "ec2_instance_type": "t3.small",
                "min_instances": 2,
                "rds_instance_class": "db.t3.micro",
                "rds_engine": "postgres",
                "rds_allocated_storage": 20,
                "rds_multi_az": False
            }
        )

        assert len(breakdown.items) > 0
        # Sollte EC2, RDS, ALB, VPC enthalten
        services = {item.service for item in breakdown.items}
        assert "EC2" in services
        assert "RDS" in services
        assert "ALB" in services
        assert "VPC" in services  # NAT Gateway

    def test_calculate_blueprint_cost_serverless_api(self):
        """Test serverless API blueprint cost"""
        breakdown = calculate_blueprint_cost(
            blueprint_id="serverless-api",
            configuration={
                "lambda_invocations_per_month": 1000000,
                "lambda_memory_mb": 512,
                "lambda_avg_duration_ms": 200,
                "api_requests_per_month": 1000000
            }
        )

        assert len(breakdown.items) > 0
        # Sollte Lambda, API Gateway enthalten
        services = {item.service for item in breakdown.items}
        assert "Lambda" in services
        assert "API Gateway" in services

    def test_calculate_blueprint_cost_unknown_blueprint(self):
        """Test unknown blueprint (sollte $0 zurückgeben)"""
        breakdown = calculate_blueprint_cost(
            blueprint_id="unknown-blueprint",
            configuration={}
        )

        assert breakdown.total == Decimal("0")
        assert len(breakdown.items) == 0
        assert any("not recognized" in assumption for assumption in breakdown.assumptions)

    def test_calculate_blueprint_cost_invalid_ec2_type(self):
        """Test blueprint mit invalid EC2 instance type"""
        with pytest.raises(ValueError, match="Unknown instance type"):
            calculate_blueprint_cost(
                blueprint_id="three-tier-web",
                configuration={
                    "ec2_instance_type": "invalid.type",
                    "min_instances": 2
                }
            )


class TestCostModels:
    """Tests für Pydantic Models"""

    def test_cost_item_model(self):
        """Test CostItem Pydantic model"""
        item = CostItem(
            service="EC2",
            resource="t3.small",
            amount=Decimal("0.0208"),
            unit="hour",
            quantity=Decimal("730"),
            total=Decimal("15.184")
        )

        assert item.service == "EC2"
        assert item.total == Decimal("15.184")

    def test_cost_breakdown_model(self):
        """Test CostBreakdown Pydantic model"""
        items = [
            CostItem(
                service="EC2",
                resource="t3.small",
                amount=Decimal("0.0208"),
                unit="hour",
                quantity=Decimal("730"),
                total=Decimal("15.184")
            )
        ]

        breakdown = CostBreakdown(
            items=items,
            subtotal=Decimal("15.184"),
            tax=Decimal("0"),
            total=Decimal("15.184"),
            assumptions=["Test assumption"]
        )

        assert len(breakdown.items) == 1
        assert breakdown.total == Decimal("15.184")
        assert breakdown.currency == "USD"
        assert breakdown.period == "monthly"
