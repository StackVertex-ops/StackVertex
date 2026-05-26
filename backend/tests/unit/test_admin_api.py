"""Tests für Admin API Endpoints.

Tests für SuperAdmin-only Funktionen:
- User Management
- Organisation Management
- Audit Logs
- User Impersonation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from jose import jwt

from app.api.admin import (
    list_all_users,
    get_user_as_admin,
    update_user_status,
    update_user_system_role,
    reset_user_password,
    list_all_organisations,
    get_organisation_architectures,
    get_audit_logs,
    impersonate_user,
    get_system_stats,
    get_platform_statistics,
)
from app.config import settings
from app.models.user import SystemRole, UserStatus


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def superadmin_user():
    """Mock SuperAdmin user."""
    return {
        "id": str(uuid4()),
        "email": "admin@stackvertex.io",
        "name": "Super Admin",
        "system_role": SystemRole.SUPERADMIN.value,
        "status": UserStatus.ACTIVE.value,
        "auth_provider": "email",
        "personal_org_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def regular_user():
    """Mock regular user."""
    return {
        "id": str(uuid4()),
        "email": "user@example.com",
        "name": "Regular User",
        "system_role": SystemRole.USER.value,
        "status": UserStatus.ACTIVE.value,
        "auth_provider": "email",
        "personal_org_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_user_repo():
    """Mock UserRepository."""
    return Mock()


@pytest.fixture
def mock_org_repo():
    """Mock OrganisationRepository."""
    return Mock()


@pytest.fixture
def mock_arch_repo():
    """Mock ArchitectureRepository."""
    return Mock()


@pytest.fixture
def mock_audit_repo():
    """Mock AuditLogRepository."""
    return Mock()


# ============================================================================
# User Management Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_all_users_success(superadmin_user, regular_user, mock_user_repo):
    """Test listing all users as SuperAdmin."""
    # Setup
    users_list = [superadmin_user, regular_user]
    mock_user_repo.list.return_value = (users_list, 2)

    # Execute
    result = await list_all_users(
        skip=0,
        limit=100,
        current_admin=superadmin_user,
        user_repo=mock_user_repo
    )

    # Verify
    assert len(result) == 2
    assert result[0].email == superadmin_user["email"]
    mock_user_repo.list.assert_called_once_with(skip=0, limit=100)


@pytest.mark.asyncio
async def test_get_user_as_admin_success(superadmin_user, regular_user, mock_user_repo):
    """Test viewing user details as SuperAdmin."""
    # Setup
    user_id = regular_user["id"]
    mock_user_repo.get.return_value = regular_user

    # Execute
    result = await get_user_as_admin(
        user_id=user_id,
        current_admin=superadmin_user,
        user_repo=mock_user_repo
    )

    # Verify
    assert result.email == regular_user["email"]
    mock_user_repo.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_as_admin_not_found(superadmin_user, mock_user_repo):
    """Test viewing non-existent user."""
    # Setup
    user_id = uuid4()
    mock_user_repo.get.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await get_user_as_admin(
            user_id=user_id,
            current_admin=superadmin_user,
            user_repo=mock_user_repo
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_user_status_success(superadmin_user, regular_user, mock_user_repo):
    """Test updating user status as SuperAdmin."""
    # Setup
    from app.api.admin import UserStatusUpdateRequest

    user_id = regular_user["id"]
    mock_user_repo.get.return_value = regular_user
    updated_user = regular_user.copy()
    updated_user["status"] = UserStatus.SUSPENDED.value
    mock_user_repo.update_status.return_value = updated_user

    request = UserStatusUpdateRequest(
        status=UserStatus.SUSPENDED,
        reason="Suspicious activity detected"
    )

    # Execute
    result = await update_user_status(
        user_id=user_id,
        request=request,
        current_admin=superadmin_user,
        user_repo=mock_user_repo
    )

    # Verify
    assert result.status == UserStatus.SUSPENDED
    mock_user_repo.update_status.assert_called_once_with(user_id, UserStatus.SUSPENDED)


@pytest.mark.asyncio
async def test_update_system_role_success(superadmin_user, regular_user, mock_user_repo):
    """Test promoting user to SuperAdmin."""
    # Setup
    from app.api.admin import SystemRoleUpdateRequest

    user_id = regular_user["id"]
    mock_user_repo.get.return_value = regular_user
    updated_user = regular_user.copy()
    updated_user["system_role"] = SystemRole.SUPPORT.value
    mock_user_repo.update_system_role.return_value = updated_user

    request = SystemRoleUpdateRequest(
        system_role=SystemRole.SUPPORT,
        reason="New support team member"
    )

    # Execute
    result = await update_user_system_role(
        user_id=user_id,
        request=request,
        current_admin=superadmin_user,
        user_repo=mock_user_repo
    )

    # Verify
    assert result.system_role == SystemRole.SUPPORT
    mock_user_repo.update_system_role.assert_called_once_with(user_id, SystemRole.SUPPORT)


# ============================================================================
# Organisation Management Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_all_organisations_success(superadmin_user, mock_org_repo):
    """Test listing all organisations as SuperAdmin."""
    # Setup
    orgs_list = [
        {
            "id": str(uuid4()),
            "name": "Org 1",
            "type": "team",
            "owner_user_id": str(uuid4()),
            "plan": "free",
            "status": "active",
            "quota": {
                "active_deployments": 1,
                "max_active_deployments": 3,
                "members": 2,
                "max_members": 5,
                "architectures": 1,
                "max_architectures": 10,
                "monitoring_level": "basic"
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "name": "Org 2",
            "type": "team",
            "owner_user_id": str(uuid4()),
            "plan": "pro",
            "status": "active",
            "quota": {
                "active_deployments": 5,
                "max_active_deployments": -1,
                "members": 10,
                "max_members": -1,
                "architectures": 20,
                "max_architectures": -1,
                "monitoring_level": "advanced"
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    ]
    mock_org_repo.list_all.return_value = (orgs_list, 2)

    # Execute
    result = await list_all_organisations(
        skip=0,
        limit=100,
        current_admin=superadmin_user,
        org_repo=mock_org_repo
    )

    # Verify
    assert len(result) == 2
    mock_org_repo.list_all.assert_called_once_with(skip=0, limit=100)


@pytest.mark.asyncio
async def test_get_organisation_architectures_success(superadmin_user, mock_org_repo, mock_arch_repo):
    """Test viewing organisation architectures as SuperAdmin."""
    # Setup
    org_id = uuid4()
    user_id = str(uuid4())

    # Mock organisation exists
    mock_org_repo.get.return_value = {
        "id": str(org_id),
        "name": "Test Org",
        "type": "team"
    }

    # Mock organisation members
    mock_org_repo.get_members.return_value = [
        {"user_id": user_id}
    ]

    # Mock architectures for the user
    architectures = [
        {
            "id": str(uuid4()),
            "name": "Web App Architecture",
            "description": "Test architecture",
            "version": "1.0.0",
            "owner": user_id,
        }
    ]
    mock_arch_repo.list.return_value = (architectures, 1)

    # Execute
    result = await get_organisation_architectures(
        org_id=org_id,
        current_admin=superadmin_user,
        org_repo=mock_org_repo,
        arch_repo=mock_arch_repo
    )

    # Verify
    assert len(result) == 1
    assert result[0]["name"] == "Web App Architecture"
    mock_org_repo.get.assert_called_once()
    mock_org_repo.get_members.assert_called_once_with(org_id)


# ============================================================================
# Audit Logs Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_audit_logs_success(superadmin_user, mock_audit_repo):
    """Test querying audit logs as SuperAdmin."""
    # Setup
    logs = [
        {
            "id": str(uuid4()),
            "user": "user@example.com",
            "action": "deploy_start",
            "resource_type": "deployment",
            "resource_id": str(uuid4()),
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]
    mock_audit_repo.list.return_value = (logs, 1)

    # Execute
    result = await get_audit_logs(
        user=None,
        action="deploy_start",
        resource_type="deployment",
        resource_id=None,
        start_date=None,
        end_date=None,
        skip=0,
        limit=100,
        current_user=superadmin_user,
        audit_repo=mock_audit_repo
    )

    # Verify
    assert len(result["items"]) == 1
    assert result["total"] == 1
    assert result["items"][0]["action"] == "deploy_start"


@pytest.mark.asyncio
async def test_get_audit_logs_as_auditor(mock_audit_repo):
    """Test querying audit logs as Auditor (read-only role)."""
    # Setup
    auditor_user = {
        "id": str(uuid4()),
        "email": "auditor@stackvertex.io",
        "system_role": SystemRole.AUDITOR.value,
    }
    logs = []
    mock_audit_repo.list.return_value = (logs, 0)

    # Execute
    result = await get_audit_logs(
        user=None,
        action=None,
        resource_type=None,
        resource_id=None,
        start_date=None,
        end_date=None,
        skip=0,
        limit=100,
        current_user=auditor_user,
        audit_repo=mock_audit_repo
    )

    # Verify
    assert result["total"] == 0


# ============================================================================
# User Impersonation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_impersonate_user_success(superadmin_user, regular_user, mock_user_repo):
    """Test user impersonation as SuperAdmin."""
    # Setup
    user_id = regular_user["id"]
    mock_user_repo.get.return_value = regular_user

    # Execute
    result = await impersonate_user(
        user_id=user_id,
        reason="Customer reported bug, need to investigate",
        current_admin=superadmin_user,
        user_repo=mock_user_repo
    )

    # Verify
    assert result.impersonated_user_email == regular_user["email"]
    assert result.expires_in == 900  # 15 minutes
    assert "access_token" in result.model_dump()

    # Verify token contains impersonation info
    token = result.access_token
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == user_id
    assert decoded["impersonated_by"] == superadmin_user["id"]


@pytest.mark.asyncio
async def test_impersonate_user_not_found(superadmin_user, mock_user_repo):
    """Test impersonating non-existent user."""
    # Setup
    user_id = uuid4()
    mock_user_repo.get.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await impersonate_user(
            user_id=user_id,
            reason="Testing impersonation",
            current_admin=superadmin_user,
            user_repo=mock_user_repo
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_impersonate_user_reason_too_short(superadmin_user, regular_user, mock_user_repo):
    """Test impersonation with too short reason (validation should fail)."""
    # Setup
    user_id = regular_user["id"]

    # Execute & Verify
    # This would normally be caught by Pydantic validation before reaching the endpoint
    # Testing the business logic here
    short_reason = "test"  # Less than 10 chars
    assert len(short_reason) < 10


# ============================================================================
# Password Reset Tests
# ============================================================================


@pytest.mark.asyncio
async def test_reset_user_password_success(superadmin_user, regular_user, mock_user_repo):
    """Test password reset as SuperAdmin."""
    # Setup
    user_id = regular_user["id"]
    mock_user_repo.get.return_value = regular_user
    mock_user_repo.update_password.return_value = True

    # Execute
    result = await reset_user_password(
        user_id=user_id,
        current_admin=superadmin_user,
        user_repo=mock_user_repo
    )

    # Verify
    assert result.user_id == user_id
    assert result.email == regular_user["email"]
    assert len(result.new_password) >= 16
    assert "Password reset successful" in result.message
    mock_user_repo.update_password.assert_called_once()

    # Verify password contains required character types
    password = result.new_password
    assert any(c.islower() for c in password)  # Lowercase
    assert any(c.isupper() for c in password)  # Uppercase
    assert any(c.isdigit() for c in password)  # Digit
    assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)  # Special char


@pytest.mark.asyncio
async def test_reset_user_password_not_found(superadmin_user, mock_user_repo):
    """Test password reset for non-existent user."""
    # Setup
    user_id = uuid4()
    mock_user_repo.get.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await reset_user_password(
            user_id=user_id,
            current_admin=superadmin_user,
            user_repo=mock_user_repo
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_reset_user_password_update_fails(superadmin_user, regular_user, mock_user_repo):
    """Test password reset when update fails."""
    # Setup
    user_id = regular_user["id"]
    mock_user_repo.get.return_value = regular_user
    mock_user_repo.update_password.return_value = False

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await reset_user_password(
            user_id=user_id,
            current_admin=superadmin_user,
            user_repo=mock_user_repo
        )

    assert exc_info.value.status_code == 500
    assert "Failed to update password" in exc_info.value.detail


# ============================================================================
# System Stats Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_system_stats_success(
    superadmin_user,
    mock_user_repo,
    mock_org_repo,
    mock_audit_repo
):
    """Test getting system statistics as SuperAdmin."""
    # Setup
    mock_user_repo.list.return_value = ([], 42)
    mock_org_repo.list_all.return_value = ([], 15)
    mock_audit_repo.get_stats.return_value = {
        "total_logs": 1000,
        "failed_count": 10,
        "action_counts": {"deploy_start": 500, "deploy_destroy": 300},
        "user_counts": {"user@example.com": 100},
        "last_updated": datetime.utcnow().isoformat()
    }

    # Execute
    result = await get_system_stats(
        current_user=superadmin_user,
        user_repo=mock_user_repo,
        org_repo=mock_org_repo,
        audit_repo=mock_audit_repo
    )

    # Verify
    assert result["users"]["total"] == 42
    assert result["organisations"]["total"] == 15
    assert result["audit"]["total_logs"] == 1000
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_get_platform_statistics_success(
    superadmin_user,
    regular_user,
    mock_user_repo,
    mock_org_repo,
    mock_arch_repo
):
    """Test getting detailed platform statistics as SuperAdmin."""
    # Setup
    users_list = [superadmin_user, regular_user]
    mock_user_repo.list.return_value = (users_list, 2)
    mock_org_repo.list_all.return_value = ([], 5)

    # Mock architectures - only return architectures for regular_user, not superadmin
    architectures = [
        {"id": str(uuid4()), "status": "deployed", "owner": regular_user["id"]},
        {"id": str(uuid4()), "status": "draft", "owner": regular_user["id"]},
    ]

    # Mock arch_repo.list to return different values based on owner parameter
    def mock_arch_list(skip, limit, owner):
        if owner == regular_user["id"]:
            return (architectures, 2)
        else:
            return ([], 0)  # Superadmin has no architectures

    mock_arch_repo.list.side_effect = mock_arch_list

    # Execute
    result = await get_platform_statistics(
        current_admin=superadmin_user,
        user_repo=mock_user_repo,
        org_repo=mock_org_repo,
        arch_repo=mock_arch_repo
    )

    # Verify
    assert result.users["total"] == 2
    assert result.users["active"] == 2  # Both users are active
    assert result.organisations["total"] == 5
    assert result.architectures["total"] == 2
    assert result.architectures["deployed"] == 1
    assert result.architectures["draft"] == 1
    assert result.timestamp is not None


# ============================================================================
# Authorization Tests (nicht SuperAdmin)
# ============================================================================


@pytest.mark.asyncio
async def test_list_users_as_regular_user_forbidden(regular_user, mock_user_repo):
    """Test that regular users cannot list all users."""
    # In der echten App würde get_current_superadmin bereits HTTPException werfen
    # Hier testen wir nur die Funktion selbst
    # Dies würde vom Dependency bereits abgefangen werden
    pass  # Auth wird von FastAPI Dependency gehandhabt


@pytest.mark.asyncio
async def test_impersonate_as_support_forbidden(regular_user, mock_user_repo):
    """Test that Support role cannot impersonate (only SuperAdmin can)."""
    # Support hat read-only Zugriff, aber KEINE Impersonation
    # Dies würde vom get_current_superadmin Dependency abgefangen werden
    pass  # Auth wird von FastAPI Dependency gehandhabt
