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
    SECRET_KEY: str  # REQUIRED in .env - min 32 chars, cryptographically random
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ENV: str = "development"  # development, staging, production
    TESTING: bool = False  # Set True in tests to disable rate limiting

    # Stripe Payment
    STRIPE_SECRET_KEY: str | None = None  # sk_test_... or sk_live_...
    STRIPE_PUBLISHABLE_KEY: str | None = None  # pk_test_... or pk_live_...
    STRIPE_WEBHOOK_SECRET: str | None = None  # whsec_...
    STRIPE_ENABLED: bool = False  # Enable Stripe integration

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure SECRET_KEY is strong enough."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v in ["your-secret-key-change-in-production", "secret", "changeme", "test"]:
            raise ValueError("SECRET_KEY must not use common/default values")
        return v

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

    # Logging & Monitoring
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_JSON_FORMAT: bool = False  # Enable JSON logging (True for production)
    ENABLE_CLOUDWATCH: bool = False  # Send logs to AWS CloudWatch
    ENABLE_SENTRY: bool = False  # Enable Sentry error tracking
    SENTRY_DSN: str | None = None  # Sentry DSN (https://xxx@sentry.io/xxx)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create settings instance
settings = Settings()
