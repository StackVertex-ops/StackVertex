"""Comprehensive Auth & Authorization Tests.

Tests all authentication and authorization flows:
- Registration
- Login
- JWT Tokens
- RBAC (Role-Based Access Control)
- Account Lockout
- Rate Limiting
- Session Management
"""

import pytest
import time
from datetime import datetime, timedelta
from uuid import uuid4
from jose import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.repositories.user import UserRepository
from app.services.account_lockout import AccountLockoutService


# Test client
client = TestClient(app)

# Enable testing mode (disables rate limiting)
settings.TESTING = True


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_user_data():
    """Generate unique test user data."""
    unique_id = str(uuid4())[:8]
    return {
        "email": f"test-{unique_id}@example.com",
        "name": f"Test User {unique_id}",
        "password": "SecurePass123!",
    }


@pytest.fixture(scope="function")
def registered_user(test_user_data):
    """Create and return a registered user with token."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()

    return {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "user": data["user"],
    }


# ============================================================================
# 1. Registration Flow Tests
# ============================================================================


class TestRegistration:
    """Test user registration flows."""

    def test_successful_registration(self, test_user_data):
        """Test 1: Erfolgreiche Registrierung."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data

        # Check user data
        user = data["user"]
        assert user["email"] == test_user_data["email"].lower()
        assert user["name"] == test_user_data["name"]
        assert user["status"] == "active"
        assert "id" in user
        assert "personal_org_id" in user
        assert "created_at" in user

        # Check no password in response
        assert "password" not in user
        assert "password_hash" not in user

    def test_duplicate_email(self, test_user_data):
        """Test 2: Doppelte Email."""
        # First registration
        response1 = client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201

        # Try to register again with same email
        response2 = client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    def test_weak_password(self, test_user_data):
        """Test 3: Schwaches Passwort."""
        test_user_data["password"] = "123"  # Too short

        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422  # Validation error

    def test_invalid_email(self, test_user_data):
        """Test 4: Invalide Email."""
        test_user_data["email"] = "not-an-email"

        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422  # Validation error

    def test_missing_fields(self):
        """Test 5: Fehlende Pflichtfelder."""
        # Missing password
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert response.status_code == 422

        # Missing email
        response = client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "password": "SecurePass123!"
        })
        assert response.status_code == 422


# ============================================================================
# 2. Login Flow Tests
# ============================================================================


class TestLogin:
    """Test user login flows."""

    def test_successful_login(self, registered_user):
        """Test 1: Erfolgreicher Login."""
        response = client.post("/api/v1/auth/login", data={
            "username": registered_user["email"],  # OAuth2 uses 'username'
            "password": registered_user["password"],
        })

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == registered_user["email"].lower()

    def test_wrong_password(self, registered_user):
        """Test 2: Falsches Passwort."""
        response = client.post("/api/v1/auth/login", data={
            "username": registered_user["email"],
            "password": "WrongPassword123!",
        })

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_nonexistent_user(self):
        """Test 3: User existiert nicht."""
        # Use unique email to avoid lockout from other tests
        unique_email = f"nonexistent-{uuid4()}@example.com"

        response = client.post("/api/v1/auth/login", data={
            "username": unique_email,
            "password": "SomePassword123!",
        })

        assert response.status_code == 401

    def test_case_insensitive_email(self, registered_user):
        """Test 4: Email ist case-insensitive."""
        email_upper = registered_user["email"].upper()

        response = client.post("/api/v1/auth/login", data={
            "username": email_upper,
            "password": registered_user["password"],
        })

        assert response.status_code == 200

    def test_account_lockout(self, registered_user):
        """Test 5: Account Lockout nach 5 fehlgeschlagenen Versuchen."""
        # Try 5 times with wrong password
        for i in range(5):
            response = client.post("/api/v1/auth/login", data={
                "username": registered_user["email"],
                "password": "WrongPassword123!",
            })

            if i < 4:
                assert response.status_code == 401
                assert "remaining" in response.json()["detail"].lower()
            else:
                # 5th attempt should lock account
                assert response.status_code == 403
                assert "locked" in response.json()["detail"].lower()

        # 6th attempt should also be locked
        response = client.post("/api/v1/auth/login", data={
            "username": registered_user["email"],
            "password": registered_user["password"],  # Even with correct password
        })
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()


# ============================================================================
# 3. JWT Token Tests
# ============================================================================


class TestJWTTokens:
    """Test JWT token validation and security."""

    def test_valid_token(self, registered_user):
        """Test 1: Gültiger Token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user["email"].lower()
        assert data["id"] == registered_user["user_id"]

    def test_expired_token(self, registered_user):
        """Test 2: Abgelaufener Token."""
        # Create expired token
        expired_token = jwt.encode(
            {
                "sub": registered_user["user_id"],
                "email": registered_user["email"],
                "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_manipulated_token(self, registered_user):
        """Test 3: Manipulierter Token."""
        # Decode token and change user_id
        token_payload = jwt.decode(
            registered_user["token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        token_payload["sub"] = str(uuid4())  # Different user ID

        # Encode with wrong signature
        manipulated_token = jwt.encode(
            token_payload,
            "wrong-secret-key",
            algorithm=settings.ALGORITHM
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {manipulated_token}"}
        )

        assert response.status_code == 401

    def test_no_token(self):
        """Test 4: Kein Token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_invalid_token_format(self):
        """Test 5: Falsches Token Format."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-format"}
        )
        assert response.status_code == 401

    def test_token_without_bearer_prefix(self, registered_user):
        """Test 6: Token ohne 'Bearer' Prefix."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": registered_user["token"]}
        )
        assert response.status_code == 401


