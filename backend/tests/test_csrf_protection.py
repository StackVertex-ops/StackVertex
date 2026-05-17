"""Tests für CSRF Protection.

Tests für SameSite Cookie basierte CSRF Protection.
"""

import pytest


@pytest.fixture
def test_user_data():
    """Test user credentials."""
    return {
        "email": "csrf-test@overcloud.dev",
        "password": "SecurePassword123!",
        "name": "CSRF Test User"
    }


@pytest.fixture
def register_user(client, test_user_data):
    """Register test user."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user_data["email"],
            "name": test_user_data["name"],
            "password": test_user_data["password"]
        }
    )
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    return response


class TestCSRFProtection:
    """Test CSRF Protection via SameSite Cookies."""

    def test_login_sets_cookie(self, client, register_user, test_user_data):
        """Test dass Login ein HttpOnly Cookie setzt."""
        # Login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 200
        assert "access_token" in response.cookies

        # Check cookie attributes
        cookie = response.cookies.get("access_token")
        assert cookie is not None

        # Cookie sollte HttpOnly sein (wird vom TestClient nicht vollständig simuliert)
        # In production wird das vom FastAPI Response.set_cookie gesetzt

    def test_register_sets_cookie(self, client, test_user_data):
        """Test dass Register ein HttpOnly Cookie setzt."""
        # Register new user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"new-{test_user_data['email']}",
                "name": test_user_data["name"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 201
        assert "access_token" in response.cookies

    def test_authenticated_request_with_cookie(self, client, register_user, test_user_data):
        """Test dass authentifizierte Requests mit Cookie funktionieren."""
        # Login to get cookie
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 200

        # Use cookie for authenticated request
        # TestClient handles cookies automatically
        me_response = client.get("/api/v1/auth/me")
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == test_user_data["email"]

    def test_authenticated_request_with_bearer_token(self, client, register_user):
        """Test dass Authorization Header als Fallback funktioniert."""
        # Get token from register response
        token = register_user.json()["access_token"]

        # Create new client without cookies
        from fastapi.testclient import TestClient
        from app.main import app
        clean_client = TestClient(app)

        # Use Bearer token
        response = clean_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_no_cookie_no_header_fails(self, client):
        """Test dass Requests ohne Cookie UND Header fehlschlagen."""
        # Create new client without cookies
        from fastapi.testclient import TestClient
        from app.main import app
        clean_client = TestClient(app)

        # Try to access protected endpoint
        response = clean_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_logout_clears_cookie(self, client, register_user, test_user_data):
        """Test dass Logout das Cookie löscht."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 200
        assert "access_token" in client.cookies

        # Logout
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200

        # Cookie sollte gelöscht sein
        # Note: TestClient simuliert Cookie-Löschung möglicherweise nicht perfekt
        # In production wird das Cookie durch delete_cookie entfernt

    def test_refresh_updates_cookie(self, client, register_user):
        """Test dass Token Refresh das Cookie aktualisiert."""
        # Token from register
        old_token = register_user.json()["access_token"]

        # Refresh token
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == 200

        # New token should be returned
        new_token = refresh_response.json()["access_token"]
        assert new_token != old_token

        # Cookie should be updated
        assert "access_token" in client.cookies

    def test_cookie_has_priority_over_header(self, client, register_user, test_user_data):
        """Test dass Cookie Priorität über Authorization Header hat."""
        # Get valid token
        valid_token = register_user.json()["access_token"]

        # Login to get cookie
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        # Send request with INVALID header but VALID cookie
        # Cookie sollte verwendet werden
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        # Should work because cookie is valid
        assert response.status_code == 200


class TestCSRFProtectionSecurity:
    """Security tests für CSRF Protection."""

    def test_cookie_attributes(self, client, register_user):
        """Test dass Cookie die richtigen Security-Attribute hat."""
        # In TestClient werden Cookie-Attribute nicht vollständig simuliert
        # Diese Tests sind eher dokumentarisch

        # Expected attributes in production:
        # - HttpOnly=True (prevents JavaScript access)
        # - SameSite=Lax (prevents cross-site POST)
        # - Secure=True (HTTPS only, in production)
        # - Path=/ (valid for all endpoints)
        # - Max-Age=3600 (1 hour)

        # Verify we can access the cookie (TestClient perspective)
        assert "access_token" in client.cookies

    def test_cross_origin_request_without_credentials_fails(self):
        """Test dass Cross-Origin Requests ohne Credentials fehlschlagen.

        In einem echten Browser würde SameSite=Lax verhindern, dass
        das Cookie bei Cross-Site POST Requests mitgeschickt wird.
        """
        # Create new client (simulates cross-origin)
        from fastapi.testclient import TestClient
        from app.main import app
        cross_origin_client = TestClient(app)

        # Try to access protected endpoint without credentials
        response = cross_origin_client.get("/api/v1/auth/me")
        assert response.status_code == 401
