"""Deployment API Endpoint Tests.

Tests für Deployment Management Endpoints.
"""

import pytest
from uuid import uuid4
from fastapi import status
from unittest.mock import patch, MagicMock


# ============================================================================
# POST /architectures/{id}/deploy - Start Deployment
# ============================================================================


def test_deploy_architecture_success(user_client, architecture_repository, sample_architecture_json):
    """Test: POST /architectures/{id}/deploy - Erfolgreicher Deployment Start."""
    # Create architecture
    from app.schemas.architecture import ArchitectureCreate

    arch = ArchitectureCreate(
        name="Test Architecture",
        description="Test description",
        version="1.0.0",
        architecture_json=sample_architecture_json,
        owner="test_user"
    )
    created = architecture_repository.create(arch)
    arch_id = created["id"]

    # Mock DeploymentManager to avoid actual Terraform execution
    with patch("app.api.deployments.deployment_manager") as mock_manager:
        mock_deployment_id = str(uuid4())
        mock_manager.start_deployment.return_value = mock_deployment_id

        # Mock repository.get to return deployment
        deployment_payload = {
            "architecture_id": arch_id,
            "deployed_by": "test_user",
            "aws_credentials": {
                "access_key_id": "test_key",
                "secret_access_key": "test_secret",
                "region": "us-east-1"
            }
        }

        response = user_client.post(
            f"/api/v1/architectures/{arch_id}/deploy",
            json=deployment_payload
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["architecture_id"] == arch_id
        assert data["deployed_by"] == "test_user"
        assert "status" in data


def test_deploy_architecture_not_found(user_client):
    """Test: POST /architectures/{id}/deploy - 404 wenn Architecture nicht existiert."""
    non_existent_id = str(uuid4())

    deployment_payload = {
        "architecture_id": non_existent_id,
        "deployed_by": "test_user",
        "aws_credentials": {
            "access_key_id": "test_key",
            "secret_access_key": "test_secret",
            "region": "us-east-1"
        }
    }

    response = user_client.post(
        f"/api/v1/architectures/{non_existent_id}/deploy",
        json=deployment_payload
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deploy_architecture_unauthorized(client, architecture_repository, sample_architecture_json):
    """Test: POST /architectures/{id}/deploy - Unauthorized ohne Auth."""
    # Create architecture
    from app.schemas.architecture import ArchitectureCreate

    arch = ArchitectureCreate(
        name="Test Architecture",
        description="Test description",
        version="1.0.0",
        architecture_json=sample_architecture_json,
        owner="test_user"
    )
    created = architecture_repository.create(arch)
    arch_id = created["id"]

    deployment_payload = {
        "architecture_id": arch_id,
        "deployed_by": "test_user"
    }

    response = client.post(
        f"/api/v1/architectures/{arch_id}/deploy",
        json=deployment_payload
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# GET /deployments/{id} - Get Deployment Status
# ============================================================================


def test_get_deployment_status_success(user_client, deployment_repository, architecture_repository, sample_architecture_json):
    """Test: GET /deployments/{id} - Hole Deployment Status mit Progress."""
    # Create architecture first
    from app.schemas.architecture import ArchitectureCreate

    arch = ArchitectureCreate(
        name="Test Architecture",
        description="Test description",
        version="1.0.0",
        architecture_json=sample_architecture_json,
        owner="test_user"
    )
    created_arch = architecture_repository.create(arch)

    # Create deployment
    from app.schemas.deployment import DeploymentCreate
    from uuid import UUID

    deployment = DeploymentCreate(
        architecture_id=UUID(created_arch["id"]),
        deployed_by="test_user"
    )
    created_deployment = deployment_repository.create(deployment)
    deployment_id = created_deployment["id"]

    response = user_client.get(f"/api/v1/deployments/{deployment_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == deployment_id
    assert data["architecture_id"] == created_arch["id"]
    assert data["deployed_by"] == "test_user"
    assert "status" in data
    assert "progress_percentage" in data
    assert "current_step" in data
    assert "elapsed_seconds" in data


def test_get_deployment_status_not_found(user_client):
    """Test: GET /deployments/{id} - 404 wenn Deployment nicht gefunden."""
    non_existent_id = str(uuid4())

    response = user_client.get(f"/api/v1/deployments/{non_existent_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# GET /deployments - List Deployments
# ============================================================================


def test_list_deployments_success(user_client, deployment_repository, architecture_repository, sample_architecture_json):
    """Test: GET /deployments - Liste alle Deployments."""
    # Create architecture
    from app.schemas.architecture import ArchitectureCreate

    arch = ArchitectureCreate(
        name="Test Architecture",
        description="Test description",
        version="1.0.0",
        architecture_json=sample_architecture_json,
        owner="test_user"
    )
    created_arch = architecture_repository.create(arch)

    # Create multiple deployments
    from app.schemas.deployment import DeploymentCreate
    from uuid import UUID

    for i in range(3):
        deployment = DeploymentCreate(
            architecture_id=UUID(created_arch["id"]),
            deployed_by=f"user_{i}"
        )
        deployment_repository.create(deployment)

    response = user_client.get("/api/v1/deployments")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


def test_list_deployments_with_pagination(user_client, deployment_repository, architecture_repository, sample_architecture_json):
    """Test: GET /deployments - Pagination funktioniert."""
    # Create architecture
    from app.schemas.architecture import ArchitectureCreate

    arch = ArchitectureCreate(
        name="Test Architecture",
        description="Test description",
        version="1.0.0",
        architecture_json=sample_architecture_json,
        owner="test_user"
    )
    created_arch = architecture_repository.create(arch)

    # Create 5 deployments
    from app.schemas.deployment import DeploymentCreate
    from uuid import UUID

    for i in range(5):
        deployment = DeploymentCreate(
            architecture_id=UUID(created_arch["id"]),
            deployed_by=f"user_{i}"
        )
        deployment_repository.create(deployment)

    response = user_client.get("/api/v1/deployments?skip=0&limit=2")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    assert data["skip"] == 0
    assert data["limit"] == 2


# Note: /cancel endpoint wurde entfernt - Deployments können nur destroyed werden


# ============================================================================
# DELETE /deployments/{id} - Destroy Deployment
# ============================================================================


@patch("app.services.deployment_manager.DeploymentManager.destroy_deployment")
def test_destroy_deployment_success(mock_destroy, user_client, deployment_repository, architecture_repository, sample_architecture_json):
    """Test: DELETE /deployments/{id} - Infrastructure zerstören."""
    # Create architecture and deployment
    from app.schemas.architecture import ArchitectureCreate

    arch = ArchitectureCreate(
        name="Test Architecture",
        description="Test description",
        version="1.0.0",
        architecture_json=sample_architecture_json,
        owner="test_user"
    )
    created_arch = architecture_repository.create(arch)

    from app.schemas.deployment import DeploymentCreate
    from uuid import UUID

    deployment = DeploymentCreate(
        architecture_id=UUID(created_arch["id"]),
        deployed_by="test_user"
    )
    created_deployment = deployment_repository.create(deployment)
    deployment_id = created_deployment["id"]

    # Mock destroy
    mock_destroy.return_value = True

    response = user_client.delete(f"/api/v1/deployments/{deployment_id}")

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]


def test_destroy_deployment_not_found(user_client):
    """Test: DELETE /deployments/{id} - 404 wenn nicht gefunden."""
    non_existent_id = str(uuid4())

    response = user_client.delete(f"/api/v1/deployments/{non_existent_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
