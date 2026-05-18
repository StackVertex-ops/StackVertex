"""
AWS Constraints Database

Zentrale Datenbank mit allen AWS-Limits, Preisen und Regeln.
Alle Preise basieren auf us-east-1 Region (Stand: Mai 2026).

Quellen:
- AWS Pricing Calculator
- AWS Service Quotas
- AWS Documentation
"""

import ipaddress
from decimal import Decimal

from pydantic import BaseModel, Field

# ============================================================================
# EC2 Instance Types
# ============================================================================

class EC2InstanceType(BaseModel):
    """EC2 Instance Type Definition"""
    name: str
    vcpus: int
    memory_gb: Decimal
    network_performance: str
    price_per_hour_usd: Decimal
    architecture: list[str]  # ["x86_64"] or ["arm64"] or both
    storage: str | None = None  # "EBS only" or instance store details
    use_cases: list[str] = Field(default_factory=list)


EC2_INSTANCE_TYPES: dict[str, EC2InstanceType] = {
    # T2 Family - Burstable Performance (Intel x86)
    "t2.micro": EC2InstanceType(
        name="t2.micro",
        vcpus=1,
        memory_gb=Decimal("1.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.0116"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["development", "testing", "low-traffic-web"]
    ),
    "t2.small": EC2InstanceType(
        name="t2.small",
        vcpus=1,
        memory_gb=Decimal("2.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.023"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "small-databases", "development"]
    ),
    "t2.medium": EC2InstanceType(
        name="t2.medium",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.0464"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "small-databases"]
    ),
    "t2.large": EC2InstanceType(
        name="t2.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.0928"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "databases"]
    ),
    "t2.xlarge": EC2InstanceType(
        name="t2.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Moderate",
        price_per_hour_usd=Decimal("0.1856"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "databases", "cache"]
    ),
    "t2.2xlarge": EC2InstanceType(
        name="t2.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Moderate",
        price_per_hour_usd=Decimal("0.3712"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "cache", "enterprise-apps"]
    ),

    # T3 Family - Burstable Performance (Intel x86, newer generation)
    "t3.micro": EC2InstanceType(
        name="t3.micro",
        vcpus=2,
        memory_gb=Decimal("1.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0104"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["development", "testing", "microservices"]
    ),
    "t3.small": EC2InstanceType(
        name="t3.small",
        vcpus=2,
        memory_gb=Decimal("2.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0208"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "microservices", "small-databases"]
    ),
    "t3.medium": EC2InstanceType(
        name="t3.medium",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0416"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "databases", "api-servers"]
    ),
    "t3.large": EC2InstanceType(
        name="t3.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0832"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "databases", "api-servers"]
    ),
    "t3.xlarge": EC2InstanceType(
        name="t3.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.1664"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "cache", "application-servers"]
    ),
    "t3.2xlarge": EC2InstanceType(
        name="t3.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.3328"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "cache", "enterprise-apps"]
    ),

    # T4g Family - ARM-based Graviton2 (best price/performance for burstable)
    "t4g.micro": EC2InstanceType(
        name="t4g.micro",
        vcpus=2,
        memory_gb=Decimal("1.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0084"),
        architecture=["arm64"],
        storage="EBS only",
        use_cases=["development", "testing", "microservices"]
    ),
    "t4g.small": EC2InstanceType(
        name="t4g.small",
        vcpus=2,
        memory_gb=Decimal("2.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0168"),
        architecture=["arm64"],
        storage="EBS only",
        use_cases=["web-servers", "microservices", "containerized-apps"]
    ),
    "t4g.medium": EC2InstanceType(
        name="t4g.medium",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0336"),
        architecture=["arm64"],
        storage="EBS only",
        use_cases=["web-servers", "api-servers", "containerized-apps"]
    ),
    "t4g.large": EC2InstanceType(
        name="t4g.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.0672"),
        architecture=["arm64"],
        storage="EBS only",
        use_cases=["web-servers", "databases", "api-servers"]
    ),
    "t4g.xlarge": EC2InstanceType(
        name="t4g.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.1344"),
        architecture=["arm64"],
        storage="EBS only",
        use_cases=["databases", "application-servers"]
    ),
    "t4g.2xlarge": EC2InstanceType(
        name="t4g.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.2688"),
        architecture=["arm64"],
        storage="EBS only",
        use_cases=["databases", "enterprise-apps"]
    ),

    # M5 Family - General Purpose (Intel x86)
    "m5.large": EC2InstanceType(
        name="m5.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.096"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "databases", "enterprise-apps"]
    ),
    "m5.xlarge": EC2InstanceType(
        name="m5.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.192"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "application-servers", "enterprise-apps"]
    ),
    "m5.2xlarge": EC2InstanceType(
        name="m5.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.384"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "enterprise-apps", "data-processing"]
    ),
    "m5.4xlarge": EC2InstanceType(
        name="m5.4xlarge",
        vcpus=16,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.768"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["large-databases", "enterprise-apps", "analytics"]
    ),
    "m5.8xlarge": EC2InstanceType(
        name="m5.8xlarge",
        vcpus=32,
        memory_gb=Decimal("128.0"),
        network_performance="10 Gigabit",
        price_per_hour_usd=Decimal("1.536"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["large-databases", "high-performance-apps", "analytics"]
    ),

    # M6i Family - General Purpose (Intel x86, latest generation)
    "m6i.large": EC2InstanceType(
        name="m6i.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.096"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["web-servers", "databases", "enterprise-apps"]
    ),
    "m6i.xlarge": EC2InstanceType(
        name="m6i.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.192"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "application-servers", "enterprise-apps"]
    ),
    "m6i.2xlarge": EC2InstanceType(
        name="m6i.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.384"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["databases", "enterprise-apps", "data-processing"]
    ),
    "m6i.4xlarge": EC2InstanceType(
        name="m6i.4xlarge",
        vcpus=16,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.768"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["large-databases", "enterprise-apps", "analytics"]
    ),

    # C5 Family - Compute Optimized (Intel x86)
    "c5.large": EC2InstanceType(
        name="c5.large",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.085"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["compute-intensive", "batch-processing", "gaming"]
    ),
    "c5.xlarge": EC2InstanceType(
        name="c5.xlarge",
        vcpus=4,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.17"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["compute-intensive", "video-encoding", "ml-inference"]
    ),
    "c5.2xlarge": EC2InstanceType(
        name="c5.2xlarge",
        vcpus=8,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.34"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["high-performance-computing", "video-encoding", "gaming"]
    ),
    "c5.4xlarge": EC2InstanceType(
        name="c5.4xlarge",
        vcpus=16,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.68"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["high-performance-computing", "scientific-modeling"]
    ),

    # C6i Family - Compute Optimized (Intel x86, latest generation)
    "c6i.large": EC2InstanceType(
        name="c6i.large",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.085"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["compute-intensive", "batch-processing", "gaming"]
    ),
    "c6i.xlarge": EC2InstanceType(
        name="c6i.xlarge",
        vcpus=4,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.17"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["compute-intensive", "video-encoding", "ml-inference"]
    ),
    "c6i.2xlarge": EC2InstanceType(
        name="c6i.2xlarge",
        vcpus=8,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.34"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["high-performance-computing", "video-encoding"]
    ),

    # R5 Family - Memory Optimized (Intel x86)
    "r5.large": EC2InstanceType(
        name="r5.large",
        vcpus=2,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.126"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["in-memory-databases", "cache", "real-time-analytics"]
    ),
    "r5.xlarge": EC2InstanceType(
        name="r5.xlarge",
        vcpus=4,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.252"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["in-memory-databases", "large-cache", "analytics"]
    ),
    "r5.2xlarge": EC2InstanceType(
        name="r5.2xlarge",
        vcpus=8,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.504"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["large-databases", "sap-hana", "big-data"]
    ),
    "r5.4xlarge": EC2InstanceType(
        name="r5.4xlarge",
        vcpus=16,
        memory_gb=Decimal("128.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("1.008"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["enterprise-databases", "sap-hana", "big-data"]
    ),

    # R6i Family - Memory Optimized (Intel x86, latest generation)
    "r6i.large": EC2InstanceType(
        name="r6i.large",
        vcpus=2,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.126"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["in-memory-databases", "cache", "real-time-analytics"]
    ),
    "r6i.xlarge": EC2InstanceType(
        name="r6i.xlarge",
        vcpus=4,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.252"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["in-memory-databases", "large-cache", "analytics"]
    ),
    "r6i.2xlarge": EC2InstanceType(
        name="r6i.2xlarge",
        vcpus=8,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.504"),
        architecture=["x86_64"],
        storage="EBS only",
        use_cases=["large-databases", "sap-hana", "big-data"]
    ),
}


