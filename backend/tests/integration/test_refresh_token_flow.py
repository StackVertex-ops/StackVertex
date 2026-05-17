"""Integration tests for Refresh Token Pattern.

Tests the complete flow: Login -> Refresh -> Logout mit Token Rotation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.api.auth import create_refresh_token, verify_refresh_token
from app.repositories.refresh_token import RefreshTokenRepository


# Test Fixtures
@pytest.fixture
def test_dynamodb_table(mock_dynamodb_table):
    """Alias for mock_dynamodb_table."""
    return mock_dynamodb_table


@pytest.fixture
def test_user(client, test_dynamodb_table):
    """Create a test user."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"test-{uuid4()}@example.com",
            "name": "Test User",
            "password": "TestPassword123!"
        }
    )
    assert response.status_code == 201
    user_data = response.json()["user"]
    # Add password for login tests
    user_data["password"] = "TestPassword123!"
    return user_data


def test_create_and_verify_refresh_token():
    """Test creating and verifying a refresh token."""
    user_id = str(uuid4())

    # Create refresh token
    token = create_refresh_token({"sub": user_id})
    assert token is not None

    # Verify token
    payload = verify_refresh_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_verify_access_token_fails_as_refresh():
    """Test that access tokens are rejected as refresh tokens."""
    from app.api.auth import create_access_token

    user_id = str(uuid4())

    # Create access token
    access_token = create_access_token({"sub": user_id})

    # Try to verify as refresh token
    with pytest.raises(Exception) as exc:
        verify_refresh_token(access_token)

    assert "Invalid token type" in str(exc.value) or "401" in str(exc.value)


def test_login_returns_refresh_token(client, test_user):
    """Test login returns both access and refresh tokens."""
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    # Check cookies
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_endpoint_with_valid_token(client, test_user, test_dynamodb_table):
    """Test /refresh endpoint with valid refresh token."""
    # Login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )
    assert login_response.status_code == 200

    old_access_token = login_response.json()["access_token"]
    old_refresh_cookie = login_response.cookies.get("refresh_token")

    # Refresh tokens
    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200

    new_access_token = refresh_response.json()["access_token"]
    new_refresh_cookie = refresh_response.cookies.get("refresh_token")

    # Verify new tokens are different
    assert new_access_token != old_access_token
    assert new_refresh_cookie != old_refresh_cookie


def test_refresh_endpoint_without_refresh_token(client):
    """Test /refresh endpoint without refresh token returns 401."""
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert "Refresh token missing" in response.json()["detail"]


def test_token_rotation_invalidates_old_token(client, test_user, test_dynamodb_table):
    """Test that old refresh token is invalidated after rotation."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )
    old_refresh_token = login_response.cookies.get("refresh_token")

    # Refresh (rotates token)
    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200

    # Try to use old refresh token again
    client.cookies.clear()
    client.cookies.set("refresh_token", old_refresh_token)

    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert "not found or expired" in response.json()["detail"]


def test_logout_revokes_all_refresh_tokens(client, test_user, test_dynamodb_table):
    """Test logout revokes all refresh tokens."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )
    refresh_token = login_response.cookies.get("refresh_token")

    # Logout
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    # Try to refresh with old token
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token)

    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_register_returns_refresh_token(client):
    """Test register returns both access and refresh tokens."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"test-{uuid4()}@example.com",
            "name": "Test User",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 201
    data = response.json()

    # Check response
    assert "access_token" in data
    assert "user" in data

    # Check cookies
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_with_inactive_user(client, test_user, test_dynamodb_table):
    """Test refresh fails if user is inactive."""
    from app.repositories.user import UserRepository
    from uuid import UUID

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )

    # Deactivate user
    user_repo = UserRepository(table=test_dynamodb_table)
    user_repo.update(UUID(test_user["id"]), {"status": "inactive"})

    # Try to refresh
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_multiple_refresh_tokens_for_user(client, test_user, test_dynamodb_table):
    """Test user can have multiple refresh tokens (multiple devices)."""
    # Login from device 1
    login1 = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )
    token1 = login1.cookies.get("refresh_token")

    # Clear cookies and login from device 2
    client.cookies.clear()
    login2 = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "TestPassword123!"}
    )
    token2 = login2.cookies.get("refresh_token")

    # Both tokens should be different
    assert token1 != token2

    # Both should work
    client.cookies.clear()
    client.cookies.set("refresh_token", token1)
    response1 = client.post("/api/v1/auth/refresh")
    assert response1.status_code == 200

    client.cookies.clear()
    client.cookies.set("refresh_token", token2)
    response2 = client.post("/api/v1/auth/refresh")
    assert response2.status_code == 200


def test_refresh_token_expiry(test_dynamodb_table):
    """Test refresh tokens expire after 7 days."""
    from app.config import settings

    repo = RefreshTokenRepository(table=test_dynamodb_table)
    user_id = uuid4()
    token = "test-token-123"

    # Create token that expires in the past
    expires_at = datetime.utcnow() - timedelta(days=1)
    repo.create(user_id=user_id, token=token, expires_at=expires_at)

    # Get token
    result = repo.get_by_token(token)

    # Should be None (expired)
    assert result is None


def test_access_token_short_lived():
    """Test access tokens expire after 15 minutes."""
    from app.api.auth import create_access_token
    from app.config import settings
    from jose import jwt

    user_id = str(uuid4())
    token = create_access_token({"sub": user_id})

    # Decode and check expiry
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.utcfromtimestamp(exp_timestamp)  # Fix: Use utcfromtimestamp to match utcnow()

    # Should expire in ~15 minutes
    now = datetime.utcnow()
    delta = exp_datetime - now
    assert delta.total_seconds() < 16 * 60  # Less than 16 minutes
    assert delta.total_seconds() > 14 * 60  # More than 14 minutes
