"""OverCloud Backend - Configuration.

Loads configuration from environment variables using Pydantic Settings.
"""

import tempfile
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Settings
    APP_NAME: str = "OverCloud API"
    DEBUG: bool = True

    # Server Settings
    # In production: Set HOST="127.0.0.1" or specific IP
    # 0.0.0.0 binds to all interfaces (OK for containers, but security risk otherwise)
    HOST: str = "127.0.0.1"  # Secure default: localhost only
    PORT: int = 8000

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Database Settings (PostgreSQL - Legacy, being replaced by DynamoDB)
    # Format: postgresql://user:password@host:port/database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/overcloud"

    # DynamoDB Settings
    DYNAMODB_TABLE_NAME: str = "overcloud-dev-main"
    DYNAMODB_ENDPOINT_URL: str | None = None  # Use for DynamoDB Local testing

    # S3 Settings
    S3_LARGE_ITEMS_BUCKET: str = "overcloud-dev-large-items"
    LARGE_ITEM_THRESHOLD: int = 300_000  # 300KB - items larger than this go to S3

    # AWS Settings (for Boto3)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str | None = None  # Use IAM roles in production
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"  # Change in .env!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Terraform Settings
    TERRAFORM_BINARY: str = "terraform"
    # Use system temp dir by default (secure, cross-platform)
    TERRAFORM_WORKSPACE_DIR: str = str(Path(tempfile.gettempdir()) / "overcloud" / "deployments")
    TERRAFORM_TEMPLATE_DIR: str = "backend/templates/terraform"
    TERRAFORM_TIMEOUT: int = 600  # seconds (10 minutes)

    # Pricing Data
    PRICING_DATA_DIR: str = "backend/data/aws_pricing"

    # Versioning
    CURRENT_SCHEMA_VERSION: str = "1.0.0"

    # Deployment
    DEPLOYMENT_RETENTION_DAYS: int = 30
    MAX_CONCURRENT_DEPLOYMENTS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create settings instance
settings = Settings()
