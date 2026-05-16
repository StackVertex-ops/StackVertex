#!/usr/bin/env python3
"""Test Script für TerraformGeneratorV2.

Testet die Terraform-Generierung aus Architecture JSON.
"""

import json
import sys
from pathlib import Path
from pprint import pprint

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.terraform_generator_v2 import TerraformGeneratorV2


def test_simple_architecture():
    """Test mit einfacher Web-App Architektur."""
    print("=" * 80)
    print("Test: Simple Web App Architecture")
    print("=" * 80)

    architecture = {
        "metadata": {
            "name": "simple-web-app",
            "provider": "aws",
            "region": "us-east-1"
        },
        "components": {
            "vpc-1": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {
                    "cidr": "10.0.0.0/16",
                    "enableDns": True,
                    "needsIGW": True
                }
            },
            "subnet-1": {
                "name": "public-subnet-a",
                "type": "subnet",
                "config": {
                    "vpc": "vpc-1",
                    "cidr": "10.0.1.0/24",
                    "az": "us-east-1a",
                    "subnetType": "public"
                }
            },
            "sg-1": {
                "name": "web-sg",
                "type": "security_group",
                "config": {
                    "vpc": "vpc-1",
                    "description": "Security group for web servers",
                    "ingressRules": [
                        {
                            "description": "Allow HTTP",
                            "fromPort": 80,
                            "toPort": 80,
                            "protocol": "tcp",
                            "cidrBlocks": ["0.0.0.0/0"]
                        },
                        {
                            "description": "Allow HTTPS",
                            "fromPort": 443,
                            "toPort": 443,
                            "protocol": "tcp",
                            "cidrBlocks": ["0.0.0.0/0"]
                        }
                    ]
                }
            },
            "ec2-1": {
                "name": "web-server",
                "type": "ec2",
                "config": {
                    "subnet": "subnet-1",
                    "instanceType": "t3.small",
                    "hasPublicIp": True,
                    "securityGroups": ["sg-1"],
                    "userData": "#!/bin/bash\nyum update -y\nyum install -y httpd\nsystemctl start httpd\nsystemctl enable httpd"
                }
            }
        },
        "connections": [
            {"from": "vpc-1", "to": "subnet-1"},
            {"from": "subnet-1", "to": "ec2-1"},
            {"from": "sg-1", "to": "ec2-1"}
        ]
    }

    try:
        generator = TerraformGeneratorV2()
        files = generator.generate(architecture)

        print(f"\n✅ Generated {len(files)} Terraform files:\n")
        for filename, content in files.items():
            print(f"\n{'=' * 80}")
            print(f"File: {filename}")
            print(f"{'=' * 80}")
            print(content)
            print()

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alb_architecture():
    """Test mit ALB + Auto-Scaling Architektur."""
    print("\n" + "=" * 80)
    print("Test: ALB + Auto-Scaling Architecture")
    print("=" * 80)

    architecture = {
        "metadata": {
            "name": "alb-web-app",
            "provider": "aws",
            "region": "us-east-1"
        },
        "components": {
            "vpc-1": {
                "name": "main-vpc",
                "type": "vpc",
                "config": {
                    "cidr": "10.0.0.0/16",
                    "enableDns": True,
                    "needsIGW": True
                }
            },
            "subnet-1": {
                "name": "public-subnet-a",
                "type": "subnet",
                "config": {
                    "vpc": "vpc-1",
                    "cidr": "10.0.1.0/24",
                    "az": "us-east-1a",
                    "subnetType": "public"
                }
            },
            "subnet-2": {
                "name": "public-subnet-b",
                "type": "subnet",
                "config": {
                    "vpc": "vpc-1",
                    "cidr": "10.0.2.0/24",
                    "az": "us-east-1b",
                    "subnetType": "public"
                }
            },
            "sg-alb": {
                "name": "alb-sg",
                "type": "security_group",
                "config": {
                    "vpc": "vpc-1",
                    "description": "Security group for ALB",
                    "ingressRules": [
                        {
                            "description": "Allow HTTP",
                            "fromPort": 80,
                            "toPort": 80,
                            "protocol": "tcp",
                            "cidrBlocks": ["0.0.0.0/0"]
                        }
                    ]
                }
            },
            "alb-1": {
                "name": "main-alb",
                "type": "alb",
                "config": {
                    "vpc": "vpc-1",
                    "internal": False,
                    "subnets": ["subnet-1", "subnet-2"],
                    "securityGroups": ["sg-alb"],
                    "targetPort": 80,
                    "protocol": "HTTP",
                    "listenerPort": 80,
                    "listenerProtocol": "HTTP",
                    "healthCheck": {
                        "path": "/",
                        "interval": 30,
                        "timeout": 5,
                        "healthyThreshold": 2,
                        "unhealthyThreshold": 2
                    }
                }
            }
        },
        "connections": [
            {"from": "vpc-1", "to": "subnet-1"},
            {"from": "vpc-1", "to": "subnet-2"},
            {"from": "sg-alb", "to": "alb-1"},
            {"from": "subnet-1", "to": "alb-1"},
            {"from": "subnet-2", "to": "alb-1"}
        ]
    }

    try:
        generator = TerraformGeneratorV2()
        files = generator.generate(architecture)

        print(f"\n✅ Generated {len(files)} Terraform files")
        print(f"Files: {', '.join(files.keys())}")

        # Print nur ALB file
        if "alb.tf" in files:
            print(f"\n{'=' * 80}")
            print("File: alb.tf")
            print(f"{'=' * 80}")
            print(files["alb.tf"])

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dynamodb_architecture():
    """Test mit DynamoDB Architektur."""
    print("\n" + "=" * 80)
    print("Test: DynamoDB Architecture")
    print("=" * 80)

    architecture = {
        "metadata": {
            "name": "dynamodb-app",
            "provider": "aws",
            "region": "us-east-1"
        },
        "components": {
            "dynamodb-1": {
                "name": "users-table",
                "type": "dynamodb",
                "config": {
                    "billingMode": "PAY_PER_REQUEST",
                    "hashKey": "userId",
                    "hashKeyType": "S",
                    "rangeKey": "timestamp",
                    "rangeKeyType": "N",
                    "attributes": [
                        {"name": "email", "type": "S"},
                        {"name": "status", "type": "S"}
                    ],
                    "globalSecondaryIndexes": [
                        {
                            "name": "email-index",
                            "hashKey": "email",
                            "projectionType": "ALL"
                        },
                        {
                            "name": "status-index",
                            "hashKey": "status",
                            "rangeKey": "timestamp",
                            "projectionType": "ALL"
                        }
                    ],
                    "ttlEnabled": True,
                    "ttlAttribute": "expiresAt",
                    "pointInTimeRecovery": True,
                    "streamEnabled": True,
                    "streamViewType": "NEW_AND_OLD_IMAGES"
                }
            }
        },
        "connections": []
    }

    try:
        generator = TerraformGeneratorV2()
        files = generator.generate(architecture)

        print(f"\n✅ Generated {len(files)} Terraform files")

        if "dynamodb.tf" in files:
            print(f"\n{'=' * 80}")
            print("File: dynamodb.tf")
            print(f"{'=' * 80}")
            print(files["dynamodb.tf"])

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    tests = [
        test_simple_architecture,
        test_alb_architecture,
        test_dynamodb_architecture,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
