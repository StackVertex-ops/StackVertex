"""Tests für Cost Estimation API.

Testet Cost API Endpoints.
"""

import pytest

from app.schemas.cost import CostEstimateResponse


class TestCostAPI:
    """Tests für Cost API Endpoints."""

    def test_estimate_cost_from_json(self, test_client, sample_architecture_minimal):
        """Test: Cost Estimation von JSON."""
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "web_server",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {"instance_type": "t3.micro"}
            }
        ]

        response = test_client.post("/api/v1/costs/estimate", json=arch)

        assert response.status_code == 200

        data = response.json()
        assert "total_hourly" in data
        assert "total_monthly" in data
        assert "total_yearly" in data
        assert "components" in data

        assert data["total_monthly"] > 0
        assert len(data["components"]) == 1

    def test_estimate_cost_empty_architecture(self, test_client, sample_architecture_minimal):
        """Test: Cost Estimation für leere Architecture."""
        response = test_client.post("/api/v1/costs/estimate", json=sample_architecture_minimal)

        assert response.status_code == 200

        data = response.json()
        assert data["total_monthly"] == 0
        assert len(data["components"]) == 0

    def test_estimate_cost_multiple_components(self, test_client, sample_architecture_minimal):
        """Test: Cost Estimation mit mehreren Components."""
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "web",
                "type": "ec2",
                "name": "Web Server",
                "configuration": {"instance_type": "t3.small"}
            },
            {
                "id": "db",
                "type": "rds",
                "name": "Database",
                "configuration": {
                    "instance_class": "db.t3.micro",
                    "allocated_storage": 20
                }
            },
            {
                "id": "storage",
                "type": "s3",
                "name": "Storage",
                "configuration": {"estimated_storage_gb": 100}
            }
        ]

        response = test_client.post("/api/v1/costs/estimate", json=arch)

        assert response.status_code == 200

        data = response.json()
        assert len(data["components"]) == 3
        assert "breakdown_by_type" in data
        assert "ec2" in data["breakdown_by_type"]
        assert "rds" in data["breakdown_by_type"]
        assert "s3" in data["breakdown_by_type"]

    @pytest.mark.skip(reason="DB Session isolation issue - tested via integration tests")
    def test_estimate_cost_for_saved_architecture(
        self, test_client, db_engine, db_session, sample_architecture_minimal, clear_db
    ):
        """Test: Cost Estimation für gespeicherte Architecture."""
        # Create architecture
        create_response = test_client.post(
            "/api/v1/architectures",
            json={
                "name": "Test Architecture",
                "owner": "test-user",
                "architecture_json": sample_architecture_minimal
            }
        )

        assert create_response.status_code == 201
        arch_id = create_response.json()["id"]

        # Estimate cost
        response = test_client.get(f"/api/v1/costs/architectures/{arch_id}/estimate")

        assert response.status_code == 200

        data = response.json()
        assert "total_monthly" in data

    @pytest.mark.skip(reason="DB Session isolation issue - tested via integration tests")
    def test_estimate_cost_architecture_not_found(self, test_client, db_engine):
        """Test: Cost Estimation für nicht-existente Architecture."""
        from uuid import uuid4

        fake_id = str(uuid4())
        response = test_client.get(f"/api/v1/costs/architectures/{fake_id}/estimate")

        assert response.status_code == 404

    def test_estimate_cost_breakdown(self, test_client, sample_architecture_minimal):
        """Test: Cost Breakdown Details."""
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "db",
                "type": "rds",
                "name": "Database",
                "configuration": {
                    "instance_class": "db.t3.micro",
                    "allocated_storage": 50,
                    "storage_type": "gp3"
                }
            }
        ]

        response = test_client.post("/api/v1/costs/estimate", json=arch)

        assert response.status_code == 200

        data = response.json()
        component = data["components"][0]

        # RDS sollte breakdown haben
        assert "breakdown" in component
        assert "instance" in component["breakdown"]
        assert "storage" in component["breakdown"]

    def test_estimate_cost_response_format(self, test_client, sample_architecture_minimal):
        """Test: Response Format entspricht Schema."""
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {"id": "test", "type": "ec2", "name": "Test", "configuration": {}}
        ]

        response = test_client.post("/api/v1/costs/estimate", json=arch)

        assert response.status_code == 200

        data = response.json()

        # Validate against schema (basic checks)
        assert isinstance(data["total_hourly"], float)
        assert isinstance(data["total_monthly"], float)
        assert isinstance(data["total_yearly"], float)
        assert isinstance(data["currency"], str)
        assert isinstance(data["components"], list)
        assert isinstance(data["breakdown_by_type"], dict)

    def test_estimate_cost_lambda_with_free_tier(self, test_client, sample_architecture_minimal):
        """Test: Lambda Cost mit Free Tier."""
        arch = sample_architecture_minimal.copy()
        arch["architecture"]["components"] = [
            {
                "id": "func",
                "type": "lambda",
                "name": "Function",
                "configuration": {
                    "estimated_monthly_requests": 500000,  # Under free tier
                    "memory_size": 128,
                    "average_duration_seconds": 0.1
                }
            }
        ]

        response = test_client.post("/api/v1/costs/estimate", json=arch)

        assert response.status_code == 200

        data = response.json()
        # Should be very low or zero cost with free tier
        assert data["total_monthly"] >= 0
