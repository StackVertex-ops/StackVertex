"""Tests für CIDR Calculator Utilities."""

import pytest
from app.utils.cidr_calculator import (
    calculate_usable_ips,
    get_reserved_ips,
    check_cidr_overlap,
    validate_vpc_cidr,
    validate_subnet_cidr,
    plan_vpc,
    suggest_subnet_split,
    SubnetAllocation,
    VPCPlan
)


class TestCalculateUsableIPs:
    """Tests für calculate_usable_ips()"""

    def test_standard_subnet(self):
        """Test /24 Subnet (256 IPs)"""
        total, usable = calculate_usable_ips("10.0.1.0/24")
        assert total == 256
        assert usable == 251  # 256 - 5 reserved

    def test_large_subnet(self):
        """Test /16 VPC (65536 IPs)"""
        total, usable = calculate_usable_ips("10.0.0.0/16")
        assert total == 65536
        assert usable == 65531

    def test_small_subnet(self):
        """Test /28 Subnet (16 IPs)"""
        total, usable = calculate_usable_ips("10.0.1.0/28")
        assert total == 16
        assert usable == 11  # 16 - 5

    def test_tiny_subnet(self):
        """Test /30 Subnet (4 IPs) - zu klein für AWS, aber valid CIDR"""
        total, usable = calculate_usable_ips("10.0.1.0/30")
        assert total == 4
        assert usable == 0  # max(0, 4-5) = 0


class TestGetReservedIPs:
    """Tests für get_reserved_ips()"""

    def test_standard_subnet_reserved_ips(self):
        """Test Reserved IPs für /24 Subnet"""
        reserved = get_reserved_ips("10.0.1.0/24")
        assert len(reserved) == 5
        assert reserved[0] == "10.0.1.0"  # Network
        assert reserved[1] == "10.0.1.1"  # VPC Router
        assert reserved[2] == "10.0.1.2"  # DNS
        assert reserved[3] == "10.0.1.3"  # Reserved
        assert reserved[4] == "10.0.1.255"  # Broadcast

    def test_small_subnet_reserved_ips(self):
        """Test Reserved IPs für kleines Subnet"""
        reserved = get_reserved_ips("10.0.1.0/28")
        assert len(reserved) == 5
        assert reserved[0] == "10.0.1.0"
        assert reserved[4] == "10.0.1.15"


class TestCheckCIDROverlap:
    """Tests für check_cidr_overlap()"""

    def test_no_overlap(self):
        """Test keine Überlappung"""
        assert not check_cidr_overlap("10.0.1.0/24", "10.0.2.0/24")

    def test_complete_overlap(self):
        """Test komplette Überlappung (identisch)"""
        assert check_cidr_overlap("10.0.1.0/24", "10.0.1.0/24")

    def test_partial_overlap(self):
        """Test teilweise Überlappung"""
        assert check_cidr_overlap("10.0.0.0/16", "10.0.1.0/24")

    def test_adjacent_no_overlap(self):
        """Test angrenzende Subnets (keine Überlappung)"""
        assert not check_cidr_overlap("10.0.1.0/24", "10.0.2.0/24")


class TestValidateVPCCIDR:
    """Tests für validate_vpc_cidr()"""

    def test_valid_vpc_cidr(self):
        """Test gültiger VPC CIDR"""
        is_valid, error = validate_vpc_cidr("10.0.0.0/16")
        assert is_valid
        assert error is None

    def test_vpc_too_small(self):
        """Test VPC CIDR zu klein (< /16)"""
        is_valid, error = validate_vpc_cidr("10.0.0.0/8")
        assert not is_valid
        assert "mindestens /16" in error

    def test_vpc_too_large(self):
        """Test VPC CIDR zu groß (> /28)"""
        is_valid, error = validate_vpc_cidr("10.0.0.0/29")
        assert not is_valid
        assert "höchstens /28" in error

    def test_public_ip_warning(self):
        """Test öffentliche IP-Range (Warnung aber valid)"""
        is_valid, error = validate_vpc_cidr("8.8.8.0/24")
        assert is_valid
        assert error is not None
        assert "Warnung" in error

    def test_invalid_cidr_format(self):
        """Test ungültiges CIDR Format"""
        is_valid, error = validate_vpc_cidr("not-a-cidr")
        assert not is_valid
        assert "Ungültige CIDR Notation" in error


class TestValidateSubnetCIDR:
    """Tests für validate_subnet_cidr()"""

    def test_valid_subnet(self):
        """Test gültiges Subnet innerhalb VPC"""
        is_valid, error = validate_subnet_cidr("10.0.1.0/24", "10.0.0.0/16")
        assert is_valid
        assert error is None

    def test_subnet_outside_vpc(self):
        """Test Subnet außerhalb VPC"""
        is_valid, error = validate_subnet_cidr("192.168.1.0/24", "10.0.0.0/16")
        assert not is_valid
        assert "außerhalb der VPC" in error

    def test_subnet_too_large(self):
        """Test Subnet zu groß (> /28)"""
        is_valid, error = validate_subnet_cidr("10.0.1.0/29", "10.0.0.0/16")
        assert not is_valid
        assert "höchstens /28" in error