# ============================================================================
# RDS Database Engines
# ============================================================================

class RDSEngine(BaseModel):
    """RDS Database Engine Definition"""
    name: str
    display_name: str
    versions: list[str]
    min_storage_gb: int
    max_storage_gb: int
    default_port: int
    supports_multi_az: bool = True
    supports_read_replicas: bool = True


RDS_ENGINES: dict[str, RDSEngine] = {
    "mysql": RDSEngine(
        name="mysql",
        display_name="MySQL",
        versions=["8.0.35", "8.0.33", "8.0.32", "5.7.44"],
        min_storage_gb=20,
        max_storage_gb=64000,  # 64 TB
        default_port=3306,
        supports_multi_az=True,
        supports_read_replicas=True
    ),
    "postgres": RDSEngine(
        name="postgres",
        display_name="PostgreSQL",
        versions=["16.1", "15.5", "14.10", "13.13", "12.17"],
        min_storage_gb=20,
        max_storage_gb=64000,
        default_port=5432,
        supports_multi_az=True,
        supports_read_replicas=True
    ),
    "mariadb": RDSEngine(
        name="mariadb",
        display_name="MariaDB",
        versions=["10.11.6", "10.6.16", "10.5.23", "10.4.32"],
        min_storage_gb=20,
        max_storage_gb=64000,
        default_port=3306,
        supports_multi_az=True,
        supports_read_replicas=True
    ),
    "aurora-mysql": RDSEngine(
        name="aurora-mysql",
        display_name="Aurora MySQL",
        versions=["8.0.mysql_aurora.3.04.1", "5.7.mysql_aurora.2.12.0"],
        min_storage_gb=10,  # Aurora has different storage model
        max_storage_gb=128000,  # 128 TB
        default_port=3306,
        supports_multi_az=True,
        supports_read_replicas=True
    ),
    "aurora-postgres": RDSEngine(
        name="aurora-postgres",
        display_name="Aurora PostgreSQL",
        versions=["15.4", "14.9", "13.12"],
        min_storage_gb=10,
        max_storage_gb=128000,
        default_port=5432,
        supports_multi_az=True,
        supports_read_replicas=True
    ),
}


