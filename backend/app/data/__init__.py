"""
AWS Constraints und Pricing Data Package

Dieses Package enthält alle AWS-Limits, Preise und Validierungsregeln
für die StackVertex-Plattform.
"""

from .aws_constraints import (
    CLOUDFRONT_PRICE_CLASSES,
    # Data structures
    EC2_INSTANCE_TYPES,
    LAMBDA_CONSTRAINTS,
    RDS_ENGINES,
    RDS_INSTANCE_CLASSES,
    RDS_STORAGE_TYPES,
    ROUTE53_PRICING,
    S3_STORAGE_CLASSES,
    VPC_CONSTRAINTS,
    CloudFrontPriceClass,
    # Models
    EC2InstanceType,
    LambdaConstraints,
    RDSEngine,
    RDSInstanceClass,
    RDSStorageType,
    Route53Pricing,
    S3StorageClass,
    VPCConstraints,
    # Cost calculation functions
    calculate_ec2_monthly_cost,
    calculate_lambda_monthly_cost,
    calculate_rds_monthly_cost,
    calculate_s3_monthly_cost,
    calculate_vpc_usable_ips,
    # Getter functions
    get_ec2_instance_type,
    get_rds_engine,
    validate_lambda_memory,
    validate_lambda_timeout,
    validate_rds_iops,
    # Validation functions
    validate_rds_storage,
    validate_vpc_cidr,
)

__all__ = [
    # Datenstrukturen
    "EC2_INSTANCE_TYPES",
    "RDS_ENGINES",
    "RDS_INSTANCE_CLASSES",
    "RDS_STORAGE_TYPES",
    "S3_STORAGE_CLASSES",
    "LAMBDA_CONSTRAINTS",
    "VPC_CONSTRAINTS",
    "CLOUDFRONT_PRICE_CLASSES",
    "ROUTE53_PRICING",
    # Modelle
    "EC2InstanceType",
    "RDSEngine",
    "RDSInstanceClass",
    "RDSStorageType",
    "S3StorageClass",
    "LambdaConstraints",
    "VPCConstraints",
    "CloudFrontPriceClass",
    "Route53Pricing",
    # Validation Helpers
    "validate_rds_storage",
    "validate_vpc_cidr",
    "calculate_vpc_usable_ips",
    "validate_lambda_memory",
    "validate_lambda_timeout",
    "validate_rds_iops",
    # Getter Functions
    "get_ec2_instance_type",
    "get_rds_engine",
    # Cost Calculation Helpers
    "calculate_ec2_monthly_cost",
    "calculate_rds_monthly_cost",
    "calculate_lambda_monthly_cost",
    "calculate_s3_monthly_cost",
]
