"""End-to-End Tests für Terraform Generator.

Testet komplette Terraform-Generierung mit real-world Architectures.
"""

import pytest
from pathlib import Path

from app.core.terraform_generator import TerraformGenerator


class TestTerraformE2E:
    """End-to-End Tests."""

    def test_generate_simple_web_app(self, sample_architecture_simple_web, tmp_path):
        """Test: Komplette Web-App Architecture generieren."""
        generator = TerraformGenerator()

        # Generate project
        project = generator.generate(sample_architecture_simple_web, validate=False)

        # Write to disk
        output_dir = tmp_path / "terraform"
        project.write_to_directory(output_dir)

        # Prüfe dass Basis-Dateien erstellt wurden
        assert (output_dir / "provider.tf").exists()
        assert (output_dir / "variables.tf").exists()
        assert (output_dir / "main.tf").exists()
        # outputs.tf ist optional (nur wenn Outputs generiert wurden)

        # Prüfe Inhalte
        provider_content = (output_dir / "provider.tf").read_text()
        assert "terraform {" in provider_content
        assert "provider \"aws\"" in provider_content

        main_content = (output_dir / "main.tf").read_text()
        # Simple web app sollte mindestens resources haben
        assert len(main_content) > 100  # Nicht leer

    def test_generated_terraform_has_valid_syntax(self, sample_architecture_minimal):
        """Test: Generierter Terraform Code hat valide Syntax (Basic Checks)."""
        generator = TerraformGenerator()

        # Add some components
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "main_vpc",
                "type": "vpc",
                "name": "Main VPC",
                "configuration": {"cidr_block": "10.0.0.0/16"}
            },
            {
                "id": "web_server",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {
                    "instance_type": "t3.micro",
                    "subnet_id": "aws_subnet.public.id"
                }
            },
            {
                "id": "storage",
                "type": "s3",
                "name": "Storage Bucket",
                "configuration": {
                    "bucket_name": "my-test-bucket",
                    "versioning_enabled": True
                }
            }
        ]

        project = generator.generate(arch, validate=False)

        # Prüfe dass alle Files valide HCL Syntax haben (basic checks)
        for filename, content in project.files.items():
            if filename.endswith(".tf"):
                # Balanced braces
                assert content.count("{") == content.count("}")

                # No obvious syntax errors
                assert "resource \"\"" not in content
                assert "variable \"\"" not in content

    def test_generate_and_validate_syntax(self, sample_architecture_minimal):
        """Test: Generate und Syntax Validation."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "test_vpc",
                "type": "vpc",
                "name": "Test VPC",
                "configuration": {}
            }
        ]

        # Generate mit Validation (nur syntax checks)
        project = generator.generate(arch, validate=True)

        # Sollte ohne Fehler durchlaufen
        assert project is not None
        assert len(project.files) > 0

    def test_multiple_component_types_in_one_architecture(self, sample_architecture_minimal):
        """Test: Architecture mit vielen verschiedenen Component-Types."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {"id": "vpc1", "type": "vpc", "name": "VPC", "configuration": {}},
            {"id": "subnet1", "type": "subnet", "name": "Subnet", "configuration": {}},
            {"id": "sg1", "type": "security_group", "name": "SG", "configuration": {}},
            {"id": "ec2_1", "type": "ec2", "name": "EC2", "configuration": {}},
            {"id": "s3_1", "type": "s3", "name": "S3", "configuration": {}},
            {"id": "rds1", "type": "rds", "name": "RDS", "configuration": {}},
            {"id": "lambda1", "type": "lambda", "name": "Lambda", "configuration": {}},
        ]

        project = generator.generate(arch, validate=False)

        main_content = project.files["main.tf"]

        # Prüfe dass alle Component-Types generiert wurden
        assert 'resource "aws_vpc"' in main_content
        assert 'resource "aws_subnet"' in main_content
        assert 'resource "aws_security_group"' in main_content
        assert 'resource "aws_instance"' in main_content
        assert 'resource "aws_s3_bucket"' in main_content
        assert 'resource "aws_db_instance"' in main_content
        assert 'resource "aws_lambda_function"' in main_content

    def test_output_includes_all_important_resources(self, sample_architecture_minimal):
        """Test: Outputs werden für alle wichtigen Resources generiert."""
        generator = TerraformGenerator()

        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {"id": "my_vpc", "type": "vpc", "name": "VPC", "configuration": {}},
            {"id": "my_ec2", "type": "ec2", "name": "EC2", "configuration": {}},
            {"id": "my_s3", "type": "s3", "name": "S3", "configuration": {}},
            {"id": "my_rds", "type": "rds", "name": "RDS", "configuration": {}},
            {"id": "my_lambda", "type": "lambda", "name": "Lambda", "configuration": {}},
        ]

        project = generator.generate(arch, validate=False)

        outputs_content = project.files["outputs.tf"]

        # Prüfe dass Outputs existieren
        assert "my_vpc_id" in outputs_content
        assert "my_ec2_public_ip" in outputs_content
        assert "my_s3_bucket_name" in outputs_content
        assert "my_rds_endpoint" in outputs_content
        assert "my_lambda_arn" in outputs_content