# ============================================================================
# RDS Instance Classes
# ============================================================================

class RDSInstanceClass(BaseModel):
    """RDS DB Instance Class Definition"""
    name: str
    vcpus: int
    memory_gb: Decimal
    network_performance: str
    price_per_hour_usd: Decimal  # Single-AZ MySQL pricing
    price_per_hour_multi_az_usd: Decimal
    architecture: list[str]
    use_cases: list[str] = Field(default_factory=list)


RDS_INSTANCE_CLASSES: dict[str, RDSInstanceClass] = {
    # T3 Family - Burstable Performance
    "db.t3.micro": RDSInstanceClass(
        name="db.t3.micro",
        vcpus=2,
        memory_gb=Decimal("1.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.016"),
        price_per_hour_multi_az_usd=Decimal("0.032"),
        architecture=["x86_64"],
        use_cases=["development", "testing", "very-small-databases"]
    ),
    "db.t3.small": RDSInstanceClass(
        name="db.t3.small",
        vcpus=2,
        memory_gb=Decimal("2.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.032"),
        price_per_hour_multi_az_usd=Decimal("0.064"),
        architecture=["x86_64"],
        use_cases=["development", "small-production", "testing"]
    ),
    "db.t3.medium": RDSInstanceClass(
        name="db.t3.medium",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Low to Moderate",
        price_per_hour_usd=Decimal("0.064"),
        price_per_hour_multi_az_usd=Decimal("0.128"),
        architecture=["x86_64"],
        use_cases=["small-production", "development", "low-traffic"]
    ),
    "db.t3.large": RDSInstanceClass(
        name="db.t3.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Moderate",
        price_per_hour_usd=Decimal("0.128"),
        price_per_hour_multi_az_usd=Decimal("0.256"),
        architecture=["x86_64"],
        use_cases=["production", "moderate-traffic"]
    ),

    # T4g Family - ARM Graviton2 (best price/performance for burstable)
    "db.t4g.micro": RDSInstanceClass(
        name="db.t4g.micro",
        vcpus=2,
        memory_gb=Decimal("1.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.013"),
        price_per_hour_multi_az_usd=Decimal("0.026"),
        architecture=["arm64"],
        use_cases=["development", "testing", "very-small-databases"]
    ),
    "db.t4g.small": RDSInstanceClass(
        name="db.t4g.small",
        vcpus=2,
        memory_gb=Decimal("2.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.026"),
        price_per_hour_multi_az_usd=Decimal("0.052"),
        architecture=["arm64"],
        use_cases=["development", "small-production", "testing"]
    ),
    "db.t4g.medium": RDSInstanceClass(
        name="db.t4g.medium",
        vcpus=2,
        memory_gb=Decimal("4.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.052"),
        price_per_hour_multi_az_usd=Decimal("0.104"),
        architecture=["arm64"],
        use_cases=["small-production", "development", "low-traffic"]
    ),
    "db.t4g.large": RDSInstanceClass(
        name="db.t4g.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 5 Gigabit",
        price_per_hour_usd=Decimal("0.104"),
        price_per_hour_multi_az_usd=Decimal("0.208"),
        architecture=["arm64"],
        use_cases=["production", "moderate-traffic"]
    ),

    # M5 Family - General Purpose
    "db.m5.large": RDSInstanceClass(
        name="db.m5.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.154"),
        price_per_hour_multi_az_usd=Decimal("0.308"),
        architecture=["x86_64"],
        use_cases=["production", "moderate-to-high-traffic"]
    ),
    "db.m5.xlarge": RDSInstanceClass(
        name="db.m5.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.308"),
        price_per_hour_multi_az_usd=Decimal("0.616"),
        architecture=["x86_64"],
        use_cases=["production", "high-traffic"]
    ),
    "db.m5.2xlarge": RDSInstanceClass(
        name="db.m5.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.616"),
        price_per_hour_multi_az_usd=Decimal("1.232"),
        architecture=["x86_64"],
        use_cases=["large-production", "high-traffic"]
    ),
    "db.m5.4xlarge": RDSInstanceClass(
        name="db.m5.4xlarge",
        vcpus=16,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("1.232"),
        price_per_hour_multi_az_usd=Decimal("2.464"),
        architecture=["x86_64"],
        use_cases=["enterprise", "very-high-traffic"]
    ),

    # M6i Family - General Purpose (latest generation)
    "db.m6i.large": RDSInstanceClass(
        name="db.m6i.large",
        vcpus=2,
        memory_gb=Decimal("8.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.154"),
        price_per_hour_multi_az_usd=Decimal("0.308"),
        architecture=["x86_64"],
        use_cases=["production", "moderate-to-high-traffic"]
    ),
    "db.m6i.xlarge": RDSInstanceClass(
        name="db.m6i.xlarge",
        vcpus=4,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.308"),
        price_per_hour_multi_az_usd=Decimal("0.616"),
        architecture=["x86_64"],
        use_cases=["production", "high-traffic"]
    ),
    "db.m6i.2xlarge": RDSInstanceClass(
        name="db.m6i.2xlarge",
        vcpus=8,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.616"),
        price_per_hour_multi_az_usd=Decimal("1.232"),
        architecture=["x86_64"],
        use_cases=["large-production", "high-traffic"]
    ),

    # R5 Family - Memory Optimized
    "db.r5.large": RDSInstanceClass(
        name="db.r5.large",
        vcpus=2,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.24"),
        price_per_hour_multi_az_usd=Decimal("0.48"),
        architecture=["x86_64"],
        use_cases=["memory-intensive", "cache", "analytics"]
    ),
    "db.r5.xlarge": RDSInstanceClass(
        name="db.r5.xlarge",
        vcpus=4,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.48"),
        price_per_hour_multi_az_usd=Decimal("0.96"),
        architecture=["x86_64"],
        use_cases=["memory-intensive", "large-datasets", "analytics"]
    ),
    "db.r5.2xlarge": RDSInstanceClass(
        name="db.r5.2xlarge",
        vcpus=8,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("0.96"),
        price_per_hour_multi_az_usd=Decimal("1.92"),
        architecture=["x86_64"],
        use_cases=["very-memory-intensive", "large-datasets", "analytics"]
    ),
    "db.r5.4xlarge": RDSInstanceClass(
        name="db.r5.4xlarge",
        vcpus=16,
        memory_gb=Decimal("128.0"),
        network_performance="Up to 10 Gigabit",
        price_per_hour_usd=Decimal("1.92"),
        price_per_hour_multi_az_usd=Decimal("3.84"),
        architecture=["x86_64"],
        use_cases=["enterprise-analytics", "very-large-datasets"]
    ),

    # R6i Family - Memory Optimized (latest generation)
    "db.r6i.large": RDSInstanceClass(
        name="db.r6i.large",
        vcpus=2,
        memory_gb=Decimal("16.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.24"),
        price_per_hour_multi_az_usd=Decimal("0.48"),
        architecture=["x86_64"],
        use_cases=["memory-intensive", "cache", "analytics"]
    ),
    "db.r6i.xlarge": RDSInstanceClass(
        name="db.r6i.xlarge",
        vcpus=4,
        memory_gb=Decimal("32.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.48"),
        price_per_hour_multi_az_usd=Decimal("0.96"),
        architecture=["x86_64"],
        use_cases=["memory-intensive", "large-datasets", "analytics"]
    ),
    "db.r6i.2xlarge": RDSInstanceClass(
        name="db.r6i.2xlarge",
        vcpus=8,
        memory_gb=Decimal("64.0"),
        network_performance="Up to 12.5 Gigabit",
        price_per_hour_usd=Decimal("0.96"),
        price_per_hour_multi_az_usd=Decimal("1.92"),
        architecture=["x86_64"],
        use_cases=["very-memory-intensive", "large-datasets", "analytics"]
    ),
    "db.r6i.32xlarge": RDSInstanceClass(
        name="db.r6i.32xlarge",
        vcpus=128,
        memory_gb=Decimal("1024.0"),
        network_performance="50 Gigabit",
        price_per_hour_usd=Decimal("15.36"),
        price_per_hour_multi_az_usd=Decimal("30.72"),
        architecture=["x86_64"],
        use_cases=["massive-enterprise-databases", "sap-hana"]
    ),
}


