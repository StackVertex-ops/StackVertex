"""Integration tests für Authentication API.

Tests mit vollständigem HTTP Request/Response Cycle.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


@pytest.fixture
def client(mock_dynamodb_table, mock_s3_bucket):
    """TestClient mit gemockten DynamoDB & S3."""
    # Override dependencies
    from app.db.dynamodb import get_dynamodb_table
    from app.db.s3_storage import get_s3_storage, S3Storage

    app.dependency_overrides[get_dynamodb_table] = lambda: mock_dynamodb_table
    app.dependency_overrides[get_s3_storage] = lambda: S3Storage(bucket_name="overcloud-test-bucket")

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestAuthRegister:
    """Tests für POST /api/v1/auth/register."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201  # Created
        data = response.json()

        # Token returned
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # User info returned
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["status"] == "active"
        assert "personal_org_id" in data["user"]

        # Password not returned
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

    def test_register_duplicate_email(self, client):
        """Test registration with existing email fails."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "name": "First User",
                "password": "password123"
            }
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "name": "Second User",
                "password": "password456"
            }
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "name": "User",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client):
        """Test registration with too short password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "name": "User",
                "password": "short"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com"
                # Missing name & password
            }
        )

        assert response.status_code == 422


class TestAuthLogin:
    """Tests für POST /api/v1/auth/login."""

    def test_login_success(self, client):
        """Test successful login with email/password."""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "loginuser@example.com",
                "name": "Login User",
                "password": "mypassword123"
            }
        )

        # Login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser@example.com",  # OAuth2PasswordRequestForm uses 'username'
                "password": "mypassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "loginuser@example.com"

    def test_login_wrong_password(self, client):
        """Test login with incorrect password."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "name": "User",
                "password": "correctpassword"
            }
        )

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "ghost@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_login_case_insensitive_email(self, client):
        """Test login with different case email."""
        # Register with lowercase
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "name": "User",
                "password": "password123"
            }
        )

        # Login with uppercase
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "USER@EXAMPLE.COM",
                "password": "password123"
            }
        )

        assert response.status_code == 200


class TestAuthMe:
    """Tests für GET /api/v1/auth/me."""

    def test_get_me_authenticated(self, client):
        """Test getting current user info when authenticated."""
        # Register & login
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "name": "Me User",
                "password": "password123"
            }
        )
        token = response.json()["access_token"]

        # Get /me
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "me@example.com"
        assert data["name"] == "Me User"
        assert "password" not in data

    def test_get_me_unauthenticated(self, client):
        """Test /me without authentication fails."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Test /me with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"}
        )

        assert response.status_code == 401


class TestAuthRefresh:
    """Tests für POST /api/v1/auth/refresh."""

    def test_refresh_token(self, client):
        """Test refreshing access token."""
        # Register user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "name": "Refresh User",
                "password": "password123"
            }
        )
        old_token = response.json()["access_token"]

        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Token is returned (might be same or different depending on timing)
        assert len(data["access_token"]) > 0

    def test_refresh_unauthenticated(self, client):
        """Test refresh without authentication fails."""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401


class TestAuthWorkflow:
    """End-to-end authentication workflow tests."""

    def test_full_auth_workflow(self, client):
        """Test complete flow: register → login → /me → refresh."""
        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "workflow@example.com",
                "name": "Workflow User",
                "password": "securepass123"
            }
        )
        assert register_response.status_code == 201
        register_token = register_response.json()["access_token"]
        user_id = register_response.json()["user"]["id"]

        # 2. Login (separate session)
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "workflow@example.com",
                "password": "securepass123"
            }
        )
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # 3. /me with login token
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["id"] == user_id

        # 4. Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {login_token}"}
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]

        # 5. /me with refreshed token
        me_response_2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert me_response_2.status_code == 200
        assert me_response_2.json()["email"] == "workflow@example.com"

    def test_token_works_across_endpoints(self, client):
        """Test that JWT token works for different protected endpoints."""
        # Register
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "crossendpoint@example.com",
                "name": "Cross User",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        token = response.json()["access_token"]
        user_id = response.json()["user"]["id"]

        # Access /me
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200

        # Access /users/{user_id}
        user_response = client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert user_response.status_code == 200
        assert user_response.json()["email"] == "crossendpoint@example.com"
