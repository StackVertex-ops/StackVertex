"""Audit Log API Endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.repositories.audit_log import AuditLogRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency injection for AuditLogRepository
def get_audit_log_repo() -> AuditLogRepository:
    """Get AuditLogRepository instance."""
    return AuditLogRepository()


class AuditLogResponse(BaseModel):
    """Audit Log Response Schema."""

    id: UUID
    user: str
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    success: str
    error_message: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Audit Log List Response."""

    items: list[AuditLogResponse] = Field(default_factory=list)
    total: int
    skip: int
    limit: int


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List Audit Logs",
    description="Query audit logs with filtering"
)
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(100, ge=1, le=1000, description="Limit"),
    user: Optional[str] = Query(None, description="Filter by user"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[UUID] = Query(None, description="Filter by resource ID"),
    repo: AuditLogRepository = Depends(get_audit_log_repo)
) -> AuditLogListResponse:
    """List audit logs with filtering.

    Args:
        skip: Offset
        limit: Limit
        user: Filter by user
        action: Filter by action
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        repo: AuditLogRepository

    Returns:
        AuditLogListResponse
    """
    items, total = repo.list(
        skip=skip,
        limit=limit,
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id
    )

    return AuditLogListResponse(
        items=[AuditLogResponse(**item) for item in items],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/audit-logs/stats",
    summary="Audit Log Statistics",
    description="Get audit log statistics"
)
async def audit_log_stats(
    repo: AuditLogRepository = Depends(get_audit_log_repo)
) -> dict:
    """Get audit log statistics.

    Args:
        repo: AuditLogRepository

    Returns:
        Statistics dict with pre-aggregated data

    Note:
        Returns pre-aggregated statistics from DynamoDB (STATS#AUDIT/REALTIME item).
        Stats are updated in real-time via DynamoDB Streams + Lambda.
    """
    # Get pre-aggregated stats (O(1) query, not O(n) scan!)
    stats = repo.get_stats()

    # Format top_users for response
    user_counts = stats.get("user_counts", {})
    top_users = [
        {"user": user, "count": count}
        for user, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return {
        "total_logs": stats.get("total_logs", 0),
        "failed_actions": stats.get("failed_count", 0),
        "actions": stats.get("action_counts", {}),
        "top_users": top_users,
        "last_updated": stats.get("last_updated")
    }
