"""Deployment Schemas.

Pydantic schemas für Deployment API.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.deployment import DeploymentStatus


class DeploymentCreate(BaseModel):
    """Schema für Deployment Creation."""

    architecture_id: UUID = Field(..., description="Architecture ID to deploy")
    deployed_by: str = Field(..., description="User who initiated deployment")
    aws_credentials: dict[str, str] | None = Field(
        None,
        description="AWS credentials (access_key_id, secret_access_key, region)"
    )


class DeploymentResponse(BaseModel):
    """Schema für Deployment Response."""

    id: UUID = Field(..., description="Deployment ID")
    architecture_id: UUID = Field(..., description="Architecture ID")
    status: DeploymentStatus = Field(..., description="Deployment status")
    terraform_version: str | None = Field(None, description="Terraform version used")
    generated_files: dict[str, str] | None = Field(None, description="Generated Terraform files")
    plan_output: str | None = Field(None, description="Terraform plan output")
    apply_output: str | None = Field(None, description="Terraform apply output")
    outputs: dict[str, Any] | None = Field(None, description="Terraform outputs")
    error_message: str | None = Field(None, description="Error message if failed")
    started_at: datetime | None = Field(None, description="Deployment start time")
    completed_at: datetime | None = Field(None, description="Deployment completion time")
    deployed_by: str = Field(..., description="User who initiated deployment")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Record last update time")

    class Config:
        from_attributes = True


class DeploymentStatusResponse(BaseModel):
    """Enhanced Deployment Status Response mit Progress Tracking."""

    id: UUID = Field(..., description="Deployment ID")
    architecture_id: UUID = Field(..., description="Architecture ID")
    status: DeploymentStatus = Field(..., description="Deployment status")
    deployed_by: str = Field(..., description="User who initiated deployment")

    # Progress Information
    progress_percentage: int = Field(..., description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current deployment step")
    elapsed_seconds: float = Field(..., description="Elapsed time in seconds")
    estimated_remaining_seconds: float | None = Field(
        None,
        description="Estimated remaining time in seconds"
    )

    # Terraform Info
    terraform_version: str | None = Field(None, description="Terraform version")
    error_message: str | None = Field(None, description="Error message if failed")

    # Timestamps
    started_at: datetime | None = Field(None, description="Start time")
    completed_at: datetime | None = Field(None, description="Completion time")

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """Schema für Deployment List Response."""

    items: list[DeploymentResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total number of deployments")
    skip: int = Field(default=0, description="Number of items skipped")
    limit: int = Field(default=100, description="Number of items returned")
