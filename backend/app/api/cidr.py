"""API Endpoints für CIDR Calculator."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

from app.utils.cidr_calculator import (
    validate_vpc_cidr,
    validate_subnet_cidr,
    calculate_usable_ips,
    plan_vpc,
    suggest_subnet_split,
    VPCPlan
)
from app.api.auth import get_current_user

router = APIRouter()


class CIDRValidationRequest(BaseModel):
    """Request für CIDR Validierung"""
    cidr: str = Field(..., description="CIDR Block (z.B. 10.0.0.0/16)")


class CIDRValidationResponse(BaseModel):
    """Response für CIDR Validierung"""
    valid: bool
    cidr: Optional[str] = None
    total_ips: Optional[int] = None
    usable_ips: Optional[int] = None
    error: Optional[str] = None
    warning: Optional[str] = None


class SubnetValidationRequest(BaseModel):
    """Request für Subnet Validierung"""
    subnet_cidr: str = Field(..., description="Subnet CIDR Block")
    vpc_cidr: str = Field(..., description="VPC CIDR Block")


class SubnetRequest(BaseModel):
    """Subnet-Anforderung"""
    name: str = Field(..., description="Subnet Name (z.B. 'public-1a')")
    cidr: str = Field(..., description="Subnet CIDR Block")
    type: str = Field(..., description="Subnet Typ: public, private, database")
    az: Optional[str] = Field(None, description="Availability Zone (z.B. 'us-east-1a')")


class VPCPlanRequest(BaseModel):
    """Request für VPC-Planung"""
    vpc_cidr: str = Field(..., description="VPC CIDR Block")
    subnets: List[SubnetRequest] = Field(default_factory=list, description="Liste von Subnets")


class SubnetSuggestionRequest(BaseModel):
    """Request für Subnet-Vorschläge"""
    vpc_cidr: str = Field(..., description="VPC CIDR Block")
    num_azs: int = Field(3, ge=1, le=6, description="Anzahl Availability Zones")
    subnet_types: Optional[List[str]] = Field(
        None,
        description="Liste von Subnet-Typen (Standard: ['public', 'private', 'database'])"
    )


@router.post("/cidr/validate", response_model=CIDRValidationResponse)
async def validate_cidr(
    request: CIDRValidationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Validiert einen VPC CIDR Block.

    AWS VPC Requirements:
    - Muss zwischen /16 und /28 sein
    - Empfohlen: Private IP Ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    """
    is_valid, error = validate_vpc_cidr(request.cidr)

    if not is_valid:
        return CIDRValidationResponse(
            valid=False,
            error=error
        )

    total_ips, usable_ips = calculate_usable_ips(request.cidr)

    return CIDRValidationResponse(
        valid=True,
        cidr=request.cidr,
        total_ips=total_ips,
        usable_ips=usable_ips,
        warning=error  # Kann Warnung enthalten auch wenn valid
    )


@router.post("/cidr/validate-subnet")
async def validate_subnet(
    request: SubnetValidationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Validiert ob ein Subnet CIDR innerhalb eines VPC CIDR liegt.
    """
    # Erst VPC validieren
    vpc_valid, vpc_error = validate_vpc_cidr(request.vpc_cidr)
    if not vpc_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiger VPC CIDR: {vpc_error}"
        )

    # Dann Subnet validieren
    subnet_valid, subnet_error = validate_subnet_cidr(request.subnet_cidr, request.vpc_cidr)

    if not subnet_valid:
        return {
            "valid": False,
            "error": subnet_error
        }

    total_ips, usable_ips = calculate_usable_ips(request.subnet_cidr)

    return {
        "valid": True,
        "subnet_cidr": request.subnet_cidr,
        "vpc_cidr": request.vpc_cidr,
        "total_ips": total_ips,
        "usable_ips": usable_ips
    }


@router.post("/cidr/plan", response_model=VPCPlan)
async def create_vpc_plan(request: VPCPlanRequest):
    """
    Plant VPC mit Subnets und prüft auf Overlaps.

    Gibt detaillierte Informationen über:
    - VPC IP-Adressbereich
    - Alle Subnets mit IP-Counts
    - Overlaps zwischen Subnets
    - Nicht allokierte IPs
    """
    # Validate VPC CIDR
    is_valid, error = validate_vpc_cidr(request.vpc_cidr)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Convert Pydantic models to dict
    subnet_dicts = [subnet.model_dump() for subnet in request.subnets]

    # Plan VPC
    plan = plan_vpc(request.vpc_cidr, subnet_dicts)

    return plan


@router.post("/cidr/suggest")
async def suggest_subnets(request: SubnetSuggestionRequest):
    """
    Schlägt eine sinnvolle Subnet-Aufteilung vor.

    Basierend auf:
    - VPC CIDR Größe
    - Anzahl Availability Zones
    - Gewünschte Subnet-Typen (public, private, database)

    Beispiel: /16 VPC → /20 Subnets (4096 IPs pro Subnet)
    """
    # Validate VPC CIDR
    is_valid, error = validate_vpc_cidr(request.vpc_cidr)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Generate suggestions
    suggestions = suggest_subnet_split(
        vpc_cidr=request.vpc_cidr,
        num_azs=request.num_azs,
        subnet_types=request.subnet_types
    )

    return {
        "vpc_cidr": request.vpc_cidr,
        "num_azs": request.num_azs,
        "suggested_subnets": suggestions
    }
