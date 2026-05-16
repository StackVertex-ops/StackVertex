#!/usr/bin/env python3
"""
Test-Script für AWS Constraints Database

Dieses Script testet die grundlegenden Funktionen der AWS Constraints Database.
"""

from app.data import (
    EC2_INSTANCE_TYPES,
    RDS_ENGINES,
    RDS_INSTANCE_CLASSES,
    RDS_STORAGE_TYPES,
    S3_STORAGE_CLASSES,
    LAMBDA_CONSTRAINTS,
    VPC_CONSTRAINTS,
    CLOUDFRONT_PRICE_CLASSES,
    ROUTE53_PRICING,
    validate_rds_storage,
    validate_vpc_cidr,
    calculate_vpc_usable_ips,
    validate_lambda_memory,
    validate_lambda_timeout,
    validate_rds_iops,
    get_ec2_instance_type,
    get_rds_engine,
    calculate_ec2_monthly_cost,
    calculate_rds_monthly_cost,
    calculate_lambda_monthly_cost,
    calculate_s3_monthly_cost,
)


def test_ec2_instance_types():
    """Test EC2 Instance Types"""
    print("=" * 80)
    print("EC2 INSTANCE TYPES TEST")
    print("=" * 80)

    print(f"\nTotal Instance Types: {len(EC2_INSTANCE_TYPES)}")

    # Test t3.medium
    instance = get_ec2_instance_type("t3.medium")
    if instance:
        print(f"\nt3.medium Details:")
        print(f"  vCPUs: {instance.vcpus}")
        print(f"  Memory: {instance.memory_gb} GB")
        print(f"  Price: ${instance.price_per_hour_usd}/hour")
        print(f"  Architecture: {', '.join(instance.architecture)}")
        print(f"  Use Cases: {', '.join(instance.use_cases)}")

        # Cost calculation
        monthly_cost = calculate_ec2_monthly_cost("t3.medium")
        print(f"  Monthly Cost (730h): ${monthly_cost:.2f}")

    # Test ARM instance
    arm_instance = get_ec2_instance_type("t4g.medium")
    if arm_instance:
        print(f"\nt4g.medium (ARM) Details:")
        print(f"  Architecture: {', '.join(arm_instance.architecture)}")
        print(f"  Price: ${arm_instance.price_per_hour_usd}/hour")
        monthly_cost = calculate_ec2_monthly_cost("t4g.medium")
        print(f"  Monthly Cost: ${monthly_cost:.2f}")

        # Price comparison
        x86_cost = calculate_ec2_monthly_cost("t3.medium")
        savings = ((x86_cost - monthly_cost) / x86_cost) * 100
        print(f"  Savings vs t3.medium: {savings:.1f}%")


def test_rds_constraints():
    """Test RDS Constraints"""
    print("\n" + "=" * 80)
    print("RDS CONSTRAINTS TEST")
    print("=" * 80)

    print(f"\nDatabase Engines: {len(RDS_ENGINES)}")
    print(f"Instance Classes: {len(RDS_INSTANCE_CLASSES)}")
    print(f"Storage Types: {len(RDS_STORAGE_TYPES)}")

    # Test MySQL constraints
    engine = get_rds_engine("mysql")
    if engine:
        print(f"\nMySQL Details:")
        print(f"  Display Name: {engine.display_name}")
        print(f"  Versions: {', '.join(engine.versions[:3])}...")
        print(f"  Min Storage: {engine.min_storage_gb} GB")
        print(f"  Max Storage: {engine.max_storage_gb} GB")
        print(f"  Default Port: {engine.default_port}")

    # Test storage validation
    print("\nStorage Validation Tests:")

    # Valid storage
    valid, msg = validate_rds_storage(100, "mysql", "gp3")
    print(f"  100 GB MySQL gp3: {'✓ Valid' if valid else f'✗ {msg}'}")

    # Invalid: too small
    valid, msg = validate_rds_storage(5, "mysql", "gp3")
    print(f"  5 GB MySQL gp3: {'✓ Valid' if valid else f'✗ {msg}'}")

    # Invalid: io1 too small
    valid, msg = validate_rds_storage(50, "postgres", "io1")
    print(f"  50 GB PostgreSQL io1: {'✓ Valid' if valid else f'✗ {msg}'}")

    # Cost calculation
    print("\nRDS Cost Examples:")
    cost = calculate_rds_monthly_cost("db.t3.medium", 100, "gp3", multi_az=False)
    print(f"  db.t3.medium + 100GB gp3 (Single-AZ): ${cost:.2f}/month")

    cost_multi_az = calculate_rds_monthly_cost("db.t3.medium", 100, "gp3", multi_az=True)
    print(f"  db.t3.medium + 100GB gp3 (Multi-AZ): ${cost_multi_az:.2f}/month")