# ============================================================================
# RDS Storage Types
# ============================================================================

class RDSStorageType(BaseModel):
    """RDS Storage Type Definition"""
    name: str
    display_name: str
    min_size_gb: int
    max_size_gb: int
    min_iops: int | None = None
    max_iops: int | None = None
    price_per_gb_month_usd: Decimal
    price_per_iops_month_usd: Decimal | None = None
    use_cases: list[str] = Field(default_factory=list)


RDS_STORAGE_TYPES: dict[str, RDSStorageType] = {
    "gp2": RDSStorageType(
        name="gp2",
        display_name="General Purpose SSD (gp2)",
        min_size_gb=20,
        max_size_gb=64000,
        min_iops=100,  # 3 IOPS per GB, min 100
        max_iops=16000,  # 3 IOPS per GB, max 16000
        price_per_gb_month_usd=Decimal("0.115"),
        use_cases=["general-purpose", "development", "most-workloads"]
    ),
    "gp3": RDSStorageType(
        name="gp3",
        display_name="General Purpose SSD (gp3)",
        min_size_gb=20,
        max_size_gb=64000,
        min_iops=3000,  # Baseline
        max_iops=16000,
        price_per_gb_month_usd=Decimal("0.092"),  # 20% cheaper than gp2
        price_per_iops_month_usd=Decimal("0.005"),  # For IOPS > 3000
        use_cases=["general-purpose", "cost-optimized", "most-workloads"]
    ),
    "io1": RDSStorageType(
        name="io1",
        display_name="Provisioned IOPS SSD (io1)",
        min_size_gb=100,
        max_size_gb=64000,
        min_iops=1000,
        max_iops=64000,
        price_per_gb_month_usd=Decimal("0.125"),
        price_per_iops_month_usd=Decimal("0.10"),
        use_cases=["high-performance", "latency-sensitive", "production"]
    ),
    "io2": RDSStorageType(
        name="io2",
        display_name="Provisioned IOPS SSD (io2)",
        min_size_gb=100,
        max_size_gb=64000,
        min_iops=1000,
        max_iops=256000,  # 4x more than io1
        price_per_gb_month_usd=Decimal("0.125"),
        price_per_iops_month_usd=Decimal("0.10"),  # Same as io1 but better durability
        use_cases=["mission-critical", "high-performance", "production"]
    ),
}


# ============================================================================
# S3 Storage Classes
# ============================================================================

