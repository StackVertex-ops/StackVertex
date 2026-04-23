"""Tests für ComponentMapper.

Testet Component-Type zu Template-Path Mapping.
"""

import pytest
from pathlib import Path

from app.core.terraform_generator.component_mapper import ComponentMapper


class TestComponentMapper:
    """Tests für ComponentMapper."""

    def test_get_template_path_vpc(self):
        """Test: VPC Template Path."""
        mapper = ComponentMapper()
        path = mapper.get_template_path("vpc")
        assert path == "networking/vpc.tf.j2"

    def test_get_template_path_ec2(self):
        """Test: EC2 Template Path."""
        mapper = ComponentMapper()
        path = mapper.get_template_path("ec2")
        assert path == "compute/ec2.tf.j2"

    def test_get_template_path_s3(self):
        """Test: S3 Template Path."""
        mapper = ComponentMapper()
        path = mapper.get_template_path("s3")
        assert path == "storage/s3.tf.j2"

    def test_get_template_path_rds(self):
        """Test: RDS Template Path."""
        mapper = ComponentMapper()
        path = mapper.get_template_path("rds")
        assert path == "database/rds.tf.j2"

    def test_get_template_path_alias(self):
        """Test: Alias wird aufgelöst."""
        mapper = ComponentMapper()

        # "network" ist Alias für "vpc"
        path = mapper.get_template_path("network")
        assert path == "networking/vpc.tf.j2"

        # "instance" ist Alias für "ec2"
        path = mapper.get_template_path("instance")
        assert path == "compute/ec2.tf.j2"

    def test_get_template_path_case_insensitive(self):
        """Test: Case-insensitive Lookup."""
        mapper = ComponentMapper()
        assert mapper.get_template_path("VPC") == "networking/vpc.tf.j2"
        assert mapper.get_template_path("EC2") == "compute/ec2.tf.j2"

    def test_get_template_path_unsupported(self):
        """Test: Unsupported Component Type wirft KeyError."""
        mapper = ComponentMapper()

        with pytest.raises(KeyError):
            mapper.get_template_path("unsupported_type")

    def test_is_supported_true(self):
        """Test: Supported Types."""
        mapper = ComponentMapper()

        assert mapper.is_supported("vpc") is True
        assert mapper.is_supported("ec2") is True
        assert mapper.is_supported("s3") is True
        assert mapper.is_supported("network") is True  # Alias

    def test_is_supported_false(self):
        """Test: Unsupported Types."""
        mapper = ComponentMapper()

        assert mapper.is_supported("unsupported") is False
        assert mapper.is_supported("random_type") is False

    def test_get_supported_types(self):
        """Test: Liste aller supported Types."""
        mapper = ComponentMapper()
        supported = mapper.get_supported_types()

        assert "vpc" in supported
        assert "ec2" in supported
        assert "s3" in supported
        assert "rds" in supported
        assert "lambda" in supported
        assert len(supported) > 10  # Mindestens 10 Types

    def test_register_template(self):
        """Test: Custom Template registrieren."""
        mapper = ComponentMapper()

        # Registriere custom template
        mapper.register_template("custom_type", "custom/custom.tf.j2")

        # Prüfe ob registriert
        assert mapper.is_supported("custom_type")
        assert mapper.get_template_path("custom_type") == "custom/custom.tf.j2"

    def test_register_alias(self):
        """Test: Custom Alias registrieren."""
        mapper = ComponentMapper()

        # Registriere alias
        mapper.register_alias("my_network", "vpc")

        # Prüfe ob Alias funktioniert
        assert mapper.get_template_path("my_network") == "networking/vpc.tf.j2"