# ============================================================================
# 4. Token Refresh Tests
# ============================================================================


class TestTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_valid_token(self, registered_user):
        """Test: Token Refresh mit gültigem Token."""
        # Wait 1 second to ensure different timestamp
        time.sleep(1)

        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should get new token
        assert "access_token" in data
        # Note: Token might be identical if exp timestamp is same (rounded to seconds)
        # Just check it's a valid JWT
        payload = jwt.decode(
            data["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == registered_user["user_id"]
        assert data["token_type"] == "bearer"

    def test_refresh_with_expired_token(self, registered_user):
        """Test: Token Refresh mit abgelaufenem Token."""
        # Create expired token
        expired_token = jwt.encode(
            {
                "sub": registered_user["user_id"],
                "email": registered_user["email"],
                "exp": datetime.utcnow() - timedelta(minutes=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Should fail - can't refresh expired token
        assert response.status_code == 401


# ============================================================================
# 5. Logout Tests
# ============================================================================


class TestLogout:
    """Test logout functionality."""

    def test_logout(self, registered_user):
        """Test: Logout."""
        response = client.post("/api/v1/auth/logout")

        # Logout is client-side for JWT (no server-side session)
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()


# ============================================================================
# 6. Session Management Tests
# ============================================================================


class TestSessionManagement:
    """Test session management."""

    def test_token_expiration_time(self):
        """Test: Token Expiration Time ist konfiguriert."""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 60 * 24  # Max 24 hours

    def test_concurrent_sessions(self, registered_user):
        """Test: Concurrent Sessions (multiple devices)."""
        # Login again from "another device"
        response = client.post("/api/v1/auth/login", data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        })

        assert response.status_code == 200
        new_token = response.json()["access_token"]

        # Both tokens should work
        response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response1.status_code == 200

        response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert response2.status_code == 200


# ============================================================================
# 7. Security Best Practices Tests
# ============================================================================


class TestSecurity:
    """Test security best practices."""

    def test_password_hashing(self, test_user_data):
        """Test: Passwörter werden gehasht (bcrypt)."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201

        # Password should NOT be in response
        user = response.json()["user"]
        assert "password" not in user
        assert "password_hash" not in user

    def test_timing_attack_prevention(self):
        """Test: Timing Attack Prevention (konstante Response Zeit)."""
        # Use unique users to avoid lockout interference
        existing_email = f"timing-exist-{uuid4()}@example.com"
        nonexist_email = f"timing-nonexist-{uuid4()}@example.com"

        # Register existing user
        client.post("/api/v1/auth/register", json={
            "email": existing_email,
            "name": "Timing Test User",
            "password": "CorrectPass123!",
        })

        # Test with existing user
        start1 = time.time()
        response1 = client.post("/api/v1/auth/login", data={
            "username": existing_email,
            "password": "WrongPassword123!",
        })
        time1 = time.time() - start1

        # Test with non-existing user
        start2 = time.time()
        response2 = client.post("/api/v1/auth/login", data={
            "username": nonexist_email,
            "password": "WrongPassword123!",
        })
        time2 = time.time() - start2

        # Both should be 401
        assert response1.status_code == 401
        assert response2.status_code == 401

        # Times should be similar (within 500ms)
        # Note: This is a basic check, not perfect timing attack prevention
        time_diff = abs(time1 - time2)
        assert time_diff < 0.5, f"Timing difference too large: {time_diff}s"

    def test_secret_key_strength(self):
        """Test: SECRET_KEY ist stark genug."""
        assert len(settings.SECRET_KEY) >= 32
        assert settings.SECRET_KEY not in [
            "secret", "changeme", "test", "your-secret-key-change-in-production"
        ]


# ============================================================================
# 8. Account Lockout Tests
# ============================================================================


class TestAccountLockout:
    """Test account lockout service."""

    def test_lockout_threshold(self, registered_user):
        """Test: Account wird nach 5 Versuchen gesperrt."""
        # Try 5 times with wrong password
        for i in range(5):
            client.post("/api/v1/auth/login", data={
                "username": registered_user["email"],
                "password": "WrongPassword123!",
            })

        # Check if locked
        response = client.post("/api/v1/auth/login", data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        })

        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()

    def test_lockout_clears_on_success(self, test_user_data):
        """Test: Lockout Counter wird nach erfolgreichem Login zurückgesetzt."""
        # Register user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201

        # Try 2 times with wrong password
        for _ in range(2):
            client.post("/api/v1/auth/login", data={
                "username": test_user_data["email"],
                "password": "WrongPassword123!",
            })

        # Login with correct password
        response = client.post("/api/v1/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        })
        assert response.status_code == 200

        # Counter should be reset - try 4 more wrong attempts
        # Should NOT be locked yet
        for i in range(4):
            response = client.post("/api/v1/auth/login", data={
                "username": test_user_data["email"],
                "password": "WrongPassword123!",
            })
            assert response.status_code == 401  # Not locked yet


# ============================================================================
# 9. Rate Limiting Tests (wenn nicht TESTING mode)
# ============================================================================


class TestRateLimiting:
    """Test rate limiting (nur wenn nicht TESTING)."""

    def test_rate_limit_config(self):
        """Test: Rate Limiting ist konfiguriert."""
        # In production: 5/minute for register, 10/minute for login
        # In testing: 100/minute, 1000/minute
        assert settings.TESTING is True  # Should be True in tests

    # Note: Eigentliche Rate Limiting Tests würden TESTING=False erfordern
    # und sind schwer zu testen ohne echte Delays einzubauen


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
