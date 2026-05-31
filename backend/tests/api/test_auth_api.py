"""Auth API Endpoint Tests.

Tests für User Registration, Login, Token Management.
"""

import pytest
from fastapi import status


# ============================================================================
# POST /auth/register - User Registration
# ============================================================================


def test_register_success(client):
    """Test: POST /auth/register - Erfolgreiche User Registrierung."""
    payload = {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "SecurePass123!",
        "auth_provider": "email"
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"
    assert data["user"]["status"] == "active"
    assert "password" not in data["user"]  # Password sollte nie returned werden
    # Refresh token is set as HttpOnly cookie, not in response body
    assert "refresh_token" in response.cookies or "Set-Cookie" in response.headers


def test_register_duplicate_email(client, user_repository):
    """Test: POST /auth/register - Fehler bei bereits existierender Email."""
    # Create first user
    user_repository.create(
        email="duplicate@example.com",
        name="Existing User",
        password="SecurePass123!"
    )

    # Try to register with same email
    payload = {
        "email": "duplicate@example.com",
        "name": "Another User",
        "password": "AnotherPass123!"
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already" in response.json()["detail"].lower()


def test_register_weak_password(client):
    """Test: POST /auth/register - Validation Error bei schwachem Passwort."""
    payload = {
        "email": "user@example.com",
        "name": "User",
        "password": "weak"  # Zu kurz, keine Complexity
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_invalid_email(client):
    """Test: POST /auth/register - Validation Error bei ungültiger Email."""
    payload = {
        "email": "not-an-email",
        "name": "User",
        "password": "SecurePass123!"
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# POST /auth/login - User Login
# ============================================================================


def test_login_success(client, user_repository):
    """Test: POST /auth/login - Erfolgreicher Login (returns access token)."""
    # Create user
    user_repository.create(
        email="loginuser@example.com",
        name="Login User",
        password="SecurePass123!"
    )

    # Login (OAuth2PasswordRequestForm format: username + password)
    payload = {
        "username": "loginuser@example.com",  # OAuth2 uses 'username' field
        "password": "SecurePass123!"
    }

    response = client.post(
        "/api/v1/auth/login",
        data=payload,  # OAuth2 uses form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "loginuser@example.com"
    # Refresh token is HttpOnly cookie
    assert "refresh_token" in response.cookies or "Set-Cookie" in response.headers


def test_login_wrong_password(client, user_repository):
    """Test: POST /auth/login - Fehler bei falschem Passwort."""
    # Create user
    user_repository.create(
        email="user@example.com",
        name="User",
        password="CorrectPass123!"
    )

    # Try login with wrong password
    payload = {
        "username": "user@example.com",
        "password": "WrongPass123!"
    }

    response = client.post(
        "/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()


def test_login_user_not_found(client):
    """Test: POST /auth/login - Fehler wenn User nicht existiert."""
    payload = {
        "username": "nonexistent@example.com",
        "password": "SomePass123!"
    }

    response = client.post(
        "/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_inactive_user(client, user_repository):
    """Test: POST /auth/login - Fehler wenn User inaktiv ist."""
    # Create user
    created = user_repository.create(
        email="inactive@example.com",
        name="Inactive User",
        password="SecurePass123!"
    )

    # Manually set user to inactive
    from uuid import UUID
    user_repository.update(
        UUID(created["id"]),
        {"status": "inactive"}
    )

    # Try login
    payload = {
        "username": "inactive@example.com",
        "password": "SecurePass123!"
    }

    response = client.post(
        "/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Inactive user returns 401 (failed authentication), not 403
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# POST /auth/refresh - Refresh Access Token
# ============================================================================


def test_refresh_token_success(client, user_repository):
    """Test: POST /auth/refresh - Erfolgreiche Token Refresh."""
    # Create user and login
    user_repository.create(
        email="refreshuser@example.com",
        name="Refresh User",
        password="SecurePass123!"
    )

    # Login to get refresh token (in cookie)
    login_payload = {
        "username": "refreshuser@example.com",
        "password": "SecurePass123!"
    }
    login_response = client.post(
        "/api/v1/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Extract refresh_token from cookie
    refresh_token = login_response.cookies.get("refresh_token")
    if not refresh_token:
        # Fallback: Try to extract from Set-Cookie header
        from app.api.auth import create_refresh_token
        # For testing, we'll create a manual refresh token
        user = user_repository.get_by_email("refreshuser@example.com")
        refresh_token = create_refresh_token({"sub": user["id"]})

    # Use refresh token to get new access token
    refresh_payload = {
        "refresh_token": refresh_token
    }

    response = client.post("/api/v1/auth/refresh", json=refresh_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client):
    """Test: POST /auth/refresh - Fehler bei ungültigem Refresh Token."""
    payload = {
        "refresh_token": "invalid.token.here"
    }

    response = client.post("/api/v1/auth/refresh", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_token_expired(client):
    """Test: POST /auth/refresh - Fehler bei abgelaufenem Refresh Token."""
    # Create an expired token
    from datetime import datetime, timedelta
    from jose import jwt
    from app.config import settings

    expired_token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            "type": "refresh"
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    payload = {
        "refresh_token": expired_token
    }

    response = client.post("/api/v1/auth/refresh", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# GET /auth/me - Get Current User
# ============================================================================


def test_get_current_user_success(user_client, mock_regular_user):
    """Test: GET /auth/me - Hole aktuellen User mit gültigem Token."""
    response = user_client.get("/api/v1/auth/me")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == mock_regular_user["email"]
    assert "id" in data
    assert "organisations" in data  # Should include user's organisations


def test_get_current_user_unauthorized(client):
    """Test: GET /auth/me - Unauthorized ohne Token."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