class TestPlanVPC:
    """Tests für plan_vpc()"""

    def test_empty_vpc(self):
        """Test VPC ohne Subnets"""
        plan = plan_vpc("10.0.0.0/16", [])
        assert plan.vpc_cidr == "10.0.0.0/16"
        assert plan.total_ips == 65536
        assert len(plan.subnets) == 0
        assert plan.unallocated_ips == 65536
        assert not plan.has_overlaps

    def test_vpc_with_valid_subnets(self):
        """Test VPC mit gültigen Subnets"""
        subnets = [
            {"name": "public-1a", "cidr": "10.0.1.0/24", "type": "public", "az": "us-east-1a"},
            {"name": "private-1a", "cidr": "10.0.2.0/24", "type": "private", "az": "us-east-1a"},
        ]

        plan = plan_vpc("10.0.0.0/16", subnets)

        assert len(plan.subnets) == 2
        assert not plan.has_overlaps
        assert plan.unallocated_ips == 65536 - 256 - 256

    def test_vpc_with_overlapping_subnets(self):
        """Test VPC mit überlappenden Subnets"""
        subnets = [
            {"name": "subnet-1", "cidr": "10.0.1.0/24", "type": "public"},
            {"name": "subnet-2", "cidr": "10.0.1.0/24", "type": "private"},  # Same CIDR
        ]

        plan = plan_vpc("10.0.0.0/16", subnets)

        assert plan.has_overlaps
        assert len(plan.overlap_details) > 0

    def test_vpc_with_subnet_outside_range(self):
        """Test VPC mit Subnet außerhalb Range"""
        subnets = [
            {"name": "invalid", "cidr": "192.168.1.0/24", "type": "public"},
        ]

        plan = plan_vpc("10.0.0.0/16", subnets)

        assert plan.has_overlaps
        assert "außerhalb der VPC" in plan.overlap_details[0]

    def test_subnet_allocation_details(self):
        """Test Details eines SubnetAllocation"""
        subnets = [
            {"name": "test-subnet", "cidr": "10.0.1.0/24", "type": "private", "az": "us-east-1a"},
        ]

        plan = plan_vpc("10.0.0.0/16", subnets)

        subnet = plan.subnets[0]
        assert subnet.name == "test-subnet"
        assert subnet.cidr == "10.0.1.0/24"
        assert subnet.subnet_type == "private"
        assert subnet.availability_zone == "us-east-1a"
        assert subnet.total_ips == 256
        assert subnet.usable_ips == 251
        assert subnet.first_ip == "10.0.1.0"
        assert subnet.last_ip == "10.0.1.255"
        assert len(subnet.reserved_ips) == 5


class TestSuggestSubnetSplit:
    """Tests für suggest_subnet_split()"""

    def test_default_suggestions(self):
        """Test Standard-Vorschläge (3 AZs, 3 Typen)"""
        suggestions = suggest_subnet_split("10.0.0.0/16")

        # 3 AZs * 3 Typen = 9 Subnets
        assert len(suggestions) == 9

        # Check first subnet
        first = suggestions[0]
        assert "name" in first
        assert "cidr" in first
        assert "type" in first
        assert "az" in first

    def test_custom_azs(self):
        """Test mit custom Anzahl AZs"""
        suggestions = suggest_subnet_split("10.0.0.0/16", num_azs=2)

        # 2 AZs * 3 Typen = 6 Subnets
        assert len(suggestions) == 6

    def test_custom_subnet_types(self):
        """Test mit custom Subnet-Typen"""
        suggestions = suggest_subnet_split(
            "10.0.0.0/16",
            num_azs=3,
            subnet_types=["public", "private"]
        )

        # 3 AZs * 2 Typen = 6 Subnets
        assert len(suggestions) == 6

    def test_no_overlapping_suggestions(self):
        """Test dass Vorschläge sich nicht überlappen"""
        suggestions = suggest_subnet_split("10.0.0.0/16")

        # Check alle Kombinationen
        for i, subnet1 in enumerate(suggestions):
            for subnet2 in suggestions[i+1:]:
                assert not check_cidr_overlap(subnet1["cidr"], subnet2["cidr"])


class TestPydanticModels:
    """Tests für Pydantic Models"""

    def test_subnet_allocation_model(self):
        """Test SubnetAllocation Model"""
        subnet = SubnetAllocation(
            cidr="10.0.1.0/24",
            name="test-subnet",
            subnet_type="private",
            total_ips=256,
            usable_ips=251,
            first_ip="10.0.1.0",
            last_ip="10.0.1.255",
            reserved_ips=["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"]
        )

        assert subnet.name == "test-subnet"
        assert subnet.availability_zone is None

    def test_vpc_plan_model(self):
        """Test VPCPlan Model"""
        plan = VPCPlan(
            vpc_cidr="10.0.0.0/16",
            total_ips=65536,
            usable_ips=65531,
            subnets=[],
            unallocated_ips=65536,
            has_overlaps=False
        )

        assert plan.vpc_cidr == "10.0.0.0/16"
        assert len(plan.overlap_details) == 0