def test_vpc_constraints():
    """Test VPC Constraints"""
    print("\n" + "=" * 80)
    print("VPC CONSTRAINTS TEST")
    print("=" * 80)

    print(f"\nVPC Limits:")
    print(f"  Min CIDR Prefix: /{VPC_CONSTRAINTS.min_cidr_prefix}")
    print(f"  Max CIDR Prefix: /{VPC_CONSTRAINTS.max_cidr_prefix}")
    print(f"  Reserved IPs per Subnet: {VPC_CONSTRAINTS.reserved_ips_per_subnet}")
    print(f"  Max Subnets per VPC: {VPC_CONSTRAINTS.max_subnets_per_vpc}")

    print("\nCIDR Validation Tests:")

    # Valid CIDRs
    test_cidrs = [
        "10.0.0.0/16",
        "172.16.0.0/20",
        "192.168.1.0/24",
        "10.0.0.0/28",
        "8.8.8.0/24",  # Public IP (warning)
        "10.0.0.0/15",  # Too large
        "10.0.0.0/29",  # Too small
    ]

    for cidr in test_cidrs:
        valid, msg = validate_vpc_cidr(cidr)
        usable_ips = calculate_vpc_usable_ips(cidr) if valid else 0
        status = "✓ Valid" if valid and not msg else f"⚠ Warning: {msg}" if valid and msg else f"✗ {msg}"
        print(f"  {cidr:20} {status} (Usable IPs: {usable_ips})")


def test_lambda_constraints():
    """Test Lambda Constraints"""
    print("\n" + "=" * 80)
    print("LAMBDA CONSTRAINTS TEST")
    print("=" * 80)

    print(f"\nLambda Limits:")
    print(f"  Memory: {LAMBDA_CONSTRAINTS.min_memory_mb} - {LAMBDA_CONSTRAINTS.max_memory_mb} MB")
    print(f"  Timeout: {LAMBDA_CONSTRAINTS.min_timeout_seconds} - {LAMBDA_CONSTRAINTS.max_timeout_seconds} seconds")
    print(f"  Ephemeral Storage: {LAMBDA_CONSTRAINTS.min_ephemeral_storage_mb} - {LAMBDA_CONSTRAINTS.max_ephemeral_storage_mb} MB")
    print(f"  Default Concurrent Executions: {LAMBDA_CONSTRAINTS.default_concurrent_executions}")

    print("\nFree Tier:")
    print(f"  Requests: {LAMBDA_CONSTRAINTS.free_tier_requests_per_month:,} per month")
    print(f"  GB-Seconds: {LAMBDA_CONSTRAINTS.free_tier_gb_seconds_per_month:,} per month")

    print("\nMemory Validation Tests:")
    test_memories = [128, 256, 512, 1024, 2048, 10240, 100, 20000]
    for mem in test_memories:
        valid, msg = validate_lambda_memory(mem)
        print(f"  {mem:6} MB: {'✓ Valid' if valid else f'✗ {msg}'}")

    print("\nCost Examples:")
    # Example: 1M requests, 200ms avg, 512MB memory
    cost = calculate_lambda_monthly_cost(1000000, 200, 512)
    print(f"  1M requests/month, 200ms avg, 512MB: ${cost:.4f}/month")

    # Example: 10M requests, 500ms avg, 1024MB memory
    cost = calculate_lambda_monthly_cost(10000000, 500, 1024)
    print(f"  10M requests/month, 500ms avg, 1024MB: ${cost:.2f}/month")


def test_s3_storage_classes():
    """Test S3 Storage Classes"""
    print("\n" + "=" * 80)
    print("S3 STORAGE CLASSES TEST")
    print("=" * 80)

    print(f"\nStorage Classes: {len(S3_STORAGE_CLASSES)}")

    for name, storage_class in S3_STORAGE_CLASSES.items():
        print(f"\n{storage_class.display_name}:")
        print(f"  Storage: ${storage_class.price_per_gb_month_usd}/GB/month")
        print(f"  Retrieval: ${storage_class.retrieval_price_per_gb_usd}/GB")
        print(f"  Min Duration: {storage_class.min_storage_duration_days} days")
        print(f"  Retrieval Time: {storage_class.retrieval_time}")

    print("\nCost Comparison (1TB storage, 10k GET requests, 1k PUT requests):")
    for name in ["STANDARD", "INTELLIGENT_TIERING", "STANDARD_IA", "GLACIER"]:
        cost = calculate_s3_monthly_cost(1024, name, 10000, 1000)
        print(f"  {name:25} ${cost:.2f}/month")


def test_cloudfront_route53():
    """Test CloudFront and Route53 Pricing"""
    print("\n" + "=" * 80)
    print("CLOUDFRONT & ROUTE53 TEST")
    print("=" * 80)

    print("\nCloudFront Price Classes:")
    for name, price_class in CLOUDFRONT_PRICE_CLASSES.items():
        print(f"\n{price_class.display_name}:")
        print(f"  Regions: {', '.join(price_class.regions)}")
        print(f"  Data Transfer: ${price_class.data_transfer_out_per_gb_usd}/GB")
        print(f"  HTTPS Requests: ${price_class.request_price_per_10k_https_usd}/10k")

    print("\nRoute53 Pricing:")
    print(f"  Hosted Zone: ${ROUTE53_PRICING.hosted_zone_per_month_usd}/month")
    print(f"  Standard Queries: ${ROUTE53_PRICING.standard_queries_per_million_usd}/million")
    print(f"  Geo Queries: ${ROUTE53_PRICING.geo_queries_per_million_usd}/million")
    print(f"  Health Check (Basic): ${ROUTE53_PRICING.health_check_basic_per_month_usd}/month")
    print(f"  Domain .com: ${ROUTE53_PRICING.domain_registration_com_per_year_usd}/year")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("AWS CONSTRAINTS DATABASE TEST SUITE")
    print("=" * 80)

    test_ec2_instance_types()
    test_rds_constraints()
    test_vpc_constraints()
    test_lambda_constraints()
    test_s3_storage_classes()
    test_cloudfront_route53()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