class S3StorageClass(BaseModel):
    """S3 Storage Class Definition"""
    name: str
    display_name: str
    price_per_gb_month_usd: Decimal
    retrieval_price_per_gb_usd: Decimal
    min_storage_duration_days: int
    retrieval_time: str
    use_cases: list[str] = Field(default_factory=list)


S3_STORAGE_CLASSES: dict[str, S3StorageClass] = {
    "STANDARD": S3StorageClass(
        name="STANDARD",
        display_name="S3 Standard",
        price_per_gb_month_usd=Decimal("0.023"),
        retrieval_price_per_gb_usd=Decimal("0.0"),
        min_storage_duration_days=0,
        retrieval_time="Instant",
        use_cases=["frequently-accessed", "hot-data", "websites", "cdn"]
    ),
    "INTELLIGENT_TIERING": S3StorageClass(
        name="INTELLIGENT_TIERING",
        display_name="S3 Intelligent-Tiering",
        price_per_gb_month_usd=Decimal("0.0125"),  # Frequent Access tier
        retrieval_price_per_gb_usd=Decimal("0.0"),
        min_storage_duration_days=30,
        retrieval_time="Instant (if in Frequent Access tier)",
        use_cases=["unknown-access-patterns", "automatic-optimization"]
    ),
    "STANDARD_IA": S3StorageClass(
        name="STANDARD_IA",
        display_name="S3 Standard-IA (Infrequent Access)",
        price_per_gb_month_usd=Decimal("0.0125"),
        retrieval_price_per_gb_usd=Decimal("0.01"),
        min_storage_duration_days=30,
        retrieval_time="Instant",
        use_cases=["infrequently-accessed", "backups", "disaster-recovery"]
    ),
    "ONEZONE_IA": S3StorageClass(
        name="ONEZONE_IA",
        display_name="S3 One Zone-IA",
        price_per_gb_month_usd=Decimal("0.01"),  # 20% cheaper than Standard-IA
        retrieval_price_per_gb_usd=Decimal("0.01"),
        min_storage_duration_days=30,
        retrieval_time="Instant",
        use_cases=["infrequently-accessed", "non-critical", "reproducible-data"]
    ),
    "GLACIER_IR": S3StorageClass(
        name="GLACIER_IR",
        display_name="S3 Glacier Instant Retrieval",
        price_per_gb_month_usd=Decimal("0.004"),
        retrieval_price_per_gb_usd=Decimal("0.03"),
        min_storage_duration_days=90,
        retrieval_time="Instant (milliseconds)",
        use_cases=["rarely-accessed", "archives", "instant-retrieval-needed"]
    ),
    "GLACIER": S3StorageClass(
        name="GLACIER",
        display_name="S3 Glacier Flexible Retrieval",
        price_per_gb_month_usd=Decimal("0.0036"),
        retrieval_price_per_gb_usd=Decimal("0.01"),  # Bulk retrieval
        min_storage_duration_days=90,
        retrieval_time="Minutes to hours (configurable)",
        use_cases=["long-term-archives", "backups", "compliance"]
    ),
    "DEEP_ARCHIVE": S3StorageClass(
        name="DEEP_ARCHIVE",
        display_name="S3 Glacier Deep Archive",
        price_per_gb_month_usd=Decimal("0.00099"),
        retrieval_price_per_gb_usd=Decimal("0.02"),
        min_storage_duration_days=180,
        retrieval_time="12-48 hours",
        use_cases=["long-term-archives", "compliance", "tape-replacement"]
    ),
}


# ============================================================================
# Lambda Constraints
# ============================================================================

class LambdaConstraints(BaseModel):
    """AWS Lambda Service Constraints"""
    min_memory_mb: int = 128
    max_memory_mb: int = 10240
    memory_increment_mb: int = 1  # Can be any value between min and max now
    min_timeout_seconds: int = 1
    max_timeout_seconds: int = 900  # 15 minutes
    min_ephemeral_storage_mb: int = 512
    max_ephemeral_storage_mb: int = 10240
    default_concurrent_executions: int = 1000
    max_deployment_package_size_mb: int = 250  # Unzipped
    max_deployment_package_zip_mb: int = 50
    # Pricing
    price_per_request_usd: Decimal = Decimal("0.0000002")  # $0.20 per 1M requests
    price_per_gb_second_usd: Decimal = Decimal("0.0000166667")  # $0.00001667 per GB-second
    free_tier_requests_per_month: int = 1000000
    free_tier_gb_seconds_per_month: int = 400000


LAMBDA_CONSTRAINTS = LambdaConstraints()


# ============================================================================
# VPC Constraints
# ============================================================================

class VPCConstraints(BaseModel):
    """AWS VPC Service Constraints"""
    min_cidr_prefix: int = 16  # /16 = 65,536 IPs
    max_cidr_prefix: int = 28  # /28 = 16 IPs
    reserved_ips_per_subnet: int = 5  # AWS reserves first 4 and last IP
    max_subnets_per_vpc: int = 200
    max_route_tables_per_vpc: int = 200
    max_security_groups_per_vpc: int = 2500
    max_rules_per_security_group: int = 60
    # Pricing
    nat_gateway_price_per_hour_usd: Decimal = Decimal("0.045")
    nat_gateway_data_processing_per_gb_usd: Decimal = Decimal("0.045")
    vpc_peering_data_transfer_same_az_per_gb_usd: Decimal = Decimal("0.01")
    vpc_peering_data_transfer_different_az_per_gb_usd: Decimal = Decimal("0.01")
    vpc_peering_data_transfer_inter_region_per_gb_usd: Decimal = Decimal("0.02")
    # Internet Gateway is free (no hourly charge)
    internet_gateway_price_per_hour_usd: Decimal = Decimal("0.0")


