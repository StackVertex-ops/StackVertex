"""Cost Calculator für AWS Resources.

Berechnet monatliche Kosten basierend auf Resource-Konfiguration.
Wird für Live-Cost-Estimation in Blueprint-Formularen verwendet.
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from app.data.aws_constraints import (
    EC2_INSTANCE_TYPES,
    RDS_INSTANCE_CLASSES,
    RDS_STORAGE_TYPES,
    ROUTE53_PRICING,
    S3_STORAGE_CLASSES,
    VPC_CONSTRAINTS,
)


class CostItem(BaseModel):
    """Single cost item mit Details"""
    service: str
    resource: str
    amount: Decimal
    unit: str
    quantity: Decimal = Decimal("1.0")
    total: Decimal


class CostBreakdown(BaseModel):
    """Complete cost breakdown für Blueprint"""
    items: list[CostItem]
    subtotal: Decimal
    tax: Decimal = Decimal("0.0")  # VAT/Sales Tax (optional)
    total: Decimal
    currency: str = "USD"
    period: str = "monthly"
    assumptions: list[str] = []


def calculate_ec2_cost(
    instance_type: str,
    count: int = 1,
    hours_per_month: int = 730  # ~24*30.5
) -> CostItem:
    """Berechnet EC2 Instance Kosten.

    Args:
        instance_type: EC2 Instance Type (z.B. "t3.medium")
        count: Anzahl Instances
        hours_per_month: Betriebsstunden pro Monat

    Returns:
        CostItem mit Details

    Raises:
        ValueError: Wenn Instance Type unbekannt
    """
    instance = EC2_INSTANCE_TYPES.get(instance_type)
    if not instance:
        raise ValueError(f"Unknown instance type: {instance_type}")

    hourly_cost = instance.price_per_hour_usd
    monthly_cost = hourly_cost * Decimal(str(hours_per_month)) * Decimal(str(count))

    return CostItem(
        service="EC2",
        resource=f"{instance_type} x {count}",
        amount=hourly_cost,
        unit="hour",
        quantity=Decimal(str(hours_per_month * count)),
        total=monthly_cost
    )


def calculate_rds_cost(
    instance_class: str,
    engine: str,
    storage_gb: int,
    storage_type: str = "gp3",
    multi_az: bool = False,
    backup_retention_days: int = 7
) -> list[CostItem]:
    """Berechnet RDS Kosten (Instance + Storage + Backups).

    Args:
        instance_class: RDS Instance Class (z.B. "db.t3.medium")
        engine: Database Engine (mysql, postgres, etc.)
        storage_gb: Allocated Storage in GB
        storage_type: Storage Type (gp2, gp3, io1, io2)
        multi_az: Multi-AZ Deployment
        backup_retention_days: Backup Retention Period

    Returns:
        Liste von CostItems

    Raises:
        ValueError: Wenn Instance Class unbekannt
    """
    items = []

    # Instance cost
    instance = RDS_INSTANCE_CLASSES.get(instance_class)
    if not instance:
        raise ValueError(f"Unknown RDS instance class: {instance_class}")

    # Get pricing for specific engine (fallback to MySQL pricing)
    instance_price = instance.price_per_hour_usd
    if multi_az:
        instance_price = instance.price_per_hour_multi_az_usd

    monthly_instance_cost = instance_price * Decimal("730")

    items.append(CostItem(
        service="RDS",
        resource=f"{instance_class} ({engine})" + (" Multi-AZ" if multi_az else ""),
        amount=instance_price,
        unit="hour",
        quantity=Decimal("730"),
        total=monthly_instance_cost
    ))

    # Storage cost
    storage_info = RDS_STORAGE_TYPES.get(storage_type)
    if storage_info:
        storage_cost = storage_info.price_per_gb_month_usd * Decimal(str(storage_gb))
        if multi_az:
            storage_cost *= Decimal("2.0")

        items.append(CostItem(
            service="RDS",
            resource=f"Storage ({storage_type})",
            amount=storage_info.price_per_gb_month_usd,
            unit="GB/month",
            quantity=Decimal(str(storage_gb * (2 if multi_az else 1))),
            total=storage_cost
        ))

    # Backup storage (beyond retention period is charged)
    if backup_retention_days > 7:
        extra_backup_gb = storage_gb * (backup_retention_days - 7) / 7
        backup_cost = Decimal("0.095") * Decimal(str(extra_backup_gb))  # S3 pricing

        items.append(CostItem(
            service="RDS",
            resource="Backup Storage",
            amount=Decimal("0.095"),
            unit="GB/month",
            quantity=Decimal(str(extra_backup_gb)),
            total=backup_cost
        ))

    return items


def calculate_s3_cost(
    storage_gb: float,
    storage_class: str = "STANDARD",
    monthly_requests: int = 100000,
    data_transfer_gb: float = 100.0
) -> list[CostItem]:
    """Berechnet S3 Kosten (Storage + Requests + Transfer).

    Args:
        storage_gb: Storage Größe in GB
        storage_class: Storage Class (STANDARD, etc.)
        monthly_requests: Anzahl Requests pro Monat
        data_transfer_gb: Data Transfer Out in GB

    Returns:
        Liste von CostItems
    """
    items = []

    # Storage cost
    storage_info = S3_STORAGE_CLASSES.get(storage_class)
    if storage_info:
        storage_cost = storage_info.price_per_gb_month_usd * Decimal(str(storage_gb))

        items.append(CostItem(
            service="S3",
            resource=f"Storage ({storage_class})",
            amount=storage_info.price_per_gb_month_usd,
            unit="GB/month",
            quantity=Decimal(str(storage_gb)),
            total=storage_cost
        ))

    # Request cost (PUT, GET)
    if monthly_requests > 0:
        request_cost = Decimal("0.0004") * Decimal(str(monthly_requests / 1000))  # $0.0004 per 1000 requests

        items.append(CostItem(
            service="S3",
            resource="Requests",
            amount=Decimal("0.0004"),
            unit="1000 requests",
            quantity=Decimal(str(monthly_requests / 1000)),
            total=request_cost
        ))

    # Data transfer out (first 1GB free)
    if data_transfer_gb > 1:
        transfer_cost = Decimal("0.09") * Decimal(str(data_transfer_gb - 1))

        items.append(CostItem(
            service="S3",
            resource="Data Transfer Out",
            amount=Decimal("0.09"),
            unit="GB",
            quantity=Decimal(str(data_transfer_gb - 1)),
            total=transfer_cost
        ))

    return items


def calculate_cloudfront_cost(
    data_transfer_gb: float,
    price_class: str = "PriceClass_100",
    monthly_requests: int = 1000000
) -> list[CostItem]:
    """Berechnet CloudFront Kosten.

    Args:
        data_transfer_gb: Data Transfer in GB
        price_class: CloudFront Price Class
        monthly_requests: Anzahl HTTPS Requests

    Returns:
        Liste von CostItems
    """
    items = []

    # Data transfer pricing (tiered)
    # First 10TB: $0.085/GB, 10TB-50TB: $0.080/GB, etc.
    if data_transfer_gb <= 10240:  # Up to 10TB
        transfer_cost = Decimal("0.085") * Decimal(str(data_transfer_gb))
    elif data_transfer_gb <= 51200:  # 10-50TB
        transfer_cost = Decimal("0.085") * Decimal("10240") + Decimal("0.080") * Decimal(str(data_transfer_gb - 10240))
    else:
        transfer_cost = Decimal("0.085") * Decimal("10240") + Decimal("0.080") * Decimal("40960") + Decimal("0.060") * Decimal(str(data_transfer_gb - 51200))

    # Apply price class multiplier
    price_class_multipliers = {
        "PriceClass_All": Decimal("1.5"),
        "PriceClass_200": Decimal("1.2"),
        "PriceClass_100": Decimal("1.0")
    }
    transfer_cost *= price_class_multipliers.get(price_class, Decimal("1.0"))

    items.append(CostItem(
        service="CloudFront",
        resource="Data Transfer",
        amount=Decimal("0.085"),  # Base price
        unit="GB",
        quantity=Decimal(str(data_transfer_gb)),
        total=transfer_cost
    ))

    # Request pricing ($0.0075 per 10,000 HTTPS requests)
    if monthly_requests > 0:
        request_cost = Decimal("0.0075") * Decimal(str(monthly_requests / 10000))

        items.append(CostItem(
            service="CloudFront",
            resource="HTTPS Requests",
            amount=Decimal("0.0075"),
            unit="10k requests",
            quantity=Decimal(str(monthly_requests / 10000)),
            total=request_cost
        ))

    return items


def calculate_lambda_cost(
    invocations_per_month: int,
    avg_duration_ms: int,
    memory_mb: int
) -> CostItem:
    """Berechnet Lambda Kosten.

    Args:
        invocations_per_month: Anzahl Invocations
        avg_duration_ms: Durchschnittliche Duration in ms
        memory_mb: Memory in MB

    Returns:
        CostItem mit kombiniertem Request + Compute Cost
    """
    # Request cost ($0.20 per 1M requests)
    # First 1M requests per month are free
    billable_requests = max(0, invocations_per_month - 1000000)
    request_cost = Decimal("0.20") * Decimal(str(billable_requests / 1000000))

    # Compute cost ($0.0000166667 per GB-second)
    # First 400,000 GB-seconds per month are free
    gb_seconds = (Decimal(str(memory_mb)) / Decimal("1024")) * (Decimal(str(avg_duration_ms)) / Decimal("1000")) * Decimal(str(invocations_per_month))
    billable_gb_seconds = max(Decimal("0"), gb_seconds - Decimal("400000"))
    compute_cost = Decimal("0.0000166667") * billable_gb_seconds

    total_cost = request_cost + compute_cost

    return CostItem(
        service="Lambda",
        resource=f"{memory_mb}MB, {avg_duration_ms}ms avg, {invocations_per_month:,} invocations",
        amount=total_cost,
        unit="month",
        quantity=Decimal("1"),
        total=total_cost
    )


def calculate_alb_cost(
    lcu_per_hour: float = 1.0
) -> CostItem:
    """Berechnet Application Load Balancer Kosten.

    Args:
        lcu_per_hour: Load Balancer Capacity Units pro Stunde

    Returns:
        CostItem
    """
    # ALB Hourly: $0.0225/hour
    # LCU: $0.008/hour
    hourly_cost = Decimal("0.0225") + (Decimal("0.008") * Decimal(str(lcu_per_hour)))
    monthly_cost = hourly_cost * Decimal("730")

    return CostItem(
        service="ALB",
        resource="Application Load Balancer",
        amount=hourly_cost,
        unit="hour",
        quantity=Decimal("730"),
        total=monthly_cost
    )


def calculate_nat_gateway_cost(
    data_processed_gb: float = 1000.0
) -> list[CostItem]:
    """Berechnet NAT Gateway Kosten.

    Args:
        data_processed_gb: Verarbeitete Daten in GB

    Returns:
        Liste von CostItems
    """
    items = []

    # NAT Gateway Hourly: $0.045/hour
    hourly_cost = VPC_CONSTRAINTS.nat_gateway_price_per_hour_usd
    monthly_cost = hourly_cost * Decimal("730")

    items.append(CostItem(
        service="VPC",
        resource="NAT Gateway (hourly)",
        amount=hourly_cost,
        unit="hour",
        quantity=Decimal("730"),
        total=monthly_cost
    ))

    # Data Processing: $0.045/GB
    if data_processed_gb > 0:
        data_cost = VPC_CONSTRAINTS.nat_gateway_data_processing_per_gb_usd * Decimal(str(data_processed_gb))

        items.append(CostItem(
            service="VPC",
            resource="NAT Gateway (data processing)",
            amount=VPC_CONSTRAINTS.nat_gateway_data_processing_per_gb_usd,
            unit="GB",
            quantity=Decimal(str(data_processed_gb)),
            total=data_cost
        ))

    return items


def calculate_route53_cost(
    hosted_zones: int = 1,
    monthly_queries: int = 1000000
) -> list[CostItem]:
    """Berechnet Route53 Kosten.

    Args:
        hosted_zones: Anzahl Hosted Zones
        monthly_queries: Anzahl DNS Queries pro Monat

    Returns:
        Liste von CostItems
    """
    items = []

    # Hosted Zone: $0.50/month per zone
    if hosted_zones > 0:
        zone_cost = ROUTE53_PRICING.hosted_zone_per_month_usd * Decimal(str(hosted_zones))

        items.append(CostItem(
            service="Route53",
            resource="Hosted Zone",
            amount=ROUTE53_PRICING.hosted_zone_per_month_usd,
            unit="zone/month",
            quantity=Decimal(str(hosted_zones)),
            total=zone_cost
        ))

    # Queries: $0.40 per million (first 1B free)
    if monthly_queries > 1000000000:
        billable_queries = monthly_queries - 1000000000
        query_cost = ROUTE53_PRICING.standard_queries_per_million_usd * Decimal(str(billable_queries / 1000000))

        items.append(CostItem(
            service="Route53",
            resource="DNS Queries",
            amount=ROUTE53_PRICING.standard_queries_per_million_usd,
            unit="million queries",
            quantity=Decimal(str(billable_queries / 1000000)),
            total=query_cost
        ))

    return items


def calculate_blueprint_cost(blueprint_id: str, configuration: dict[str, Any]) -> CostBreakdown:
    """
    Berechnet Gesamtkosten für Blueprint-Konfiguration.

    Args:
        blueprint_id: ID des Blueprints
        configuration: User-Konfiguration aus Form

    Returns:
        Detaillierte Kostenaufschlüsselung

    Raises:
        ValueError: Bei ungültiger Konfiguration
    """
    items: list[CostItem] = []
    assumptions: list[str] = []

    # Blueprint-specific calculation logic
    if blueprint_id == "static-website":
        # S3 + CloudFront + Route53
        storage_gb = configuration.get("storage_gb", 50)
        traffic_gb = configuration.get("traffic_gb", 1000)
        monthly_requests = configuration.get("monthly_requests", 1000000)

        items.extend(calculate_s3_cost(
            storage_gb=storage_gb,
            storage_class="STANDARD",
            monthly_requests=monthly_requests,
            data_transfer_gb=0  # CloudFront übernimmt Transfer
        ))

        items.extend(calculate_cloudfront_cost(
            data_transfer_gb=traffic_gb,
            price_class=configuration.get("cloudfront_price_class", "PriceClass_100"),
            monthly_requests=monthly_requests
        ))

        if configuration.get("domain_name"):
            items.extend(calculate_route53_cost(hosted_zones=1))

        assumptions.append(f"~{storage_gb}GB stored files")
        assumptions.append(f"~{traffic_gb}GB traffic per month")
        assumptions.append(f"~{monthly_requests:,} requests per month")

    elif blueprint_id == "three-tier-web":
        # EC2 + RDS + ALB + NAT Gateway

        # EC2 Instances
        ec2_instance_type = configuration.get("ec2_instance_type", "t3.small")
        min_instances = configuration.get("min_instances", 2)

        items.append(calculate_ec2_cost(
            instance_type=ec2_instance_type,
            count=min_instances
        ))

        # RDS Database
        rds_instance_class = configuration.get("rds_instance_class", "db.t3.micro")
        rds_engine = configuration.get("rds_engine", "postgres")
        rds_storage = configuration.get("rds_allocated_storage", 20)
        rds_multi_az = configuration.get("rds_multi_az", False)

        items.extend(calculate_rds_cost(
            instance_class=rds_instance_class,
            engine=rds_engine,
            storage_gb=rds_storage,
            storage_type="gp3",
            multi_az=rds_multi_az
        ))

        # Application Load Balancer
        items.append(calculate_alb_cost(lcu_per_hour=1.0))

        # NAT Gateway (for private subnets)
        items.extend(calculate_nat_gateway_cost(data_processed_gb=500))

        assumptions.append(f"{min_instances}x {ec2_instance_type} instances running 24/7")
        assumptions.append(f"RDS {rds_instance_class} ({rds_engine}) running 24/7")
        if rds_multi_az:
            assumptions.append("RDS Multi-AZ enabled (2x storage cost)")
        assumptions.append("~500GB NAT Gateway data processing per month")

    elif blueprint_id == "serverless-api":
        # Lambda + API Gateway + DynamoDB

        # Lambda
        lambda_invocations = configuration.get("lambda_invocations_per_month", 1000000)
        lambda_memory = configuration.get("lambda_memory_mb", 512)
        lambda_duration = configuration.get("lambda_avg_duration_ms", 200)

        items.append(calculate_lambda_cost(
            invocations_per_month=lambda_invocations,
            avg_duration_ms=lambda_duration,
            memory_mb=lambda_memory
        ))

        # API Gateway (placeholder - simplified)
        api_requests = configuration.get("api_requests_per_month", lambda_invocations)
        api_cost = Decimal("3.50") * Decimal(str(api_requests / 1000000))  # $3.50 per million

        items.append(CostItem(
            service="API Gateway",
            resource="REST API Requests",
            amount=Decimal("3.50"),
            unit="million requests",
            quantity=Decimal(str(api_requests / 1000000)),
            total=api_cost
        ))

        assumptions.append(f"{lambda_invocations:,} Lambda invocations per month")
        assumptions.append(f"{lambda_memory}MB memory, {lambda_duration}ms avg duration")
        assumptions.append("DynamoDB On-Demand pricing (light usage)")

    else:
        # Unknown blueprint - return empty cost
        assumptions.append(f"Blueprint '{blueprint_id}' not recognized - returning $0 cost")

    # Calculate totals
    subtotal = sum(item.total for item in items)
    tax = Decimal("0.0")  # No tax by default
    total = subtotal + tax

    return CostBreakdown(
        items=items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        currency="USD",
        period="monthly",
        assumptions=assumptions
    )
