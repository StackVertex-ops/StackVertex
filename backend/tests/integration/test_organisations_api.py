"""Integration tests für Organisations API.

Tests mit Role-Based Access Control und Multi-Tenancy.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(mock_dynamodb_table, mock_s3_bucket):
    """TestClient mit gemockten Dependencies."""
    from app.db.dynamodb import get_dynamodb_table
    from app.db.s3_storage import get_s3_storage, S3Storage

    app.dependency_overrides[get_dynamodb_table] = lambda: mock_dynamodb_table
    app.dependency_overrides[get_s3_storage] = lambda: S3Storage(bucket_name="stackvertex-test-bucket")

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def owner_user(client):
    """Create owner user, return (token, user_id, personal_org_id)."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "name": "Owner User",
            "password": "SecurePass123!"
        }
    )
    data = response.json()
    return data["access_token"], data["user"]["id"], data["user"]["personal_org_id"]


@pytest.fixture
def member_user(client):
    """Create member user, return (token, user_id)."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "name": "Member User",
            "password": "SecurePass123!"
        }
    )
    data = response.json()
    return data["access_token"], data["user"]["id"]


class TestOrganisationsCreate:
    """Tests für POST /api/v1/organisations."""

    def test_create_organisation(self, client, owner_user):
        """Test creating a team organisation."""
        token, _, _ = owner_user

        response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Test Team Org"
        assert data["type"] == "team"
        assert data["plan"] == "free"
        assert data["status"] == "active"
        assert "id" in data

    def test_create_organisation_unauthenticated(self, client):
        """Test creating organisation without authentication."""
        response = client.post(
            "/api/v1/organisations",
            json={
                "name": "Org",
                "organisation_type": "team"
            }
        )

        assert response.status_code == 401


class TestOrganisationsGet:
    """Tests für GET /api/v1/organisations/{org_id}."""

    def test_get_own_organisation(self, client, owner_user):
        """Test getting organisation where user is member."""
        token, _, personal_org_id = owner_user

        response = client.get(
            f"/api/v1/organisations/{personal_org_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == personal_org_id
        assert data["type"] == "personal"

    def test_get_organisation_not_member(self, client, owner_user, member_user):
        """Test getting organisation where user is not a member."""
        owner_token, _, personal_org_id = owner_user
        member_token, _ = member_user

        # Member tries to access owner's personal org
        response = client.get(
            f"/api/v1/organisations/{personal_org_id}",
            headers={"Authorization": f"Bearer {member_token}"}
        )

        assert response.status_code == 403


class TestOrganisationsUpdate:
    """Tests für PATCH /api/v1/organisations/{org_id}."""

    def test_update_organisation_as_owner(self, client, owner_user):
        """Test updating organisation as owner."""
        token, _, personal_org_id = owner_user

        response = client.patch(
            f"/api/v1/organisations/{personal_org_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Org Name"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Org Name"

    def test_update_organisation_as_member_forbidden(self, client, owner_user, member_user):
        """Test that members cannot update organisation."""
        owner_token, _, org_id = owner_user
        member_token, member_id = member_user

        # Add member to org
        client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "member@example.com",
                "role": "member"
            }
        )

        # Member tries to update
        response = client.patch(
            f"/api/v1/organisations/{org_id}",
            headers={"Authorization": f"Bearer {member_token}"},
            json={"name": "Hacked Name"}
        )

        assert response.status_code == 403


class TestOrganisationMembers:
    """Tests für member management endpoints."""

    def test_add_member_as_owner(self, client, owner_user):
        """Test adding member to organisation as owner."""
        owner_token, _, _ = owner_user

        # Create a fresh member user for this test
        member_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "fresh_member@example.com",
                "name": "Fresh Member",
                "password": "SecurePass123!"
            }
        )
        member_id = member_response.json()["user"]["id"]

        # Clear cookies after member creation
        client.cookies.clear()

        # Create team org (personal org has max_members=1)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )
        org_id = create_response.json()["id"]

        # Upgrade to PRO plan to allow multiple members (FREE has max_members=1)
        client.post(
            f"/api/v1/organisations/{org_id}/upgrade-plan",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"new_plan": "pro"}
        )

        # Clear cookies to ensure clean state
        client.cookies.clear()

        response = client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "fresh_member@example.com",
                "role": "member"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["user_id"] == member_id
        assert data["role"] == "member"

    def test_add_member_as_member_forbidden(self, client, owner_user, member_user):
        """Test that members cannot add other members."""
        owner_token, _, _ = owner_user
        member_token, member_id = member_user

        # Create team org (personal org has max_members=1)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )
        org_id = create_response.json()["id"]

        # Upgrade to PRO plan to allow multiple members (FREE has max_members=1)
        client.post(
            f"/api/v1/organisations/{org_id}/upgrade-plan",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"new_plan": "pro"}
        )

        # Add first member
        client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "member@example.com",
                "role": "member"
            }
        )

        # Create third user
        response3 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user3@example.com",
                "name": "User 3",
                "password": "SecurePass123!"
            }
        )
        user3_id = response3.json()["user"]["id"]

        # Member tries to add user3
        response = client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {member_token}"},
            json={
                "email": "user3@example.com",
                "role": "member"
            }
        )

        assert response.status_code == 403

    def test_list_members(self, client, owner_user):
        """Test listing organisation members."""
        token, user_id, org_id = owner_user

        response = client.get(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Response is list, not dict with "items"
        assert isinstance(data, list)
        assert len(data) >= 1  # At least owner

        # Owner should be in members
        owner_members = [m for m in data if m["user_id"] == user_id]
        assert len(owner_members) == 1
        assert owner_members[0]["role"] == "owner"

    def test_remove_member_as_owner(self, client, owner_user):
        """Test removing member as owner."""
        owner_token, _, _ = owner_user

        # Create a fresh member user for this test
        member_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "removable_member@example.com",
                "name": "Removable Member",
                "password": "SecurePass123!"
            }
        )
        member_id = member_response.json()["user"]["id"]

        # Clear cookies
        client.cookies.clear()

        # Create team org (personal org has max_members=1)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )
        org_id = create_response.json()["id"]

        # Upgrade to PRO plan to allow multiple members (FREE has max_members=1)
        client.post(
            f"/api/v1/organisations/{org_id}/upgrade-plan",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"new_plan": "pro"}
        )

        # Clear cookies
        client.cookies.clear()

        # Add member
        client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "removable_member@example.com",
                "role": "member"
            }
        )

        # Clear cookies
        client.cookies.clear()

        # Remove member
        response = client.delete(
            f"/api/v1/organisations/{org_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 204

    def test_update_member_role(self, client, owner_user):
        """Test updating member role."""
        owner_token, _, _ = owner_user

        # Create a fresh member user for this test
        member_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "promotable_member@example.com",
                "name": "Promotable Member",
                "password": "SecurePass123!"
            }
        )
        member_id = member_response.json()["user"]["id"]

        # Clear cookies
        client.cookies.clear()

        # Create team org (personal org has max_members=1)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )
        org_id = create_response.json()["id"]

        # Upgrade to PRO plan to allow multiple members (FREE has max_members=1)
        client.post(
            f"/api/v1/organisations/{org_id}/upgrade-plan",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"new_plan": "pro"}
        )

        # Clear cookies
        client.cookies.clear()

        # Add member
        client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "promotable_member@example.com",
                "role": "member"
            }
        )

        # Clear cookies
        client.cookies.clear()

        # Promote to admin
        response = client.patch(
            f"/api/v1/organisations/{org_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "admin"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["role"] == "admin"


class TestOrganisationQuota:
    """Tests für quota management."""

    def test_get_quota(self, client, owner_user):
        """Test getting organisation quota."""
        token, _, org_id = owner_user

        response = client.get(
            f"/api/v1/organisations/{org_id}/quota",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "active_deployments" in data
        assert "max_active_deployments" in data
        assert "members" in data
        assert "max_members" in data
        assert "architectures" in data
        assert "max_architectures" in data
        assert "monitoring_level" in data

    @pytest.mark.skip(reason="Endpoint GET /{org_id}/quota/check/{quota_type} not implemented yet")
    def test_quota_check_within_limit(self, client, owner_user):
        """Test quota check when within limit."""
        token, _, org_id = owner_user

        response = client.get(
            f"/api/v1/organisations/{org_id}/quota/check/active_deployments",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["can_proceed"] is True
        assert "current" in data
        assert "max_allowed" in data


class TestOrganisationAWSCredentials:
    """Tests für AWS credentials management."""

    def test_update_aws_credentials_as_owner(self, client, owner_user):
        """Test updating AWS credentials as owner."""
        token, _, org_id = owner_user

        response = client.post(
            f"/api/v1/organisations/{org_id}/aws-credentials",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "aws_role_arn": "arn:aws:iam::123456789012:role/StackVertexRole"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["connected"] is True
        assert data["aws_account_id"] == "123456789012"

    def test_update_aws_credentials_as_member_forbidden(self, client, owner_user):
        """Test that members cannot update AWS credentials."""
        owner_token, _, _ = owner_user

        # Create a fresh member user for this test
        member_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "aws_test_member@example.com",
                "name": "AWS Test Member",
                "password": "SecurePass123!"
            }
        )
        member_token = member_response.json()["access_token"]

        # Clear cookies
        client.cookies.clear()

        # Create team org (personal org has max_members=1)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )
        org_id = create_response.json()["id"]

        # Upgrade to PRO plan to allow multiple members (FREE has max_members=1)
        client.post(
            f"/api/v1/organisations/{org_id}/upgrade-plan",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"new_plan": "pro"}
        )

        # Clear cookies
        client.cookies.clear()

        # Add member
        client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "aws_test_member@example.com",
                "role": "member"
            }
        )

        # Clear cookies so we only use member_token
        client.cookies.clear()

        # Member tries to update AWS credentials
        response = client.post(
            f"/api/v1/organisations/{org_id}/aws-credentials",
            headers={"Authorization": f"Bearer {member_token}"},
            json={
                "aws_role_arn": "arn:aws:iam::999999999999:role/HackedRole"
            }
        )

        assert response.status_code == 403


class TestOrganisationDelete:
    """Tests für DELETE /api/v1/organisations/{org_id}."""

    def test_delete_organisation_as_owner(self, client, owner_user):
        """Test deleting organisation as owner."""
        token, _, _ = owner_user

        # Create a team org (can't delete personal org)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Delete Me Org",
                "organisation_type": "team"
            }
        )
        org_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/organisations/{org_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(
            f"/api/v1/organisations/{org_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert get_response.status_code == 404

    def test_delete_organisation_as_member_forbidden(self, client, owner_user):
        """Test that members cannot delete organisation."""
        owner_token, _, _ = owner_user

        # Create a fresh admin user for this test
        admin_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "delete_test_admin@example.com",
                "name": "Delete Test Admin",
                "password": "SecurePass123!"
            }
        )
        admin_token = admin_response.json()["access_token"]

        # Clear cookies
        client.cookies.clear()

        # Create team org (personal org has max_members=1)
        create_response = client.post(
            "/api/v1/organisations",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Team Org",
                "organisation_type": "team",
                "plan": "free"
            }
        )
        org_id = create_response.json()["id"]

        # Upgrade to PRO plan to allow multiple members (FREE has max_members=1)
        client.post(
            f"/api/v1/organisations/{org_id}/upgrade-plan",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"new_plan": "pro"}
        )

        # Clear cookies
        client.cookies.clear()

        # Add admin member
        client.post(
            f"/api/v1/organisations/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": "delete_test_admin@example.com",
                "role": "admin"  # Even admin can't delete
            }
        )

        # Clear cookies so we only use admin_token
        client.cookies.clear()

        # Admin tries to delete (should fail - only owner can delete)
        response = client.delete(
            f"/api/v1/organisations/{org_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 403