VPC_CONSTRAINTS = VPCConstraints()


# ============================================================================
# CloudFront Price Classes
# ============================================================================

class CloudFrontPriceClass(BaseModel):
    """CloudFront Price Class Definition"""
    name: str
    display_name: str
    regions: list[str]
    data_transfer_out_per_gb_usd: Decimal  # First 10 TB/month
    request_price_per_10k_https_usd: Decimal
    use_cases: list[str] = Field(default_factory=list)


CLOUDFRONT_PRICE_CLASSES: dict[str, CloudFrontPriceClass] = {
    "PriceClass_All": CloudFrontPriceClass(
        name="PriceClass_All",
        display_name="All Edge Locations",
        regions=["North America", "Europe", "Asia", "Middle East", "Africa", "South America", "Australia"],
        data_transfer_out_per_gb_usd=Decimal("0.085"),
        request_price_per_10k_https_usd=Decimal("0.0100"),
        use_cases=["global-audience", "best-performance-worldwide"]
    ),
    "PriceClass_200": CloudFrontPriceClass(
        name="PriceClass_200",
        display_name="North America, Europe, Asia, Middle East, Africa",
        regions=["North America", "Europe", "Asia", "Middle East", "Africa"],
        data_transfer_out_per_gb_usd=Decimal("0.085"),
        request_price_per_10k_https_usd=Decimal("0.0100"),
        use_cases=["most-regions", "exclude-south-america"]
    ),
    "PriceClass_100": CloudFrontPriceClass(
        name="PriceClass_100",
        display_name="North America and Europe Only",
        regions=["North America", "Europe"],
        data_transfer_out_per_gb_usd=Decimal("0.085"),
        request_price_per_10k_https_usd=Decimal("0.0100"),
        use_cases=["north-america-europe-only", "cost-optimization"]
    ),
}


# ============================================================================
# Route53 Pricing
# ============================================================================

class Route53Pricing(BaseModel):
    """Route53 DNS Service Pricing"""
    hosted_zone_per_month_usd: Decimal = Decimal("0.50")
    standard_queries_per_million_usd: Decimal = Decimal("0.40")
    geo_queries_per_million_usd: Decimal = Decimal("0.70")
    latency_queries_per_million_usd: Decimal = Decimal("0.60")
    health_check_basic_per_month_usd: Decimal = Decimal("0.50")
    health_check_https_per_month_usd: Decimal = Decimal("1.00")
    domain_registration_com_per_year_usd: Decimal = Decimal("13.00")
    domain_registration_net_per_year_usd: Decimal = Decimal("13.00")
    domain_registration_org_per_year_usd: Decimal = Decimal("14.00")


ROUTE53_PRICING = Route53Pricing()


# ============================================================================
# Validation Helper Functions
# ============================================================================

def validate_rds_storage(
    size_gb: int,
    engine: str,
    storage_type: str = "gp3"
) -> tuple[bool, str | None]:
    """
    Validiert RDS Storage-Konfiguration.

    Args:
        size_gb: Gewünschte Storage-Größe in GB
        engine: Database Engine (mysql, postgres, mariadb, etc.)
        storage_type: Storage Type (gp2, gp3, io1, io2)

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Engine prüfen
    if engine not in RDS_ENGINES:
        return False, f"Unbekannte Database Engine: {engine}. Verfügbar: {', '.join(RDS_ENGINES.keys())}"

    engine_config = RDS_ENGINES[engine]

    # Minimum Storage prüfen
    if size_gb < engine_config.min_storage_gb:
        return False, f"{engine_config.display_name} benötigt mindestens {engine_config.min_storage_gb} GB Storage"

    # Maximum Storage prüfen
    if size_gb > engine_config.max_storage_gb:
        return False, f"{engine_config.display_name} unterstützt maximal {engine_config.max_storage_gb} GB Storage"

    # Storage Type prüfen
    if storage_type not in RDS_STORAGE_TYPES:
        return False, f"Unbekannter Storage Type: {storage_type}. Verfügbar: {', '.join(RDS_STORAGE_TYPES.keys())}"

    storage_config = RDS_STORAGE_TYPES[storage_type]

    # Storage Type Limits prüfen
    if size_gb < storage_config.min_size_gb:
        return False, f"{storage_config.display_name} benötigt mindestens {storage_config.min_size_gb} GB"

    if size_gb > storage_config.max_size_gb:
        return False, f"{storage_config.display_name} unterstützt maximal {storage_config.max_size_gb} GB"

    return True, None


def validate_vpc_cidr(cidr: str) -> tuple[bool, str | None]:
    """
    Validiert VPC CIDR-Block.

    Args:
        cidr: CIDR-Notation (z.B. "10.0.0.0/16")

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as e:
        return False, f"Ungültiger CIDR-Block: {str(e)}"

    # Prefix Length prüfen
    if network.prefixlen < VPC_CONSTRAINTS.min_cidr_prefix:
        return False, f"CIDR-Prefix muss mindestens /{VPC_CONSTRAINTS.min_cidr_prefix} sein (aktuell: /{network.prefixlen})"

    if network.prefixlen > VPC_CONSTRAINTS.max_cidr_prefix:
        return False, f"CIDR-Prefix darf maximal /{VPC_CONSTRAINTS.max_cidr_prefix} sein (aktuell: /{network.prefixlen})"

    # AWS empfiehlt private IP ranges (RFC 1918)
    private_ranges = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
    ]

    is_private = any(network.subnet_of(private_range) for private_range in private_ranges)

    if not is_private:
        # Warnung, kein Error - öffentliche IPs sind technisch möglich
        return True, f"Warnung: {cidr} ist kein privater IP-Bereich (RFC 1918). AWS empfiehlt 10.0.0.0/8, 172.16.0.0/12 oder 192.168.0.0/16"

    return True, None


