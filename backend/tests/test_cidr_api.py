"""Tests für CIDR API Endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestCIDRValidateEndpoint:
    """Tests für /api/v1/cidr/validate"""

    def test_validate_valid_cidr(self, user_client):
        """Test Validierung eines gültigen CIDR Blocks"""
        response = user_client.post(
            "/api/v1/cidr/validate",
            json={"cidr": "10.0.0.0/16"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["cidr"] == "10.0.0.0/16"
        assert data["total_ips"] == 65536
        assert data["usable_ips"] == 65531
        assert data["error"] is None

    def test_validate_invalid_cidr_too_small(self, user_client):
        """Test Validierung eines zu kleinen CIDR Blocks"""
        response = user_client.post(
            "/api/v1/cidr/validate",
            json={"cidr": "10.0.0.0/8"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "mindestens /16" in data["error"]

    def test_validate_invalid_cidr_format(self, user_client):
        """Test Validierung eines ungültigen CIDR Formats"""
        response = user_client.post(
            "/api/v1/cidr/validate",
            json={"cidr": "not-a-cidr"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "Ungültige CIDR Notation" in data["error"]

    def test_validate_public_ip_warning(self, user_client):
        """Test Warnung bei öffentlicher IP-Range"""
        response = user_client.post(
            "/api/v1/cidr/validate",
            json={"cidr": "8.8.8.0/24"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["warning"] is not None
        assert "Warnung" in data["warning"]


class TestCIDRValidateSubnetEndpoint:
    """Tests für /api/v1/cidr/validate-subnet"""

    def test_validate_subnet_within_vpc(self, user_client):
        """Test Validierung eines Subnets innerhalb VPC"""
        response = user_client.post(
            "/api/v1/cidr/validate-subnet",
            json={
                "subnet_cidr": "10.0.1.0/24",
                "vpc_cidr": "10.0.0.0/16"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["subnet_cidr"] == "10.0.1.0/24"
        assert data["vpc_cidr"] == "10.0.0.0/16"
        assert data["total_ips"] == 256
        assert data["usable_ips"] == 251

    def test_validate_subnet_outside_vpc(self, user_client):
        """Test Validierung eines Subnets außerhalb VPC"""
        response = user_client.post(
            "/api/v1/cidr/validate-subnet",
            json={
                "subnet_cidr": "192.168.1.0/24",
                "vpc_cidr": "10.0.0.0/16"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "außerhalb der VPC" in data["error"]

    def test_validate_subnet_invalid_vpc(self, user_client):
        """Test Validierung mit ungültigem VPC CIDR"""
        response = user_client.post(
            "/api/v1/cidr/validate-subnet",
            json={
                "subnet_cidr": "10.0.1.0/24",
                "vpc_cidr": "invalid"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Ungültiger VPC CIDR" in data["detail"]


class TestCIDRPlanEndpoint:
    """Tests für /api/v1/cidr/plan"""

    def test_plan_vpc_no_subnets(self, user_client):
        """Test VPC Plan ohne Subnets"""
        response = user_client.post(
            "/api/v1/cidr/plan",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "subnets": []
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["vpc_cidr"] == "10.0.0.0/16"
        assert data["total_ips"] == 65536
        assert data["usable_ips"] == 65531
        assert len(data["subnets"]) == 0
        assert data["unallocated_ips"] == 65536
        assert data["has_overlaps"] is False

    def test_plan_vpc_with_valid_subnets(self, user_client):
        """Test VPC Plan mit gültigen Subnets"""
        response = user_client.post(
            "/api/v1/cidr/plan",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "subnets": [
                    {
                        "name": "public-1a",
                        "cidr": "10.0.1.0/24",
                        "type": "public",
                        "az": "us-east-1a"
                    },
                    {
                        "name": "private-1a",
                        "cidr": "10.0.2.0/24",
                        "type": "private",
                        "az": "us-east-1a"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["subnets"]) == 2
        assert data["has_overlaps"] is False
        assert data["unallocated_ips"] == 65536 - 256 - 256

        # Check first subnet details
        subnet1 = data["subnets"][0]
        assert subnet1["name"] == "public-1a"
        assert subnet1["cidr"] == "10.0.1.0/24"
        assert subnet1["subnet_type"] == "public"
        assert subnet1["availability_zone"] == "us-east-1a"
        assert subnet1["total_ips"] == 256
        assert subnet1["usable_ips"] == 251
        assert len(subnet1["reserved_ips"]) == 5

    def test_plan_vpc_with_overlapping_subnets(self, user_client):
        """Test VPC Plan mit überlappenden Subnets"""
        response = user_client.post(
            "/api/v1/cidr/plan",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "subnets": [
                    {
                        "name": "subnet-1",
                        "cidr": "10.0.1.0/24",
                        "type": "public"
                    },
                    {
                        "name": "subnet-2",
                        "cidr": "10.0.1.0/24",
                        "type": "private"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["has_overlaps"] is True
        assert len(data["overlap_details"]) > 0
        assert "Overlap" in data["overlap_details"][0]

    def test_plan_vpc_invalid_vpc_cidr(self, user_client):
        """Test VPC Plan mit ungültigem VPC CIDR"""
        response = user_client.post(
            "/api/v1/cidr/plan",
            json={
                "vpc_cidr": "10.0.0.0/8",  # Zu klein
                "subnets": []
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "mindestens /16" in data["detail"]

    def test_plan_vpc_subnet_outside_range(self, user_client):
        """Test VPC Plan mit Subnet außerhalb VPC"""
        response = user_client.post(
            "/api/v1/cidr/plan",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "subnets": [
                    {
                        "name": "invalid",
                        "cidr": "192.168.1.0/24",
                        "type": "public"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["has_overlaps"] is True
        assert "außerhalb der VPC" in data["overlap_details"][0]


class TestCIDRSuggestEndpoint:
    """Tests für /api/v1/cidr/suggest"""

    def test_suggest_default_parameters(self, user_client):
        """Test Subnet-Vorschläge mit Standard-Parametern"""
        response = user_client.post(
            "/api/v1/cidr/suggest",
            json={
                "vpc_cidr": "10.0.0.0/16"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["vpc_cidr"] == "10.0.0.0/16"
        assert data["num_azs"] == 3
        # 3 AZs * 3 Typen = 9 Subnets
        assert len(data["suggested_subnets"]) == 9

        # Check structure
        subnet = data["suggested_subnets"][0]
        assert "name" in subnet
        assert "cidr" in subnet
        assert "type" in subnet
        assert "az" in subnet

    def test_suggest_custom_azs(self, user_client):
        """Test Subnet-Vorschläge mit custom AZ-Anzahl"""
        response = user_client.post(
            "/api/v1/cidr/suggest",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "num_azs": 2
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 2 AZs * 3 Typen = 6 Subnets
        assert len(data["suggested_subnets"]) == 6

    def test_suggest_custom_subnet_types(self, user_client):
        """Test Subnet-Vorschläge mit custom Subnet-Typen"""
        response = user_client.post(
            "/api/v1/cidr/suggest",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "num_azs": 3,
                "subnet_types": ["public", "private"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 3 AZs * 2 Typen = 6 Subnets
        assert len(data["suggested_subnets"]) == 6

    def test_suggest_invalid_vpc_cidr(self, user_client):
        """Test Subnet-Vorschläge mit ungültigem VPC CIDR"""
        response = user_client.post(
            "/api/v1/cidr/suggest",
            json={
                "vpc_cidr": "invalid"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Ungültige CIDR Notation" in data["detail"]

    def test_suggest_invalid_num_azs(self, user_client):
        """Test Subnet-Vorschläge mit ungültiger AZ-Anzahl"""
        response = user_client.post(
            "/api/v1/cidr/suggest",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "num_azs": 10  # Max ist 6
            }
        )

        assert response.status_code == 422  # Validation error


class TestCIDREndpointsIntegration:
    """Integrationstests für CIDR API"""

    def test_full_workflow(self, user_client):
        """Test kompletter Workflow: Validate → Suggest → Plan"""

        # 1. Validate VPC
        validate_response = user_client.post(
            "/api/v1/cidr/validate",
            json={"cidr": "10.0.0.0/16"}
        )
        assert validate_response.status_code == 200
        assert validate_response.json()["valid"] is True

        # 2. Get suggestions
        suggest_response = user_client.post(
            "/api/v1/cidr/suggest",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "num_azs": 2,
                "subnet_types": ["public", "private"]
            }
        )
        assert suggest_response.status_code == 200
        suggested_subnets = suggest_response.json()["suggested_subnets"]

        # 3. Plan VPC with suggestions
        plan_response = user_client.post(
            "/api/v1/cidr/plan",
            json={
                "vpc_cidr": "10.0.0.0/16",
                "subnets": suggested_subnets
            }
        )
        assert plan_response.status_code == 200
        plan = plan_response.json()

        assert plan["has_overlaps"] is False
        assert len(plan["subnets"]) == 4  # 2 AZs * 2 types
        assert plan["unallocated_ips"] > 0
