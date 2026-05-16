"""Zentrale pytest Fixtures für OverCloud Backend Tests.

DynamoDB-basierte Tests mit Mocks oder DynamoDB Local.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


# =============================================================================
# FastAPI Test Client Fixtures
# =============================================================================


@pytest.fixture
def client() -> TestClient:
    """Provide FastAPI test client.

    Note: Tests should mock DynamoDB/S3 operations or use DynamoDB Local.
    """
    return TestClient(app)


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_architecture_json() -> Dict[str, Any]:
    """Provide sample architecture JSON for testing."""
    return {
        "version": "1.0.0",
        "metadata": {
            "name": "Test Web Application",
            "description": "Simple web app architecture",
            "created_by": "test_user"
        },
        "requirements": {
            "compute": {
                "type": "container",
                "replicas": 2,
                "cpu": "1vcpu",
                "memory": "2GB"
            },
            "storage": {
                "type": "object_storage",
                "size": "100GB"
            },
            "networking": {
                "public_access": True,
                "ssl": True
            }
        },
        "components": [
            {
                "id": "web-app",
                "type": "ecs_service",
                "properties": {
                    "image": "nginx:latest",
                    "port": 80,
                    "cpu": 512,
                    "memory": 1024
                }
            },
            {
                "id": "storage",
                "type": "s3_bucket",
                "properties": {
                    "versioning": True,
                    "encryption": "AES256"
                }
            }
        ]
    }


@pytest.fixture
def sample_deployment_data() -> Dict[str, Any]:
    """Provide sample deployment data for testing."""
    return {
        "architecture_id": str(uuid4()),
        "deployed_by": "test_user",
        "aws_credentials": {
            "access_key_id": "test_key",
            "secret_access_key": "test_secret",
            "region": "us-east-1"
        }
    }


# =============================================================================
# Temporary Directory Fixtures
# =============================================================================


@pytest.fixture
def temp_terraform_dir() -> Generator[Path, None, None]:
    """Provide temporary directory for Terraform files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# DynamoDB & S3 Mock Fixtures (moto-basiert)
# =============================================================================


@pytest.fixture
def aws_credentials():
    """Fake AWS credentials für moto."""
    import os
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def mock_dynamodb_resource(aws_credentials):
    """Mocked DynamoDB Resource mit moto."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture
def mock_dynamodb_table(mock_dynamodb_resource):
    """Mocked DynamoDB Table mit vollem Schema (alle 6 GSIs)."""
    from mypy_boto3_dynamodb.service_resource import Table

    table: Table = mock_dynamodb_resource.create_table(
        TableName="overcloud-test-table",
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
            {"AttributeName": "GSI2PK", "AttributeType": "S"},
            {"AttributeName": "GSI2SK", "AttributeType": "S"},
            {"AttributeName": "GSI3PK", "AttributeType": "S"},
            {"AttributeName": "GSI3SK", "AttributeType": "S"},
            {"AttributeName": "GSI4PK", "AttributeType": "S"},
            {"AttributeName": "GSI4SK", "AttributeType": "S"},
            {"AttributeName": "GSI5PK", "AttributeType": "S"},
            {"AttributeName": "GSI5SK", "AttributeType": "S"},
            {"AttributeName": "GSI6PK", "AttributeType": "S"},
            {"AttributeName": "GSI6SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
            {
                "IndexName": "GSI2",
                "KeySchema": [
                    {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI2SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
            {
                "IndexName": "GSI3",
                "KeySchema": [
                    {"AttributeName": "GSI3PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI3SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
            {
                "IndexName": "GSI4",
                "KeySchema": [
                    {"AttributeName": "GSI4PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI4SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
            {
                "IndexName": "GSI5",
                "KeySchema": [
                    {"AttributeName": "GSI5PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI5SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
            {
                "IndexName": "GSI6",
                "KeySchema": [
                    {"AttributeName": "GSI6PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI6SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    # Wait for table to be ready
    table.meta.client.get_waiter("table_exists").wait(TableName="overcloud-test-table")

    return table


@pytest.fixture
def mock_s3_resource(aws_credentials):
    """Mocked S3 Resource mit moto."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):
    """Mocked S3 Bucket für Large Item Testing."""
    bucket_name = "overcloud-test-bucket"
    bucket = mock_s3_resource.create_bucket(Bucket=bucket_name)
    return bucket