def calculate_vpc_usable_ips(cidr: str) -> int:
    """
    Berechnet nutzbare IP-Adressen in einem Subnet (total - 5 von AWS reserviert).

    Args:
        cidr: CIDR-Notation (z.B. "10.0.1.0/24")

    Returns:
        int: Anzahl nutzbarer IP-Adressen

    AWS reserviert:
    - Erste IP: Network address
    - Zweite IP: VPC router
    - Dritte IP: DNS server
    - Vierte IP: Future use
    - Letzte IP: Broadcast address
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        total_ips = network.num_addresses
        usable_ips = max(0, total_ips - VPC_CONSTRAINTS.reserved_ips_per_subnet)
        return usable_ips
    except ValueError:
        return 0


def validate_lambda_memory(memory_mb: int) -> tuple[bool, str | None]:
    """
    Validiert Lambda Memory-Konfiguration.

    Args:
        memory_mb: Memory in MB

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if memory_mb < LAMBDA_CONSTRAINTS.min_memory_mb:
        return False, f"Lambda Memory muss mindestens {LAMBDA_CONSTRAINTS.min_memory_mb} MB sein"

    if memory_mb > LAMBDA_CONSTRAINTS.max_memory_mb:
        return False, f"Lambda Memory darf maximal {LAMBDA_CONSTRAINTS.max_memory_mb} MB sein"

    return True, None


def validate_lambda_timeout(timeout_seconds: int) -> tuple[bool, str | None]:
    """
    Validiert Lambda Timeout-Konfiguration.

    Args:
        timeout_seconds: Timeout in Sekunden

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if timeout_seconds < LAMBDA_CONSTRAINTS.min_timeout_seconds:
        return False, f"Lambda Timeout muss mindestens {LAMBDA_CONSTRAINTS.min_timeout_seconds} Sekunde sein"

    if timeout_seconds > LAMBDA_CONSTRAINTS.max_timeout_seconds:
        return False, f"Lambda Timeout darf maximal {LAMBDA_CONSTRAINTS.max_timeout_seconds} Sekunden (15 Minuten) sein"

    return True, None


def get_ec2_instance_type(instance_type: str) -> EC2InstanceType | None:
    """
    Holt EC2 Instance Type Details.

    Args:
        instance_type: Instance Type Name (z.B. "t3.medium")

    Returns:
        Optional[EC2InstanceType]: Instance Type oder None wenn nicht gefunden
    """
    return EC2_INSTANCE_TYPES.get(instance_type)


def get_rds_engine(engine: str) -> RDSEngine | None:
    """
    Holt RDS Engine Details.

    Args:
        engine: Engine Name (z.B. "mysql", "postgres")

    Returns:
        Optional[RDSEngine]: Engine Details oder None wenn nicht gefunden
    """
    return RDS_ENGINES.get(engine)


def validate_rds_iops(
    storage_type: str,
    iops: int,
    storage_gb: int
) -> tuple[bool, str | None]:
    """
    Validiert RDS IOPS-Konfiguration.

    Args:
        storage_type: Storage Type (gp2, gp3, io1, io2)
        iops: Gewünschte IOPS
        storage_gb: Storage-Größe in GB

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if storage_type not in RDS_STORAGE_TYPES:
        return False, f"Unbekannter Storage Type: {storage_type}"

    storage_config = RDS_STORAGE_TYPES[storage_type]

    # gp2: 3 IOPS per GB, min 100, max 16000
    if storage_type == "gp2":
        calculated_iops = min(storage_gb * 3, 16000)
        if iops != calculated_iops:
            return False, f"gp2 IOPS werden automatisch berechnet (3 IOPS/GB). Für {storage_gb}GB: {calculated_iops} IOPS"

    # gp3: Baseline 3000 IOPS, bis zu 16000
    elif storage_type == "gp3":
        if iops < 3000:
            return False, "gp3 hat eine Baseline von 3000 IOPS"
        if iops > 16000:
            return False, "gp3 unterstützt maximal 16000 IOPS"

    # io1/io2: Provisioned IOPS
    elif storage_type in ["io1", "io2"]:
        if not storage_config.min_iops or not storage_config.max_iops:
            return False, f"IOPS-Limits für {storage_type} nicht definiert"

        if iops < storage_config.min_iops:
            return False, f"{storage_config.display_name} benötigt mindestens {storage_config.min_iops} IOPS"

        if iops > storage_config.max_iops:
            return False, f"{storage_config.display_name} unterstützt maximal {storage_config.max_iops} IOPS"

        # Ratio Check: io1 = 50:1, io2 = 500:1 (IOPS:GB)
        max_ratio = 500 if storage_type == "io2" else 50
        max_iops_for_storage = storage_gb * max_ratio

        if iops > max_iops_for_storage:
            return False, f"Für {storage_gb}GB Storage sind maximal {max_iops_for_storage} IOPS möglich (Ratio {max_ratio}:1)"

    return True, None


