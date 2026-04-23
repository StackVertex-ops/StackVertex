"""Tests für PricingDataLoader.

Testet Laden von AWS Pricing-Daten.
"""

import pytest
from decimal import Decimal

from app.services.pricing_data import PricingDataLoader


class TestPricingDataLoader:
    """Tests für PricingDataLoader."""

    def test_create_loader(self):
        """Test: Loader erstellen."""
        loader = PricingDataLoader()

        assert loader.pricing_dir is not None

    def test_get_ec2_price(self):
        """Test: EC2 Preis laden."""
        loader = PricingDataLoader()

        price = loader.get_ec2_price("t3.micro", "us-east-1")

        assert price is not None
        assert isinstance(price, Decimal)
        assert price > 0

    def test_get_ec2_price_different_regions(self):
        """Test: EC2 Preise in verschiedenen Regionen."""
        loader = PricingDataLoader()

        price_us = loader.get_ec2_price("t3.micro", "us-east-1")
        price_eu = loader.get_ec2_price("t3.micro", "eu-central-1")

        assert price_us is not None
        assert price_eu is not None
        # EU sollte teurer sein
        assert price_eu > price_us

    def test_get_ec2_price_invalid_instance(self):
        """Test: Invalider Instance Type."""
        loader = PricingDataLoader()

        price = loader.get_ec2_price("invalid.type", "us-east-1")

        assert price is None

    def test_get_rds_price(self):
        """Test: RDS Preis laden."""
        loader = PricingDataLoader()

        price = loader.get_rds_price("db.t3.micro", "us-east-1")

        assert price is not None
        assert isinstance(price, Decimal)
        assert price > 0

    def test_get_rds_storage_price(self):
        """Test: RDS Storage Preis."""
        loader = PricingDataLoader()

        price = loader.get_rds_storage_price("gp3", "us-east-1")

        assert price is not None
        assert isinstance(price, Decimal)
        assert price > 0

    def test_get_s3_price(self):
        """Test: S3 Preis laden."""
        loader = PricingDataLoader()

        price = loader.get_s3_price("standard", "us-east-1")

        assert price is not None
        assert isinstance(price, Decimal)
        assert price > 0

    def test_get_lambda_price(self):
        """Test: Lambda Preis laden."""
        loader = PricingDataLoader()

        pricing = loader.get_lambda_price("us-east-1")

        assert "requests_per_million" in pricing
        assert "compute_per_gb_second" in pricing
        assert isinstance(pricing["requests_per_million"], Decimal)
        assert isinstance(pricing["compute_per_gb_second"], Decimal)

    def test_get_all_ec2_instances(self):
        """Test: Alle EC2 Instances für Region."""
        loader = PricingDataLoader()

        instances = loader.get_all_ec2_instances("us-east-1")

        assert len(instances) > 0
        assert "t3.micro" in instances
        assert "m5.large" in instances

    def test_pricing_data_cached(self):
        """Test: Pricing-Daten werden gecached."""
        loader = PricingDataLoader()

        # First call
        price1 = loader.get_ec2_price("t3.micro", "us-east-1")

        # Second call (should use cache)
        price2 = loader.get_ec2_price("t3.micro", "us-east-1")

        assert price1 == price2
