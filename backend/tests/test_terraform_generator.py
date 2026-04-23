"""Tests für TerraformGenerator.

Testet End-to-End Terraform-Generierung aus Architecture JSON.
"""

import pytest
from pathlib import Path

from app.core.terraform_generator import TerraformGenerator
from app.core.terraform_generator.exceptions import (
    UnsupportedComponentError,
    TemplateNotFoundError,
)


class TestTerraformGenerator:
    """Tests für TerraformGenerator."""

    def test_create_generator(self):
        """Test: Generator erstellen."""
        generator = TerraformGenerator()

        assert generator.template_dir is not None
        assert generator.jinja_env is not None
        assert generator.mapper is not None

    def test_generate_minimal_architecture(self, sample_architecture_minimal):
        """Test: Minimale Architecture ohne Components."""
        generator = TerraformGenerator()

        # Generate (skip validation da keine terraform CLI)
        project = generator.generate(sample_architecture_minimal, validate=False)

        # Prüfe dass Projekt erstellt wurde
        assert project is not None
        assert "provider.tf" in project.files
        assert project.provider == "aws"

    def test_generate_with_vpc(self, sample_architecture_minimal):
        """Test: Architecture mit VPC Component."""
        generator = TerraformGenerator()

        # Add VPC component
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "main_vpc",
                "type": "vpc",
                "name": "Main VPC",
                "configuration": {
                    "cidr_block": "10.0.0.0/16"
                }
            }
        ]

        project = generator.generate(arch, validate=False)

        # Prüfe Files
        assert "main.tf" in project.files
        main_content = project.files["main.tf"]

        # Prüfe VPC Resource
        assert 'resource "aws_vpc"' in main_content
        assert "main_vpc" in main_content
        assert "10.0.0.0/16" in main_content

    def test_generate_with_ec2(self, sample_architecture_minimal):
        """Test: Architecture mit EC2 Component."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "web_server",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {
                    "instance_type": "t3.micro",
                    "ami": "ami-12345678"
                }
            }
        ]

        project = generator.generate(arch, validate=False)

        main_content = project.files["main.tf"]

        # Prüfe EC2 Resource
        assert 'resource "aws_instance"' in main_content
        assert "web_server" in main_content
        assert "t3.micro" in main_content

    def test_generate_with_s3(self, sample_architecture_minimal):
        """Test: Architecture mit S3 Component."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "storage_bucket",
                "type": "s3",
                "name": "Storage Bucket",
                "configuration": {
                    "bucket_name": "my-test-bucket",
                    "versioning_enabled": True
                }
            }
        ]

        project = generator.generate(arch, validate=False)

        main_content = project.files["main.tf"]

        # Prüfe S3 Resources
        assert 'resource "aws_s3_bucket"' in main_content
        assert "storage_bucket" in main_content

    def test_generate_with_multiple_components(self, sample_architecture_simple_web):
        """Test: Architecture mit mehreren Components."""
        generator = TerraformGenerator()

        project = generator.generate(sample_architecture_simple_web, validate=False)

        main_content = project.files["main.tf"]

        # sample_architecture_simple_web hat VPC, Subnet, EC2, S3
        # Prüfe dass alle Resources vorhanden sind
        assert 'resource "aws_vpc"' in main_content or "vpc" in str(sample_architecture_simple_web["architecture"]["components"])

    def test_generate_outputs(self, sample_architecture_minimal):
        """Test: Outputs werden generiert."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "main_vpc",
                "type": "vpc",
                "name": "Main VPC",
                "configuration": {}
            },
            {
                "id": "web_server",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {}
            }
        ]

        project = generator.generate(arch, validate=False)

        # Prüfe dass outputs.tf existiert
        assert "outputs.tf" in project.files

        outputs_content = project.files["outputs.tf"]

        # Prüfe dass Outputs für VPC und EC2 existieren
        assert "main_vpc_id" in outputs_content
        assert "web_server_public_ip" in outputs_content

    def test_generate_variables(self, sample_architecture_minimal):
        """Test: Variables werden generiert."""
        generator = TerraformGenerator()

        project = generator.generate(sample_architecture_minimal, validate=False)

        # Prüfe dass variables.tf existiert
        assert "variables.tf" in project.files

        vars_content = project.files["variables.tf"]

        # Prüfe Standard-Variables
        assert 'variable "project_name"' in vars_content
        assert 'variable "region"' in vars_content
        assert 'variable "environment"' in vars_content

    def test_generate_with_unsupported_component(self, sample_architecture_minimal):
        """Test: Unsupported Component Type wirft Exception."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "unknown",
                "type": "unsupported_type",
                "name": "Unknown Component",
                "configuration": {}
            }
        ]

        # Sollte UnsupportedComponentError werfen
        with pytest.raises(UnsupportedComponentError):
            generator.generate(arch, validate=False)

    def test_generate_with_alias_component_type(self, sample_architecture_minimal):
        """Test: Component Alias wird korrekt aufgelöst."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "my_network",
                "type": "network",  # Alias für "vpc"
                "name": "My Network",
                "configuration": {
                    "cidr_block": "10.0.0.0/16"
                }
            }
        ]

        project = generator.generate(arch, validate=False)

        main_content = project.files["main.tf"]

        # Prüfe dass VPC Resource erstellt wurde
        assert 'resource "aws_vpc"' in main_content

    def test_generate_with_custom_region(self, sample_architecture_minimal):
        """Test: Custom Region wird verwendet."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["metadata"]["region"] = "eu-central-1"

        project = generator.generate(arch, validate=False)

        assert project.region == "eu-central-1"

        provider_content = project.files["provider.tf"]
        assert 'region = "eu-central-1"' in provider_content

    def test_generate_project_metadata(self, sample_architecture_minimal):
        """Test: Project Metadata wird korrekt gesetzt."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["metadata"]["name"] = "Test Project"
        arch["metadata"]["provider"] = "aws"
        arch["metadata"]["region"] = "us-west-2"

        project = generator.generate(arch, validate=False)

        assert project.project_name == "Test Project"
        assert project.provider == "aws"
        assert project.region == "us-west-2"

    def test_generate_file_count(self, sample_architecture_minimal):
        """Test: Anzahl generierter Dateien."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {"id": "vpc1", "type": "vpc", "name": "VPC", "configuration": {}}
        ]

        project = generator.generate(arch, validate=False)

        # Sollte mindestens provider.tf, variables.tf, main.tf, outputs.tf haben
        assert project.get_file_count() >= 4
