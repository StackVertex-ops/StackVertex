"""Tests für Designer API Endpoints.

Umfassende Tests für /api/v1/designer/* Endpoints:
- POST /designer/save
- GET /designer/load/{id}
- POST /designer/generate-terraform
- POST /designer/validate
"""

import json
from uuid import uuid4
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.services.terraform_generator_v2 import TerraformGeneratorV2


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_designer_architecture():
    """Sample architecture JSON from Infrastructure Designer."""
    return {
        "version": "1.0.0",
        "metadata": {
            "name": "Test Web App",
            "description": "Simple test architecture",
            "provider": "aws",
            "region": "us-east-1",
            "created_at": datetime.now(timezone.utc).isoformat()
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
                "name": "public-subnet",
                "type": "subnet",
                "config": {
                    "vpc": "vpc-1",
                    "cidr": "10.0.1.0/24",
                    "az": "us-east-1a",
                    "subnetType": "public"
                }
            },
            "ec2-1": {
                "name": "web-server",
                "type": "ec2",
                "config": {
                    "subnet": "subnet-1",
                    "instanceType": "t3.small",
                    "hasPublicIp": True
                }
            }
        },
        "connections": [
            {"from": "vpc-1", "to": "subnet-1"},
            {"from": "subnet-1", "to": "ec2-1"}
        ]
    }


@pytest.fixture
def sample_empty_architecture():
    """Minimal architecture with empty components (edge case)."""
    return {
        "version": "1.0.0",
        "metadata": {
            "name": "Empty Architecture",
            "provider": "aws"
        },
        "components": {},
        "connections": []
    }


@pytest.fixture
def sample_invalid_architecture():
    """Invalid architecture (missing components field)."""
    return {
        "version": "1.0.0",
        "metadata": {
            "name": "Invalid Architecture"
        }
        # Missing 'components' field
    }


@pytest.fixture
def mock_architecture_repo():
    """Mock ArchitectureRepository for testing."""
    with patch("app.api.designer.ArchitectureRepository") as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_terraform_generator():
    """Mock TerraformGeneratorV2 for testing."""
    with patch("app.api.designer.TerraformGeneratorV2") as mock:
        generator = MagicMock()
        mock.return_value = generator
        yield generator


# =============================================================================
# POST /designer/save Tests
# =============================================================================


def test_save_designer_architecture_success(client, sample_designer_architecture, mock_architecture_repo):
    """Test successful architecture save."""
    # Mock repository response
    arch_id = str(uuid4())
    now = datetime.now(timezone.utc)
    mock_architecture_repo.create.return_value = {
        "id": arch_id,
        "name": "Test Web App",
        "version": "1.0.0",
        "created_at": now,
        "updated_at": now,
        "definition": sample_designer_architecture
    }

    # Dependency override
    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    # API request
    response = client.post(
        "/api/v1/designer/save",
        json={
            "name": "Test Web App",
            "description": "Test description",
            "architecture_json": sample_designer_architecture,
            "owner": "test-user"
        }
    )

    # Cleanup
    app.dependency_overrides.clear()

    # Assertions
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["architecture_id"] == arch_id
    assert data["name"] == "Test Web App"
    assert data["version"] == "1.0.0"
    assert "created_at" in data
    assert "updated_at" in data

    # Verify repository was called
    mock_architecture_repo.create.assert_called_once()


def test_save_designer_architecture_missing_components(client, sample_invalid_architecture, mock_architecture_repo):
    """Test save with missing components field."""
    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    response = client.post(
        "/api/v1/designer/save",
        json={
            "name": "Invalid Architecture",
            "architecture_json": sample_invalid_architecture
        }
    )

    app.dependency_overrides.clear()

    # Should return 422 Unprocessable Entity
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "components" in response.json()["detail"].lower()


def test_save_designer_architecture_empty_components(client, sample_empty_architecture, mock_architecture_repo):
    """Test save with empty components (edge case - should succeed)."""
    arch_id = str(uuid4())
    now = datetime.now(timezone.utc)
    mock_architecture_repo.create.return_value = {
        "id": arch_id,
        "name": "Empty Architecture",
        "created_at": now,
        "updated_at": now,
        "definition": sample_empty_architecture
    }

    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    response = client.post(
        "/api/v1/designer/save",
        json={
            "name": "Empty Architecture",
            "architecture_json": sample_empty_architecture
        }
    )

    app.dependency_overrides.clear()

    # Empty components dict should be valid (edge case)
    assert response.status_code == status.HTTP_201_CREATED


