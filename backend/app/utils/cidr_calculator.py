"""CIDR Calculator Utilities.

Hilfsfunktionen für VPC/Subnet CIDR-Berechnungen.
"""

import ipaddress
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel


class SubnetAllocation(BaseModel):
    """Subnet Allocation Info"""
    cidr: str
    name: str
    availability_zone: Optional[str] = None
    subnet_type: str  # "public", "private", "database"
    total_ips: int
    usable_ips: int  # AWS reserviert 5 IPs
    first_ip: str
    last_ip: str
    reserved_ips: List[str]  # Die 5 von AWS reservierten IPs


class VPCPlan(BaseModel):
    """VPC Planning Result"""
    vpc_cidr: str
    total_ips: int
    usable_ips: int
    subnets: List[SubnetAllocation]
    unallocated_ips: int
    has_overlaps: bool
    overlap_details: List[str] = []


def calculate_usable_ips(cidr: str) -> Tuple[int, int]:
    """
    Berechne Total IPs und Usable IPs für einen CIDR Block.

    AWS reserviert 5 IPs pro Subnet:
    - .0: Network address
    - .1: VPC Router
    - .2: DNS Server
    - .3: Reserved for future use
    - .255 (last): Broadcast address

    Args:
        cidr: CIDR notation (z.B. "10.0.1.0/24")

    Returns:
        Tuple (total_ips, usable_ips)
    """
    network = ipaddress.IPv4Network(cidr, strict=False)
    total_ips = network.num_addresses
    usable_ips = max(0, total_ips - 5)  # AWS reserviert 5
    return total_ips, usable_ips


def get_reserved_ips(cidr: str) -> List[str]:
    """Gibt die 5 von AWS reservierten IPs zurück."""
    network = ipaddress.IPv4Network(cidr, strict=False)
    hosts = list(network.hosts())

    if len(hosts) < 4:
        # Zu kleines Subnet - nur Netzwerk- und Broadcast-Adresse zurückgeben
        return [
            str(network.network_address),
            str(network.broadcast_address),
        ]

    return [
        str(network.network_address),  # .0
        str(hosts[0]),  # .1 (VPC Router)
        str(hosts[1]),  # .2 (DNS)
        str(hosts[2]),  # .3 (Reserved)
        str(network.broadcast_address),  # .255 (Broadcast)
    ]


def check_cidr_overlap(cidr1: str, cidr2: str) -> bool:
    """Prüft ob zwei CIDR Blocks sich überlappen."""
    net1 = ipaddress.IPv4Network(cidr1, strict=False)
    net2 = ipaddress.IPv4Network(cidr2, strict=False)
    return net1.overlaps(net2)