# ============================================================================
# Cost Calculation Helpers
# ============================================================================

def calculate_ec2_monthly_cost(
    instance_type: str,
    hours_per_month: int = 730  # ~30 days * 24 hours
) -> Decimal:
    """
    Berechnet monatliche EC2-Kosten.

    Args:
        instance_type: EC2 Instance Type
        hours_per_month: Stunden pro Monat (Standard: 730)

    Returns:
        Decimal: Monatliche Kosten in USD
    """
    instance = EC2_INSTANCE_TYPES.get(instance_type)
    if not instance:
        return Decimal("0")

    return instance.price_per_hour_usd * Decimal(hours_per_month)


def calculate_rds_monthly_cost(
    instance_class: str,
    storage_gb: int,
    storage_type: str = "gp3",
    multi_az: bool = False,
    backup_storage_gb: int = 0,
    iops: int | None = None
) -> Decimal:
    """
    Berechnet monatliche RDS-Kosten.

    Args:
        instance_class: RDS Instance Class (z.B. "db.t3.medium")
        storage_gb: Storage-Größe in GB
        storage_type: Storage Type (gp2, gp3, io1, io2)
        multi_az: Multi-AZ Deployment
        backup_storage_gb: Backup Storage in GB (first 100% of DB storage is free)
        iops: Provisioned IOPS (für io1/io2 oder zusätzliche gp3 IOPS)

    Returns:
        Decimal: Monatliche Kosten in USD
    """
    total_cost = Decimal("0")

    # Instance Kosten
    instance = RDS_INSTANCE_CLASSES.get(instance_class)
    if instance:
        hourly_rate = instance.price_per_hour_multi_az_usd if multi_az else instance.price_per_hour_usd
        total_cost += hourly_rate * Decimal("730")  # ~30 days * 24 hours

    # Storage Kosten
    storage = RDS_STORAGE_TYPES.get(storage_type)
    if storage:
        total_cost += storage.price_per_gb_month_usd * Decimal(storage_gb)

        # IOPS Kosten (für io1/io2 oder gp3 > 3000 IOPS)
        if storage.price_per_iops_month_usd and iops:
            if storage_type in ["io1", "io2"]:
                total_cost += storage.price_per_iops_month_usd * Decimal(iops)
            elif storage_type == "gp3" and iops > 3000:
                additional_iops = iops - 3000
                total_cost += storage.price_per_iops_month_usd * Decimal(additional_iops)

    # Backup Storage Kosten (nur für Storage > DB Size)
    if backup_storage_gb > storage_gb:
        billable_backup = backup_storage_gb - storage_gb
        # Backup storage costs $0.095 per GB/month
        total_cost += Decimal("0.095") * Decimal(billable_backup)

    return total_cost


def calculate_lambda_monthly_cost(
    invocations_per_month: int,
    avg_duration_ms: int,
    memory_mb: int
) -> Decimal:
    """
    Berechnet monatliche Lambda-Kosten.

    Args:
        invocations_per_month: Anzahl Invocations pro Monat
        avg_duration_ms: Durchschnittliche Laufzeit in Millisekunden
        memory_mb: Memory in MB

    Returns:
        Decimal: Monatliche Kosten in USD
    """
    # Request Kosten (nach Free Tier)
    billable_requests = max(0, invocations_per_month - LAMBDA_CONSTRAINTS.free_tier_requests_per_month)
    request_cost = Decimal(billable_requests) * LAMBDA_CONSTRAINTS.price_per_request_usd

    # Compute Kosten (nach Free Tier)
    gb_seconds = (Decimal(memory_mb) / Decimal("1024")) * (Decimal(avg_duration_ms) / Decimal("1000")) * Decimal(invocations_per_month)
    billable_gb_seconds = max(Decimal("0"), gb_seconds - Decimal(LAMBDA_CONSTRAINTS.free_tier_gb_seconds_per_month))
    compute_cost = billable_gb_seconds * LAMBDA_CONSTRAINTS.price_per_gb_second_usd

    return request_cost + compute_cost


def calculate_s3_monthly_cost(
    storage_gb: int,
    storage_class: str = "STANDARD",
    get_requests_per_month: int = 0,
    put_requests_per_month: int = 0
) -> Decimal:
    """
    Berechnet monatliche S3-Kosten.

    Args:
        storage_gb: Storage-Größe in GB
        storage_class: Storage Class
        get_requests_per_month: GET/SELECT Requests pro Monat
        put_requests_per_month: PUT/COPY/POST/LIST Requests pro Monat

    Returns:
        Decimal: Monatliche Kosten in USD
    """
    storage = S3_STORAGE_CLASSES.get(storage_class)
    if not storage:
        return Decimal("0")

    # Storage Kosten
    storage_cost = storage.price_per_gb_month_usd * Decimal(storage_gb)

    # Request Kosten (vereinfacht)
    # GET: $0.0004 per 1,000 requests
    # PUT: $0.005 per 1,000 requests
    get_cost = (Decimal(get_requests_per_month) / Decimal("1000")) * Decimal("0.0004")
    put_cost = (Decimal(put_requests_per_month) / Decimal("1000")) * Decimal("0.005")

    return storage_cost + get_cost + put_cost