def test_save_designer_architecture_repository_error(client, sample_designer_architecture, mock_architecture_repo):
    """Test save when repository raises exception."""
    mock_architecture_repo.create.side_effect = Exception("Database error")

    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    response = client.post(
        "/api/v1/designer/save",
        json={
            "name": "Test",
            "architecture_json": sample_designer_architecture
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "error" in response.json()["detail"].lower()


# =============================================================================
# GET /designer/load/{id} Tests
# =============================================================================


def test_load_designer_architecture_success(client, sample_designer_architecture, mock_architecture_repo):
    """Test successful architecture load."""
    arch_id = str(uuid4())
    mock_architecture_repo.get.return_value = {
        "id": arch_id,
        "name": "Test Web App",
        "definition": sample_designer_architecture,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    response = client.get(f"/api/v1/designer/load/{arch_id}")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["version"] == "1.0.0"
    assert "components" in data
    assert len(data["components"]) == 3


def test_load_designer_architecture_not_found(client, mock_architecture_repo):
    """Test load when architecture not found."""
    arch_id = str(uuid4())
    mock_architecture_repo.get.return_value = None

    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    response = client.get(f"/api/v1/designer/load/{arch_id}")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_load_designer_architecture_invalid_uuid(client):
    """Test load with invalid UUID format."""
    response = client.get("/api/v1/designer/load/not-a-uuid")

    # FastAPI returns 422 for invalid UUID path parameter
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_load_designer_architecture_repository_error(client, mock_architecture_repo):
    """Test load when repository raises exception."""
    arch_id = str(uuid4())
    mock_architecture_repo.get.side_effect = Exception("Database error")

    from app.api.designer import get_architecture_repo
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo

    response = client.get(f"/api/v1/designer/load/{arch_id}")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# POST /designer/generate-terraform Tests
# =============================================================================


def test_generate_terraform_success(client, sample_designer_architecture, mock_terraform_generator):
    """Test successful Terraform generation."""
    # Mock generator response
    mock_terraform_generator.generate.return_value = {
        "main.tf": "provider \"aws\" {\n  region = \"us-east-1\"\n}",
        "vpc.tf": "resource \"aws_vpc\" \"main_vpc\" {\n  cidr_block = \"10.0.0.0/16\"\n}",
        "ec2.tf": "resource \"aws_instance\" \"web_server\" {\n  instance_type = \"t3.small\"\n}"
    }

    from app.api.designer import get_terraform_generator
    app.dependency_overrides[get_terraform_generator] = lambda: mock_terraform_generator

    response = client.post(
        "/api/v1/designer/generate-terraform",
        json={"architecture_json": sample_designer_architecture}
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 3
    assert "main.tf" in data["files"]
    assert "vpc.tf" in data["files"]
    assert "ec2.tf" in data["files"]
    assert data["component_count"] == 3
    assert isinstance(data["warnings"], list)


def test_generate_terraform_missing_components(client, sample_invalid_architecture, mock_terraform_generator):
    """Test generation with missing components."""
    from app.api.designer import get_terraform_generator
    app.dependency_overrides[get_terraform_generator] = lambda: mock_terraform_generator

    response = client.post(
        "/api/v1/designer/generate-terraform",
        json={"architecture_json": sample_invalid_architecture}
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "components" in response.json()["detail"].lower()


def test_generate_terraform_generator_error(client, sample_designer_architecture, mock_terraform_generator):
    """Test generation when generator raises exception."""
    mock_terraform_generator.generate.side_effect = Exception("Template error")

    from app.api.designer import get_terraform_generator
    app.dependency_overrides[get_terraform_generator] = lambda: mock_terraform_generator

    response = client.post(
        "/api/v1/designer/generate-terraform",
        json={"architecture_json": sample_designer_architecture}
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "error" in response.json()["detail"].lower()


def test_generate_terraform_empty_components(client, sample_empty_architecture, mock_terraform_generator):
    """Test generation with empty components."""
    # Empty components dict should still validate but might fail in generator
    mock_terraform_generator.generate.return_value = {
        "main.tf": "provider \"aws\" {\n  region = \"us-east-1\"\n}",
        "variables.tf": ""
    }

    from app.api.designer import get_terraform_generator
    app.dependency_overrides[get_terraform_generator] = lambda: mock_terraform_generator

    response = client.post(
        "/api/v1/designer/generate-terraform",
        json={"architecture_json": sample_empty_architecture}
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["component_count"] == 0


# =============================================================================
# POST /designer/validate Tests
# =============================================================================


def test_validate_architecture_success(client, sample_designer_architecture):
    """Test successful validation."""
    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": sample_designer_architecture}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Debug: print errors if any
    if data["errors"]:
        print(f"Validation errors: {data['errors']}")

    assert data["valid"] is True, f"Expected valid=True, got errors: {data['errors']}"
    assert len(data["errors"]) == 0
    assert data["component_count"] == 3
    assert data["connection_count"] == 2


def test_validate_architecture_missing_version(client, sample_designer_architecture):
    """Test validation with missing version."""
    arch = sample_designer_architecture.copy()
    del arch["version"]

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert any("version" in error.lower() for error in data["errors"])


def test_validate_architecture_missing_components(client, sample_invalid_architecture):
    """Test validation with missing components."""
    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": sample_invalid_architecture}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert any("components" in error.lower() for error in data["errors"])


def test_validate_architecture_invalid_connection(client, sample_designer_architecture):
    """Test validation with connection referencing non-existent component."""
    arch = sample_designer_architecture.copy()
    arch["connections"].append({"from": "vpc-1", "to": "non-existent-id"})

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert any("non-existent-id" in error for error in data["errors"])


def test_validate_architecture_component_missing_type(client):
    """Test validation with component missing type field."""
    arch = {
        "version": "1.0.0",
        "metadata": {"name": "Test"},
        "components": {
            "comp-1": {
                "name": "test-component",
                # Missing 'type' field
                "config": {}
            }
        },
        "connections": []
    }

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert any("type" in error.lower() for error in data["errors"])


def test_validate_architecture_subnet_missing_vpc(client):
    """Test VPC-specific validation: subnet without vpc_id."""
    arch = {
        "version": "1.0.0",
        "metadata": {"name": "Test"},
        "components": {
            "vpc-1": {
                "name": "vpc",
                "type": "vpc",
                "config": {"cidr": "10.0.0.0/16"}
            },
            "subnet-1": {
                "name": "subnet",
                "type": "subnet",
                "config": {
                    "cidr": "10.0.1.0/24"
                    # Missing 'vpc_id' field
                }
            }
        },
        "connections": []
    }

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert any("vpc_id" in error.lower() for error in data["errors"])


def test_validate_architecture_subnet_invalid_vpc(client):
    """Test VPC-specific validation: subnet referencing unknown VPC."""
    arch = {
        "version": "1.0.0",
        "metadata": {"name": "Test"},
        "components": {
            "subnet-1": {
                "name": "subnet",
                "type": "subnet",
                "config": {
                    "cidr": "10.0.1.0/24",
                    "vpc_id": "non-existent-vpc"
                }
            }
        },
        "connections": []
    }

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is False
    assert any("vpc" in error.lower() and "non-existent-vpc" in error for error in data["errors"])


def test_validate_architecture_warnings(client):
    """Test validation warnings (missing metadata, name)."""
    arch = {
        "version": "1.0.0",
        # Missing 'metadata' field
        "components": {
            "comp-1": {
                # Missing 'name' field
                "type": "vpc",
                # Missing 'config' field
            }
        },
        "connections": []
    }

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["warnings"]) > 0
    assert any("metadata" in warning.lower() for warning in data["warnings"])


def test_validate_architecture_empty_components(client, sample_empty_architecture):
    """Test validation with empty components."""
    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": sample_empty_architecture}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is True  # Empty components is technically valid
    assert data["component_count"] == 0
    assert data["connection_count"] == 0


# =============================================================================
# Integration Tests (Full Flow)
# =============================================================================


def test_full_flow_save_load_validate_generate(
    client,
    sample_designer_architecture,
    mock_architecture_repo,
    mock_terraform_generator
):
    """Test complete workflow: Save → Load → Validate → Generate."""
    # Setup mocks
    arch_id = str(uuid4())
    now = datetime.now(timezone.utc)

    saved_architecture = {
        "id": arch_id,
        "name": "Test Web App",
        "version": "1.0.0",
        "created_at": now,
        "updated_at": now,
        "definition": sample_designer_architecture
    }

    mock_architecture_repo.create.return_value = saved_architecture
    mock_architecture_repo.get.return_value = saved_architecture

    mock_terraform_generator.generate.return_value = {
        "main.tf": "provider \"aws\" {}",
        "vpc.tf": "resource \"aws_vpc\" \"main\" {}"
    }

    # Override dependencies
    from app.api.designer import get_architecture_repo, get_terraform_generator
    app.dependency_overrides[get_architecture_repo] = lambda: mock_architecture_repo
    app.dependency_overrides[get_terraform_generator] = lambda: mock_terraform_generator

    # Step 1: Save
    save_response = client.post(
        "/api/v1/designer/save",
        json={
            "name": "Test Web App",
            "description": "Test",
            "architecture_json": sample_designer_architecture
        }
    )
    assert save_response.status_code == status.HTTP_201_CREATED
    saved_id = save_response.json()["architecture_id"]

    # Step 2: Load
    load_response = client.get(f"/api/v1/designer/load/{saved_id}")
    assert load_response.status_code == status.HTTP_200_OK
    loaded_arch = load_response.json()

    # Step 3: Validate
    validate_response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": loaded_arch}
    )
    assert validate_response.status_code == status.HTTP_200_OK
    validation = validate_response.json()
    assert validation["valid"] is True

    # Step 4: Generate
    generate_response = client.post(
        "/api/v1/designer/generate-terraform",
        json={"architecture_json": loaded_arch}
    )
    assert generate_response.status_code == status.HTTP_200_OK
    terraform = generate_response.json()
    assert len(terraform["files"]) > 0

    # Cleanup
    app.dependency_overrides.clear()


def test_complex_architecture_with_all_validations(client):
    """Test complex architecture with multiple validation rules."""
    complex_arch = {
        "version": "1.0.0",
        "metadata": {
            "name": "Complex Web App",
            "description": "Multi-tier architecture",
            "provider": "aws",
            "region": "eu-central-1"
        },
        "components": {
            "vpc-main": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {
                    "cidr": "10.0.0.0/16",
                    "enableDns": True
                }
            },
            "subnet-public-a": {
                "name": "public-subnet-a",
                "type": "subnet",
                "config": {
                    "vpc_id": "vpc-main",
                    "cidr": "10.0.1.0/24",
                    "az": "eu-central-1a",
                    "subnetType": "public"
                }
            },
            "subnet-private-a": {
                "name": "private-subnet-a",
                "type": "subnet",
                "config": {
                    "vpc_id": "vpc-main",
                    "cidr": "10.0.2.0/24",
                    "az": "eu-central-1a",
                    "subnetType": "private"
                }
            },
            "sg-web": {
                "name": "web-sg",
                "type": "security_group",
                "config": {
                    "vpc": "vpc-main",
                    "description": "Web security group"
                }
            },
            "alb-main": {
                "name": "main-alb",
                "type": "alb",
                "config": {
                    "vpc": "vpc-main",
                    "subnets": ["subnet-public-a"],
                    "securityGroups": ["sg-web"]
                }
            }
        },
        "connections": [
            {"from": "vpc-main", "to": "subnet-public-a"},
            {"from": "vpc-main", "to": "subnet-private-a"},
            {"from": "sg-web", "to": "alb-main"},
            {"from": "subnet-public-a", "to": "alb-main"}
        ]
    }

    response = client.post(
        "/api/v1/designer/validate",
        json={"architecture_json": complex_arch}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is True
    assert data["component_count"] == 5
    assert data["connection_count"] == 4
    assert len(data["errors"]) == 0