@pytest.fixture
def mock_secrets_manager_client(aws_credentials):
    """Mocked AWS Secrets Manager Client mit moto."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        yield boto3.client("secretsmanager", region_name="us-east-1")


@pytest.fixture
def mock_secrets_manager(mock_secrets_manager_client):
    """Mocked SecretsManager Service für Testing."""
    from app.services.secrets_manager import SecretsManager

    # SecretsManager nutzt den gemockten Client
    return SecretsManager(client=mock_secrets_manager_client)


# =============================================================================
# Sample Large Data Fixtures
# =============================================================================


@pytest.fixture
def sample_large_architecture_json() -> Dict[str, Any]:
    """Generate architecture JSON > 300KB für S3 Offload Testing."""
    # Create base structure
    arch = {
        "version": "1.0.0",
        "metadata": {
            "name": "Large Architecture",
            "description": "Test architecture exceeding 300KB"
        },
        "components": []
    }

    # Add many components to exceed 300KB threshold
    # Each component is ~3KB, need ~100 components for 300KB
    for i in range(120):
        component = {
            "id": f"component-{i}",
            "type": "ecs_service",
            "properties": {
                "image": f"nginx:latest-{i}",
                "port": 80 + i,
                "cpu": 512,
                "memory": 1024,
                "environment": {
                    f"VAR_{j}": "x" * 100 for j in range(20)
                },
                "tags": {
                    f"tag_{k}": "value" * 50 for k in range(10)
                }
            }
        }
        arch["components"].append(component)

    # Verify size > 300KB
    json_str = json.dumps(arch, ensure_ascii=False)
    assert len(json_str.encode("utf-8")) > 300_000, "Test data must exceed 300KB"

    return arch


@pytest.fixture
def sample_architecture_minimal() -> Dict[str, Any]:
    """Provide minimal architecture JSON (Alias für sample_architecture_json).

    Für Rückwärtskompatibilität mit alten Tests.
    """
    from datetime import datetime, timezone
    from uuid import uuid4

    return {
        "version": "1.0.0",
        "metadata": {
            "id": str(uuid4()),
            "name": "Minimal Test Architecture",
            "description": "Minimal architecture for testing",
            "provider": "aws",
            "region": "us-east-1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "requirements": {
            "compute": {},
            "storage": {},
            "networking": {}
        },
        "architecture": {
            "components": [],
            "relationships": []
        }
    }


@pytest.fixture
def sample_architecture_simple_web() -> Dict[str, Any]:
    """Provide simple web app architecture for E2E testing."""
    return {
        "version": "1.0.0",
        "metadata": {
            "name": "Simple Web Application",
            "description": "Basic web app with VPC, subnet, EC2, and S3",
            "provider": "aws",
            "region": "us-east-1"
        },
        "architecture": {
            "components": [
                {
                    "id": "main_vpc",
                    "type": "vpc",
                    "name": "Main VPC",
                    "configuration": {
                        "cidr_block": "10.0.0.0/16",
                        "enable_dns_hostnames": True,
                        "enable_dns_support": True
                    }
                },
                {
                    "id": "public_subnet",
                    "type": "subnet",
                    "name": "Public Subnet",
                    "configuration": {
                        "cidr_block": "10.0.1.0/24",
                        "availability_zone": "us-east-1a",
                        "map_public_ip_on_launch": True
                    }
                },
                {
                    "id": "web_server",
                    "type": "ec2",
                    "name": "Web Server",
                    "configuration": {
                        "instance_type": "t3.micro",
                        "ami": "ami-0c55b159cbfafe1f0"
                    }
                },
                {
                    "id": "storage_bucket",
                    "type": "s3",
                    "name": "Storage Bucket",
                    "configuration": {
                        "bucket_name": "simple-web-app-storage",
                        "versioning_enabled": True
                    }
                }
            ]
        }
    }


# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture
def base_repository(mock_dynamodb_table, mock_s3_bucket):
    """BaseRepository mit mocked AWS resources."""
    from app.repositories.base import BaseRepository
    from app.db.s3_storage import S3Storage

    # Create S3Storage with mocked client
    s3_storage = S3Storage(bucket_name="overcloud-test-bucket")

    return BaseRepository(table=mock_dynamodb_table, s3_storage=s3_storage)


@pytest.fixture
def architecture_repository(mock_dynamodb_table, mock_s3_bucket):
    """ArchitectureRepository mit mocked AWS resources."""
    from app.repositories.architecture import ArchitectureRepository
    from app.db.s3_storage import S3Storage

    s3_storage = S3Storage(bucket_name="overcloud-test-bucket")
    return ArchitectureRepository(table=mock_dynamodb_table, s3_storage=s3_storage)


@pytest.fixture
def deployment_repository(mock_dynamodb_table, mock_s3_bucket):
    """DeploymentRepository mit mocked AWS resources."""
    from app.repositories.deployment import DeploymentRepository
    from app.db.s3_storage import S3Storage

    s3_storage = S3Storage(bucket_name="overcloud-test-bucket")
    return DeploymentRepository(table=mock_dynamodb_table, s3_storage=s3_storage)


@pytest.fixture
def audit_log_repository(mock_dynamodb_table):
    """AuditLogRepository mit mocked DynamoDB."""
    from app.repositories.audit_log import AuditLogRepository

    return AuditLogRepository(table=mock_dynamodb_table)


@pytest.fixture
def user_repository(mock_dynamodb_table):
    """UserRepository mit mocked DynamoDB."""
    from app.repositories.user import UserRepository

    return UserRepository(table=mock_dynamodb_table)


@pytest.fixture
def organisation_repository(mock_dynamodb_table, mock_s3_bucket, mock_secrets_manager):
    """OrganisationRepository mit mocked AWS resources und SecretsManager."""
    from app.repositories.organisation import OrganisationRepository
    from app.db.s3_storage import S3Storage

    s3_storage = S3Storage(bucket_name="overcloud-test-bucket")
    return OrganisationRepository(
        table=mock_dynamodb_table,
        s3_storage=s3_storage,
        secrets_manager=mock_secrets_manager
    )
