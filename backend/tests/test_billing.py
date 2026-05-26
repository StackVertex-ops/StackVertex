"""Unit Tests für Billing System.

Tests für:
- Subscription Repository
- AWS Cost Repository
- Invoice Repository
- Invoice Generator
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from app.models.billing import (
    BillingTier,
    BillingPeriod,
    BillingStatus,
    InvoiceStatus,
    get_tier_config,
    calculate_monthly_cost_example
)
from app.repositories.subscription import SubscriptionRepository
from app.repositories.aws_cost import AWSCostRepository
from app.repositories.invoice import InvoiceRepository
from app.services.invoice_generator import InvoiceGenerator


class TestBillingModels:
    """Tests für Billing Models."""

    def test_tier_config_all_tiers(self):
        """Test dass alle Tiers gültige Configs haben."""
        for tier in [BillingTier.STARTER, BillingTier.PRO, BillingTier.ENTERPRISE, BillingTier.PAY_AS_YOU_GO]:
            config = get_tier_config(tier)

            assert "base_price_monthly" in config
            assert "base_price_annual" in config
            assert "aws_cost_percentage" in config
            assert "limits" in config
            assert "features" in config

    def test_tier_pricing_starter(self):
        """Test STARTER Tier Pricing."""
        config = get_tier_config(BillingTier.STARTER)

        assert config["base_price_monthly"] == 10.00
        assert config["aws_cost_percentage"] == 15
        assert config["limits"]["max_deployments"] == 3

    def test_tier_pricing_pro(self):
        """Test PRO Tier Pricing."""
        config = get_tier_config(BillingTier.PRO)

        assert config["base_price_monthly"] == 50.00
        assert config["aws_cost_percentage"] == 10
        assert config["limits"]["max_deployments"] == 20

    def test_tier_pricing_enterprise(self):
        """Test ENTERPRISE Tier Pricing."""
        config = get_tier_config(BillingTier.ENTERPRISE)

        assert config["base_price_monthly"] == 250.00
        assert config["aws_cost_percentage"] == 5
        assert config["limits"]["max_deployments"] == -1  # unlimited

    def test_cost_calculation_pro_tier(self):
        """Test Cost Calculation für PRO Tier."""
        result = calculate_monthly_cost_example(
            tier=BillingTier.PRO,
            aws_costs=200.00,
            num_deployments=0
        )

        assert float(result["base_price"]) == 50.00
        assert float(result["aws_costs"]) == 200.00
        assert result["markup_percentage"] == 10
        assert float(result["markup_fee"]) == 20.00  # 10% of 200
        assert float(result["deployment_fees"]) == 0.00
        assert float(result["subtotal"]) == 70.00  # 50 + 20
        assert float(result["tax"]) == pytest.approx(13.30, rel=0.01)  # 19% VAT
        assert float(result["total"]) == pytest.approx(83.30, rel=0.01)

    def test_cost_calculation_payg_tier(self):
        """Test Cost Calculation für PAYG Tier mit Deployments."""
        result = calculate_monthly_cost_example(
            tier=BillingTier.PAY_AS_YOU_GO,
            aws_costs=50.00,
            num_deployments=3
        )

        assert result["base_price"] == 0.00
        assert result["aws_costs"] == 50.00
        assert result["markup_percentage"] == 20
        assert result["markup_fee"] == 10.00  # 20% of 50
        assert result["deployment_fees"] == 15.00  # 3 * 5
        assert result["subtotal"] == 25.00  # 0 + 10 + 15

    def test_annual_pricing_discount(self):
        """Test dass Annual Pricing günstiger ist."""
        config = get_tier_config(BillingTier.PRO)

        monthly_annual_cost = config["base_price_monthly"] * 12
        annual_cost = config["base_price_annual"]

        assert annual_cost < monthly_annual_cost
        # 2 Monate gratis = ~17% discount
        discount_percent = float((monthly_annual_cost - annual_cost) / monthly_annual_cost) * 100
        assert discount_percent == pytest.approx(16.67, rel=0.1)


# Note: mock_dynamodb_table fixture is imported from conftest.py


class TestSubscriptionRepository:
    """Tests für Subscription Repository."""

    def test_create_subscription(self, mock_dynamodb_table):
        """Test Subscription Creation."""
        repo = SubscriptionRepository(table=mock_dynamodb_table)
        org_id = uuid4()

        subscription = repo.create(
            org_id=org_id,
            tier=BillingTier.PRO,
            billing_period=BillingPeriod.MONTHLY
        )

        assert subscription["org_id"] == str(org_id)
        assert subscription["tier"] == BillingTier.PRO.value
        assert subscription["billing_period"] == BillingPeriod.MONTHLY.value
        assert subscription["status"] == BillingStatus.ACTIVE.value
        # BaseRepository converts floats to Decimal for DynamoDB
        assert float(subscription["base_price"]) == 50.00
        assert subscription["aws_cost_percentage"] == 10

        # Verify item was stored in DynamoDB by retrieving it
        retrieved = repo.get_by_org(org_id)
        assert retrieved is not None
        assert retrieved["org_id"] == str(org_id)

    def test_create_subscription_with_trial(self, mock_dynamodb_table):
        """Test Subscription Creation mit Trial Period."""
        repo = SubscriptionRepository(table=mock_dynamodb_table)
        org_id = uuid4()

        subscription = repo.create(
            org_id=org_id,
            tier=BillingTier.PRO,
            billing_period=BillingPeriod.MONTHLY,
            trial_days=14
        )

        assert subscription["status"] == BillingStatus.TRIALING.value
        assert subscription["trial_end"] is not None

        # Verify trial end is ~14 days from now
        trial_end = datetime.fromisoformat(subscription["trial_end"])
        expected_trial_end = datetime.utcnow() + timedelta(days=14)
        assert abs((trial_end - expected_trial_end).total_seconds()) < 60  # Within 1 minute

    def test_update_tier(self, mock_dynamodb_table):
        """Test Tier Update (Upgrade/Downgrade)."""
        repo = SubscriptionRepository(table=mock_dynamodb_table)
        org_id = uuid4()

        # Create initial subscription
        repo.create(
            org_id=org_id,
            tier=BillingTier.STARTER,
            billing_period=BillingPeriod.MONTHLY
        )

        # Upgrade to PRO tier
        updated = repo.update_tier(org_id, BillingTier.PRO)

        assert updated["tier"] == BillingTier.PRO.value
        assert float(updated["base_price"]) == 50.00
        assert updated["aws_cost_percentage"] == 10

        # Verify persistence
        retrieved = repo.get_by_org(org_id)
        assert retrieved["tier"] == BillingTier.PRO.value


class TestAWSCostRepository:
    """Tests für AWS Cost Repository."""

    def test_store_monthly_costs(self, mock_dynamodb_table):
        """Test Storing Monthly Costs."""
        repo = AWSCostRepository(table=mock_dynamodb_table)
        org_id = uuid4()

        deployment_costs = {
            "deployment-1": {
                "EC2": 50.00,
                "RDS": 80.00,
                "S3": 5.00
            },
            "deployment-2": {
                "EC2": 30.00,
                "ALB": 20.00
            }
        }

        total_aws_costs = 185.00
        percentage_fee = 18.50  # 10% of 185

        cost_record = repo.store_monthly_costs(
            org_id=org_id,
            month="2026-05",
            deployment_costs=deployment_costs,
            total_aws_costs=total_aws_costs,
            percentage_fee=percentage_fee
        )

        assert cost_record["org_id"] == str(org_id)
        assert cost_record["month"] == "2026-05"
        # DynamoDB stores numbers as Decimal
        assert float(cost_record["total_aws_costs"]) == total_aws_costs
        assert float(cost_record["stackvertex_percentage_fee"]) == percentage_fee

        # Verify persistence
        retrieved = repo.get_monthly_costs(org_id, "2026-05")
        assert retrieved is not None
        assert float(retrieved["total_aws_costs"]) == total_aws_costs


class TestInvoiceRepository:
    """Tests für Invoice Repository."""

    def test_create_invoice(self, mock_dynamodb_table):
        """Test Invoice Creation."""
        repo = InvoiceRepository(table=mock_dynamodb_table)
        org_id = uuid4()

        line_items = [
            {
                "description": "StackVertex PRO - Base Fee",
                "amount": 50.00,
                "currency": "EUR"
            },
            {
                "description": "AWS Infrastructure Costs (10% markup)",
                "amount": 20.00,
                "currency": "EUR"
            }
        ]

        invoice = repo.create(
            org_id=org_id,
            invoice_number="INV-2026-05-001",
            period_start=datetime(2026, 5, 1),
            period_end=datetime(2026, 6, 1),
            line_items=line_items,
            subtotal=70.00,
            tax=13.30,
            total=83.30
        )

        assert invoice["org_id"] == str(org_id)
        assert invoice["invoice_number"] == "INV-2026-05-001"
        # DynamoDB stores numbers as Decimal
        assert float(invoice["subtotal"]) == 70.00
        assert float(invoice["tax"]) == 13.30
        assert float(invoice["total"]) == 83.30
        assert invoice["status"] == InvoiceStatus.DRAFT.value

        # Verify persistence
        retrieved = repo.get_by_number(org_id, "INV-2026-05-001")
        assert retrieved is not None
        assert retrieved["invoice_number"] == "INV-2026-05-001"

    def test_generate_invoice_number(self, mock_dynamodb_table):
        """Test Invoice Number Generation."""
        repo = InvoiceRepository(table=mock_dynamodb_table)
        org_id = uuid4()

        invoice_number = repo.generate_invoice_number(org_id, "2026-05")

        assert invoice_number.startswith("INV-2026-05-")
        assert len(invoice_number) == len("INV-2026-05-") + 8  # UUID prefix


class TestInvoiceGenerator:
    """Tests für Invoice Generator."""

    def test_preview_next_invoice(self, mock_dynamodb_table):
        """Test Invoice Preview."""
        subscription_repo = SubscriptionRepository(table=mock_dynamodb_table)
        cost_repo = AWSCostRepository(table=mock_dynamodb_table)
        invoice_repo = InvoiceRepository(table=mock_dynamodb_table)

        generator = InvoiceGenerator(invoice_repo, subscription_repo, cost_repo)

        # Create real subscription
        org_id = uuid4()
        subscription_repo.create(
            org_id=org_id,
            tier=BillingTier.PRO,
            billing_period=BillingPeriod.MONTHLY
        )

        # Store real costs for current month
        current_month = datetime.utcnow().strftime("%Y-%m")
        cost_repo.store_monthly_costs(
            org_id=org_id,
            month=current_month,
            deployment_costs={},
            total_aws_costs=200.00,
            percentage_fee=20.00
        )

        # Generate preview
        preview = generator.preview_next_invoice(org_id)

        assert preview["preview"] is True
        assert preview["tier"] == BillingTier.PRO.value
        assert len(preview["line_items"]) >= 1
        # DynamoDB stores as Decimal, but calculations should work
        assert float(preview["subtotal"]) == 70.00  # 50 base + 20 markup
        assert float(preview["tax"]) == pytest.approx(13.30, rel=0.01)
        assert float(preview["total"]) == pytest.approx(83.30, rel=0.01)


def test_integration_full_billing_cycle(mock_dynamodb_table):
    """Integration Test: Full Billing Cycle."""
    org_id = uuid4()

    # 1. Create Subscription
    subscription_repo = SubscriptionRepository(table=mock_dynamodb_table)
    subscription = subscription_repo.create(
        org_id=org_id,
        tier=BillingTier.PRO,
        billing_period=BillingPeriod.MONTHLY
    )

    assert subscription["status"] == BillingStatus.ACTIVE.value

    # 2. Store AWS Costs
    cost_repo = AWSCostRepository(table=mock_dynamodb_table)
    cost_record = cost_repo.store_monthly_costs(
        org_id=org_id,
        month="2026-05",
        deployment_costs={"deployment-1": {"EC2": 200.00}},
        total_aws_costs=200.00,
        percentage_fee=20.00
    )

    # DynamoDB stores as Decimal
    assert float(cost_record["total_aws_costs"]) == 200.00

    # 3. Generate Invoice
    invoice_repo = InvoiceRepository(table=mock_dynamodb_table)

    invoice = invoice_repo.create(
        org_id=org_id,
        invoice_number="INV-2026-05-001",
        period_start=datetime(2026, 5, 1),
        period_end=datetime(2026, 6, 1),
        line_items=[
            {"description": "Base Fee", "amount": 50.00, "currency": "EUR"},
            {"description": "AWS Markup", "amount": 20.00, "currency": "EUR"}
        ],
        subtotal=70.00,
        tax=13.30,
        total=83.30
    )

    assert invoice["status"] == InvoiceStatus.DRAFT.value
    # DynamoDB stores as Decimal
    assert float(invoice["total"]) == 83.30
