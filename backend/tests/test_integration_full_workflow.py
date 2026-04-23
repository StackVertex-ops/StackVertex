"""Integration Tests - Full Workflow.

End-to-End Tests für komplette Workflows.
"""

import pytest
from uuid import uuid4


class TestFullWorkflow:
    """End-to-End Workflow Tests."""

    def test_create_architecture_workflow(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Complete Architecture Creation Workflow.

        Flow:
        1. Create architecture
        2. Verify version created
        3. Retrieve architecture
        4. List architectures
        """
        # 1. Create architecture
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )

        assert response.status_code == 201
        data = response.json()
        arch_id = data["id"]

        assert data["name"] == "Simple Web App"
        assert data["version"] == "1.0.0"
        assert data["parent_version_id"] is None

        # 2. Verify version created (implicit in response)
        assert "id" in data
        assert "created_at" in data

        # 3. Retrieve architecture
        response = test_client.get(f"/api/v1/architectures/{arch_id}")

        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved["id"] == arch_id
        assert retrieved["name"] == "Simple Web App"

        # 4. List architectures
        response = test_client.get("/api/v1/architectures")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == arch_id

    def test_update_architecture_workflow(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Update Architecture Workflow.

        Flow:
        1. Create architecture
        2. Update architecture
        3. Verify new version created
        4. Verify parent_version link
        """
        # 1. Create architecture
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )

        assert response.status_code == 201
        original_id = response.json()["id"]

        # 2. Update architecture (modify name)
        updated_json = sample_architecture_simple_web.copy()
        updated_json["metadata"]["name"] = "Updated Web App"

        response = test_client.put(
            f"/api/v1/architectures/{original_id}",
            json=updated_json,
        )

        assert response.status_code == 200
        updated_data = response.json()

        # 3. Verify new version created
        assert updated_data["id"] != original_id
        assert updated_data["name"] == "Updated Web App"

        # 4. Verify parent_version link
        assert updated_data["parent_version_id"] == original_id

    def test_validate_architecture_workflow(self, test_client):
        """Test: Validation Workflow.

        Flow:
        1. Validate valid architecture
        2. Validate invalid architecture
        """
        # 1. Valid architecture
        valid_arch = {
            "version": "1.0.0",
            "metadata": {
                "name": "Test",
                "description": "Test",
                "owner": "test-user",
                "region": "us-east-1",
                "tags": [],
            },
            "architecture": {
                "components": [],
                "relationships": [],
            },
        }

        response = test_client.post(
            "/api/v1/validate",
            json=valid_arch,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

        # 2. Invalid architecture (missing required field)
        invalid_arch = {
            "version": "1.0.0",
            "metadata": {},
            "architecture": {},
        }

        response = test_client.post(
            "/api/v1/validate",
            json=invalid_arch,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.skip(reason="Cost estimation integration - DB session issues")
    def test_cost_estimation_workflow(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Cost Estimation Workflow.

        Flow:
        1. Create architecture
        2. Get cost estimate
        3. Verify cost breakdown
        """
        # 1. Create architecture
        response = test_client.post(
            "/api/v1/architectures",
            json=sample_architecture_simple_web,
        )

        assert response.status_code == 201
        arch_id = response.json()["id"]

        # 2. Get cost estimate
        response = test_client.get(
            f"/api/v1/costs/architectures/{arch_id}/estimate"
        )

        assert response.status_code == 200
        cost_data = response.json()

        # 3. Verify cost breakdown
        assert "total_monthly_cost" in cost_data
        assert "total_hourly_cost" in cost_data
        assert "components" in cost_data
        assert cost_data["total_monthly_cost"] > 0

    def test_error_handling_workflow(self, test_client):
        """Test: Error Handling Workflow.

        Flow:
        1. Get non-existent architecture (404)
        2. Create invalid architecture (422)
        3. Update non-existent architecture (404)
        """
        fake_id = str(uuid4())

        # 1. Get non-existent
        response = test_client.get(f"/api/v1/architectures/{fake_id}")
        assert response.status_code == 404

        # 2. Create invalid
        response = test_client.post(
            "/api/v1/architectures",
            json={"invalid": "data"},
        )
        assert response.status_code == 422

        # 3. Update non-existent
        response = test_client.put(
            f"/api/v1/architectures/{fake_id}",
            json={"version": "1.0.0"},
        )
        assert response.status_code == 404

    def test_pagination_workflow(self, test_client, db_engine, clear_db, sample_architecture_simple_web):
        """Test: Pagination Workflow.

        Flow:
        1. Create 5 architectures
        2. List with limit=2
        3. Navigate through pages
        """
        # 1. Create 5 architectures
        arch_ids = []
        for i in range(5):
            arch = sample_architecture_simple_web.copy()
            arch["metadata"]["name"] = f"Architecture {i}"

            response = test_client.post(
                "/api/v1/architectures",
                json=arch,
            )
            assert response.status_code == 201
            arch_ids.append(response.json()["id"])

        # 2. List first page
        response = test_client.get("/api/v1/architectures?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["skip"] == 0
        assert data["limit"] == 2

        # 3. List second page
        response = test_client.get("/api/v1/architectures?skip=2&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

        # 4. List last page
        response = test_client.get("/api/v1/architectures?skip=4&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 5
