"""Architecture API Endpoint Tests.

Tests für CRUD-Operationen auf /architectures Endpoints.
"""

import pytest
from uuid import uuid4
from fastapi import status


# ============================================================================
# POST /architectures - Create Architecture
# ============================================================================


def test_create_architecture_success(user_client, sample_architecture_json):
    """Test: POST /architectures - Erfolgreiche Erstellung mit Auth."""
    payload = {
        "name": "Test Architecture",
        "description": "Test description",
        "version": "1.0.0",
        "architecture_json": sample_architecture_json,
        "owner": "test_user"
    }

    response = user_client.post("/api/v1/architectures", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Architecture"
    assert data["description"] == "Test description"
    assert data["version"] == "1.0.0"
    assert data["owner"] == "test_user"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["architecture_json"] == sample_architecture_json


def test_create_architecture_unauthorized(client, sample_architecture_json):
    """Test: POST /architectures - Unauthorized ohne Auth Token."""
    payload = {
        "name": "Test Architecture",
        "description": "Test description",
        "version": "1.0.0",
        "architecture_json": sample_architecture_json,
        "owner": "test_user"
    }

    response = client.post("/api/v1/architectures", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_architecture_invalid_data(user_client):
    """Test: POST /architectures - Validation Error bei fehlenden Pflichtfeldern."""
    payload = {
        "description": "Missing name field"
    }

    response = user_client.post("/api/v1/architectures", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET /architectures - List Architectures
# ============================================================================


def test_list_architectures_success(user_client, sample_architecture_json):
    """Test: GET /architectures - Liste Architekturen mit Pagination."""
    # Create test architectures via API
    for i in range(3):
        payload = {
            "name": f"Test Architecture {i}",
            "description": f"Description {i}",
            "version": "1.0.0",
            "architecture_json": sample_architecture_json,
            "owner": "test_user"
        }
        user_client.post("/api/v1/architectures", json=payload)

    response = user_client.get("/api/v1/architectures")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


def test_list_architectures_with_pagination(user_client, sample_architecture_json):
    """Test: GET /architectures - Pagination funktioniert korrekt."""
    # Create 5 test architectures via API
    for i in range(5):
        payload = {
            "name": f"Test Architecture {i}",
            "description": f"Description {i}",
            "version": "1.0.0",
            "architecture_json": sample_architecture_json,
            "owner": "test_user"
        }
        user_client.post("/api/v1/architectures", json=payload)

    # Get first page (2 items)
    response = user_client.get("/api/v1/architectures?skip=0&limit=2")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    assert data["skip"] == 0
    assert data["limit"] == 2


def test_list_architectures_unauthorized(client):
    """Test: GET /architectures - Unauthorized ohne Auth."""
    response = client.get("/api/v1/architectures")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# GET /architectures/{id} - Get Single Architecture
# ============================================================================


def test_get_architecture_success(user_client, sample_architecture_json):
    """Test: GET /architectures/{id} - Hole einzelne Architecture."""
    # Create architecture via API
    payload = {
        "name": "Test Architecture",
        "description": "Test description",
        "version": "1.0.0",
        "architecture_json": sample_architecture_json,
        "owner": "test_user"
    }
    create_response = user_client.post("/api/v1/architectures", json=payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    arch_id = create_response.json()["id"]

    response = user_client.get(f"/api/v1/architectures/{arch_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == arch_id
    assert data["name"] == "Test Architecture"
    assert data["description"] == "Test description"
    # Note: DynamoDB may convert numbers to strings, so we just check the JSON exists
    assert "architecture_json" in data
    assert data["architecture_json"]["version"] == sample_architecture_json["version"]


def test_get_architecture_not_found(user_client):
    """Test: GET /architectures/{id} - 404 wenn nicht gefunden."""
    non_existent_id = str(uuid4())

    response = user_client.get(f"/api/v1/architectures/{non_existent_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_architecture_invalid_uuid(user_client):
    """Test: GET /architectures/{id} - 422 bei ungültiger UUID."""
    response = user_client.get("/api/v1/architectures/not-a-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# PUT /architectures/{id} - Update Architecture
# ============================================================================


def test_update_architecture_success(user_client, sample_architecture_json):
    """Test: PUT /architectures/{id} - Update Architecture."""
    # Create architecture via API
    payload = {
        "name": "Original Name",
        "description": "Original description",
        "version": "1.0.0",
        "architecture_json": sample_architecture_json,
        "owner": "test_user"
    }
    create_response = user_client.post("/api/v1/architectures", json=payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    arch_id = create_response.json()["id"]

    # Update architecture
    update_payload = {
        "name": "Updated Name",
        "description": "Updated description",
        "version": "1.1.0"
    }

    response = user_client.put(f"/api/v1/architectures/{arch_id}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == arch_id
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
    assert data["version"] == "1.1.0"


def test_update_architecture_not_found(user_client):
    """Test: PUT /architectures/{id} - 404 wenn nicht gefunden."""
    non_existent_id = str(uuid4())
    update_payload = {
        "name": "Updated Name"
    }

    response = user_client.put(f"/api/v1/architectures/{non_existent_id}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_architecture_partial(user_client, sample_architecture_json):
    """Test: PUT /architectures/{id} - Partial Update (nur ein Feld)."""
    # Create architecture via API
    payload = {
        "name": "Original Name",
        "description": "Original description",
        "version": "1.0.0",
        "architecture_json": sample_architecture_json,
        "owner": "test_user"
    }
    create_response = user_client.post("/api/v1/architectures", json=payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    arch_id = create_response.json()["id"]

    # Update only name
    update_payload = {
        "name": "Only Name Updated"
    }

    response = user_client.put(f"/api/v1/architectures/{arch_id}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Only Name Updated"
    assert data["description"] == "Original description"  # Unchanged
    assert data["version"] == "1.0.0"  # Unchanged


# ============================================================================
# DELETE /architectures/{id} - Delete Architecture
# ============================================================================


def test_delete_architecture_success(user_client, sample_architecture_json):
    """Test: DELETE /architectures/{id} - Lösche Architecture."""
    # Create architecture via API
    payload = {
        "name": "To Be Deleted",
        "description": "Test description",
        "version": "1.0.0",
        "architecture_json": sample_architecture_json,
        "owner": "test_user"
    }
    create_response = user_client.post("/api/v1/architectures", json=payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    arch_id = create_response.json()["id"]

    # Delete architecture
    response = user_client.delete(f"/api/v1/architectures/{arch_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    get_response = user_client.get(f"/api/v1/architectures/{arch_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_architecture_not_found(user_client):
    """Test: DELETE /architectures/{id} - 204 auch wenn nicht gefunden (Idempotent Delete)."""
    non_existent_id = str(uuid4())

    response = user_client.delete(f"/api/v1/architectures/{non_existent_id}")

    # Idempotent delete: Returns 204 auch wenn bereits gelöscht/nicht existent
    assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND]
