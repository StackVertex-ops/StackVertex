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
# DynamoDB Mock Fixtures (TODO: Implement with moto or DynamoDB Local)
# =============================================================================


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing.

    TODO: Implement using moto or DynamoDB Local
    """
    # Placeholder - tests should mock at repository level for now
    pass


@pytest.fixture
def mock_s3_bucket():
    """Mock S3 bucket for testing.

    TODO: Implement using moto
    """
    # Placeholder - tests should mock at repository level for now
    pass
