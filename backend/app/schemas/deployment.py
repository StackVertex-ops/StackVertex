"""Deployment Schemas.

Pydantic schemas für Deployment API.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.deployment import DeploymentStatus


class DeploymentCreate(BaseModel):
    """Schema für Deployment Creation."""

    architecture_id: UUID = Field(..., description="Architecture ID to deploy")
    deployed_by: str = Field(..., description="User who initiated deployment")
    aws_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="AWS credentials (access_key_id, secret_access_key, region)"
    )


class DeploymentResponse(BaseModel):
    """Schema für Deployment Response."""

    id: UUID = Field(..., description="Deployment ID")
    architecture_id: UUID = Field(..., description="Architecture ID")
    status: DeploymentStatus = Field(..., description="Deployment status")
    terraform_version: Optional[str] = Field(None, description="Terraform version used")
    generated_files: Optional[Dict[str, str]] = Field(None, description="Generated Terraform files")
    plan_output: Optional[str] = Field(None, description="Terraform plan output")
    apply_output: Optional[str] = Field(None, description="Terraform apply output")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Terraform outputs")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Deployment start time")
    completed_at: Optional[datetime] = Field(None, description="Deployment completion time")
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
    estimated_remaining_seconds: Optional[float] = Field(
        None,
        description="Estimated remaining time in seconds"
    )

    # Terraform Info
    terraform_version: Optional[str] = Field(None, description="Terraform version")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """Schema für Deployment List Response."""

    items: list[DeploymentResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total number of deployments")
    skip: int = Field(default=0, description="Number of items skipped")
    limit: int = Field(default=100, description="Number of items returned")
