"""
IDOR Prevention Tests

Tests für Authorization Checks in User Endpoints.
"""

import pytest
from uuid import uuid4
from fastapi import status

from app.repositories.user import UserRepository


@pytest.fixture
def test_users(client):
    """Create test users with unique emails."""
    # Generate unique emails per test run
    unique_id = str(uuid4())[:8]

    # User A
    response_a = client.post("/api/v1/auth/register", json={
        "email": f"user_a_{unique_id}@example.com",
        "name": "User A",
        "password": "SecurePass123!"
    })
    assert response_a.status_code == status.HTTP_201_CREATED, f"User A registration failed: {response_a.json()}"
    user_a = response_a.json()
    token_a = user_a["access_token"]
    user_a_id = user_a["user"]["id"]

    # User B
    response_b = client.post("/api/v1/auth/register", json={
        "email": f"user_b_{unique_id}@example.com",
        "name": "User B",
        "password": "SecurePass456!"
    })
    assert response_b.status_code == status.HTTP_201_CREATED, f"User B registration failed: {response_b.json()}"
    user_b = response_b.json()
    token_b = user_b["access_token"]
    user_b_id = user_b["user"]["id"]

    # Clear cookies so tests only use tokens, not cookies
    client.cookies.clear()

    return {
        "user_a_id": user_a_id,
        "token_a": token_a,
        "user_b_id": user_b_id,
        "token_b": token_b,
    }


class TestIDORPrevention:
    """Test IDOR (Insecure Direct Object Reference) prevention."""

    def test_user_cannot_view_other_user_profile(self, client, test_users):
        """User A cannot view User B's profile."""
        response = client.get(
            f"/api/v1/users/{test_users['user_b_id']}",
            headers={"Authorization": f"Bearer {test_users['token_a']}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

    def test_user_can_view_own_profile(self, client, test_users):
        """User A can view their own profile."""
        response = client.get(
            f"/api/v1/users/{test_users['user_a_id']}",
            headers={"Authorization": f"Bearer {test_users['token_a']}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_users['user_a_id']
        # Email has unique_id suffix, just check it starts correctly
        assert data["email"].startswith("user_a_")

    def test_user_cannot_update_other_user_profile(self, client, test_users):
        """User A cannot update User B's profile."""
        response = client.patch(
            f"/api/v1/users/{test_users['user_b_id']}",
            headers={"Authorization": f"Bearer {test_users['token_a']}"},
            json={"name": "Hacked Name"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_update_own_profile(self, client, test_users):
        """User A can update their own profile."""
        response = client.patch(
            f"/api/v1/users/{test_users['user_a_id']}",
            headers={"Authorization": f"Bearer {test_users['token_a']}"},
            json={"name": "Updated Name"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_user_cannot_delete_other_user(self, client, test_users):
        """User A cannot delete User B."""
        response = client.delete(
            f"/api/v1/users/{test_users['user_b_id']}",
            headers={"Authorization": f"Bearer {test_users['token_a']}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_view_other_user_organisations(self, client, test_users):
        """User A cannot view User B's organisations."""
        response = client.get(
            f"/api/v1/users/{test_users['user_b_id']}/organisations",
            headers={"Authorization": f"Bearer {test_users['token_a']}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_view_own_organisations(self, client, test_users):
        """User A can view their own organisations."""
        response = client.get(
            f"/api/v1/users/{test_users['user_a_id']}/organisations",
            headers={"Authorization": f"Bearer {test_users['token_a']}"}
        )

        assert response.status_code == status.HTTP_200_OK
        # Should return list (possibly empty)
        assert isinstance(response.json(), list)


class TestSuperAdminAccess:
    """Test SuperAdmin can access all resources."""

    @pytest.fixture
    def superadmin_user(self, client, mock_dynamodb_table):
        """Create superadmin user."""
        # Register normal user first
        response = client.post("/api/v1/auth/register", json={
            "email": "admin@example.com",
            "name": "Admin User",
            "password": "AdminPass123!"
        })
        assert response.status_code == 201
        user_data = response.json()

        # Manually upgrade to superadmin in DB
        user_repo = UserRepository(table=mock_dynamodb_table)
        user_repo.update(user_data["user"]["id"], {"system_role": "superadmin"})

        # Login again to get token with updated role
        login_response = client.post("/api/v1/auth/login", data={
            "username": "admin@example.com",
            "password": "AdminPass123!"
        })
        assert login_response.status_code == 200

        # Clear cookies so tests only use token
        client.cookies.clear()

        return login_response.json()

    def test_superadmin_can_view_any_user(self, client, test_users, superadmin_user):
        """SuperAdmin can view any user's profile."""
        response = client.get(
            f"/api/v1/users/{test_users['user_a_id']}",
            headers={"Authorization": f"Bearer {superadmin_user['access_token']}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_users['user_a_id']

    def test_superadmin_can_update_any_user(self, client, test_users, superadmin_user):
        """SuperAdmin can update any user's profile."""
        response = client.patch(
            f"/api/v1/users/{test_users['user_a_id']}",
            headers={"Authorization": f"Bearer {superadmin_user['access_token']}"},
            json={"name": "Admin Changed Name"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Admin Changed Name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