def validate_vpc_cidr(cidr: str) -> Tuple[bool, Optional[str]]:
    """
    Validiert VPC CIDR Block.

    AWS VPC Requirements:
    - Muss zwischen /16 und /28 sein
    - Empfohlen: Private IP Ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)

    Returns:
        (is_valid, error_message)
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)

        # Check CIDR range
        if network.prefixlen < 16:
            return False, "VPC CIDR muss mindestens /16 sein (AWS Limit)"
        if network.prefixlen > 28:
            return False, "VPC CIDR darf höchstens /28 sein (AWS Limit)"

        # Warn if not private IP range
        if not network.is_private:
            return True, "⚠️ Warnung: Öffentliche IP-Range wird normalerweise nicht für VPC verwendet"

        return True, None

    except ValueError as e:
        return False, f"Ungültige CIDR Notation: {e}"


def validate_subnet_cidr(subnet_cidr: str, vpc_cidr: str) -> Tuple[bool, Optional[str]]:
    """
    Validiert ob ein Subnet CIDR innerhalb eines VPC CIDR liegt.

    Args:
        subnet_cidr: Subnet CIDR Block
        vpc_cidr: VPC CIDR Block

    Returns:
        (is_valid, error_message)
    """
    try:
        subnet_network = ipaddress.IPv4Network(subnet_cidr, strict=False)
        vpc_network = ipaddress.IPv4Network(vpc_cidr, strict=False)

        # Check if subnet is within VPC
        if not subnet_network.subnet_of(vpc_network):
            return False, f"Subnet {subnet_cidr} liegt außerhalb der VPC {vpc_cidr}"

        # Check subnet size
        if subnet_network.prefixlen > 28:
            return False, "Subnet CIDR darf höchstens /28 sein (AWS Limit)"

        return True, None

    except ValueError as e:
        return False, f"Ungültige CIDR Notation: {e}"


def plan_vpc(vpc_cidr: str, subnet_requests: List[Dict]) -> VPCPlan:
    """
    Plant VPC mit Subnets und prüft auf Overlaps.

    Args:
        vpc_cidr: VPC CIDR Block (z.B. "10.0.0.0/16")
        subnet_requests: Liste von Subnet-Anforderungen
            [{"name": "public-1a", "cidr": "10.0.1.0/24", "type": "public", "az": "us-east-1a"}, ...]

    Returns:
        VPCPlan mit Details zu allen Subnets und Overlaps
    """
    vpc_network = ipaddress.IPv4Network(vpc_cidr, strict=False)
    vpc_total_ips, vpc_usable_ips = calculate_usable_ips(vpc_cidr)

    subnets = []
    allocated_ips = 0
    overlaps = []

    for req in subnet_requests:
        subnet_cidr = req["cidr"]

        # Validate subnet is within VPC
        is_valid, error = validate_subnet_cidr(subnet_cidr, vpc_cidr)
        if not is_valid:
            overlaps.append(error)
            continue

        # Check overlaps with other subnets
        for other_subnet in subnets:
            if check_cidr_overlap(subnet_cidr, other_subnet.cidr):
                overlaps.append(
                    f"Overlap: {req['name']} ({subnet_cidr}) überschneidet sich mit "
                    f"{other_subnet.name} ({other_subnet.cidr})"
                )

        subnet_network = ipaddress.IPv4Network(subnet_cidr, strict=False)
        total_ips, usable_ips = calculate_usable_ips(subnet_cidr)
        reserved = get_reserved_ips(subnet_cidr)

        allocation = SubnetAllocation(
            cidr=subnet_cidr,
            name=req["name"],
            availability_zone=req.get("az"),
            subnet_type=req["type"],
            total_ips=total_ips,
            usable_ips=usable_ips,
            first_ip=str(subnet_network.network_address),
            last_ip=str(subnet_network.broadcast_address),
            reserved_ips=reserved
        )

        subnets.append(allocation)
        allocated_ips += total_ips

    return VPCPlan(
        vpc_cidr=vpc_cidr,
        total_ips=vpc_total_ips,
        usable_ips=vpc_usable_ips,
        subnets=subnets,
        unallocated_ips=vpc_total_ips - allocated_ips,
        has_overlaps=len(overlaps) > 0,
        overlap_details=overlaps
    )


def suggest_subnet_split(vpc_cidr: str, num_azs: int = 3, subnet_types: Optional[List[str]] = None) -> List[Dict]:
    """
    Schlägt eine sinnvolle Subnet-Aufteilung vor.

    Args:
        vpc_cidr: VPC CIDR Block (z.B. "10.0.0.0/16")
        num_azs: Anzahl Availability Zones (Standard: 3)
        subnet_types: Liste von Subnet-Typen (Standard: ["public", "private", "database"])

    Returns:
        Liste von vorgeschlagenen Subnet-Konfigurationen
    """
    if subnet_types is None:
        subnet_types = ["public", "private", "database"]

    vpc_network = ipaddress.IPv4Network(vpc_cidr, strict=False)
    vpc_prefix = vpc_network.prefixlen

    # Berechne sinnvolle Subnet-Größe
    # Für /16 VPC → /20 Subnets (4096 IPs pro Subnet)
    # Für /20 VPC → /24 Subnets (256 IPs pro Subnet)
    subnet_prefix = min(28, vpc_prefix + 4)

    subnets = []
    az_letters = ['a', 'b', 'c', 'd', 'e', 'f']

    # Generiere Subnets für jeden Typ und jede AZ
    subnet_index = 0
    for subnet_type in subnet_types:
        for az_index in range(num_azs):
            if subnet_index >= 2**(subnet_prefix - vpc_prefix):
                break  # Nicht mehr genug Platz

            # Berechne CIDR für dieses Subnet
            subnet = list(vpc_network.subnets(new_prefix=subnet_prefix))[subnet_index]

            subnets.append({
                "name": f"{subnet_type}-{az_letters[az_index]}",
                "cidr": str(subnet),
                "type": subnet_type,
                "az": f"region-{az_letters[az_index]}"
            })

            subnet_index += 1

    return subnets
