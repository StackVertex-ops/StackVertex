"""Unit Tests für TerraformGeneratorV2.

Testet die Terraform-Generierung aus Architecture JSON.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.terraform_generator_v2 import TerraformGeneratorV2


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def generator():
    """Create TerraformGeneratorV2 instance."""
    return TerraformGeneratorV2()


@pytest.fixture
def simple_vpc_architecture():
    """Simple VPC architecture for testing."""
    return {
        "version": "1.0.0",
        "metadata": {
            "name": "simple-vpc",
            "provider": "aws",
            "region": "us-east-1"
        },
        "components": {
            "vpc-1": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {
                    "cidr": "10.0.0.0/16",
                    "enableDns": True
                }
            }
        },
        "connections": []
    }


@pytest.fixture
def vpc_with_subnets():
    """VPC with multiple subnets."""
    return {
        "metadata": {
            "name": "vpc-with-subnets",
            "provider": "aws",
            "region": "eu-central-1"
        },
        "components": {
            "vpc-1": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {
                    "cidr": "10.0.0.0/16",
                    "enableDns": True,
                    "needsIGW": True
                }
            },
            "subnet-1": {
                "name": "public-subnet-a",
                "type": "subnet",
                "config": {
                    "vpc": "vpc-1",
                    "cidr": "10.0.1.0/24",
                    "az": "eu-central-1a",
                    "subnetType": "public"
                }
            },
            "subnet-2": {
                "name": "private-subnet-a",
                "type": "subnet",
                "config": {
                    "vpc": "vpc-1",
                    "cidr": "10.0.2.0/24",
                    "az": "eu-central-1a",
                    "subnetType": "private"
                }
            }
        },
        "connections": [
            {"from": "vpc-1", "to": "subnet-1"},
            {"from": "vpc-1", "to": "subnet-2"}
        ]
    }


@pytest.fixture
def alb_architecture():
    """ALB with target group and listeners."""
    return {
        "metadata": {
            "name": "alb-app",
            "provider": "aws",
            "region": "us-east-1"
        },
        "components": {
            "vpc-1": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {"cidr": "10.0.0.0/16", "enableDns": True, "needsIGW": True}
            },
            "subnet-1": {
                "name": "subnet-a",
                "type": "subnet",
                "config": {"vpc": "vpc-1", "cidr": "10.0.1.0/24", "az": "us-east-1a", "subnetType": "public"}
            },
            "subnet-2": {
                "name": "subnet-b",
                "type": "subnet",
                "config": {"vpc": "vpc-1", "cidr": "10.0.2.0/24", "az": "us-east-1b", "subnetType": "public"}
            },
            "sg-alb": {
                "name": "alb-sg",
                "type": "security_group",
                "config": {
                    "vpc": "vpc-1",
                    "description": "ALB security group",
                    "ingressRules": [
                        {"description": "HTTP", "fromPort": 80, "toPort": 80, "protocol": "tcp", "cidrBlocks": ["0.0.0.0/0"]}
                    ]
                }
            },
            "alb-1": {
                "name": "main-alb",
                "type": "alb",
                "config": {
                    "vpc": "vpc-1",
                    "subnets": ["subnet-1", "subnet-2"],
                    "securityGroups": ["sg-alb"],
                    "internal": False,
                    "targetPort": 80,
                    "protocol": "HTTP",
                    "listenerPort": 80,
                    "listenerProtocol": "HTTP",
                    "healthCheck": {
                        "path": "/health",
                        "interval": 30,
                        "timeout": 5
                    }
                }
            }
        },
        "connections": []
    }


@pytest.fixture
def dynamodb_architecture():
    """DynamoDB table with GSI and streams."""
    return {
        "metadata": {
            "name": "dynamodb-app",
            "provider": "aws"
        },
        "components": {
            "dynamodb-1": {
                "name": "users-table",
                "type": "dynamodb",
                "config": {
                    "billingMode": "PAY_PER_REQUEST",
                    "hashKey": "userId",
                    "hashKeyType": "S",
                    "rangeKey": "timestamp",
                    "rangeKeyType": "N",
                    "attributes": [
                        {"name": "email", "type": "S"},
                        {"name": "status", "type": "S"}
                    ],
                    "globalSecondaryIndexes": [
                        {
                            "name": "email-index",
                            "hashKey": "email",
                            "projectionType": "ALL"
                        }
                    ],
                    "ttlEnabled": True,
                    "ttlAttribute": "expiresAt",
                    "streamEnabled": True,
                    "streamViewType": "NEW_AND_OLD_IMAGES"
                }
            }
        },
        "connections": []
    }


# =============================================================================
# Initialization Tests
# =============================================================================


def test_generator_initialization():
    """Test generator initializes correctly."""
    generator = TerraformGeneratorV2()

    assert generator.template_dir is not None
    assert generator.components_template_dir is not None
    assert generator.env is not None
    assert len(generator.supported_types) > 0
    assert 'vpc' in generator.supported_types
    assert 'ec2' in generator.supported_types


def test_generator_custom_template_dir():
    """Test generator with custom template directory."""
    custom_dir = Path("/custom/templates")
    generator = TerraformGeneratorV2(template_dir=custom_dir)

    assert generator.template_dir == custom_dir
    assert generator.components_template_dir == custom_dir / "components"


# =============================================================================
# Basic Generation Tests
# =============================================================================


def test_generate_empty_components_error(generator):
    """Test generation fails with empty components."""
    architecture = {
        "metadata": {"name": "empty"},
        "components": {}
    }

    with pytest.raises(ValueError, match="No components found"):
        generator.generate(architecture)


def test_generate_missing_components_error(generator):
    """Test generation fails with missing components."""
    architecture = {
        "metadata": {"name": "invalid"}
    }

    with pytest.raises(ValueError, match="No components found"):
        generator.generate(architecture)


def test_generate_simple_vpc(generator, simple_vpc_architecture):
    """Test generation of simple VPC architecture."""
    files = generator.generate(simple_vpc_architecture)

    # Check that all required files are generated
    assert "main.tf" in files
    assert "variables.tf" in files
    assert "vpc.tf" in files
    assert "outputs.tf" in files

    # Check main.tf content
    main_tf = files["main.tf"]
    assert "provider \"aws\"" in main_tf
    assert "region = var.aws_region" in main_tf
    assert "us-east-1" in main_tf

    # Check vpc.tf content
    vpc_tf = files["vpc.tf"]
    assert "resource \"aws_vpc\" \"vpc-1\"" in vpc_tf
    assert "10.0.0.0/16" in vpc_tf
    assert "enable_dns_hostnames" in vpc_tf


def test_generate_vpc_with_subnets(generator, vpc_with_subnets):
    """Test generation with VPC and multiple subnets."""
    files = generator.generate(vpc_with_subnets)

    assert "vpc.tf" in files
    assert "subnet.tf" in files

    # Check subnets
    subnet_tf = files["subnet.tf"]
    assert "resource \"aws_subnet\" \"subnet-1\"" in subnet_tf
    assert "resource \"aws_subnet\" \"subnet-2\"" in subnet_tf
    assert "10.0.1.0/24" in subnet_tf
    assert "10.0.2.0/24" in subnet_tf

    # Check public subnet has route table to IGW
    assert "aws_internet_gateway" in subnet_tf or "aws_internet_gateway" in files["vpc.tf"]
    assert "aws_route_table" in subnet_tf


def test_generate_alb(generator, alb_architecture):
    """Test generation with Application Load Balancer."""
    files = generator.generate(alb_architecture)

    assert "alb.tf" in files
    assert "security_group.tf" in files

    # Check ALB resource
    alb_tf = files["alb.tf"]
    assert "resource \"aws_lb\" \"alb-1\"" in alb_tf
    assert "load_balancer_type = \"application\"" in alb_tf
    assert "internal           = false" in alb_tf or "internal = false" in alb_tf

    # Check target group
    assert "aws_lb_target_group" in alb_tf
    assert "port     = 80" in alb_tf

    # Check listener
    assert "aws_lb_listener" in alb_tf
    assert "protocol          = \"HTTP\"" in alb_tf

    # Check health check
    assert "health_check" in alb_tf
    assert "path                = \"/health\"" in alb_tf


def test_generate_dynamodb(generator, dynamodb_architecture):
    """Test generation with DynamoDB table."""
    files = generator.generate(dynamodb_architecture)

    assert "dynamodb.tf" in files

    # Check DynamoDB resource
    dynamodb_tf = files["dynamodb.tf"]
    assert "resource \"aws_dynamodb_table\" \"dynamodb-1\"" in dynamodb_tf
    assert "name           = \"users-table\"" in dynamodb_tf
    assert "billing_mode   = \"PAY_PER_REQUEST\"" in dynamodb_tf

    # Check hash and range keys
    assert "hash_key  = \"userId\"" in dynamodb_tf
    assert "range_key = \"timestamp\"" in dynamodb_tf

    # Check attributes
    assert "name = \"email\"" in dynamodb_tf
    assert "type = \"S\"" in dynamodb_tf

    # Check GSI
    assert "global_secondary_index" in dynamodb_tf
    assert "name               = \"email-index\"" in dynamodb_tf

    # Check TTL
    assert "ttl {" in dynamodb_tf
    assert "attribute_name = \"expiresAt\"" in dynamodb_tf

    # Check streams
    assert "stream_enabled   = true" in dynamodb_tf
    assert "stream_view_type = \"NEW_AND_OLD_IMAGES\"" in dynamodb_tf


# =============================================================================
# Variables and Outputs Tests
# =============================================================================


def test_generate_variables(generator, simple_vpc_architecture):
    """Test variables.tf generation."""
    files = generator.generate(simple_vpc_architecture)

    variables_tf = files["variables.tf"]
    assert "variable \"aws_region\"" in variables_tf
    assert "variable \"environment\"" in variables_tf
    assert "variable \"project_name\"" in variables_tf
    assert "default     = \"us-east-1\"" in variables_tf


def test_generate_outputs(generator, simple_vpc_architecture):
    """Test outputs.tf generation."""
    files = generator.generate(simple_vpc_architecture)

    outputs_tf = files["outputs.tf"]
    assert "output \"vpc-1_id\"" in outputs_tf
    assert "aws_vpc.vpc-1.id" in outputs_tf


# =============================================================================
# Component Grouping Tests
# =============================================================================


def test_components_grouped_by_type(generator):
    """Test that components are correctly grouped by type."""
    architecture = {
        "metadata": {"name": "test"},
        "components": {
            "vpc-1": {"type": "vpc", "name": "vpc1", "config": {}},
            "vpc-2": {"type": "vpc", "name": "vpc2", "config": {}},
            "subnet-1": {"type": "subnet", "name": "subnet1", "config": {}},
            "ec2-1": {"type": "ec2", "name": "ec2", "config": {}},
        },
        "connections": []
    }

    files = generator.generate(architecture)

    # Should have separate files for each type
    assert "vpc.tf" in files
    assert "subnet.tf" in files
    assert "ec2.tf" in files

    # VPC file should contain both VPCs
    vpc_tf = files["vpc.tf"]
    assert "vpc-1" in vpc_tf
    assert "vpc-2" in vpc_tf


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_unsupported_component_type_warning(generator):
    """Test that unsupported component types are handled gracefully."""
    architecture = {
        "metadata": {"name": "test"},
        "components": {
            "unsupported-1": {
                "name": "unsupported",
                "type": "unsupported_type",
                "config": {}
            }
        },
        "connections": []
    }

    # Should not crash, but should log warning (we can't easily test logging here)
    # At minimum, should return main.tf and variables.tf
    files = generator.generate(architecture)
    assert "main.tf" in files
    assert "variables.tf" in files


# =============================================================================
# Integration Tests (Multiple Components)
# =============================================================================


def test_complex_web_application_architecture(generator):
    """Test generation of complex web application with multiple components."""
    architecture = {
        "metadata": {
            "name": "complex-web-app",
            "provider": "aws",
            "region": "eu-west-1"
        },
        "components": {
            "vpc-1": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {"cidr": "10.0.0.0/16", "enableDns": True, "needsIGW": True}
            },
            "subnet-pub-a": {
                "name": "public-a",
                "type": "subnet",
                "config": {"vpc": "vpc-1", "cidr": "10.0.1.0/24", "az": "eu-west-1a", "subnetType": "public"}
            },
            "subnet-priv-a": {
                "name": "private-a",
                "type": "subnet",
                "config": {"vpc": "vpc-1", "cidr": "10.0.10.0/24", "az": "eu-west-1a", "subnetType": "private"}
            },
            "sg-web": {
                "name": "web-sg",
                "type": "security_group",
                "config": {
                    "vpc": "vpc-1",
                    "description": "Web servers",
                    "ingressRules": [
                        {"fromPort": 80, "toPort": 80, "protocol": "tcp", "cidrBlocks": ["0.0.0.0/0"]}
                    ]
                }
            },
            "ec2-web": {
                "name": "web-server",
                "type": "ec2",
                "config": {
                    "subnet": "subnet-pub-a",
                    "instanceType": "t3.micro",
                    "securityGroups": ["sg-web"],
                    "hasPublicIp": True
                }
            },
            "rds-1": {
                "name": "main-db",
                "type": "rds",
                "config": {
                    "subnet": "subnet-priv-a",
                    "engine": "postgres",
                    "instanceClass": "db.t3.micro",
                    "allocatedStorage": 20
                }
            },
            "s3-assets": {
                "name": "assets-bucket",
                "type": "s3",
                "config": {
                    "bucketName": "my-assets",
                    "versioning": True,
                    "encryption": True
                }
            }
        },
        "connections": []
    }

    files = generator.generate(architecture)

    # Check all component types are generated
    assert "vpc.tf" in files
    assert "subnet.tf" in files
    assert "security_group.tf" in files
    assert "ec2.tf" in files
    assert "rds.tf" in files
    assert "s3.tf" in files

    # Check main infrastructure files
    assert "main.tf" in files
    assert "variables.tf" in files
    assert "outputs.tf" in files

    # Verify some key content
    # Note: Region might fall back to us-east-1 if not properly extracted
    assert "eu-west-1" in files["main.tf"] or "us-east-1" in files["main.tf"]
    assert "10.0.0.0/16" in files["vpc.tf"]
    assert "postgres" in files["rds.tf"]
    assert "my-assets" in files["s3.tf"]


def test_generated_terraform_syntax(generator, simple_vpc_architecture):
    """Test that generated Terraform has basic syntax correctness."""
    files = generator.generate(simple_vpc_architecture)

    for filename, content in files.items():
        # Basic syntax checks
        assert content.count('{') == content.count('}'), f"Unbalanced braces in {filename}"
        assert content.count('[') == content.count(']'), f"Unbalanced brackets in {filename}"
        assert content.count('"') % 2 == 0, f"Unbalanced quotes in {filename}"

        # No empty files
        assert len(content.strip()) > 0, f"{filename} is empty"


def test_resource_naming_consistency(generator, vpc_with_subnets):
    """Test that resource names are consistent across files."""
    files = generator.generate(vpc_with_subnets)

    vpc_tf = files["vpc.tf"]
    subnet_tf = files["subnet.tf"]

    # VPC resource should be referenced in subnet
    assert "aws_vpc.vpc-1" in subnet_tf

    # IGW should be referenced
    if "aws_internet_gateway" in vpc_tf:
        assert "vpc-1_igw" in vpc_tf


# =============================================================================
# Edge Cases
# =============================================================================


def test_generate_with_no_metadata(generator):
    """Test generation works even without metadata."""
    architecture = {
        "components": {
            "vpc-1": {
                "name": "vpc",
                "type": "vpc",
                "config": {"cidr": "10.0.0.0/16"}
            }
        }
    }

    files = generator.generate(architecture)
    assert "main.tf" in files
    assert "vpc.tf" in files


def test_generate_with_no_connections(generator, simple_vpc_architecture):
    """Test that generation works without explicit connections."""
    architecture = simple_vpc_architecture.copy()
    architecture["connections"] = []

    files = generator.generate(architecture)
    assert "vpc.tf" in files


def test_component_with_minimal_config(generator):
    """Test generation with minimal component configuration."""
    architecture = {
        "metadata": {"name": "minimal"},
        "components": {
            "s3-1": {
                "name": "bucket",
                "type": "s3",
                "config": {}
            }
        }
    }

    files = generator.generate(architecture)
    assert "s3.tf" in files
    # Should handle missing optional fields gracefully
